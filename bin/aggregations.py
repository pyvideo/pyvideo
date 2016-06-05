from pelican import signals
from pelican.contents import Article

from collections import defaultdict

_categories = defaultdict(dict)
_speakers = defaultdict(dict)

SLUG_BLACKLIST = set(['videos'])
SPEAKER_BLACKLIST = set(['Unknown'])


def _handle_content_object_init(obj):
    if isinstance(obj, Article):
        category = getattr(obj, 'category')
        speaker = getattr(obj, 'author')
        if category and category.slug:
            if not category.slug in SLUG_BLACKLIST:
                count = _categories[category.slug].get('count', 0)
                latest = _categories[category.slug].get('latest')
                if not latest or obj.date > latest:
                    latest = obj.date
                _categories[category.slug]['count'] = count + 1
                _categories[category.slug]['latest'] = latest
                _categories[category.slug]['name'] = category.name
                _categories[category.slug]['slug'] = category.slug
                _categories[category.slug]['url'] = category.url
        if speaker:
            if speaker.name not in SPEAKER_BLACKLIST:
                count = _speakers[speaker.slug].get('count', 0)
                _speakers[speaker.slug]['name'] = speaker.name
                _speakers[speaker.slug]['slug'] = speaker.slug
                _speakers[speaker.slug]['url'] = speaker.url
                _speakers[speaker.slug]['count'] = count + 1


def _inject_aggregates(generator):
    latest_categories = sorted(_categories.values(), key=lambda x: x.get('latest'), reverse=True)
    active_speakers = sorted(_speakers.values(), key=lambda x: x.get('count'), reverse=True)
    generator.context['latest_categories'] = latest_categories
    generator.context['active_speakers'] = active_speakers


def register():
    signals.content_object_init.connect(_handle_content_object_init)
    signals.article_generator_finalized.connect(_inject_aggregates)
