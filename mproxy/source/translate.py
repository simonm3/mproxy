import json
import logging

import requests
from googletrans import Translator

log = logging.getLogger(__name__)


class Translate:
    """ manager client for google translate

    todo this does not currently work as google recognises proxy switches

    Usage::

        t = Translate(manager)
        t.translate("something", src="en", dest="de")
    """

    def __init__(self, manager=None):
        """
        :param manager: manager object or client connection. None for translate without proxies
        """
        self.manager = manager

        if manager is None:
            self.proxy = None
            self.translator = Translator()
        else:
            self.proxy = manager.get_url()
            # note cannot set translator.session directly as translator init passes session to other objects
            self.translator = Translator(
                proxies=dict(http=self.proxy, https=self.proxy), timeout=7
            )

    def refresh(self):
        """ refresh translator session with a new proxy """
        self.manager.replace(self.proxy)
        self.translator.session.close()
        self.proxy = self.manager.get_url()
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
        raise NotImplementedError(
            "this does not currently work as google recognises proxy switches even if elite"
        )
        while True:
            try:
                log.info(f"translating {src} to {dest} for {text[:100]}")
                return self.translator.translate(text, src=src, dest=dest).text
            except Exception as e:
                if self.manager is None:
                    raise
                # get new proxy and try again
                log.warning(
                    f"api limit reached. replacing {self.proxy}. exception={type(e)}"
                )
                self.refresh()
                return ""
