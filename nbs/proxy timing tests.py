# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.2'
#       jupytext_version: 1.2.1
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# %% [markdown]
# # Tests of different search methods
# Conclusions:
#
# * mostly duckduckgo is much faster than google. however it depends on time of day.
# * mostly using a translator is faster than not using a translator

import requests

from fake_useragent import UserAgent
from ipstartup import *
from mproxy import Mproxy, Search

m = Mproxy()

# %%
# start two proxy servers. takes a couple of minutes to start. cost is <0.1c/hour/proxy
m = Mproxy()
m.start(2)

# %% [markdown]
# # Timings google

# %%
url = "http://www.google.com/search"

# %%
# without proxy
# %timeit requests.get(url, params=dict(q=np.random.randint(100000)))

# %%
# proxy
proxies = dict(http=m.get_url())
# %timeit r = requests.get(url,\
#                          params=dict(q=np.random.randint(100000)),\
#                          headers=dict(User_Agent=UserAgent().chrome),\
#                          proxies=proxies)

# %%
# proxy with translator
s = requests.session()
s.headers = dict(User_Agent=UserAgent().chrome)
s.proxies = dict(http=m.get_url())
# %timeit r = s.get(url, params=dict(q=np.random.randint(100000)))

# %% [markdown]
# # Timings duckduckgo

# %%
url = "http://www.duckduckgo.com"

# %%
# without proxy
# %timeit requests.get(url, params=dict(q=np.random.randint(100000)))

# %%
# proxy
proxies = dict(http=m.get_url())
# %timeit r = requests.get(url,\
#                          params=dict(q=np.random.randint(100000)),\
#                          headers=dict(User_Agent=UserAgent().chrome),\
#                          proxies=proxies)

# %%
# proxy with translator
s = requests.session()
s.headers = dict(User_Agent=UserAgent().chrome)
s.proxies = dict(http=m.get_url())
# %timeit r = s.get(url, params=dict(q=np.random.randint(100000)))

# %%
