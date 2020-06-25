from urllib.parse import urlparse


def ip2url(ip):
    """ ip used by aws; url used by client """
    return f"http://{ip}:8888"


def url2ip(url):
    """ ip used by aws; url used by client """
    return urlparse(url).netloc.split(":")[0]
