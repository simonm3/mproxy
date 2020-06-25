import random

import requests

from aws2 import Spot

from .proxyaws import ProxyAWS


class ProxyAWSNord(ProxyAWS):
    """ extends proxyAWS to use nordVPN. Enables switch ip rather than launch a new machine.
    
    limited to 6 ip addresses including any already used

    NOT TESTED
    """

    def start(self, n):
        """ start n servers connected to nordvpn """
        super().start(n)
        self.wait(n)
        for ip in self.ready.ip:
            i = Spot(ip)
            i.run(
                "wget https://repo.nordvpn.com/deb/nordvpn/debian/pool/main/nordvpn-release_1.0.0_all.deb"
            )
            i.run("sudo apt-get install ./nordvpn-release_1.0.0_all.deb")
            self.replace(ip)

    def replace(self, ip):
        """ replace nordvpn connection with random ip from the UK list """
        r = requests.get("https://nordvpn.com/api/server/stats")
        vpns = [x for x in r.json().keys() if x.startswith("uk")]
        vpn = random.choice(vpns)
        i = Spot(ip)
        i.run(f"nordvpn -c -n {vpn}")
