import logging
import os
import pandas as pd

from .utils import Retry

log = logging.getLogger(__name__)

HERE = os.path.dirname(__file__)
names = pd.read_csv(f"{HERE}/babies-first-names-top-100-girls.csv").FirstForename
ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36"


class ProxyException(Exception):
    """ raised when proxy is rejected """

    pass


class Proxy:
    """ proxy using a group of AWS servers
    """
    def get_session(self):
        """ return next requests session. alternative to get_url.
        :return: requests session
        """
        # define in child class
        raise NotImplementedError

    # optional #######################################################

    def start(self, target=1):
        """ start proxies to reach target
        :param target: number of proxies required
        """
        pass

    def stop(self):
        """ stop all instances """
        pass

    def stop_instance(self, ip):
        """ terminate instance and remove from proxy list
        :param ip: ip OR url
        """
        pass

    def replace(self, ip):
        """ remove proxy and start another
        :param ip: ip OR url
        """
        pass

    @Retry(tries=30, delay=10, warn=1)
    def wait(self, n):
        """ wait until proxies available
        :param n: number of proxies for which to wait
        """
        pass

