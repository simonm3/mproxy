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

# +
from ipstartup import *
import logging

import requests

from mproxy import Manager, Task, AWS, Tor
from mproxy.source import google

log = logging.getLogger(__name__)
# -

m = Manager()
m.add(Tor, 1)

t=Task(m)
search = t.use_proxies(google.search)

urls = search("trump", before="20200701", after="20200701")
len(urls), urls[:10]

# stop proxies
m.stop()
