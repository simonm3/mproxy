#!/usr/bin/env python

import requests
from fake_useragent import UserAgent
from datetime import datetime, timedelta
from urllib.parse import urlparse, parse_qs
from bs4 import BeautifulSoup

import logging

log = logging.getLogger(__name__)


class Stypes:
    """ types of results required """

    images = "isch"
    news = "nws"
    videos = "vid"
    shop = "shop"
    books = "bks"
    apps = "app"


class Proxysearch:
    """ enables search using multiple proxies """
    def __init__(self, mproxy):
        self.mproxy = mproxy
        self.refresh()

    @property
    def proxy_url(self):
        return self.session.proxies["http"]

    def refresh(self):
        """ refresh session with a new proxy """
        self.mproxy.wait(1)
        proxy = self.mproxy.get_proxy_url()
        s = requests.session()
        s.proxies = dict(http=proxy)
        s.headers = {"User-Agent": UserAgent().chrome}
        # do not overwrite with environment variables
        s.trust_env = False
        self.session = s

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
        :param safe: no porn
        :param n: number of results
        :param start: index of first result
        :param lang: language
        :param from_date: YYYYMMDD or python date. default is 365 days before today.
        :param to_date: YYYYMMDD or python date. default is today.
        :param domain: e.g. www.guardian.co.uk
        :param stype: from search.Stypes. type of search e.g. video
        :return: list of urls

        todo: tld, country no longer work. may need to change settings via selenium as done via cookies even incognito
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

        path = "/search"
        params = dict(
            q=f"site:{domain} {query}",
            hl=lang,
            num=min(n, 100),
            start=start,
            tbs=tbs,
            safe=safe,
            tbm=stype,
        )

        # iterate pages
        urls = []
        while True:
            # get page
            r = self.get(f"http://www.google.com{path}", params=params)

            # extract urls
            soup = BeautifulSoup(r.text, "lxml")
            urls.extend(self.extract_urls(soup))
            urls = list(dict.fromkeys(urls))

            # limit reached
            if len(urls) >= n:
                break

            # next page
            next_page = soup.find(id="pnnext")
            if not next_page:
                break
            path = next_page["href"]
            params = dict()

        return list(urls)

    def get(self, url, params):
        """ get with retry """
        while True:
            try:
                r = self.session.get(url, params=params)
                r.raise_for_status()
            except requests.exceptions.ProxyError:
                log.warning(f"proxy error. replacing proxy {self.proxy_url}")
                self.mproxy.replace(self.proxy_url)
                self.refresh()
                continue
            except requests.exceptions.HTTPError:
                if self.proxy_failed(r):
                    log.warning(f"api limit reached. replacing {self.proxy_url}")
                    self.mproxy.replace(self.proxy_url)
                    self.refresh()
                    continue
            return r

    def proxy_failed(self, r):
        """ overwrite to define when proxy needs replacing """
        return r.status_code == 429

    def extract_urls(self, soup):
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