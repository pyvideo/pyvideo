import argparse
from datetime import datetime
import glob
import json
from multiprocessing import Pool, Lock
import os
import re
import shutil

from pelican import DEFAULT_CONFIG_NAME
from pelican.readers import RstReader
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
OPTION_INDENT = ' ' * 4


class RstValidationError(Exception):
    pass


class ArticleMaker:
    """
    Take a JSON file and make an rST file out of the data it contains.
    """
    def __init__(self, json_file_path, lock):
        self.input = json_file_path
        self.lock = lock
        self.subdirectory = ''
        self.data = {}
        self.output = ''

    def make(self):
        """
        Tie all other methods together to get produce a final rST file.
        """
        self.parse_subdirectory()
        self.read_input()
        self.build_header()
        self.build_body()
        self.build_details()
        self.write_output()

    def read_input(self):
        with open(self.input) as fp:
            self.data = json.load(fp)

    def parse_subdirectory(self):
        """
        Parse the subdirectory for this article from self.input
        """
        dirs = self.input.split(os.sep)
        # assume subdirectory is second dir in path
        self.subdirectory = dirs[1]
        if not self.subdirectory:
            raise ValueError('subdirectory not found')

    def build_header(self):
        # build title line
        title = self.data.get('title').strip()
        title = title.replace('*', '\*')
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

        tags = self.data.get('tags')
        self.tags = tags
        if tags:
            # strip tags of whitespace
            tags = map(lambda x: x.strip(), tags)
            # strip out dots in tags
            tags = map(lambda x: x.replace('.', ''), tags)
            # ignore empty tags
            tags = filter(lambda x: bool(x), tags)
            tags = self.quote_text_list(tags)
            if tags:
                tags_line = ':tags: {}'.format(', '.join(tags))

        category = self.data.get('category', '').strip()
        self.category = category
        if not category:
            raise ValueError('Each article requires a category')
        category_line = ':category: {}'.format(category)

        # Remove slug
        slug = self.data.get('slug', '').strip()
        if slug:
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
        return 'http://'

    @property
    def media_thubmnail_url(self):
        return 'http://'

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

        description = self.data.get('description').strip()
        description = 'Description\n-----------\n\n' + description + '\n'

        self.output += '\n' + image_block + '\n\n' + description

    def build_details(self):
        header_line = '\nDetails\n-------\n'

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
            msg = msg_template.format(self.input, snippet)
            raise RstValidationError(msg)


def process_json_file(file_path):
    maker = ArticleMaker(file_path, lock)
    maker.make()


def set_lock(lock_instance):
    """Add lock to worker globals"""
    global lock
    lock = lock_instance


def run_article_maker_pool(process_count=None):
    # clear content dir of most content
    contents = set(os.listdir('content'))
    contents_to_delete = contents - set(('pages',))
    for content_dir in contents_to_delete:
        shutil.rmtree(os.path.join('content', content_dir))
    if os.path.exists('output'):
        shutil.rmtree('output')

    pattern = '{}/**/*.json'.format(DATA_DIR)
    json_file_paths = glob.iglob(pattern, recursive=True)
    #json_file_paths = [list(json_file_paths)[1000]]

    pool_kwargs = {
        'processes': process_count,
        'initializer': set_lock,
        'initargs': (Lock(),),
    }

    with Pool(**pool_kwargs) as p:
        p.map(process_json_file, json_file_paths)


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

    return parser.parse_args()


def main():
    args = parse_arguments()

    if args.file:
        set_lock(Lock())
        process_json_file(args.file)
    else:
        run_article_maker_pool(args.process_count)


if __name__ == '__main__':
    main()

