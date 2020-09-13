import logging
from datetime import datetime, timedelta
from urllib.parse import parse_qs, urlparse

import requests
from bs4 import BeautifulSoup

from ..proxysession import ProxyException

log = logging.getLogger(__name__)


class Stypes:
    """ types of results required """

    images = "isch"
    news = "nws"
    videos = "vid"
    shopping = "shop"
    books = "bks"
    apps = "app"


def search(
    session,
    query,
    n=99,
    start=1,
    lang="en",
    after=None,
    before=None,
    site=None,
    stype="",
    **kwargs,
):
    """ search google and return list of urls
    :param query: search string
    :param n: number of results. 99/page so 100 returns 198.
    :param start: index of first result
    :param lang: language
    :param after: YYYYMMDD; YYYY-MM-DD; python date
    :param before: YYYYMMDD; YYYY-MM-DD; python date
    :param site: e.g. www.guardian.co.uk
    :param stype: from search.Stypes. type of search e.g. video
    :return: list of urls

    searches are location specific based on ip address (google ignores tld and country)
    can change location in settings but this is encrypted so unclear how to encode
    """

    def get_date(d):
        """ allow yyyymmdd or yyyy-mm-dd or datetime"""
        if isinstance(d, str):
            if "-" in d:
                d = datetime.strptime(d, "%Y-%m-%d")
            else:
                d = datetime.strptime(d, "%Y%m%d")
        return d.strftime("%Y-%m-%d")

    after = get_date(after)
    before = get_date(before)

    if before:
        query = f"before:{before} {query}"
    if after:
        query = f"after:{after} {query}"
    if site:
        query = f"site:{site} {query}"

    # results per page=num-1. maximum num=100 which returns up to 99 results.
    path = "/search"
    params = dict(q=query, hl=lang, tbm=stype, start=start, num=min(n, 100), **kwargs)

    # iterate pages
    urls = []
    while True:
        # get page. must be https to include date search.
        r = session.get(f"https://google.com{path}", params=params)
        log.debug(r.url)
        if r.status_code != 200:
            raise ProxyException

        # extract urls from page
        soup = BeautifulSoup(r.text, "lxml")
        urls.extend(extract_urls(soup))

        # next page
        if len(urls) >= n:
            break
        path = None
        params = None
        try:
            path = soup.find(id="pnnext").get("href")
        except:
            break
    return list(urls)


def extract_urls(soup):
    """ return search result urls from page """
    urls = []
    links = soup.findAll("a")
    for link in links:
        url = link.get("href")
        if not url:
            continue
        if url.startswith("/url?"):
            o = urlparse(url, "http")
            url = parse_qs(o.query)["q"][0]
        o = urlparse(url, "http")
        if o.netloc and "google" not in o.netloc:
            urls.append(url)
    # dedupe
    urls = list(dict.fromkeys(urls))
    return urls
