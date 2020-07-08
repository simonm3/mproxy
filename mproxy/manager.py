import logging
from threading import Thread
from urllib.parse import urlparse

from libcloud.compute.providers import get_driver
from libcloud.compute.types import NodeState, Provider

from .utils import Retry

log = logging.getLogger(__name__)


class Manager:
    """ manage collection of proxies """

    def __init__(self):
        # database of proxies dict(ip=proxy)
        self.proxies = dict()

        # index of next proxy to select
        self.next = 0

    def add(self, proxy_class, n=1):
        """ add n proxies """

        def target():
            proxy = proxy_class()
            ip = proxy.start()
            self.proxies[ip] = proxy

        for _ in range(n):
            t = Thread(target=target, daemon=True)
            t.start()

    def block(self, ip):
        """ treat as blocked. replace.
        :param ip: url or ip
        """
        ip = urlparse(ip).netloc.split(":")[0]

        # remove blocked proxy
        proxy = self.proxies[ip]
        del self.proxies[ip]
        proxy.stop()
        log.info(f"{ip} stopped after {proxy.counter} requests")

        # add replacement of same class
        self.add(proxy.__class__)

    def get_session(self):
        """ return next proxy session """
        self.wait(1)
        self.next += 1
        if self.next >= len(self.proxies):
            self.next = 0

        index = list(self.proxies.keys())[self.next]
        proxy = self.proxies[index]
        return proxy.session

    def stop(self):
        """ stop all proxies """
        for proxy in self.proxies.values():
            proxy.stop()
        self.proxies = dict()

    @Retry(tries=999, delay=10, warn=1)
    def wait(self, n):
        """ wait until proxies available
        :param n: number of proxies for which to wait
        """
        if len(self.proxies) < n:
            raise Exception
