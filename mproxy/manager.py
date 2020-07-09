import logging
from threading import Thread
from urllib.parse import urlparse

from libcloud.compute.providers import get_driver
from libcloud.compute.types import NodeState, Provider

from .proxysession import ProxySession
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

    def remove(self, ip=None):
        """ treat as blocked. replace.
        :param ip: url or ip
        """
        if ip is None:
            try:
                ip = list(self.proxies.keys())[0]
            except IndexError:
                log.warning("no proxies to remove")
                return
        ip = urlparse(ip).netloc.split(":")[0] if ip.startswith("http") else ip

        proxy = self.proxies[ip]
        del self.proxies[ip]
        proxy.stop()
        log.info(f"{ip} stopped after {proxy.counter} requests")

    def block(self, ip):
        """ treat as blocked. replace.
        :param ip: url or ip
        """
        ip = urlparse(ip).netloc.split(":")[0]

        proxy = self.proxies[ip]
        self.remove(ip)
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

    def get_proxy_session(self):
        """ return session that will automatically switch proxies """
        return ProxySession(self)

    def get_proxy_function(self, func):
        """ return function that replaces session and retries
        :param func: function to be wrapped. raises ProxyException
        :return: wrapped function that handles ProxyException.
        """
        s = ProxySession(self)
        return s.get_proxy_function(func)

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
