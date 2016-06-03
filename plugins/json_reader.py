from pelican import signals
from pelican.readers import BaseReader
import json
from urllib.parse import urlparse

def _get_and_check_none(my_dict, key, default=None):
    if key not in my_dict or my_dict[key] == None:
        return default
    else:
        return my_dict[key]

def _get_youtube_url(url):
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

def _get_media_url(json_data):
    source_url = _get_and_check_none(json_data, "source_url", "")
    if "youtu" in source_url:
        source_url = _get_youtube_url(source_url)
    return source_url

# Create a new reader class, inheriting from the pelican.reader.BaseReader
class JSONReader(BaseReader):
    enabled = True  # Yeah, you probably want that :-)

    # The list of file extensions you want this reader to match with.
    # If multiple readers were to use the same extension, the latest will
    # win (so the one you're defining here, most probably).
    file_extensions = ['json']

    # You need to have a read method, which takes a filename and returns
    # some content and the associated metadata.
    def read(self, filename):
        with open(filename, 'r') as f:
            json_data = json.loads(f.read())

        metadata = {'title': _get_and_check_none(json_data, 'title', 'Title'),
                    'category': _get_and_check_none(json_data, 'category', 'Default'),
                    'tags': _get_and_check_none(json_data, 'tags', []),
                    'date': _get_and_check_none(json_data, 'recorded', '1990-01-01'),
                    'slug': _get_and_check_none(json_data, 'slug', 'Slug'),
                    'authors': _get_and_check_none(json_data, 'speakers', []),
                    'videos': _get_and_check_none(json_data, 'videos', []),
                    'media_url': _get_media_url(json_data),
                    'thumbnail_url': _get_and_check_none(json_data, 'thumbnail_url', ''),
                    'language': _get_and_check_none(json_data, 'language', ''),
        }

        parsed = {}
        for key, value in metadata.items():
            parsed[key] = self.process_metadata(key, value)

        content = '<h1>Summary</h1>'
        if 'summary' in json_data:
            content += '<p>{}</p>'.format(json_data['summary'])
        if 'description' in json_data:
            content += '<p>{}</p>'.format(json_data['description'])

        return content, parsed

def add_reader(readers):
    readers.reader_classes['json'] = JSONReader

# This is how pelican works.
def register():
    signals.readers_init.connect(add_reader)
