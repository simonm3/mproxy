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
# # Proxy with requests
#
# Typically it is easier to use proxy with automatic replacement. However it can also be used directly with requests

# %%
from ipstartup import *
from mproxy import Mproxy, Search, Stypes
import requests
from fake_useragent import UserAgent
from time import sleep

# %%
# start two proxy servers
m = Mproxy()
m.set(2)
m.wait(2)

# %%
m.df

# %%
# get a proxy url
m.get_proxy_url()

# %% [markdown]
# To use with requests just obtain a proxy url and set the proxies parameter. Running this cell repeatedly iterates the proxies.

# %%
# call requests.get as normal with the proxies parameter
proxy_url = m.get_proxy_url()
proxies = dict(http=proxy_url)
url = "http://api.ipify.org"
r = requests.get(url, headers=dict(User_Agent=UserAgent().chrome), proxies=proxies)
print(proxy_url)
r.text

# %%
# when there is a proxy failure then replace it
m.replace(proxy_url)

# %%
# stop all proxy servers
m.stop()

# %%
