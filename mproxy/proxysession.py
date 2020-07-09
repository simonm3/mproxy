from functools import wraps

from .utils import Retry


class ProxyException(BaseException):
    """ source get function raises this when proxy is blocked """

    pass


class ProxySession:
    """ a session that uses rotating proxies """

    def __init__(self, manager):
        self.manager = manager
        self.session = manager.get_session()

    def __getattr__(self, attr):
        """ return attributes from embedded session """
        return getattr(self.session, attr)

    def get_proxy_function(self, func, tries=2):
        """ wrap function with ProxyException handler """

        @Retry(tries=tries, exceptions=ProxyException, warn=0)
        @wraps(func)
        def inner(*args, **kwargs):
            try:
                return func(self.session, *args, **kwargs)
            except ProxyException:
                self.replace()
                raise

        return inner

    def replace(self):
        """ replace proxy """
        self.manager.block(self.session.proxies["http"])
        self.session = self.manager.get_session()
