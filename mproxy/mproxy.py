import subprocess
import shlex
from aws2 import aws, Spot
from threading import Thread
import os
import pandas as pd
from time import sleep
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


class Mproxy:
    """ manages a rotating set of http proxy_url servers. has no fixed state as it refreshes from aws

    each proxy_url uses aws spot instances and ebs volumes (<1c/proxy_url/hour)
    does not use any aws resources when not running
    """

    # cache dataframe of instances from aws
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

    def get_proxy_url(self):
        """ return url of next proxy_url in cycle
        :return: proxy_url url
        """
        if len(self.df) == 0:
            log.error("There are no proxies available")
            return

        if self.index >= len(self.df):
            self.index = 0
        ip = self.df.ip.iloc[self.index]
        self.index += 1

        return ip2url(ip)

    def set(self, n):
        """ set number of proxies required
        :param n: number of proxies
        """
        if n > len(self.df):
            self.start(n - len(self.df))
        elif n < len(self.df):
            self.stop(self.df.ip[:n].tolist())

    def start(self, count=1):
        """ launch each proxy in a thread
        :param count: number of proxies to start
        """
        for index in range(count):
            t = Thread(target=self.start_thread)
            t.start()

    def stop(self, ips=None):
        """ stop proxies
        :param ips: ip, url, list of ips, list of urls. if None then stop all.
        :return: number stopped
        """
        df = self.df.copy()
        if ips:
            if not isinstance(ips, list):
                ips = [ips]
            ips = [url2ip(ip) if ip.startswith("http:") else ip for ip in ips]
            df = df[df.ip.isin(ips)]

        for i, row in df.iterrows():
            s = Spot(row.instance_id)
            s.name = ""
            s.res.terminate()
            self.df = self.df.drop(index=i)
            log.info(f"{row.ip} stopped")

    def replace(self, ips):
        """ remove proxy and start another
        :param ips: ip, url, list of ips, list of urls
        """
        if not isinstance(ips, list):
            ips = [ips]
        current = len(self.df)
        self.stop(ips)
        self.set(current)

    def refresh(self):
        """ refresh df cache from aws """
        df = aws.get_instancesdf()
        self.df = df[
            df["name"].str.startswith(f"{self.name}_") & (df.state == "running")
        ]

    def wait(self, n=1):
        """ wait until proxies available
        :param n: at least n proxies
        :return: True if available. False if keyboard interrupt
        """
        try:
            warned = False
            while True:
                if len(self.df) >= n:
                    log.info(f"{len(self.df)} proxies are available")
                    return
                if not warned:
                    log.warning(f"waiting until {n} proxies available.")
                    warned = True
                sleep(1)
        except KeyboardInterrupt:
            log.info("keyboard interrupt")
            return

    def start_thread(self):
        """ start spot instance on aws running proxy server
        """
        name = names.sample(1).item().lower()
        i = Spot(f"{self.name}_{name}", specfile=f"{HERE}/proxy.yaml")
        i.persistent = False
        self.post_launch(i)
        log.info(f" {i.public_ip_address} started")
        self.refresh()

    # todo remove retry. here to check for infrequent errors. probably resolves?
    @Retry(warn=3)
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
