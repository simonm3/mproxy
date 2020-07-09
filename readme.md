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

Option 1 - automatically replaces proxy and retries once (can increase tries param for get_proxy_function)
    session = m.get_proxysession()
    search = session.get_proxy_function(google.search)
    urls = search("trump", before="20200701", after="20200701")
    
    # onProxyException => raise ProxyException

Option 2 - manual retry and exception handling:
    session = m.get_proxysession()
    urls = search(session, "trump", before="20200701", after="20200701")
    
    # onProxyException => session.replace(); handle retry
    
Multiprocessing usage::

    from mproxy.utils import create_server, create_client

    # main process
    m = Manager()
    m = create_server(m)
    m.add(AWS, 2)
    
    # other processes
    m = create_client()
    session = m.get_proxysession()
    search = session.get_proxy_function(search)

    urls = search("trump", before="20200701", after="20200701")
    # onProxyException => raise ProxyException
    

Modules
-------

Manager - rotates proxies
Proxy (AWS, AWSNord, Tor) - proxy server
Session - requests session. get method traps ProxyException; replace method replaces proxy.
source (google, translate) - function that takes a session parameter; raises ProxyException or calls session.replace() 
  

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
