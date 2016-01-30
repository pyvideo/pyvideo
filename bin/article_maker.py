import argparse
from datetime import datetime
import glob
import json
import multiprocessing
import os
import re
import shutil

from pelican import DEFAULT_CONFIG_NAME
from pelican.readers import METADATA_PROCESSORS, RstReader
from pelican.settings import read_settings
from pelican.utils import slugify


DATA_DIR = 'data'
DATETIME_FORMAT = '%Y-%m-%d %H:%M'
DATETIME_FORMATS_BY_RE_PATTERN = {
    r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$': '%Y-%m-%d %H:%M:%S',
    r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$': '%Y-%m-%dT%H:%M:%S',
    r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$': '%Y-%m-%d %H:%M',
}
DATETIME_FORMATS_BY_RE_PATTERN = {
    re.compile(key): value for key, value in
    DATETIME_FORMATS_BY_RE_PATTERN.items()
}
DATETIME_WITH_MICRO_PATTERN = re.compile(r'^(.*)\.\d+$')
DEFAULT_SETTINGS = read_settings(DEFAULT_CONFIG_NAME)
DEFAULT_THUMBNAIL_URL = '/default_thumbnail_url.png'
# Ordered by preference
MEDIA_URL_KEYS = (
    'source_url',
    'video_flv_url',
    'video_mp4_url',
    'video_ogv_url',
    'video_webm_url'
)
OPTION_INDENT = ' ' * 4

# Unused
#def patch_metadata_processors():
#    def thumbnail_url_processor(x, y):
#        return x.strip()
#
#    METADATA_PROCESSORS.update({'thumbnail_url': thumbnail_url_processor})
#patch_metadata_processors()


class RstValidationError(Exception):
    pass


class ArticleMaker:
    """
    Take a JSON file and make an rST file out of the data it contains.
    """
    def __init__(self, subdirectory, data, lock):
        self.lock = lock
        self.subdirectory = subdirectory
        self.data = data
        self.output = ''
        self.verbose = False

    def make(self, verbose=False):
        """
        Tie all other methods together to get produce a final rST file.
        """
        self.title = self.data.get('title') or ''
        self.title = self.title.strip()
        if verbose:
            print('Making {}'.format(self.title), flush=True)

        self.build_header()
        self.build_body()
        self.build_details()
        self.write_output()

    def build_header(self):
        # build title line
        title = self.title.replace('*', '\*')
        title_lines = title + '\n'
        title_lines += '#' * len(bytes(title.encode())) + '\n'

        # These lines are optional
        modified_line = tags_line = slug_line = None

        # build meta data section
        date_string = self.get_date_string()
        self.date_string = date_string
        date_line = ':date: {}'.format(date_string)

        modified_string = self.get_modified_string()
        if modified_string:
            modified_line = ':modified: {}'.format(modified_string)

        self.tags = None
        tags = self.data.get('tags')
        if tags:
            # strip tags of whitespace
            tags = map(lambda x: x.strip(), tags)
            # strip out dots in tags
            tags = map(lambda x: x.replace('.', ''), tags)
            # ignore empty tags
            tags = filter(lambda x: bool(x), tags)
            tags = list(self.quote_text_list(tags))
            self.tags = tags
            if tags:
                tags_line = ':tags: {}'.format(', '.join(tags))

        category = self.data.get('category', '').strip()
        self.category = category
        if not category:
            raise ValueError('Each article requires a category')
        category_line = ':category: {}'.format(category)

        # Remove slug
        slug = '{}-{}'.format(category, title)
        slug = slugify(slug)
        slug_line = ':slug: {}'.format(slug)

        authors = self.data.get('speakers')
        authors = map(lambda x: x.strip(), authors)
        author = filter(lambda x: bool(x), authors)
        authors = self.quote_text_list(authors)
        authors_string = ', '.join(authors) or 'Unknown'
        authors_line = ':authors: {}'.format(authors_string)

        lines = (
            title_lines,
            date_line,
            modified_line,
            tags_line,
            category_line,
            slug_line,
            authors_line,
        )

        self.output += '\n'.join(line for line in lines if line is not None)
        self.output += '\n'

    def quote_text_list(self, text_list):
        for text in text_list:
            if '.' in text:
                text = '"' + text + '"'
            yield text

    def get_date_string(self):
        date = self.data.get('date', '').strip()
        if not date:
            date = self.data.get('added', '').strip()

        date = self.coerce_datetime(date)

        if not date:
            raise ValueError('date must be defined')

        return date

    def get_modified_string(self):
        modified = self.data.get('updated', '').strip()
        if not modified:
            return None

        return self.coerce_datetime(modified)

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

        raise ValueError('date pattern not recognized to datetime')

    @property
    def media_url(self):
        for url_key in MEDIA_URL_KEYS:
            url = self.data.get(url_key) or ''
            url = url.strip()
            if url:
                break

        if not url:
            msg = 'no valid media URL found for file {}'.format(self.title)
            raise ValueError(msg)

        return url

    @property
    def media_thubmnail_url(self):
        thumbnail_url = self.data.get('thumbnail_url') or ''
        thumbnail_url = thumbnail_url.strip()
        thumbnail_url = thumbnail_url or DEFAULT_THUMBNAIL_URL
        return thumbnail_url

    def build_body(self):
        image_block = '.. image:: {}\n'
        image_block += OPTION_INDENT + ':width: 600px\n'
        image_block += OPTION_INDENT + ':target: {}\n'
        image_block += OPTION_INDENT + ':alt: {}'
        image_block = image_block.format(
            self.media_thubmnail_url,
            self.media_url,
            self.data.get('title', '').strip()
        )

        summary = self.data.get('summary') or ''
        summary = summary.strip()
        # temporarily disable summary
        summary = ''
        if summary:
            summary = '\n\nSummary\n-----------\n\n' + summary + '\n'

        description = self.data.get('description') or ''
        description = description.strip()
        if description:
            description_header = '\n\nDescription\n-----------\n\n'
            description = description_header + description + '\n'

        self.output += '\n' + image_block + summary + description

    def build_details(self):
        header_line = '\n\nDetails\n-------\n'

        category_line = 'Category: {}'.format(self.category)

        language_line = None
        language = self.data.get('language') or ''
        language = language.strip()
        if language:
            language_line = 'Language: {}'.format(language) 

        media_url_line = 'Direct Link: {}'.format(self.media_url)

        copyright_line = None
        copyright = self.data.get('copyright', '').strip()
        if copyright:
            copyright_line = 'Copyright: {}'.format(copyright)

        tags_line = None
        if self.tags:
            tags_line = 'Tags: {}'.format(', '.join(self.tags))

        details = (
            header_line,
            category_line,
            language_line,
            media_url_line,
            copyright_line,
            tags_line,
        )

        details = '\n- '.join(d for d in details if d)

        self.output += details + '\n\n'

    def write_output(self):
        # make category dir if neccessary
        sub_dir_path = os.path.join('content', self.subdirectory)

        self.lock.acquire()
        if not os.path.exists(sub_dir_path):
            os.mkdir(sub_dir_path)
        self.lock.release()

        name = slugify(self.data.get('title').strip()) + '.rst'
        path = os.path.join(sub_dir_path, name)
        self.lock.acquire()
        with open(path, 'w') as fp:
            fp.write(self.output)
        self.lock.release()

        # Validate rST
        content, metadata = RstReader(DEFAULT_SETTINGS).read(path)
        if all(map(lambda x: x in content, ('system-message', 'docutils'))):
            start = content.find('<p class="system-message')
            end = content.find('</p>', start)
            snippet = content[start:end]
            msg_template = 'Unable to parse rST document generated from: {}\n'
            msg_template += '{}'
            msg = msg_template.format(self.title, snippet)
            raise RstValidationError(msg)


def process_json_file(args):
    subdirectory, data, verbose = args
    maker = ArticleMaker(subdirectory, data, lock)
    maker.make(verbose=verbose)


def get_subdirectory_from_path(path):
    parts = path.split(os.sep)
    return parts[1]


def generate_media_records(json_file_paths, verbose=False):
    for json_file_path in json_file_paths:

        subdirectory = get_subdirectory_from_path(json_file_path)

        with open(json_file_path) as fp:
            data = json.load(fp)

        if isinstance(data, dict):
            data = [data]

        for media_record in data:
            yield subdirectory, media_record, verbose


def set_lock(lock_instance):
    """Add lock to worker globals"""
    global lock
    lock = lock_instance


def run_article_maker_pool(process_count=None, verbose=False):
    if verbose:
        print('Searching for media records (JSON files) ...', flush=True)

    # clear content dir of most content
    contents = set(os.listdir('content'))
    contents_to_delete = contents - set(('pages', 'images', 'extra'))
    for content_dir in contents_to_delete:
        shutil.rmtree(os.path.join('content', content_dir))
    if os.path.exists('output'):
        shutil.rmtree('output')

    pattern = '{}/**/*.json'.format(DATA_DIR)
    json_file_paths = glob.iglob(pattern, recursive=True)

    media_records = generate_media_records(json_file_paths, verbose)

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
        p.map(process_json_file, media_records)


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

    parser.add_argument('-p', '--process-count',
                        dest='process_count',
                        help='Number of processes',
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
        subdirectory = get_subdirectory_from_path(args.file)
        with open(args.file) as fp:
            data = json.load(fp)
        process_json_file((subdirectory, data, args.verbose))
    else:
        run_article_maker_pool(args.process_count, verbose=args.verbose)


if __name__ == '__main__':
    main()

