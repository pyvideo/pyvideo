# -*- coding: utf-8 -*-
from pathlib import Path

from bok_choy.page_object import PageObject

PORT = 8081


class AboutPage(PageObject):
    """
    Testing representation of the About page
    """
    url = 'http://localhost:{}/pages/about.html'.format(PORT)

    def is_browser_on_page(self):
        return self.browser.title == 'PyTube.org \u00B7 About'


class EventsPage(PageObject):
    """
    Testing representation of the events listing page
    """
    url = 'http://localhost:{}/events.html'.format(PORT)

    def is_browser_on_page(self):
        return self.browser.title == 'PyTube.org \u00B7 Events'


class IndexPage(PageObject):
    """
    Testing representation of the main page of the site
    """
    url = 'http://localhost:{}/index.html'.format(PORT)

    def is_browser_on_page(self):
        return self.browser.title == 'PyTube.org'


class SpeakersPage(PageObject):
    """
    Testing representation of the speakers listing page
    """
    url = 'http://localhost:{}/speakers.html'.format(PORT)

    def is_browser_on_page(self):
        return self.browser.title == 'PyTube.org \u00B7 Speakers'


class TagsPage(PageObject):
    """
    Testing representation of the tags listing page
    """
    url = 'http://localhost:{}/tags.html'.format(PORT)

    def is_browser_on_page(self):
        return self.browser.title == 'PyTube.org \u00B7 Tags'
