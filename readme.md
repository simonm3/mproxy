Mproxy
======

This enables http requests via rotating proxies that are automatically replaced if blocked.
AWS proxies cost less than 1c/hour/proxy OR one can use an existing NordVPN account
It can easily be adapted to other cloud or VPN providers

Installation
------------

    ~/.aws folder containing "config", credentials" and "key"
    aws securitygroup "proxy" that opens inbound ports 22 and 8888 (ssh and proxy requests)
    pip install mproxy

Usage
-----

See nbs/aws.ipynb for example::

    from mproxy import Manager, Task, AWS
    from mproxy.source import google
    m.add(AWS, 2)
    
    t = Task(m)
    search = t.use_proxies(google.search)
    urls = search("trump", before="20200701", after="20200701")
    
Multiprocessing usage::

    from mproxy.utils import create_server, create_client

    # main process
    m = Manager
    m = create_server(m)
    
    
    # other processes
    m = create_client()
    t = Task(m)
    search = t.use_proxies(google.search)
    urls = search("trump", before="20200701", after="20200701")

Modules
-------

Manager - rotates proxies
Proxy (AWS, AWSNord, Tor) - proxy server
source (google, translate) - function to get data
Task - wraps a source to capture ProxyException and maintain session.    
  

Installing tor as a service on windows
--------------------------------------

This seems to be a waste of time as most websites block tor. Still it may be useful somewhere.

To use tor with python/stem it must be installed as a service. Take care with these instructions as mistakes fail silently::

    open powershell in admin mode
    install tor into c:/ NOT program files as need write permissions

    cd "C:\Tor Browser\Browser\TorBrowser\tor"
    tor --hash-password <password> | more
    edit data/torrc to add "HashedControlPassword <hashed password>"
    tor --service install -options ControlPort 9151

Monthly costs
-------------

Blazing Proxies (min 5)
shared US       50c =====> $2.50 for 5
dedicated US    $1.20
dedicated UK    $2

AWS             1c/hour => $7.20
NordVPN         $3.50 + AWS cost
Tor             0

