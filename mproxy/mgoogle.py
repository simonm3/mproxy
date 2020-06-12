import logging

from .google import Google
from .mproxy import ProxyException, ua
from .utils import Retry

log = logging.getLogger(__name__)


class Stypes:
    """ types of results required """

    images = "isch"
    news = "nws"
    videos = "vid"
    shopping = "shop"
    books = "bks"
    apps = "app"


class MGoogle(Google):
    """ mproxy client for google search

    Usage::

        s = Google(mproxy)
        s.search("something")
    """

    def __init__(self, mproxy):
        """
        :param mproxy: mproxy object
        """
        self.mproxy = mproxy
        self.session = self.mproxy.get_session()

    def _refresh(self):
        """ refresh with a new proxy """
        # new session
        self.mproxy.replace(self.session.proxies["http"])
        self.session.close()
        self.session = self.mproxy.get_session()

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
