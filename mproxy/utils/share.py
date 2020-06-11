"""
convenience functions for sharing objects with multiple processes or machines
"""
import logging
from multiprocessing.managers import BaseManager
from threading import Thread

log = logging.getLogger(__name__)

ip = "127.0.0.1"
port = 4006
authkey = b"aaa"


def create_server(obj, ip=ip, port=port, authkey=authkey):
    """ start server to share object with multiple processes

    :param obj: object to publish on server
    :param ip: ip address for server
    :param port: port number for server
    :param authkey: binary key to be used by server and client
    """

    def target(obj):
        try:
            Manager.register("get_obj", callable=lambda: obj)
            m = Manager((ip, port), authkey=authkey)
            try:
                s = m.get_server()
                s.serve_forever()
            except OSError:
                log.warning("server already running")
        except:
            log.exception("error creating server")

    class Manager(BaseManager):
        pass

    t = Thread(
        target=target, daemon=True, args=(obj,), name=f"create_server port={port}"
    )
    t.start()


def create_client(ip=ip, port=port, authkey=authkey):
    """ return client to use object in multiple processes

    :param ip: ip address for server
    :param port: port number for server
    :param authkey: binary key to be used by server and client
    :return: proxy_object for use in processes
    """
    # redefined here as must be different class to the create_server but with same name
    class Manager(BaseManager):
        pass

    Manager.register("get_obj")
    m = Manager((ip, port), authkey=authkey)
    m.connect()
    return m.get_obj()
