#!/usr/bin/env python
# -*- coding: utf-8 -*- #
from __future__ import unicode_literals
import json
import os

AUTHOR = 'Unknown'
SITENAME = 'PyVideo.org'

PATH = 'content'
DATA_DIR = 'conferences'
NO_PUBLISH_FILE = 'NO_PUBLISH.json'
IGNORE_FILES = [
    '.#*',
    'category.json',
    'CONTRIBUTING.rst',
    'CONTRIBUTORS_WITHOUT_COMMITS.rst',
    NO_PUBLISH_FILE,
    'README.rst',
    '*.schemas/video.json',
    '*posters/apsimregions-a-gridded-modeling-framework-for-th.json',
]

TIMEZONE = 'UTC'

DEFAULT_LANG = 'en'

DEFAULT_PAGINATION = 10

DEFAULT_CATEGORY = "Undefined"

AUTHOR_URL = AUTHOR_SAVE_AS = 'speaker/{slug}.html'
ARTICLE_URL = ARTICLE_SAVE_AS = '{category}/{slug}.html'
ARTICLE_LANG_URL = ARTICLE_LANG_SAVE_AS = '{category}/{slug}-{lang}.html'
DRAFT_URL = DRAFT_SAVE_AS = 'drafts/{category}/{slug}.html'
DRAFT_LANG_URL = DRAFT_LANG_SAVE_AS = 'drafts/{category}/{slug}-{lang}.html'
PAGE_URL = PAGE_SAVE_AS = 'pages/{slug}.html'
PAGE_LANG_URL = PAGE_LANG_SAVE_AS = 'pages/{slug}-{lang}.html'
CATEGORY_URL = CATEGORY_SAVE_AS = 'events/{slug}.html'
TAGS_URL = TAGS_SAVE_AS = 'tags.html'
# Hack to avoid this issue: https://github.com/getpelican/pelican/issues/1137
TAG_URL = 'tag/{slug}/'
TAG_SAVE_AS = 'tag/{slug}/index.html'
# End hack to avoid issue #1137
YEAR_ARCHIVE_SAVE_AS = 'archives/{date:%Y}/index.html'
MONTH_ARCHIVE_SAVE_AS = 'archives/{date:%Y}/{date:%b}/index.html'
CATEGORIES_SAVE_AS = 'events.html'
AUTHORS_SAVE_AS = 'speakers.html'

USE_FOLDER_AS_CATEGORY = False

# Feeds
FEED_MAX_ITEMS = 100
FEED_ALL_ATOM = 'feeds/all.atom.xml'
FEED_ALL_RSS = 'feeds/all.rss.xml'
CATEGORY_FEED_ATOM = 'feeds/event_%s.atom.xml'
CATEGORY_FEED_RSS = 'feeds/event_%s.rss.xml'
AUTHOR_FEED_ATOM = 'feeds/speaker_%s.atom.xml'
AUTHOR_FEED_RSS = 'feeds/speaker_%s.rss.xml'
TAG_FEED_ATOM = 'feeds/tag_%s.atom.xml'
TAG_FEED_RSS = 'feeds/tag_%s.rss.xml'

# Uncomment following line if you want document-relative URLs when developing
RELATIVE_URLS = True

DELETE_OUTPUT_DIRECTORY = True

THEME = 'themes/pytube-201601/'

GITHUB_URL = 'https://github.com/pyvideo/pyvideo'
CONTRIBUTE_URL = 'https://github.com/pyvideo/pyvideo/wiki/How-to-Contribute-Media'
API_URL = 'https://api.pyvideo.org'

STATIC_PATHS = [
    'images',
    'extra/robots.txt',
    'extra/favicon.ico',
    'extra/CNAME',
]

EXTRA_PATH_METADATA = {
    'extra/CNAME': {'path': 'CNAME'},
    'extra/robots.txt': {'path': 'robots.txt'},
    'extra/favicon.ico': {'path': 'favicon.ico'}
}

PLUGIN_PATHS = ['plugins']
PLUGINS = [
    'pelican_alias',
    'drop_no_publish',
    'json_reader',
    'replace_underscore',
    'extended_sitemap',
    'event_series',
    'event_info',
    'aggregations',
    'writer',
]

# https://en.wikipedia.org/wiki/ISO_639-3
# https://en.wikipedia.org/wiki/List_of_ISO_639-3_codes
VIDEO_LANGUAGE_NAMES = {
    'ita': 'Italian',
    'zho': 'Chinese',
    'por': 'Portuguese',
    'ukr': 'Ukrainian',
    'deu': 'German',
    'eng': 'English',
    'rus': 'Russian',
    'fra': 'French',
    'spa': 'Spanish',
    'eus': 'Basque',
    'cat': 'Catalan',
    'glg': 'Galician',
    'kor': 'Korean',
    'lit': 'Lithuanian',
    'jpn': 'Japanese',
    'slk': 'Slovak',
}

def jinja_language_name(code):
    return VIDEO_LANGUAGE_NAMES.get(code, code)

JINJA_FILTERS = {
    'language_name': jinja_language_name,
}

try:
    PR_NUMBER = int(os.environ.get('TRAVIS_PULL_REQUEST'))
except (TypeError, ValueError):
    PR_NUMBER = None
