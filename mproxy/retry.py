from functools import wraps
from time import sleep

class RetryException(Exception):
    pass

class Retry:
    """ decorator to retry a function """

    def __init__(self, retry=3, delay=1, exceptions=None, warn=1):
        """
        :param retry: number of times to retry
        :param delay: seconds to delay between retries
        :param exceptions: exceptions to retry. None is all.
        :param warn: number of warnings to issue
        """
        self.retry = retry
        self.delay = delay
        self.exceptions = exceptions
        self.warn = warn

    def __call__(self, func):
        @wraps(func)
        def inner(*args, **kwargs):
            for n in range(self.retry):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if self.exceptions and not isinstance(e, self.exceptions):
                        raise
                    if self.warn > 0:
                        log.warning(f"failed {func.__name__}. retrying {self.retry} times")
                        self.warn -= 1
                    if n == self.retry-1:
                        log.error(f"{func.__name__} attempted {self.retry} times and failed")
                        raise
                sleep(self.delay)
        return inner