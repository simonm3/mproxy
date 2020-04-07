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
# # Search with automatic proxy replacement

# %% [markdown]
# This bypasses ip blocking by passing search calls via proxies. Whenever a proxy is blocked then the search switches to a new one and replaces the failed proxy.
#
# install:
#
# * pip install mproxy
# * create security group "proxy" with inbound ports 22 and 8080
# * create ~/.aws folder put "credentials" and "key"
#
# what are the classes?
# * mproxy represents all the running proxies. it initialises from aws so can be created any time.
# * proxysearch represents a search session. It uses one proxy that will be replaced when it fails.
#
# how many proxies are needed?
# * you can use mproxy.set(n) at any time to set the number of running proxies.
# * 1 proxy means that when it fails there is a delay until replacement is ready.
# * 2 proxies means that when it fails it switches to proxy 2 immediately and relaunches proxy 1 in the background.
# * \>2 proxies can cope with more frequent requests and failures without delays.
# * Proxies can be shared by multiple threads and processes.

# %%
from ipstartup import *
from sm.search import *

# %%
# set the number of proxy servers and wait until ready (they setup in the background)
m = Mproxy()
m.set(2)
m.wait(2)

# %%
# show running proxies
m.df

# %%
# create proxysearch. this is a session that uses one proxy but replaces on failure.
s = Proxysearch(m)

# %%
# search using google. if this cell fails then rerun will try again with new proxy_url.
# maximum 300 results per search. can be increased by running separate searches per week.
q = "sport"
n = 1000
domain = "www.guardian.co.uk"
urls = s.search(q, n=n, domain=domain, stype=Stypes.news, to_date="20191230", from_date="20190101")
len(urls), urls

# %%
# stop all proxy servers
m.stop()

# %%
sys.path

# %%
for path in sys.path:
    for root, dirs, files in os.walk(path):
        for item in files:
            if "top_level" in item:
                item = os.path.join(root, item)
                print(item)
                open(item, "r") 

# %%
