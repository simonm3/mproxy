import subprocess
from multiprocessing.managers import BaseManager
import multiprocessing as mp
import shlex
import requests
from requests.adapters import HTTPAdapter
from aws2 import aws, Spot
from threading import Thread
import os
import pandas as pd
from urllib.parse import urlparse
from .retry import Retry
from . import ua
import logging

log = logging.getLogger(__name__)

# fixed port as dedicated server instance for each proxy so no need to change it.
ip2url = lambda ip: f"http://{ip}:8888"
url2ip = lambda url: urlparse(url).netloc.split(":")[0]

HERE = os.path.dirname(__file__)

# random names are easier to read than numbers
names = pd.read_csv(f"{HERE}/babies-first-names-top-100-girls.csv").FirstForename

# params for mproxy server. note authkey is mandatory for different processes.
connect_params = dict(address=("127.0.0.1", 4006), authkey=b"aaa")


def subprocess_run(cmd, **kwargs):
    """ run command and return results
    :param cmd: system command
    :return:  results
    """
    kwargs.setdefault("check", True)
    kwargs.setdefault("capture_output", True)
    cmd = shlex.split(cmd)
    r = subprocess.run(cmd, **kwargs)
    return r


class Manager(BaseManager):
    pass


class Mproxy:
    """ manages a rotating set of http proxy servers. has no fixed state as it refreshes from aws

    each proxy uses aws spot instances and ebs volumes (<1c/proxy/hour)
    does not use any aws resources when not running
    """
    # master copy of dataframe of instances relating to proxy
    # NOTE initialised from aws but the latter is unreliable due to "eventual consistency"
    df = None

    def __init__(self, name="proxy"):
        """
        :param name: prefix for instance name. identifies which instances are proxies.
        """
        self.name = name
        self.index = 0

        # load from aws
        self.refresh()

    @property
    def ready(self):
        """ return dataframe of ready proxies """
        # todo dont use true/false as confused with strings or logical
        return self.df[self.df.ready == "True"]

    def get_proxy_url(self):
        """ return url of next proxy in cycle
        :return: proxy url
        """
        if self.ready.empty:
            self.wait(1)

        if self.index >= len(self.ready):
            self.index = 0
        ip = self.ready.ip.iloc[self.index]
        self.index += 1

        proxy = ip2url(ip)
        return proxy

    def get_session(self):
        """ get a requests session with a new proxy
        :return: requests session
        """
        s = requests.Session()
        adapter = HTTPAdapter(max_retries=3)
        s.mount("http://", adapter)
        s.mount("https://", adapter)
        s.headers = {"User-Agent": ua}
        proxy = self.get_proxy_url()
        s.proxies = dict(http=proxy, https=proxy)
        s.trust_env = False
        return s

    def set(self, n):
        """ set number of proxies required
        :param n: number of proxies
        """
        if n > len(self.ready):
            self.start(n - len(self.ready))
        elif n < len(self.ready):
            for ip in self.ready.ip.tolist()[:n]:
                self.stop(ip)

    def start(self, count=1):
        """ launch each proxy in a thread
        :param count: number of proxies to start
        """
        for index in range(count):
            t = Thread(target=self.start_thread)
            t.start()

    def stop(self, ip=None):
        """ stop proxy
        :param ip: ip, url. if None then stop all.
        """
        # single ip
        if ip:
            ip = url2ip(ip) if ip.startswith("http") else ip
            df2 = self.df[self.df.ip == ip]
        # all instances including stopped
        else:
            # get all the instances. this seems up to date on aws whereas tags are not.
            self.refresh()
            df2 = self.df

        for i, row in df2.iterrows():
            try:
                # update dataframe first
                self.df.loc[self.df.instance_id==row.instance_id, "ready"] = "False"

                # stop on aws
                s = Spot(row.instance_id)
                s.set_tags(ready="False")
                s.res.terminate()
            except:
                log.exception(f"problem stopping {row.instance_id}")

    def replace(self, ip):
        """ remove proxy and start another
        :param ip: ip address to stop
        """
        # lock needed otherwise multiple processes want to replace the same instance
        with mp.Lock():
            ip = url2ip(ip) if ip.startswith("http") else ip

            if ip in self.ready.ip.tolist():
                log.info(f"replacing {ip}")
                self.stop(ip)
                self.start()
            else:
                log.info(f"already replaced {ip}")
                return

    def get_df(self):
        return self.df

    def refresh(self):
        """ refresh df cache from aws
         ..warning:: this takes 9 seconds and data is NOT live. hence only used in __init__ and stop """
        df = aws.get_instancesdf()

        # add any tags used here as may be no instances with them set
        for col in set(["name", "ready"]) - set(df.columns):
            df[col] = ""

        # filter instances relating to this proxy
        self.df = df[df["name"].str.startswith(f"{self.name}_")]
        return self.df

    def wait(self, n):
        log.info("waiting for proxy")
        self.retry_wait(n)

    @Retry(tries=3000, delay=10, warn=0)
    def retry_wait(self, n):
        """ wait 5 minutes until proxies available. check every 10 seconds.
        :param n: number of proxies for which to wait
        """
        if len(self.ready) < n:
            raise Exception()

    def start_thread(self):
        """ start spot instance on aws running proxy server
        """
        # create instance
        name = names.sample(1).item().lower()
        i = Spot(f"{self.name}_{name}", specfile=f"{HERE}/server.yaml")
        i.persistent = False

        # configure instance
        # todo why is the restart necessary?
        i.set_connection()
        i.connection.put(f"{HERE}/tinyproxy.conf")
        i.run(
            "sudo apt-get -qq update && "
            "sudo apt-get -y -q install dos2unix tinyproxy && "
            "dos2unix tinyproxy.conf && "
            "sudo cp tinyproxy.conf /etc/tinyproxy/tinyproxy.conf && "
            "tinyproxy && "
            "sudo service tinyproxy restart",
            hide="both",
        )
        i.connection.close()

        # wait for proxy to be working
        try:
            self.check_proxy(i.public_ip_address)
        except:
            log.error(
                f"Failed to start proxy for {i.instance_id} at {i.public_ip_address}"
            )
            raise

        # make available
        i.set_tags(ready="True")
        log.info(f" {i.public_ip_address} started")

        # add to dataframe as master copy as aws is slow to update.
        row = dict(name=i.name, instance_id=i.instance_id, ip=i.public_ip_address, ready="True")
        row = pd.DataFrame.from_dict([row])
        self.df = pd.concat([self.df, row])

    # todo reduce retries depending on results
    @Retry(tries=99, delay=1, warn=99)
    def check_proxy(self, ip):
        """ wait for proxy ready """
        r = requests.get("http://api.ipify.org", proxies=dict(http=ip2url(ip)))
        r.raise_for_status()

    @classmethod
    def create_server(cls):
        # todo move all this to utils
        """ create server for proxy object so it can be accessed from multiple processes
        :return: actual object for use in calling process
        todo consider using spot fleet instead to ensure enough proxies
        """
        def target(obj):
            Manager.register("get_obj", callable=lambda: obj)
            m = Manager(**connect_params)
            try:
                s = m.get_server()
                s.serve_forever()
            except OSError:
                log.warning("server already running")
                return
        obj = cls()
        t = Thread(target=target, daemon=True, args=(obj,))
        t.start()
        return obj

    @classmethod
    def create_client(cls):
        """ create client for proxy object inside a process
        :return: proxy_object for use in processes
        """
        Manager.register("get_obj")
        m = Manager(**connect_params)
        m.connect()
        return m.get_obj()
