# ---
# jupyter:
#   jupytext:
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

from ipstartup import *
from mproxy import AWS, Manager, Tor
from mproxy.source import google

# initialise
m = Manager()
m.add(AWS, 2)
search = m.get_proxy_function(google.search)

for _ in range(2):
    print(m.get_session().get("https://api.ipify.org").text)

# run searches
urls = search("trump", before="20200701", after="20200701")
len(urls), urls[:10]

# remove a single proxy
m.remove()

# stop proxies
m.stop()


