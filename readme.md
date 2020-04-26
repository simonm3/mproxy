Mproxy
======

This enables http requests via proxies that are automatically replaced if blocked.
The proxies run on AWS and cost less than 1c/hour/proxy.

Installation
------------

    ~/.aws folder containing "config", credentials" and "key"
    aws securitygroup "proxy" that opens inbound ports 22 and 8888 (ssh and proxy requests)
    pip install mproxy

Usage
-----

See nbs folder for example::

    proxy_search.ipynb - search using automatic proxy replacement
    
Multiprocessing usage::

    # for main process
    m = Mproxy.create_server()
    
    # for other processes
    m = Mproxy.create_client()
    s = Search(m)
    r = s.search("some stuff")

Todo
----

* run mproxy as server that accepts http requests; sends them as https; responds using http.
Note it cannot be https end to end and still change request or response headers
* rotate proxies or allocate them in other ways
* with 8 processes using 8 proxies they all expire at the same time 
* does not work with google translate which somehow detects the new proxy
    
Classes
-------

* Mproxy represents all the running proxies. it initialises from aws so can be created any time.
* Search represents a search session. It uses one proxy that will be replaced when it fails.
* Translate represents a translate session. It uses one proxy that will be replaced when it fails.

how many proxies are needed?
----------------------------

* you can use mproxy.set(n) at any time to set the number of running proxies.
* 1 proxy means that when it fails there is a delay until replacement is ready.
* 2 proxies means that when it fails it switches to proxy 2 immediately and relaunches proxy 1 in the background.
* \>2 proxies can cope with more frequent requests and failures without delays.
Proxies can be shared by multiple threads and processes; and by search and translate.

