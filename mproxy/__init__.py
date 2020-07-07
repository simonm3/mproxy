from mproxy.proxy.proxyaws import ProxyAWS

from .google import Google, Stypes
from .googleproxy import GoogleProxy
from .translate import Translate
from .utils.share import create_client, create_server

"""
todo convert to libcloud

search(session, query)

session
    start
    stop
    get = return result. raise StopException. and stop.

proxymanager(session)
    start - n
    stop - all
    get 
        try different sessions
        on stop exception create/start new session

"""
