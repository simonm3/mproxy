import logging
from datetime import datetime, timedelta
from urllib.parse import parse_qs, urlparse

import requests
from bs4 import BeautifulSoup

log = logging.getLogger(__name__)


class Stypes:
    """ types of results required """

    images = "isch"
    news = "nws"
    videos = "vid"
    shopping = "shop"
    books = "bks"
    apps = "app"


class Google:
    """ google search

    Usage::

        s = Google()
        s.search("something)
    """

    def __init__(self):
        self.session = requests.session()

    def search(
        self,
        query,
        safe="off",
        n=10,
        start=1,
        lang="en",
        from_date=None,
        to_date=None,
        domain=None,
        stype="",
    ):
        """ search google and return list of urls
        :param query: search string
        :param safe: "on" filters porn and other things
        :param n: number of results. 99/page so 100 returns 198.
        :param start: index of first result
        :param lang: language
        :param from_date: YYYYMMDD or python date. default is 365 days before today.
        :param to_date: YYYYMMDD or python date. default is today.
        :param domain: e.g. www.guardian.co.uk
        :param stype: from search.Stypes. type of search e.g. video
        :return: list of urls

        searches are location specific based on ip address (tld and country are ignored)
        can change location in settings but this is encrypted so unclear how to encode
        """
        # date range
        tbs = ""
        if from_date or to_date:
            # convert to datetime
            if isinstance(from_date, str):
                from_date = datetime.strptime(from_date, "%Y%m%d")
            if isinstance(to_date, str):
                to_date = datetime.strptime(to_date, "%Y%m%d")

            # defaults
            if not to_date:
                to_date = datetime.today()
            if not from_date:
                from_date = to_date - timedelta(days=365)

            # convert to str
            from_date = from_date.strftime("%m/%d/%Y")
            to_date = to_date.strftime("%m/%d/%Y")
            tbs = f"cdr:1,cd_min:{from_date},cd_max:{to_date}"

        if domain:
            query = f"site:{domain} {query}"

        # results per page=num-1. maximum num=100 which returns up to 99 results.
        path = "/search"
        params = dict(
            q=query,
            hl=lang,
            num=min(n, 100),
            start=start,
            tbs=tbs,
            safe=safe,
            tbm=stype,
            btnG="Google Search",
            cr="",
        )

        # iterate pages
        urls = []
        while True:
            # get page. must be https to include date search.
            r = self._get(f"https://google.com{path}", params=params)

            # extract urls from page
            soup = BeautifulSoup(r.text, "lxml")
            urls.extend(self._extract_urls(soup))

            # dedupe
            urls = list(dict.fromkeys(urls))

            # limit reached
            if len(urls) >= n:
                break

            # next page
            path = None
            params = None
            try:
                path = soup.find(id="pnnext").get("href")
            except:
                pass
            if not path:
                break
        return list(urls)

    def _extract_urls(self, soup):
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
        return urls

    def _get(self, url, params):
        return self.session.get(url, params=params)
