import sys, tempfile, os
from subprocess import call
from collections import OrderedDict
import datetime
import json


EDITOR = os.environ.get('EDITOR', 'vim')


def reorder_dict(data):
    new_dict = OrderedDict()
    # FIXME: Change this to use the structure in validate rather than
    # have the set of information in two places.
    # FIXME: This needs to reorder videos, too.
    for key in ('id', 'category', 'slug', 'title', 'summary', 'description',
                'quality_notes', 'language', 'copyright_text', 'thumbnail_url',
                'duration', 'videos', 'source_url', 'tags', 'speakers',
                'recorded'):
        if key in data:
            new_dict[key] = data[key]
    return new_dict


def json_convert(obj):
    if isinstance(obj, datetime.date):
        return obj.strftime('%Y-%m-%d')
    if isinstance(obj, datetime.datetime):
        return obj.strftime('%Y-%m-%d %H:%M:%S')
    return obj


def get_edited_text(original_text):
    with tempfile.NamedTemporaryFile(suffix=".tmp") as tf:
        tf.write(original_text.encode())
        tf.flush()
        call([EDITOR, tf.name])

        with open(tf.name) as fp:
            return fp.read()


def edit_file(file_path):
    with open(file_path) as fp:
        data = json.load(fp)

    for key in ('summary', 'description'):
        value = (data.get(key) or '').strip()
        if value:
            data[key] = get_edited_text(value)

    ordered_data = reorder_dict(data)
    with open(file_path, 'w') as fp:
        json.dump(ordered_data, fp,
                  indent=2,
                  sort_keys=False,
                  default=json_convert,
                  separators=(',', ': '))


edit_file(sys.argv[1])

