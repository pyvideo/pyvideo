import argparse
from datetime import datetime
import glob
import json
import multiprocessing
import os
import re
import shutil
import signal
from urllib.parse import urlparse

from pelican import DEFAULT_CONFIG_NAME
from pelican.readers import RstReader
from pelican.settings import read_settings
from pelican.utils import slugify


CONTENT_DIR = 'content'
CONTENT_DIR_KEEP = set(('pages', 'images', 'extra'))
DEFUALT_DATA_DIR = os.path.join('pyvideo-data', 'data')
DATETIME_FORMAT = '%Y-%m-%d %H:%M'
DATETIME_FORMATS_BY_RE_PATTERN = {
    r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$': '%Y-%m-%d %H:%M:%S',
    r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$': '%Y-%m-%dT%H:%M:%S',
    r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$': '%Y-%m-%d %H:%M',
    r'^\d{4}-\d{2}-\d{2}$': '%Y-%m-%d',
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


class RstValidationError(Exception):
    pass


class PyTubeError(Exception):
    pass


class TimeoutWrapper:
    def __init__(self, seconds=1):
        self.seconds = seconds

    def handler(self, _sig_num, _frame):
        raise TimeoutError()

    def __enter__(self):
        signal.signal(signal.SIGALRM, self.handler)
        signal.alarm(self.seconds)

    def __exit__(self, _type, _value, _traceback):
        signal.alarm(0)


class ArticleMaker:
    """
    Take a JSON file and make an rST file out of the data it contains.
    """
    def __init__(self, json_file_path, lock):
        self.lock = lock
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
            msg = 'Error in {}: No date provided'.format(self.json_file_path)
            raise PyTubeError(msg)

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
        raise PyTubeError(msg)

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
            self.category = path.split(os.sep)[0]

        if not self.category:
            raise ValueError('Each article requires a category')

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
            raise PyTubeError(msg)

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

        status_string = self.data.get('status') or 'draft'
        lines.append(':status: {}'.format(status_string))

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

        self.output += '\n'.join(lines)
        self.output += '\n'

    def write(self):
        path_parts = self.json_file_path.split(os.sep)

        # make category dir if necessary
        subdirectory = path_parts[2]
        sub_dir_path = os.path.join(CONTENT_DIR, subdirectory)

        self.lock.acquire(timeout=1)
        if not os.path.exists(sub_dir_path):
            if self.verbose:
                print('Creating sub dir {}'.format(sub_dir_path), flush=True)
            os.mkdir(sub_dir_path)
        self.lock.release()

        name = path_parts[-1][:-4] + 'rst'
        path = os.path.join(sub_dir_path, name)

        self.lock.acquire(timeout=1)
        if self.verbose:
            print('Writing {}'.format(path), flush=True)
        with open(path, 'w') as fp:
            fp.write(self.output)
        self.lock.release()

        self.validate_rst(path)

    def validate_rst(self, path):
        if self.verbose:
            print('Validating {}'.format(path), flush=True)
        with TimeoutWrapper(seconds=2):
            content, metadata = RstReader(DEFAULT_SETTINGS).read(path)
        if self.verbose:
            print('Validation complete {}'.format(path), flush=True)
        if all(map(lambda x: x in content, ('system-message', 'docutils'))):
            start = content.find('<p class="system-message')
            end = content.find('</p>', start)
            snippet = content[start:end]
            msg = 'Unable to parse rST document generated from {}\n{}'
            msg = msg.format(self.json_file_path, snippet)
            raise RstValidationError(msg)


def process_json_file(args):
    json_file_path, verbose = args
    maker = ArticleMaker(json_file_path, lock)
    try:
        maker.make(verbose=verbose)
    except BaseException as e:
        print(e)


def set_lock(lock_instance):
    """Add lock to worker globals"""
    global lock
    lock = lock_instance


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


def run_article_maker_pool(data_dir, process_count, verbose=False):
    if verbose:
        print('Searching for media records (JSON files) ...', flush=True)

    remove_old_content(verbose)

    json_file_paths = []
    pattern = '{}/**/*.json'.format(data_dir)
    for path in glob.iglob(pattern, recursive=True):
        if path.split(os.sep)[-1] != 'category.json':
            json_file_paths.append(path)

    args_gen = ((path, verbose) for path in json_file_paths)

    process_count = process_count or multiprocessing.cpu_count()
    pool_kwargs = {
        'processes': process_count,
        'initializer': set_lock,
        'initargs': (multiprocessing.Lock(),),
    }

    if verbose:
        msg = 'Starting pool of {} processes ...'.format(process_count)
        print(msg, flush=True)

    with multiprocessing.Pool(**pool_kwargs) as p:
        p.map(process_json_file, args_gen)


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
        set_lock(multiprocessing.Lock())
        process_json_file((args.file, args.verbose))
    else:
        run_article_maker_pool(args.data_dir, args.process_count, args.verbose)


if __name__ == '__main__':
    main()

