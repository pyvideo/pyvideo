from pelican import signals
from pelican.readers import BaseReader
import json

def _get_and_check_none(my_dict, key, default=None):
    if key not in my_dict or my_dict[key] == None:
        return default
    else:
        return my_dict[key]

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
                    'media_url': _get_and_check_none(json_data, 'source_url', ''),
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
