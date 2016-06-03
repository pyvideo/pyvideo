from multiprocessing import Process
import os
from socketserver import TCPServer
import sys
from time import sleep
import unittest

from bok_choy.web_app_test import WebAppTest
from pelican.server import ComplexHTTPRequestHandler

from .pages import AboutPage, EventsPage, IndexPage, PORT, SpeakersPage, TagsPage

def start_test_server():
    os.chdir('output')
    TCPServer.allow_reuse_address = True
    httpd = TCPServer(('', PORT), ComplexHTTPRequestHandler)
    httpd.serve_forever()

class TestAccessibility(WebAppTest):
    """
    Tests for the accessibility of various pages
    """

    @classmethod
    def setUpClass(cls):
        cls.server = Process(target=start_test_server)
        cls.server.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.terminate()

    def test_about(self):
        """
        The About page should have good accessibility
        """
        self._check_a11y(AboutPage)

    def test_events(self):
        """
        The events listing page should have good accessibility
        """
        self._check_a11y(EventsPage)

    def test_index(self):
        """
        The main page should have good accessibility
        """
        self._check_a11y(IndexPage)

    def test_speakers(self):
        """
        The speakers listing page should have good accessibility
        """
        self._check_a11y(SpeakersPage)

    def test_tags(self):
        """
        The events listing page should have good accessibility
        """
        self._check_a11y(TagsPage)

    def _check_a11y(self, page_class):
        """
        Visit the specified page and run accessibility checks on it
        """
        page = page_class(self.browser)
        page.visit()
        report = page.a11y_audit.check_for_accessibility_errors()

if __name__ == '__main__':
    unittest.main()
