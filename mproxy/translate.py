#!/usr/bin/env python

from googletrans import Translator
import requests
import json
import logging

log = logging.getLogger(__name__)


class Translate:
    """ mproxy client for google translate

    Usage::

        t = Translate(mproxy)
        t.translate("something", src="en", dest="de")
    """

    def __init__(self, mproxy=None):
        """
        :param mproxy: mproxy object or client connection. None for translate without proxies
        """
        self.mproxy = mproxy

        if mproxy is None:
            self.proxy = None
            self.translator = Translator()
        else:
            self.proxy = mproxy.get_proxy_url()
            # note cannot set translator.session directly as translator init passes session to other objects
            self.translator = Translator(
                proxies=dict(http=self.proxy, https=self.proxy), timeout=7
            )

    def refresh(self):
        """ refresh translator session with a new proxy """
        self.mproxy.replace(self.proxy)
        self.translator.session.close()
        self.proxy = self.mproxy.get_proxy_url()
        self.translator = Translator(
            proxies=dict(http=self.proxy, https=self.proxy), timeout=7
        )
        # if google translate not responding then raise exception
        text = self.translator.translate(
            "The cat sat on the mat", src="en", dest="fr"
        ).text
        log.info(f"{self.proxy} {text}")

    def translate(self, text, src="auto", dest="en"):
        """
        :return: translated text
        """
        while True:
            try:
                log.info(f"translating {src} to {dest} for {text[:100]}")
                return self.translator.translate(text, src=src, dest=dest).text
            except Exception as e:
                if self.mproxy is None:
                    raise
                # get new proxy and try again
                log.warning(
                    f"api limit reached. replacing {self.proxy}. exception={type(e)}"
                )
                self.refresh()
                return ""