Mproxy
======

This enables http requests via rotating proxies that are automatically replaced if blocked.
AWS proxies cost less than 1c/hour/proxy OR one can use an existing NordVPN account (NOTE I have not tested the NordVPN code so may need to be adapted to work!).

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

Probably option 1 is most useful but YMMV.

Option 1 - automatically replaces proxy and retries
    search = m.get_proxy_function(google.search)
    urls = search("trump", before="20200701", after="20200701")
    # onProxyException => search function raises ProxyException

Option 2 - manual retry and exception handling. more control and access to current session:
    session = m.get_proxy_session()
    urls = search(session, "trump", before="20200701", after="20200701")
    # onProxyException => search function calls session.replace(); handles retries.

Option 3 - automatic but with access to session
    session = m.get_proxy_session()
    search = session.get_proxy_function(google.search)
    urls = search("trump", before="20200701", after="20200701")
    # onProxyException => search function raises ProxyException
    
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
