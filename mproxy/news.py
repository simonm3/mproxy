from datetime import datetime, timedelta
import dateutil
import json
import pandas as pd

import googlesearch
from fake_useragent import UserAgent
import bs4
from newspaper import Article
from tqdm import tqdm_notebook as tqdm
import lxml

from pipemaker.worker.task import progress
import logging

log = logging.getLogger()


def make_urls(
    domain, searchtext="", startdate=None, startperiod=0, endperiod=26, days=14, n=20
):
    """ search across range of dates to get top articles each week rather than top articles for the year
    :param domain: domain to search
    :param searchtext: search string
    :param startdate: python date on which to start. default 2018-01-01
    :param startperiod: period number to start
    :param endperiod: period number to end
    :param days: days per period
    :param n: number of urls to retrieve per period. rate limited to 20?

    range of weeks brings variety otherwise could get lots of articles on single story/week
    default is 26 periods of 14 days i.e. 1 year. rate limit is 35 searches?
    Google do not publish rate limits
    """
    if startdate is None:
        startdate = datetime(2019, 1, 1)

    all_urls = []
    total = len(range(startperiod, endperiod))
    for i, period in enumerate(tqdm(range(startperiod, endperiod))):
        fromDate = startdate + timedelta(days=days * period)
        toDate = fromDate + timedelta(days=days - 1)
        try:
            urls = _search(searchtext, domain=domain, n=n, daterange=(fromDate, toDate))

            # filters
            if domain.startswith("theguardian"):
                urls = [u for u in urls if not u.endswith(("altdate", "all", "audio"))]
        except:
            log.exception(f"failed at {period}")
            # still return so can use results and restart
            return all_urls
        all_urls.extend(urls)

        progress(i, total)

    return all_urls


def make_articles(urls):
    """ download urls and parse into articles
    :param urls: list of urls
    :return: list of article objects
    """

    articles = []
    total = len(urls)
    for i, url in enumerate(tqdm(urls)):
        try:
            a = Article(url)
            a.download()
            a.parse()
            try:
                _add_schema(a)
            except:
                pass
            articles.append(a)
        except KeyboardInterrupt:
            break
        except Exception as e:
            log.exception(f"cannot process {url}\n{e}")
            continue
        progress(i, total)

    # cannot pickle HtmlElements so refresh them
    for article in articles:
        for k, v in article.__dict__.items():
            if isinstance(v, lxml.html.HtmlElement) or isinstance(
                v, bs4.element.ResultSet
            ):
                setattr(article, k, None)

        # this is very large and not needed as we just want the text
        article.html = None

    return articles

def make_keywords(articles, n=3):
    """ return series of top keywords used """
    texts = pd.read_pickle(articles)
    allwords = []
    for text in tqdm(texts):
        try:
            if len(text.split())<20:
                continue
            words = keywords(text, words=n, lemmatize=True)
            if words:
                allwords.extend(words.split("\n"))
        except KeyboardInterrupt:
            break
        except:
            log.warning(f)
    return pd.Series(allwords)


def _add_schema(article):
    """ fill missing values in Article metadata from schema.org which is not supported by newspaper
    :param article: newspaper article object
    todo this can be removed at next newspaper release which includes schema
    """
    ad = article.__dict__

    # map article to schema
    mapping = dict(
        url="url", title="headline", publish_date="datePublished", authors="author"
    )

    # get all schemas on the page
    soup = bs4.BeautifulSoup(article.html, features="lxml")
    schemas = soup.find_all("script", type="application/ld+json")
    ad["schemas"] = schemas

    # get all schemas
    schemas = [json.loads(s.text) for s in schemas]

    # get first article schema
    schema = [
        s for s in schemas if s.get("@type") in ["NewsArticle", "ReportageNewsArticle"]
    ][0]
    if not schema:
        return
    ad["schema"] = schema

    # fill missing values in Article from schema
    for k, v in mapping.items():
        # not missing
        if ad[k]:
            continue

        # missing
        try:
            if k == "authors":
                # convert to list
                author = schema.get(v)
                ad[k] = author if isinstance(author, list) else [author]
            elif k == "publish_date":
                # convert from ISO to python date
                ad[k] = dateutil.parser.parse(schema.get(v))
            else:
                ad[k] = schema.get(v)

            # todo temporary message to check if this function is adding value
            if ad[k]:
                log.warning(f"{k} found in using schema.org")
        except:
            pass


def _search(searchtext, domain=None, daterange=None, n=10, **kwargs):
    """ return google _search in pagerank order for date range
    :param searchtext: _search term
    :param domain: site
    :param daterange: str "yyyymmdd-yyyymmdd" OR python dates tuple (fromDate, toDate)
    :param n: number of links to fetch
    :return: generator of links in pagerank order

    this is rate limited.todo enable use of scrapoxy which makes requests via a pool of proxies
    paid google _search api does not support _search by date
    """
    #  format tbs parameter for date range
    tbs = None
    if daterange:
        # convert yyyymmdd-yyyymmdd to dates
        if isinstance(daterange, str):
            convertdate = lambda date: datetime.strptime(date, "%Y%m%d")
            daterange = daterange.split("-")
            daterange = convertdate(daterange[0]), convertdate(daterange[1])
        tbs = googlesearch.get_tbs(*daterange)

    # daterange ignored unless up to date useragent. ignored if none or outdated such as googlesearch random/default.
    r = googlesearch.search(
        searchtext,
        domains=[domain],
        tld="com",
        user_agent=UserAgent().random,
        tbs=tbs,
        num=n,
        stop=n,
        **kwargs,
    )
    return r
