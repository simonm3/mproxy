# for testing only
user_agents = dict(
    win10="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.163 Safari/537.36",
    win6="Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.0)",
    requests="python-requests/2.22.0",
)
uacode = "win10"
ua = user_agents[uacode]

from .retry import Retry
from .mproxy import Mproxy
from .search import Search, Stypes
from .translate import Translate
