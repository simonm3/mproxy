import logging
import os
from os.path import expanduser

import pandas as pd
import requests

from ..utils import Retry

log = logging.getLogger(__name__)

HOME = expanduser("~").replace("\\", "/")
HERE = os.path.dirname(__file__)
names = pd.read_csv(f"{HERE}/babies-first-names-top-100-girls.csv").FirstForename
ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36"


class Proxy:
    """ base class for proxy
    """

    def __init__(self):
        self.node = None
        self.lc = None
        self.con = None
        self.counter = 0
        self.session = None

    def get(self, query, params=None):
        """ return response to request """
        r = self.session.get(query, params=params)
        self.counter += 1
        return r

    def get_session(self, ip):
        """ get session with proxies and retries """
        s = requests.session()
        adapter = requests.adapters.HTTPAdapter(max_retries=3)
        s.mount("http://", adapter)
        s.mount("https://", adapter)
        s.headers = {"User-Agent": ua}
        proxy = f"{ip}:8888"
        s.proxies = dict(http=f"http://{proxy}", https=f"https://{proxy}")
        s.trust_env = False
        return s

    def start(self):
        """ initialise the proxy provider e.g. start server """
        raise NotImplementedError

    def stop(self):
        self.lc.ex_create_tags(self.node, dict(ready="False", name=""))
        self.con.close()
        self.session.close()
        self.node.destroy()

    @Retry(tries=5, delay=1, warn=1)
    def check_proxy(self):
        """ wait for proxy ready """
        r = self.get("http://api.ipify.org")
        r.raise_for_status()
