"""
This plugin provides the data for the "latest"-boxes on the frontpage. It has
to come after the event_info plugin as this is prepares the event data which
is used here.
"""
from pelican import generators
from pelican import signals
from pelican.contents import Article

from collections import defaultdict

_categories = defaultdict(dict)
_speakers = defaultdict(dict)
_tags = defaultdict(dict)
_languages = defaultdict(dict)

CATEGORY_BLACKLIST = {'Undefined'}
SPEAKER_BLACKLIST = {'Unknown', 'Various speakers'}
TAGS_BLACKLIST = {'pycon'}
LANGUAGE_BLACKLIST = {}


def _handle_content_object_init(obj):
    if isinstance(obj, Article):
        language = getattr(obj, 'language')
        if not language:
            language = 'missing'
        if language:
            if language not in LANGUAGE_BLACKLIST:
                count = _languages[language].get('count', 0)
                latest = _languages[language].get('latest')
                if not latest or obj.date > latest:
                    latest = obj.date
                _languages[language]['count'] = count + 1
                _languages[language]['latest'] = latest
                _languages[language]['name'] = language
                if 'videos' not in _languages[language]:
                    _languages[language]['videos'] = []
                _languages[language]['videos'].append(obj)

        category = getattr(obj, 'category')
        if category and category.slug:
            if category.name not in CATEGORY_BLACKLIST:
                count = _categories[category.slug].get('count', 0)
                latest = _categories[category.slug].get('latest')
                if not latest or obj.date > latest:
                    latest = obj.date
                _categories[category.slug]['count'] = count + 1
                _categories[category.slug]['latest'] = latest
                _categories[category.slug]['name'] = category.name

        for speaker in getattr(obj, 'authors'):
            if speaker.name not in SPEAKER_BLACKLIST:
                count = _speakers[speaker.slug].get('count', 0)
                _speakers[speaker.slug]['name'] = speaker.name
                _speakers[speaker.slug]['slug'] = speaker.slug
                _speakers[speaker.slug]['url'] = speaker.url
                _speakers[speaker.slug]['count'] = count + 1

        tags = getattr(obj, 'tags', ())
        if tags:
            for tag in tags:
                if tag.name not in TAGS_BLACKLIST:
                    count = _tags[tag.slug].get('count', 0)
                    _tags[tag.slug]['name'] = tag.name
                    _tags[tag.slug]['slug'] = tag.slug
                    _tags[tag.slug]['url'] = tag.url
                    _tags[tag.slug]['count'] = count + 1


def _inject_aggregates(generator):
    if isinstance(generator, generators.ArticlesGenerator):
        latest_categories = sorted(_categories.values(), key=lambda x: x.get('latest'), reverse=True)[:5]
        active_speakers = sorted(_speakers.values(), key=lambda x: x.get('count'), reverse=True)
        active_tags = sorted(_tags.values(), key=lambda x: x.get('count'), reverse=True)
        fn = generator.settings['VIDEO_LANGUAGE_NAMES']
        languages = sorted(map(lambda lang: (fn.get(lang.get('name'), lang.get('name')), lang.get('name'), lang.get('count'), lang.get('videos')), _languages.values()), reverse=True)
        active_languages = sorted(map(lambda lang: (lang.get('count'), fn.get(lang.get('name'), lang.get('name')), lang.get('name')), _languages.values()), reverse=True)
        # The actual category URL has to be fetched in the
        # article_generator_finalized hook in order for the event_info plugin to
        # have done its magic.
        for category in latest_categories:
            category['url'] = generator.event_by_name[category['name']].url
        generator.context['latest_categories'] = latest_categories
        generator.context['active_speakers'] = active_speakers
        generator.context['active_tags'] = active_tags
        generator.context['languages'] = languages
        generator.context['active_languages'] = active_languages


def register():
    signals.content_object_init.connect(_handle_content_object_init)
    signals.article_generator_finalized.connect(_inject_aggregates)

