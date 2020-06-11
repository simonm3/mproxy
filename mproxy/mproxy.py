import logging
import multiprocessing as mp
import os
from threading import Thread
from urllib.parse import urlparse

import pandas as pd
import requests
from requests.adapters import HTTPAdapter

from aws2 import Spot, aws

from .utils import Retry

log = logging.getLogger(__name__)

HERE = os.path.dirname(__file__)
names = pd.read_csv(f"{HERE}/babies-first-names-top-100-girls.csv").FirstForename
ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36"


def ip2url(ip):
    """ ip used by aws; url used by client """
    return f"http://{ip}:8888"


def url2ip(url):
    """ ip used by aws; url used by client """
    return urlparse(url).netloc.split(":")[0]


class ProxyException(Exception):
    """ raised when proxy is rejected """

    pass


class Borg:
    """ simplified singleton """

    _shared_state = {}

    def __init__(self):
        self.__dict__ = self._shared_state


class Mproxy(Borg):
    """ manages a group of https proxy servers
    each proxy uses aws spot instances and ebs volumes (<1c/proxy/hour)
    """

    def __init__(self):
        # identifies proxy instances on aws
        self.prefix = "proxy_"

        # next proxy to select
        self.next = 0

        # master database of instances initialised from aws
        self.df = self.get_instances()

    # client methods ################################################################################

    def start(self, target=1):
        """ start proxies to reach target
        :param target: number of proxies required
        """
        n = target - len(self.ready)
        if n > 0:
            for _ in range(n):
                self.start_instance()
        elif n < 0:
            for ip in self.ready.ip.tolist()[: abs(n)]:
                self.stop_instance(ip)

    def stop(self):
        """ stop all instances """
        self.df = self.get_instances()
        for ip in self.df.ip:
            try:
                self.stop_instance(ip)
            except:
                log.exception(f"problem stopping {ip}")

    def stop_instance(self, ip):
        """ terminate instance and remove from proxy list
        :param ip: ip OR url
        """
        ip = url2ip(ip) if ip.startswith("http") else ip

        self.df.loc[self.df.ip == ip, "ready"] = "False"
        s = Spot(self.df.loc[self.df.ip == ip].instance_id.iloc[0])
        s.set_tags(ready="False")
        s.res.terminate()

    def replace(self, ip):
        """ remove proxy and start another
        :param ip: ip OR url
        """
        ip = url2ip(ip) if ip.startswith("http") else ip

        if ip in self.ready.ip.tolist():
            log.info(f"replacing {ip}")
            try:
                self.stop_instance(ip)
            except:
                log.exception(f"could not stop {ip} so not starting a new one")
                return
            self.start()
        else:
            log.info(f"already replaced {ip}")

    @Retry(tries=30, delay=10, warn=1)
    def wait(self, n):
        """ wait until proxies available
        :param n: number of proxies for which to wait
        """
        if len(self.ready) < n:
            raise Exception()

    def get_df(self):
        """ enable access from client """
        return self.df

    def get_url(self):
        """ return next url
        :return: proxy url
        """
        if self.ready.empty:
            self.wait(1)

        if self.next >= len(self.ready):
            self.next = 0
        ip = self.ready.ip.iloc[self.next]
        self.next += 1
        return ip2url(ip)

    def get_session(self):
        """ return next requests session. alternative to get_url.
        :return: requests session
        """
        url = self.get_url()
        s = requests.Session()
        adapter = HTTPAdapter(max_retries=3)
        s.mount("http://", adapter)
        s.mount("https://", adapter)
        s.headers = {"User-Agent": ua}
        s.proxies = dict(http=url, https=url)
        s.trust_env = False
        return s

    # internal methiods ###################################################################################

    @property
    def ready(self):
        """ return dataframe of ready proxies """
        return self.df[self.df.ready == "True"]

    def get_instances(self):
        """ get instances from aws
         ..warning:: this takes 9 seconds and data is NOT live. hence only used in __init__ and stop
         :return: dataframe of proxy instances
        """
        df = aws.get_instancesdf()
        for col in set(["name", "ready"]) - set(df.columns):
            df[col] = ""
        return df[df["name"].str.startswith(self.prefix)]

    def start_instance(self):
        """ start instance in a thread
        """
        t = Thread(target=self.start_thread, daemon=True)
        t.start()

    def start_thread(self):
        """ start spot instance on aws running proxy server
        """
        # create instance
        name = names.sample(1).item().lower()
        i = Spot(f"{self.prefix}{name}", specfile=f"{HERE}/server.yaml")
        i.persistent = False

        # configure instance
        i.set_connection()
        i.connection.put(f"{HERE}/tinyproxy.conf")
        i.run(
            "sudo apt-get -qq update && "
            "sudo apt-get -y -q install dos2unix tinyproxy && "
            "dos2unix tinyproxy.conf && "
            "sudo cp tinyproxy.conf /etc/tinyproxy/tinyproxy.conf && "
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
        row = dict(
            name=i.name, instance_id=i.instance_id, ip=i.public_ip_address, ready="True"
        )
        row = pd.DataFrame.from_dict([row])
        self.df = pd.concat([self.df, row])

    @Retry(tries=99, delay=1, warn=99)
    def check_proxy(self, ip):
        """ wait for proxy ready """
        r = requests.get("http://api.ipify.org", proxies=dict(http=ip2url(ip)))
        r.raise_for_status()
