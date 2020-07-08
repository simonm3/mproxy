from pathlib import Path

from stem import Signal
from stem.connection import connect

from .proxy import Proxy

with (Path.home() / ".tor/creds").open() as f:
    password = f.read()


class Tor(Proxy):
    """ proxy using tor
    Note many websites block tor ip addresses making it useless as a proxy server
    e.g. google search
    """

    def start(self):
        # force new ip address
        controller = connect()
        controller.authenticate(password=password)
        controller.signal("NEWNYM")
        ip = "socks5://localhost:9050"
        self.session = self.get_session(ip)
        self.session.proxies = dict(http=ip, https=ip)
        return "localhost"

    def stop(self):
        pass
