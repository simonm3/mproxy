#!/usr/bin/env python3

""" simple http proxy_url server using twisted. does not support https.

this runs on AWS spot instance
"""

from twisted.web import proxy, http
from twisted.internet import reactor
from twisted.python import log
import sys

log.startLogging(sys.stdout)


class ProxyFactory(http.HTTPFactory):
    protocol = proxy.Proxy


def main():
    reactor.listenTCP(8080, ProxyFactory())
    reactor.run()


if __name__ == "__main__":
    main()
