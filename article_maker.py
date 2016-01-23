from datetime import datetime
import glob
import json
from multiprocessing import Pool, Lock
import os
import re
import shutil


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

    def build_header(self):
        # build title line
        title = self.data.get('title').strip()
        title_lines = title + '\n' + '#' * len(title) + '\n'

        # These lines are optional
        modified_line = tags_line = slug_line = None

        # build meta data section
        date_string = self.get_date_string()
        date_line = ':date: {}'.format(date_string)

        modified_string = self.get_modified_string()
        if modified_string:
            modified_line = ':modified: {}'.format(modified_string)

        tags = self.data.get('tags')
        if tags:
            tags = map(lambda x: x.strip(), tags)
            tags_line = ':tags: {}'.format(', '.join(tags))

        category = self.data.get('category').strip()
        category_line = ':category: {}'.format(category)

        slug = self.data.get('slug', '').strip()
        if slug:
            slug_line = ':slug: {}'.format(slug)

        authors = self.data.get('speakers')
        authors = map(lambda x: x.strip(), authors)
        authors_line = ':authors: {}'.format(' ,'.join(authors))

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

    def build_body(self):
        # video (determine best media src)
        # Title
        # description
        pass

    def build_side_panel(self):
        # category
        # speakers
        # Language
        # Recorded (Datetime)
        # Last updated (Datetime)
        # Video Origin (whaever was picked for media above)
        # Download ???
        # Meta data - THIS JSON FIle
        # Copyright
        # tags
        pass

    def write_output(self):
        # acquire write lock
        # make category dir if neccessary
        # release write lock

        # acquire write lock
        # write file
        print(self.output)
        # release write lock
        pass


def process_json_file(file_path, lock):
    maker = ArticleMaker(file_path, lock)
    maker.make()


def run_article_maker_pool(proc_count):
    # clear content dir of most content
    contents = set(os.listdir('content'))
    contents_to_delete = contents - set(('pages',))
    for content_dir in contents_to_delete:
        shutil.rmtree(os.sep.join(('content', content_dir)))

    pattern = '{}/**/*.json'.format(DATA_DIR)
    json_file_paths = glob.iglob(pattern, recursive=True)
    #json_file_paths = [list(json_file_paths)[1000]]

    lock = Lock()

    arg_generator = ((path, lock) for path in json_file_paths)

    with Pool(proc_count) as p:
        p.map(process_json_file, arg_generator)


def main():
    run_article_maker_pool(5)


if __name__ == '__main__':
    main()

