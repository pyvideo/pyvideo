import docutils
import docutils.io
import io
import json

from pelican.readers import PelicanHTMLTranslator
from pelican import generators
from pelican import signals
from pathlib import Path


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
    collected_metadata = {}
    if isinstance(generator, generators.ArticlesGenerator):
        for event in [x[0] for x in generator.categories]:
            event.meta = _load_event_metadata(event.slug)


def _load_event_metadata(slug):
    path = Path('content') / 'conferences' / slug / 'category.json'
    if not path.exists():
        return None
    with io.open(str(path), encoding='utf-8') as fp:
        data = json.load(fp)
        if data['description']:
            data['description'] = _generate_html(data['description'])
        return data


def register():
    signals.article_generator_finalized.connect(_collect_event_info)
