import random

import requests

from .aws import AWS


class AWSNord(AWS):
    """ proxy using aws server and nordVPN. Enables switch ip rather than launch a new machine.
    
    limited to 6 ip addresses including any already used

    NOT TESTED
    """

    def start(self):
        """ start and connect to nordvpn """

        # new server
        if self.node is None:
            super().start()
            self.con.run(
                "wget https://repo.nordvpn.com/deb/nordvpn/debian/pool/main/nordvpn-release_1.0.0_all.deb "
                "sudo apt-get install ./nordvpn-release_1.0.0_all.deb"
            )
        # existing server with new ip
        else:
            r = requests.get("https://nordvpn.com/api/server/stats")
            vpns = [x for x in r.json().keys() if x.startswith("uk")]
            ip = random.choice(vpns)
            self.con.run(f"nordvpn -c -n {ip}")
            self.session = self.get_session(ip)
            self.counter = 0

    def stop(self):
        pass
