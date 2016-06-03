"""
NOTE: This file is no longer being used to generate the website.
      However, it is possible that not all logic has been ported over,
      so we will keep it around for now as a reference.
"""

import argparse
from collections import defaultdict
from datetime import datetime
import docutils
import glob
import io
import json
import os
import re
import shutil
import signal
import sys
from urllib.parse import urlparse

from pelican import DEFAULT_CONFIG_NAME
from pelican.readers import RstReader, PelicanHTMLTranslator
from pelican.settings import read_settings
from pelican.utils import slugify

CONTENT_DIR = 'content'
CONTENT_DIR_KEEP = set(('pages', 'images', 'extra'))
DEFUALT_DATA_DIR = os.path.join('pyvideo-data', 'data')
DATE_FORMAT = '%Y-%m-%d'
DATETIME_FORMAT = '%Y-%m-%d %H:%M'
DATETIME_FORMATS_BY_RE_PATTERN = {
    r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$': '%Y-%m-%d %H:%M:%S',
    r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$': '%Y-%m-%dT%H:%M:%S',
    r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$': '%Y-%m-%d %H:%M',
    r'^\d{4}-\d{2}-\d{2}$': DATE_FORMAT,
}
DATETIME_FORMATS_BY_RE_PATTERN = {
    re.compile(key): value for key, value in
    DATETIME_FORMATS_BY_RE_PATTERN.items()
}
DATETIME_WITH_MICRO_PATTERN = re.compile(r'^(.*)\.\d+$')
DEFAULT_SETTINGS = read_settings(DEFAULT_CONFIG_NAME)
DEFAULT_THUMBNAIL_URL = '/images/default_thumbnail_url.png'
# Ordered by preference
MEDIA_URL_KEYS = (
    'source_url',
    'video_flv_url',
    'video_mp4_url',
    'video_ogv_url',
    'video_webm_url'
)
OPTION_INDENT = ' ' * 4


TITLES_BY_CATEGORY = defaultdict(set)


class ArticleMaker:
    """
    Take a JSON file and make an rST file out of the data it contains.
    """
    def __init__(self, json_file_path):
        self.json_file_path = json_file_path
        with open(self.json_file_path) as fp:
            data = json.load(fp)
        self.data = data
        self.output = ''
        self.verbose = False

    def make(self, verbose=False):
        """
        Tie all other methods together to get produce a final rST file.
        """
        self.verbose = verbose
        self.parse()
        self.build()
        self.write()

    def parse(self):
        self.parse_title()
        if self.verbose:
            print('Making {}'.format(self.json_file_path), flush=True)
        self.parse_date_datetime()
        self.parse_modified_datetime()
        self.parse_tags()
        self.parse_category()
        if self.title in TITLES_BY_CATEGORY[self.category]:
            raise ValueError('Duplicate file {}'.format(self.json_file_path))
        else:
            TITLES_BY_CATEGORY[self.category].add(self.title)
        self.parse_authors()
        self.parse_thubmnail_url()
        self.parse_media_url()
        self.parse_summary()
        self.parse_description()

    def build(self):
        self.build_header()
        self.build_body()

    def parse_title(self):
        self.title = (self.data.get('title') or '').strip()

    def parse_date_datetime(self):
        date = (self.data.get('date') or '').strip()
        if not date:
            date = (self.data.get('added') or '').strip()
        if not date:
            date = (self.data.get('recorded') or '').strip()

        if not date:
            # fall back to an old date
            date = datetime(1990, 1, 1).date().strftime(DATE_FORMAT)

        self.date = self.coerce_datetime(date)

    def parse_modified_datetime(self):
        modified = (self.data.get('updated') or '').strip()
        if not modified:
            self.modified_date = None
            return

        self.modified_date = self.coerce_datetime(modified)

    def coerce_datetime(self, datetime_string):
        """
        Return a string in DATETIME_FORMAT given datetime_string
        """
        # strip microseconds from all datetimes
        match = DATETIME_WITH_MICRO_PATTERN.match(datetime_string)
        if match:
            datetime_string = match.group(1)

        for pattern, format_ in DATETIME_FORMATS_BY_RE_PATTERN.items():
            if pattern.match(datetime_string):
                dt = datetime.strptime(datetime_string, format_)
                return dt.strftime(DATETIME_FORMAT)

        msg = 'Error in {}: Date pattern not recognized'.format(datetime_string)
        raise ValueError(msg)

    def parse_tags(self):
        tags = self.data.get('tags') or ()
        # strip tags of whitespace
        tags = map(lambda x: x.strip(), tags)
        # ignore empty tags
        tags = filter(lambda x: bool(x), tags)
        tags = map(slugify, tags)
        self.tags = tags

    def parse_category(self):
        self.category = (self.data.get('category') or '').strip()
        if not self.category:
            path = self.json_file_path.replace(CONTENT_DIR, '')
            self.category = path.split(os.sep)[-3]

    def parse_authors(self):
        authors = self.data.get('speakers') or ()
        authors = map(lambda x: x.strip(), authors)
        author = filter(lambda x: bool(x), authors)
        self.authors = list(self.quote_text_list(authors))

    def quote_text_list(self, text_list):
        for text in text_list:
            if '.' in text:
                text = '"' + text + '"'
            yield text

    def parse_thubmnail_url(self):
        thumbnail_url = (self.data.get('thumbnail_url') or '').strip()
        thumbnail_url = thumbnail_url or DEFAULT_THUMBNAIL_URL
        self.media_thubmnail_url = thumbnail_url

    def parse_media_url(self):
        for url_key in MEDIA_URL_KEYS:
            url = (self.data.get(url_key) or '').strip()
            if url:
                break

        if not url:
            videos = self.data.get('videos') or []
            for video in videos:
                url = video.get('url')
                if url:
                    break

        if not url:
            msg = 'Error in {}: no valid media URL found'.format(self.json_file_path)
            raise ValueError(msg)

        if 'youtu' in url:
            url = self.get_youtube_url(url)

        self.media_url = url

    def get_youtube_url(self, url):
        video_id = ''
        o = urlparse(url)
        if '/watch?v=' in url:
            query_pairs = o.query.split('&')
            pairs = (pair.split('=') for pair in query_pairs if '=' in pair)
            video_id = dict(pairs).get('v')
        elif '/v/' in url:
            video_id = o.path.replace('/v/', '')
        elif 'youtu.be/' in url:
            video_id = o.path

        return 'https://www.youtube.com/embed/{}'.format(video_id)

    def parse_summary(self):
        self.summary = (self.data.get('summary') or '').strip()

    def parse_description(self):
        self.description = (self.data.get('description') or '').strip()

    def build_header(self):
        lines = []

        # build title line and underline
        title_line = self.title.replace('*', '\*')
        lines.append(title_line)
        lines.append('#' * len(bytes(title_line.encode())))
        lines.append('')  # add extra line break after title

        # build meta data section
        lines.append(':date: {}'.format(self.date))

        if self.modified_date:
            lines.append(':modified: {}'.format(self.modified_date))

        if self.tags:
            lines.append(':tags: {}'.format(', '.join(self.tags)))

        lines.append(':category: {}'.format(self.category))
        lines.append(':slugified_category: {}'.format(slugify(self.category)))

        #lines.append(':slug: {}'.format(slugify(self.title)))

        authors_string = ', '.join(self.authors) or 'Unknown'
        lines.append(':authors: {}'.format(authors_string))

        # The RstReader has trouble reading metadata strings that
        # contain underscores, even if those underscores are escaped with
        # backslashes. Thus, underscores are escaped here with a string.
        # Real underscores are re-introduced by the replace_underscore
        # plugin defined in bin/plugins.
        thumbnail_url = self.media_thubmnail_url.replace('_', 'UNDERSCORE')
        lines.append(':thumbnail_url: {}'.format(thumbnail_url))

        media_url = self.media_url.replace('_', 'UNDERSCORE')
        lines.append(':media_url: {}'.format(media_url))

        lines.append(':data_file: {}'.format(self.json_file_path))

        self.output += '\n'.join(lines)
        self.output += '\n'

    def build_body(self):
        lines = []

        if self.summary:
            summary = '\n\nSummary\n-----------\n\n' + self.summary
            lines.append(summary)

        if self.description:
            description_header = '\n\nDescription\n-----------\n\n'
            self.description = description_header + self.description
            lines.append(self.description)

        body = '\n'.join(lines)

        error_string = self.validate_rst(body)
        if error_string:
            msg = '\n\nRendering Error. Could not render {}\n'
            self.output += msg.format(self.json_file_path)
        else:
            self.output += body + '\n\n'

    def write(self):
        path_parts = self.json_file_path.split(os.sep)

        # make category dir if necessary
        subdirectory = path_parts[-3]
        sub_dir_path = os.path.join(CONTENT_DIR, subdirectory)

        if not os.path.exists(sub_dir_path):
            if self.verbose:
                print('Creating sub dir {}'.format(sub_dir_path), flush=True)
            os.mkdir(sub_dir_path)

        name = path_parts[-1][:-4] + 'rst'
        path = os.path.join(sub_dir_path, name)

        if self.verbose:
            print('Writing {}'.format(path), flush=True)
        with open(path, 'w') as fp:
            fp.write(self.output)

    def validate_rst(self, body):
        if self.verbose:
            print('Validating {}'.format(self.json_file_path), flush=True)

        source = io.StringIO(body)
        error_string = None
        try:
            with StdOutRedirect(os.devnull), StdErrRedirect(os.devnull):
                TestRstReader(DEFAULT_SETTINGS).read(source)
        except BaseException as e:
            error_string = str(e)

        if self.verbose:
            print('Validation complete {}'.format(self.json_file_path), flush=True)

        return error_string


class TestRstReader(RstReader):
    def _get_publisher(self, source):
        extra_params = {'initial_header_level': '2',
                        'syntax_highlight': 'short',
                        'input_encoding': 'utf-8',
                        'exit_status_level': 2,
                        'embed_stylesheet': False}
        user_params = self.settings.get('DOCUTILS_SETTINGS')
        if user_params:
            extra_params.update(user_params)

        pub = docutils.core.Publisher(
            source_class=self.FileInput,
            destination_class=docutils.io.StringOutput)
        pub.set_components('standalone', 'restructuredtext', 'html')
        pub.writer.translator_class = PelicanHTMLTranslator
        pub.process_programmatic_settings(None, extra_params, None)
        pub.set_source(source=source)
        pub.publish(enable_exit_status=True)
        return pub

    def read(self, source):
        """Parses restructured text"""
        pub = self._get_publisher(source)
        parts = pub.writer.parts
        content = parts.get('body')

        metadata = self._parse_metadata(pub.document)
        metadata.setdefault('title', parts.get('title'))

        return content, metadata


class StdOutRedirect(object):
    def __init__(self, filename):
        self.stream = open(filename, 'w')
        self.old_stdout = None

    def __enter__(self):
        self.old_stdout = sys.stdout
        sys.stdout = self.stream

    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout = self.old_stdout


class StdErrRedirect(object):
    def __init__(self, filename):
        self.stream = open(filename, 'w')
        self.old_stderr = None

    def __enter__(self):
        self.old_stderr = sys.stderr
        sys.stderr = self.stream

    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stderr = self.old_stderr


def process_json_file(args):
    json_file_path, verbose = args
    maker = ArticleMaker(json_file_path)
    try:
        maker.make(verbose=verbose)
    except BaseException as e:
        print(e, flush=True)


def remove_old_content(verbose=False):
    if verbose:
        print('Remove old content ...', flush=True)

    # clear content dir of most content
    contents = set(os.listdir(CONTENT_DIR))
    contents_to_delete = contents - CONTENT_DIR_KEEP
    for sub_dir in contents_to_delete:
        shutil.rmtree(os.path.join(CONTENT_DIR, sub_dir))

    if verbose:
        print('Remove old output directory ...', flush=True)

    # remove output dir
    if os.path.exists('output'):
        shutil.rmtree('output')


def run_article_maker(data_dir, process_count, verbose=False):
    if verbose:
        print('Searching for media records (JSON files) ...', flush=True)

    remove_old_content(verbose)

    json_file_paths = []
    pattern = '{}/**/*.json'.format(data_dir)
    for path in glob.iglob(pattern, recursive=True):
        if path.split(os.sep)[-1] != 'category.json':
            json_file_paths.append(path)

    args_gen = ((path, verbose) for path in json_file_paths)
    for args in args_gen:
        process_json_file(args)


def parse_arguments():
    parser = argparse.ArgumentParser(
        description=(
            "A tool for converting JSON data in to Pelican ready rST files"
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument('-f', '--file',
                        help='File to run article maker on',
                        default=None)

    parser.add_argument('-d', '--data-dir',
                        dest='data_dir',
                        help='data directory to run article maker over',
                        default=DEFUALT_DATA_DIR)

    parser.add_argument('-p', '--process-count',
                        dest='process_count',
                        help='Number of processes',
                        type=int,
                        default=None)

    parser.add_argument('-v', '--verbose',
                        action='store_true',
                        help='Print lots of details of progress',
                        default=False)

    return parser.parse_args()


def main():
    args = parse_arguments()

    if args.file:
        process_json_file((args.file, args.verbose))
    else:
        run_article_maker(args.data_dir, args.process_count, args.verbose)


if __name__ == '__main__':
    main()

