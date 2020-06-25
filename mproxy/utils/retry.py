from functools import wraps
from time import sleep

import logging

log = logging.getLogger(__name__)


class Retry:
    """ decorator to retry a function after exceptions """

    def __init__(self, tries=3, delay=1, exceptions=None, warn=1):
        """
        :param tries: number of times to try
        :param delay: seconds to delay between retries
        :param exceptions: exception or list/tuple of exceptions to tries. None is all.
        :param warn: number of warning messages to issue
        """
        self.tries = tries
        self.delay = delay
        self.exceptions = exceptions or Exception
        if not (
            isinstance(self.exceptions, list) or isinstance(self.exceptions, tuple)
        ):
            self.exceptions = (self.exceptions,)
        self.warn = warn

    def __call__(self, func):
        @wraps(func)
        def inner(*args, **kwargs):
            last_exception = Exception
            for n in range(self.tries):
                try:
                    return func(*args, **kwargs)
                except self.exceptions as e:
                    last_exception = type(e)
                    if self.warn > 0:
                        log.warning(
                            f"waiting for {func.__module__}.{func.__name__} tries={n+1}"
                        )
                        self.warn -= 1
                    sleep(self.delay)
            raise last_exception(
                f"failed {func.__module__}.{func.__name__} tries={n+1}"
            )

        return inner
