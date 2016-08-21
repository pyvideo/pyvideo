"""
This plugin injects as much metadata into the category/event objects
as possible. Among other things it also manipulates the category's
slug to reflect the one stored within the category.json file.

That's necessary because each video refers to each event through its name and
not its slug.
"""
import docutils
import docutils.io
import json
import logging

from pelican.readers import PelicanHTMLTranslator
from pelican import generators
from pelican import signals
from pelican.utils import slugify
from pathlib import Path


log = logging.getLogger(__name__)


def _generate_html(data):
    extra_params = {'initial_header_level': '2',
                    'syntax_highlight': 'short',
                    'input_encoding': 'utf-8',
                    'exit_status_level': 2,
                    'compact_p': False,
                    'embed_stylesheet': False}
    pub = docutils.core.Publisher(
        source_class=docutils.io.StringInput,
        destination_class=docutils.io.StringOutput)
    pub.set_components('standalone', 'restructuredtext', 'html')
    pub.writer.translator_class = PelicanHTMLTranslator
    pub.process_programmatic_settings(None, extra_params, None)
    pub.set_source(source=data, source_path=None)
    pub.publish(enable_exit_status=True)
    return pub.writer.parts['body']


def _collect_event_info(generator):
    events = _load_events()
    if isinstance(generator, generators.ArticlesGenerator):
        event_by_name = {}
        for event in [x[0] for x in generator.categories]:
            meta = events.get(event.name)
            # Update the slug of the event with the one provided
            # by the metadata object.
            if meta and 'slug' in meta:
                event.slug = meta['slug']
            event.meta = meta
            event_by_name[event.name] = event
        generator.event_by_name = event_by_name


def _load_events():
    path = Path('content') / 'conferences'
    events = {}
    slugs = set()
    for metafile in path.glob('*/category.json'):
        # skip the schema "category.json" file
        if metafile.parent and metafile.parent.name.startswith('.'):
            continue
        with open(str(metafile), encoding='utf-8') as fp:
            data = json.load(fp)
            title = data['title']
            slug = slugify(title)
            if data.get('description'):
                data['description'] = _generate_html(data['description'])
            if title in events:
                log.critical('{} is not a unique category title!'.format(title))
            if slug in slugs:
                log.critical('{} is not a unique slug!'.format(slug))
            slugs.add(slug)
            events[title] = data
    return events


def register():
    signals.article_generator_finalized.connect(_collect_event_info)
