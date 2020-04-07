Mproxy
======

This enables http requests via proxies that are automatically replaced if blocked.
The proxies run on AWS and cost less than 1c/hour/proxy.

Installation
------------

    ~/.aws folder containing "config", credentials" and "key"
    aws securitygroup "proxy" that opens inbound ports 22 and 8080 (ssh and proxy requests)
    pip install mproxy

Usage
-----

See nbs folder for example::

    proxy_search.ipynb - search using automatic proxy replacement
    
Classes
-------

mproxy represents all the running proxies. it initialises from aws so can be created any time.
proxysearch represents a search session. It uses one proxy that will be replaced when it fails.

how many proxies are needed?
----------------------------

you can use mproxy.set(n) at any time to set the number of running proxies.
1 proxy means that when it fails there is a delay until replacement is ready.
2 proxies means that when it fails it switches to proxy 2 immediately and relaunches proxy 1 in the background.
>2 proxies can cope with more frequent requests and failures without delays.
Proxies can be shared by multiple threads and processes.