# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.5.0
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

from ipstartup import *
from mproxy import AWS, Manager, Tor
from mproxy.source import google

# initialise
m = Manager()
m.add(AWS, 2)
session = m.get_proxysession()
search = session.get_proxy_function(google.search)

# run searches
urls = search("trump", before="20200701", after="20200701")
len(urls), urls[:10]

m.remove()

# stop proxies
m.stop()
