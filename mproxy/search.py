#!/usr/bin/env python

import requests
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs
from . import ua, uacode

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


class Search:
    """ mproxy client for google search

    Usage::

        s = Search(mproxy)
        s.search("something")
    """

    def __init__(self, mproxy=None):
        """
        :param mproxy: mproxy object. None to search without proxies
        """
        self.mproxy = mproxy
        if mproxy is None:
            self.session = requests.session()
            self.session.headers = {"User-Agent": ua}
        else:
            self.mproxy = mproxy
            self.session = self.mproxy.get_session()
            self.proxy = self.session.proxies["http"]
        self.session.trust_env = False

    def refresh(self):
        """ refresh with a new proxy """
        self.mproxy.replace(self.proxy)
        self.session.close()
        self.session = self.mproxy.get_session()

        # fail if google search not responding
        r = self.session.get(f"https://google.com/search?q=something")
        r.raise_for_status()

    def get(self, url, params):
        """ get with proxy replacement for google search """
        while True:
            try:
                r = self.session.get(url, params=params, timeout=7)
                r.raise_for_status()
                return r
            except Exception as e:
                if self.mproxy is None:
                    raise
                # get new proxy and try again
                log.warning(
                    f"api limit reached. replacing {self.proxy}. exception={type(e)}"
                )
                self.refresh()

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
        :param n: number of results. 99/page so 100 returns 198.
        :param start: index of first result
        :param lang: language
        :param from_date: YYYYMMDD or python date. default is 365 days before today.
        :param to_date: YYYYMMDD or python date. default is today.
        :param domain: e.g. www.guardian.co.uk
        :param stype: from search.Stypes. type of search e.g. video
        :return: list of urls

        todo: tld, country no longer work. may need to change settings via selenium as done via cookies even incognito
        todo thread pages. separate url parse and get OR batch request urls with callback
        todo request limit exceeded describe instances?
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

        # results/page=num-1. maximum 100 which returns up to 99 results.
        path = "/search"
        params = dict(
            q=query,
            hl=lang,
            num=100,
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
            r = self.get(f"https://google.com{path}", params=params)

            # extract urls
            soup = BeautifulSoup(r.text, "lxml")
            urls.extend(self.extract_urls(soup))
            urls = list(dict.fromkeys(urls))

            # limit reached
            if len(urls) >= n:
                break

            # next page
            path = None
            params = None
            try:
                if uacode == "win10":
                    path = soup.find(id="pnnext").get("href")

                elif uacode == "requests":
                    path = [
                        a
                        for a in soup.find_all("a")
                        if a.get("aria-label") == "Next page"
                    ][0].get("href")
                elif uacode == "win6":
                    path = [a for a in soup.find_all("a") if a.text == "Next\xa0>"][
                        0
                    ].get("href")
                else:
                    raise Exception("ua code is required")
            except:
                pass
            if not path:
                break
        return list(urls)

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
