# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:light
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.5.2
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# +
from ipstartup import *
import logging

import requests
from mproxy.source import google

log = logging.getLogger(__name__)
# -

# no proxies
s = requests.Session()
urls = google.search(s, "trump", before="20200701", after="20200701")
len(urls), urls[:10]


