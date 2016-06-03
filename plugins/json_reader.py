import json
import logging
from urllib.parse import urlparse

import docutils
import docutils.io
from docutils.core import publish_parts
from pelican import signals
from pelican.readers import BaseReader, PelicanHTMLTranslator


log = logging.getLogger(__name__)


def _get_and_check_none(target, key, default=None):
    value = target.get(key)
    if value is None:
        return default
    return value


def _get_youtube_url(url):
    video_id = ''
    url_parsed = urlparse(url)
    if '/watch?v=' in url:
        query_pairs = url_parsed.query.split('&')
        pairs = (pair.split('=') for pair in query_pairs if '=' in pair)
        video_id = dict(pairs).get('v')
    elif '/v/' in url:
        video_id = url_parsed.path.replace('/v/', '')
    elif 'youtu.be/' in url:
        video_id = url_parsed.path

    return 'https://www.youtube.com/embed/{}'.format(video_id)


def _get_vimeo_url(url):
    o = urlparse(url)
    video_id = o.path.replace('/', '')
    return 'https://player.vimeo.com/video/{}'.format(video_id)


def _get_media_url(json_data):
    source_url = _get_and_check_none(json_data, 'source_url', '')
    if 'youtu' in source_url:
        source_url = _get_youtube_url(source_url)
    elif 'vimeo' in source_url:
        source_url = _get_vimeo_url(source_url)
    return source_url


class JSONReader(BaseReader):
    enabled = True

    # The list of file extensions you want this reader to match with.
    # If multiple readers were to use the same extension, the latest will
    # win (so the one you're defining here, most probably).
    file_extensions = ['json']

    def _get_publisher(self, source, source_file_path):
        # This is a slightly modified copy of `RstReader._get_publisher`
        extra_params = {'initial_header_level': '2',
                        'syntax_highlight': 'short',
                        'input_encoding': 'utf-8',
                        'exit_status_level': 2,
                        'embed_stylesheet': False}
        user_params = self.settings.get('DOCUTILS_SETTINGS')
        if user_params:
            extra_params.update(user_params)

        pub = docutils.core.Publisher(
            source_class=docutils.io.StringInput,
            destination_class=docutils.io.StringOutput)
        pub.set_components('standalone', 'restructuredtext', 'html')
        pub.writer.translator_class = PelicanHTMLTranslator
        pub.process_programmatic_settings(None, extra_params, None)
        pub.set_source(source=source, source_path=source_file_path)
        pub.publish(enable_exit_status=True)
        return pub

    # You need to have a read method, which takes a filename and returns
    # some content and the associated metadata.
    def read(self, filename):
        with open(filename, 'rt', encoding='UTF-8') as f:
            json_data = json.loads(f.read())

        metadata = {'title': _get_and_check_none(json_data, 'title', 'Title'),
                    'category': _get_and_check_none(json_data, 'category',
                                                    self.settings['DEFAULT_CATEGORY']),
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

        content = []
        for part in ['summary', 'description']:
            content.append('<h1>{}</h1>'.format(part.title()))
            json_part = json_data.get(part)
            if json_part:
                try:
                    publisher = self._get_publisher(json_part, filename)
                    content.append(publisher.writer.parts.get('body'))
                except SystemExit:
                    log.warn(
                        "Invalid ReST markup in %s['%s']. Rendering as plain text.",
                        filename.replace(self.settings.get('PATH'), "").strip("/"),
                        part
                    )
                    content.append('<pre>{}</pre>'.format(json_part))

        return "".join(content), parsed


def register():
    def add_reader(readers):
        readers.reader_classes['json'] = JSONReader

    signals.readers_init.connect(add_reader)
