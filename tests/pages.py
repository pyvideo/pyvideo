# -*- coding: utf-8 -*-
from pathlib import Path

from bok_choy.page_object import PageObject
from selenium.webdriver.common.keys import Keys

PORT = 8081
TITLE_TEMPLATE = 'PyTube.org \u00B7 {}'


class AboutPage(PageObject):
    """
    Testing representation of the About page
    """
    url = 'http://localhost:{}/pages/about.html'.format(PORT)

    def is_browser_on_page(self):
        return self.browser.title == TITLE_TEMPLATE.format('About')


class EventPage(PageObject):
    """
    Testing representation of a sample event page
    """
    url = 'http://localhost:{}/events/pydata.html'.format(PORT)

    def is_browser_on_page(self):
        return self.browser.title == TITLE_TEMPLATE.format('PyData')


class EventsPage(PageObject):
    """
    Testing representation of the events listing page
    """
    url = 'http://localhost:{}/events.html'.format(PORT)

    def is_browser_on_page(self):
        return self.browser.title == TITLE_TEMPLATE.format('Events')


class IndexPage(PageObject):
    """
    Testing representation of the main page of the site
    """
    url = 'http://localhost:{}/index.html'.format(PORT)

    def is_browser_on_page(self):
        return self.browser.title == 'PyTube.org'

    def search(self, phrase):
        """
        Enter a search phrase and display the results
        """
        selector = 'input.gsc-input'
        self.wait_for_element_visibility(selector, 'Search input available')
        self.q(css=selector).fill(phrase + Keys.ENTER)
        self.wait_for_element_visibility('.gsc-results', 'Search results shown')


class MP4Page(PageObject):
    """
    Testing representation of a sample MP4 video page
    """
    url = 'http://localhost:{}/pyohio-2011/pyohio-2011--saturday-lightning-talks.html'.format(PORT)

    def is_browser_on_page(self):
        return self.browser.title == TITLE_TEMPLATE.format('PyOhio 2011: Saturday Lightning Talks')


class OGVPage(PageObject):
    """
    Testing representation of a sample OGV video page
    """
    url = 'http://localhost:{}/pycon-za-2013/python-in-debian-and-ubuntu.html'.format(PORT)

    def is_browser_on_page(self):
        return self.browser.title == TITLE_TEMPLATE.format('Python in Debian and Ubuntu')


class SpeakerPage(PageObject):
    """
    Testing representation of a sample speaker page
    """
    url = 'http://localhost:{}/speaker/glyph.html'.format(PORT)

    def is_browser_on_page(self):
        return self.browser.title == TITLE_TEMPLATE.format('Glyph')


class SpeakersPage(PageObject):
    """
    Testing representation of the speakers listing page
    """
    url = 'http://localhost:{}/speakers.html'.format(PORT)

    def is_browser_on_page(self):
        return self.browser.title == TITLE_TEMPLATE.format('Speakers')


class TagPage(PageObject):
    """
    Testing representation of a sample tag page
    """
    url = 'http://localhost:{}/tag/subtitles/'.format(PORT)

    def is_browser_on_page(self):
        return self.browser.title == TITLE_TEMPLATE.format('subtitles')


class TagsPage(PageObject):
    """
    Testing representation of the tags listing page
    """
    url = 'http://localhost:{}/tags.html'.format(PORT)

    def is_browser_on_page(self):
        return self.browser.title == TITLE_TEMPLATE.format('Tags')


class VimeoPage(PageObject):
    """
    Testing representation of a sample Vimeo video page
    """
    url = 'http://localhost:{}/boston-python-meetup/boston-python-meetup--testing--where-do-i-start.html'.format(PORT)

    def is_browser_on_page(self):
        return self.browser.title == TITLE_TEMPLATE.format('Boston Python Meetup: Testing: Where do I start?')


class YouTubePage(PageObject):
    """
    Testing representation of a sample YouTube video page
    """
    url = 'http://localhost:{}/europython-2011/browse-and-print-problems-and-solutions.html'.format(PORT)

    def is_browser_on_page(self):
        return self.browser.title == TITLE_TEMPLATE.format('Browse and print problems and solutions')
