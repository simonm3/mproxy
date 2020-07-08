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

# +
# initialise manager/proxies
m = Manager()
m.add(AWS, 2)

# initialise task for each process. can use multiple tasks to rotate proxies manually.
t = Task(m)
search = t.use_proxies(google.search)
# -

# run searches
urls = search("trump", before="20200701", after="20200701")
len(urls), urls[:10]

# stop proxies
m.stop()
