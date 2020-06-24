import logging

from .google import Google
from .proxyaws import ProxyException
from .utils import Retry

log = logging.getLogger(__name__)

class GoogleAWS(Google):
    """ google using aws or awsnord proxy

    Usage::

        s = Google(manager)
        s.search("something")
    """

    def __init__(self, proxy):
        """
        :param proxy: proxy manager
        """
        self.proxy = proxy
        self.session = self.proxy.get_session()

    def _refresh(self):
        """ refresh with a new proxy """
        # replace proxy
        self.proxy.replace(self.session.proxies["http"])

        # new session
        self.session.close()
        self.session = self.proxy.get_session()

        # check working else fail
        urls = self.search("something")
        if len(urls) < 5:
            url = self.session.proxies["http"]
            raise Exception(f"Proxy failed {url}")

    @Retry()
    def _get(self, url, params):
        """ get with proxy replacement for google search """
        try:
            r = self.session.get(url, params=params, timeout=7)
            if r.status_code != 200:
                raise ProxyException
            return r
        except ProxyException:
            self._refresh()
            raise
