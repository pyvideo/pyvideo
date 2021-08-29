import json
import logging
import os
import pathlib
from urllib.parse import urlparse, urlunparse

import docutils
import docutils.io
from docutils.core import publish_parts
from pelican import signals
from pelican.readers import BaseReader, PelicanHTMLTranslator
from pelican.utils import slugify


log = logging.getLogger(__name__)


CATEGORY_INFO_BY_FILENAME = {}


def _convert_to_label(type_):
    labels = {
        'youtube': 'YouTube',
        'vimeo': 'Vimeo',
        'wistia': 'Wistia',
        'peertube': 'PeerTube',
    }
    return labels.get(type_.lower(), type_.upper())


def _convert_to_icon(type_):
    icons = {
        'youtube': 'youtube',
        'vimeo': 'vimeo',
    }
    return icons.get(type_.lower(), 'file-video-o')


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
        video_id = url_parsed.path.lstrip("/")

    return 'https://www.youtube.com/embed/{}'.format(video_id)


def _get_vimeo_url(url):
    o = urlparse(url)
    video_id = o.path.replace('/', '')
    return 'https://player.vimeo.com/video/{}'.format(video_id)


def _get_peertube_url(url):
    url_parsed = urlparse(url)
    embed_url = list(url_parsed)
    embed_url[2] = embed_url[2].replace('/videos/watch/', '/videos/embed/')
    return urlunparse(embed_url)


def _get_media_url(url, media_type=""):
    source_url = url

    # If specified in data, prefer to use the media type
    # Otherwise, try to infer from the url
    if media_type == "youtube" or "youtu" in source_url:
        source_url = _get_youtube_url(source_url)
    elif media_type == "vimeo" or "vimeo" in source_url:
        source_url = _get_vimeo_url(source_url)
    elif media_type == "peertube":
        source_url = _get_peertube_url(source_url)
    elif media_type == "mp4":
        pass
    elif media_type == "ogv":
        pass

    return source_url


def _get_category_data(video_filename):
    """
    Get category info from category file.
    """
    category_dir = os.path.dirname(os.path.dirname(video_filename))
    category_filename = os.path.join(category_dir, 'category.json')

    if not os.path.exists(category_filename):
        return {}

    if category_filename not in CATEGORY_INFO_BY_FILENAME:
        with open(category_filename, 'rt', encoding='UTF-8') as f:
            json_data = json.loads(f.read())
        CATEGORY_INFO_BY_FILENAME[category_filename] = json_data

    return CATEGORY_INFO_BY_FILENAME[category_filename]


class JSONReader(BaseReader):
    enabled = True

    # The list of file extensions you want this reader to match with.
    # If multiple readers were to use the same extension, the latest will
    # win (so the one you're defining here, most probably).
    file_extensions = ['json']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._absolute_data_path = (pathlib.Path(self.settings['PATH']) / self.settings['DATA_DIR']).resolve()

    def _get_publisher(self, source, source_file_path):
        # This is a slightly modified copy of `RstReader._get_publisher`
        extra_params = {'initial_header_level': '4',
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

        data_path = str(pathlib.Path(filename).resolve().relative_to(self._absolute_data_path))
        videos = list()
        iframe_types = ["youtube", "vimeo", "wistia", "peertube"]
        html5_types = ["ogv", "mp4"]
        if 'videos' in json_data and isinstance(json_data['videos'], list) and len(json_data['videos']) > 0:
            for v in json_data['videos']:
                v_data = dict()
                v_data["type"] = v["type"]
                v_data['label'] = _convert_to_label(v['type'])
                v_data['icon'] = _convert_to_icon(v['type'])
                v_data["source_url"] = _get_and_check_none(v, 'url', '')
                v_data["media_url"] = _get_media_url(v["url"], media_type=v["type"])
                if v["type"] in iframe_types:
                    v_data["tag_type"] = "iframe"
                elif v["type"] in html5_types:
                    v_data["tag_type"] = "html5"

                videos.append(v_data)
        else:
            # Handle data which doesn't have the videos list
            v_data = dict()
            v_data["source_url"] = _get_and_check_none(json_data, 'source_url', '')
            v_data["media_url"] = _get_media_url(v_data['source_url'])
            if "youtube" in v_data["media_url"]:
                v_data["type"] = "youtube"
                v_data["tag_type"] = "iframe"
            elif "vimeo" in v_data["media_url"]:
                v_data["type"] = "vimeo"
                v_data["tag_type"] = "iframe"
            elif v_data["media_url"].endswith(".mp4"):
                v_data["type"] = "mp4"
                v_data["tag_type"] = "html5"
            elif re.search('/videos/watch/{hex}{{8}}-({hex}{{4}}-){{3}}{hex}{{12}}$'.format(hex='[0-9A-Fa-f]'),
                           v_data["media_url"]):
                v_data["type"] = "peertube"
                v_data["tag_type"] = "iframe"
            v_data['label'] = _convert_to_label(v_data['type'])
            v_data['icon'] = _convert_to_icon(v_data['type'])
            videos.append(v_data)

        category_data = _get_category_data(filename)
        category = _get_and_check_none(category_data, 'title')
        if not category:
            category = _get_and_check_none(
                json_data,
                'category',
                self.settings['DEFAULT_CATEGORY']
            )

        title = _get_and_check_none(json_data, 'title', 'Title')
        slug = _get_and_check_none(json_data, 'slug')
        if slug is None:
            slug = slugify(title)

        metadata = {
            'title': title,
            'category': category,
            'tags': _get_and_check_none(json_data, 'tags', []),
            'date': _get_and_check_none(json_data, 'recorded', '1990-01-01'),
            'slug': slug,
            'authors': _get_and_check_none(json_data, 'speakers', []),
            'videos': videos,
            'data_path': data_path,
            'media_url': _get_media_url(_get_and_check_none(json_data, 'source_url', '')),
            'thumbnail_url': _get_and_check_none(json_data, 'thumbnail_url', '/images/default_thumbnail_url.png'),
            'language': _get_and_check_none(json_data, 'language', ''),
            'related_urls': map_related_urls(_get_and_check_none(json_data, 'related_urls', [])),
        }

        alias = _get_and_check_none(json_data, 'alias')
        if alias:
            if not alias.endswith('/'):
                alias += '/'
            metadata['alias'] = alias

        # Send metadata through pelican parser to check pelican required formats
        metadata = {key: self.process_metadata(key, value) for key, value in metadata.items()}

        content = []
        for part in ['summary', 'description']:
            json_part = json_data.get(part)
            if json_part:
                content.append('<h3>{}</h3>'.format(part.title()))
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

        return "".join(content), metadata


def map_related_urls(urls):
    result = []
    for url in urls:
        if isinstance(url, dict):
            result.append(url)
        else:
            result.append({
                'url': url,
                'label': None,
            })
    return result


def add_reader(readers):
    readers.reader_classes['json'] = JSONReader


def register():
    signals.readers_init.connect(add_reader)
