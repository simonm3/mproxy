from stem import Signal
from stem.connection import connect
from pathlib import Path

from .proxy import Proxy

with (Path.home() / ".tor/creds").open() as f:
    password = f.read()


class ProxyTor(Proxy):
    """ proxy using tor
    Note many websites block tor ip addresses
    """

    def get_url(self):
        # force new ip address
        controller = connect()
        controller.authenticate(password=password)
        controller.signal(Signal.NEWNYM)
        controller.close()
        proxy = "socks5://localhost:9050"
        return proxy
