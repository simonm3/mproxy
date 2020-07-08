from functools import wraps


class ProxyException(BaseException):
    """ source get function raises this when proxy is blocked """

    pass


class Task:
    """ a task that replaces the session when ProxyException is raised
    func:
        first argument has a"get" method
        raises ProxyException if blocked
    """

    def __init__(self, manager):
        self.manager = manager
        self.session = manager.get_session()

    def use_proxies(self, func):
        """ wrap function with ProxyException handler """

        @wraps(func)
        def inner(*args, **kwargs):
            try:
                return func(self.session, *args, **kwargs)
            except ProxyException:
                self.replace()

        return inner

    def replace(self):
        self.manager.block(self.session.proxies["http"])
        self.session = self.manager.get_session()
