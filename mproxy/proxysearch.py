#!/usr/bin/env python

import requests
from fake_useragent import UserAgent
from .search import Search
import multiprocessing as mp
import logging

log = logging.getLogger(__name__)


class Proxysearch(Search):
    """ enables search using multiple proxies """

    def __init__(self, mproxy):
        """
        :param mproxy: mproxy object or client connection
        """
        self.mproxy = mproxy
        self.refresh()

    @property
    def proxy_url(self):
        return self.session.proxies["http"]

    def refresh(self):
        """ refresh session with a new proxy """
        log.info(f"requesting new proxy {mp.current_process().name}")
        proxy = self.mproxy.get_proxy_url()
        log.info(f"received new proxy {proxy} for process {mp.current_process().name}")

        s = requests.session()
        s.proxies = dict(http=proxy)
        s.trust_env = False
        self.session = s

    def get(self, url, params):
        """ get with retry """
        while True:
            try:
                r = self.session.get(url, params=params)
                r.raise_for_status()
                return r
            except requests.exceptions.ProxyError:
                log.exception(f"proxy error. replacing proxy {self.proxy_url} for process {mp.current_process().name}")
                self.mproxy.replace(self.proxy_url)
                self.refresh()
                continue
            except requests.exceptions.HTTPError:
                if self.proxy_failed(r):
                    log.warning(f"api limit reached. replacing {self.proxy_url} for process {mp.current_process().name}")
                    self.mproxy.replace(self.proxy_url)
                    self.refresh()
                    continue
                else:
                    raise

    def proxy_failed(self, r):
        """ overwrite to define when proxy needs replacing """
        return r.status_code == 429
