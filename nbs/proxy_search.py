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

from ipstartup import *
from mproxy import Google, ProxyAWS

# %%
# set the number of proxy servers and wait until ready (they setup in the background)
m = ProxyAWS()
m.start(2)
m.wait(2)

# %%
# show running proxies
m.df

# %%
# create proxysearch. this is a translator that uses one proxy but replaces on failure.
s = Google(m)

# %%
# search using google. if this cell fails then rerun will try again with new proxy.
# maximum 300 results per search. can be increased by running separate searches per week.
q = "sport"
n = 1000
domain = "www.guardian.co.uk"
urls = s.search(q, n=n, site=domain, before="20191230", after="20190101")
len(urls), urls

# %%
# stop all proxy servers
m.stop()
