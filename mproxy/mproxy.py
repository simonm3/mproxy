import subprocess
from multiprocessing.managers import BaseManager
import multiprocessing
import shlex
from aws2 import aws, Spot
from threading import Thread
import os
import pandas as pd
import requests
from urllib.parse import urlparse
from .retry import Retry
import logging

log = logging.getLogger(__name__)

# fixed port as dedicated server instance for each proxy_url so no need to change it.
ip2url = lambda ip: f"http://{ip}:8080"
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
    """ manages a rotating set of http proxy_url servers. has no fixed state as it refreshes from aws

    each proxy_url uses aws spot instances and ebs volumes (<1c/proxy_url/hour)
    does not use any aws resources when not running
    todo add localhost proxy for quick tests
    todo does set work correctly or sometimes replace?
    """

    # cache dataframe of instances relating to this proxy. includes all states.
    df = None

    def __init__(self, name="proxy"):
        """
        :param name: instance.name is set to name_rname where rname is a random girls name
        typically default name is fine. different name can be used for different applications if required.
        """
        self.name = name
        self.index = 0

        # load from aws
        self.refresh()

    @property
    def ready(self):
        """ return dataframe of ready proxies """
        return self.df[self.df.ready == "True"]

    def get_proxy_url(self):
        """ return url of next proxy_url in cycle
        :return: proxy_url url
        """
        if self.ready.empty:
            self.wait(1)

        if self.index >= len(self.ready):
            self.index = 0
        ip = self.ready.ip.iloc[self.index]
        self.index += 1

        return ip2url(ip)

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
            df2 = self.df

        for i, row in df2.iterrows():
            self.df.iloc[i].ready = "False"
            s = Spot(row.instance_id)
            s.set_tags(ready="False")
            s.res.terminate()
            log.info(f"{row.ip} stopped")

    def replace(self, ip):
        """ remove proxy and start another
        :param ip: ip address to stop
        """
        log.info(f"replacing {ip}")
        ip = url2ip(ip) if ip.startswith("http") else ip

        # already replaced by another process
        if ip not in self.ready.ip.tolist():
            log.info(f"already replaced {ip}")
            return
        self.stop(ip)
        self.start()

    def refresh(self):
        """ refresh df cache from aws """
        df = aws.get_instancesdf()

        # add any tags used here as may be no instances with them set
        for col in set(["name", "ready"]) - set(df.columns):
            df[col] = ""

        # filter instances relating to this proxy
        self.df = df[df["name"].str.startswith(f"{self.name}_")]
        return self.df

    @Retry(retry=3000, delay=10)
    def wait(self, n):
        """ wait 5 minutes until proxies available
        :param n: number of proxies for which to wait
        """
        if len(self.ready) < n:
            raise Exception()

    def start_thread(self):
        """ start spot instance on aws running proxy server
        """
        name = names.sample(1).item().lower()
        i = Spot(f"{self.name}_{name}", specfile=f"{HERE}/proxy.yaml")
        i.persistent = False
        self.post_launch(i)
        log.info(f" {i.public_ip_address} started")
        self.refresh()

    def post_launch(self, i):
        # configure and run
        i.connection.put(f"{HERE}/proxy.py")
        i.run(
            "sudo apt-get -qq update && "
            "sudo apt-get -y -q install dos2unix python3-pip && "
            "pip3 install -q twisted && "
            "dos2unix proxy.py && "
            "chmod +x proxy.py && "
            "tmux new -d -s proxy ./proxy.py",
            hide="both",
        )
        # wait for proxy to be working
        try:
            self.check_proxy(i.public_ip_address)
        except:
            log.error(
                f"Failed to start proxy for {i.instance_id} at {i.public_ip_address}"
            )
            raise
        i.set_tags(ready="True")

    # todo reduce retries depending on results
    @Retry(retry=99, delay=10, warn=99)
    def check_proxy(self, ip):
        """ wait for new proxy to respond correctly """
        r = requests.get("http://api.ipify.org", proxies=dict(http=ip2url(ip)))
        r.raise_for_status()

    @classmethod
    def create_server(cls):
        """ create Mproxy object and run server so it can be accessed from multiple processes
        :return: Mproxy object
        todo consider using spot fleet instead to ensure enough proxies
        """
        # setup
        obj = cls()
        Manager.register("get_obj", callable=lambda: obj)
        m = Manager(**connect_params)

        def target():
            from defaultlog import log

            try:
                s = m.get_server()
            except (multiprocessing.context.ProcessError, OSError):
                log.warning("server already running")
                return
            s.serve_forever()

        t = Thread(target=target, daemon=True).start()
        return obj

    @classmethod
    def create_client(cls):
        """ create Mproxy client to access shared Mproxy object
        :return: proxy_object that can be used as an Mproxy
        """
        # setup
        obj = cls()
        Manager.register("get_obj", callable=lambda: obj)
        m = Manager(**connect_params)

        m.connect()
        return m.get_obj()
