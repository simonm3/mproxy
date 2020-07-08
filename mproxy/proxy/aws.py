import logging
from configparser import ConfigParser
from threading import Thread

import pandas as pd
from fabric import Connection
from libcloud.compute.providers import get_driver
from libcloud.compute.types import NodeState, Provider

from ..utils import Retry
from .proxy import HERE, HOME, Proxy, names

log = logging.getLogger(__name__)


def get_libcloud():
    """ get libcloud driver """
    cfg = ConfigParser()
    cfg.read(f"{HOME}/.aws/credentials")
    access = cfg.get("default", "aws_access_key_id")
    secret = cfg.get("default", "aws_secret_access_key")
    cls = get_driver(Provider.EC2)
    lc = cls(access, secret, region="eu-west-1")
    return lc


# single driver for all nodes
lc = get_libcloud()


class AWS(Proxy):
    """ proxy on AWS """

    def __init__(self, name=None):
        """
        :param name: create object for existing node
        """
        super().__init__()
        self.lc = lc
        if name:
            try:
                self.node = [n for n in lc.list_nodes() if n.name == name][0]
                self.session = self.get_session(self.node.public_ips[0])
            except IndexError:
                pass

    def start(self):
        """ start node """

        # launch server. ubuntu.
        name = names.sample(1).item().lower()
        size = [s for s in lc.list_sizes() if s.name == "t3.nano"][0]
        image = lc.list_images(ex_image_ids=["ami-03d8261f577d71b6a"])[0]
        node = lc.create_node(
            name,
            size,
            image,
            ex_keyname="key",
            ex_spot=True,
            ex_security_groups=["proxy"],
            ex_metadata=dict(app="proxy", ready=False),
        )
        log.info(f"waiting for {name} to start")
        node = lc.wait_until_running([node])[0][0]
        self.node = node
        ip = node.public_ips[0]
        self.session = self.get_session(ip)

        # configure using fabric
        con = Connection(
            ip, user="ubuntu", connect_kwargs=dict(key_filename=f"{HOME}/.aws/key"),
        )
        self.con = con
        # retry until ssh available
        Retry(tries=3, delay=2, warn=1)(con.open)()
        con.put(f"{HERE}/tinyproxy.conf")
        con.run(
            "sudo apt-get -qq update && "
            "sudo apt-get -y -q install dos2unix tinyproxy && "
            "dos2unix tinyproxy.conf && "
            "sudo cp tinyproxy.conf /etc/tinyproxy/tinyproxy.conf && "
            "sudo service tinyproxy restart",
            hide="both",
        )

        # wait for proxy to be working
        try:
            self.check_proxy()
        except:
            log.error(f"Failed to start proxy for {node.extra.instance_id} at {ip}")
            raise

        # make available
        lc.ex_create_tags(node, dict(ready="True"))
        log.info(f" {ip} started")

        return ip
