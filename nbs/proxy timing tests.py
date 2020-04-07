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
# * duckduckgo is 4 times as fast as google
# * using a session is twice as fast as not

# %%
from ipstartup import *
from sm.search import *
import requests
from fake_useragent import UserAgent
m = Mproxy()

# %%
# start two proxy_url servers. takes a couple of minutes to start. cost is <0.1c/hour/proxy_url
m = Mproxy()
m.start(2)

# %% [markdown]
# # Timings google

# %%
url = "http://www.google.com/search"

# %%
# without proxy_url
# %timeit requests.get(url, params=dict(q=np.random.randint(100000)))

# %%
# proxy_url
proxies=dict(http=m.get_proxy_url())
# %timeit r = requests.get(url,\
#                          params=dict(q=np.random.randint(100000)),\
#                          headers=dict(User_Agent=UserAgent().chrome),\
#                          proxies=proxies)

# %%
# proxy_url with session
s = requests.session()
s.headers=dict(User_Agent=UserAgent().chrome)
s.proxies=dict(http=m.get_proxy_url())
# %timeit r = s.get(url, params=dict(q=np.random.randint(100000)))

# %% [markdown]
# # Timings duckduckgo

# %%
url = "http://www.duckduckgo.com"

# %%
# without proxy_url
# %timeit requests.get(url, params=dict(q=np.random.randint(100000)))

# %%
# proxy_url
proxies=dict(http=m.get_proxy_url())
# %timeit r = requests.get(url,\
#                          params=dict(q=np.random.randint(100000)),\
#                          headers=dict(User_Agent=UserAgent().chrome),\
#                          proxies=proxies)

# %%
# proxy_url with session
s = requests.session()
s.headers=dict(User_Agent=UserAgent().chrome)
s.proxies=dict(http=m.get_proxy_url())
# %timeit r = s.get(url, params=dict(q=np.random.randint(100000)))
