import re
from itertools import groupby
from logging import getLogger
from operator import attrgetter

from pelican import signals

EVENT_HAS_YEAR_RE = re.compile("^(?P<event>[^0-9]+) (?P<year>[0-9]{4})$")
log = getLogger(__name__)


class EventSeries:
    def __init__(self, name, members, labels):
        self.name = name
        self.members = members
        self.labels = labels
        for idx, member in enumerate(members):
            member.series = EventMemberSeriesWrapper(self, idx)
            member.series_label = labels[idx]

    def __len__(self):
        return len(self.members)

    def __str__(self):
        return self.name


class EventMemberSeriesWrapper:
    def __init__(self, series: EventSeries, index):
        self.series = series
        self.index = index

    @property
    def label(self):
        return self.series.labels[self.index]

    @property
    def members(self):
        return self.series.members


def _match_dict(match):
    if match:
        return match.groupdict()


def group_event_series(generator):
    """
    Create yearly event series out of the individual events.
    """
    # Pelican offers no way to directly access all events so we gather them from the talks
    initial_events = {talk.category for talk in generator.articles}

    # Process categories with regex and filter out those without years
    yearly_events = {
        event: match
        for event, match in {
            event: _match_dict(EVENT_HAS_YEAR_RE.match(event.name))
            for event in initial_events
        }.items()
        if match
    }

    # Keep standalone events for later
    standalone_events = initial_events - set(yearly_events.keys())

    # Group events by common name
    grouped_events = groupby(
        sorted(yearly_events.items(), key=lambda itm: "{m[event]}-{m[year]}".format(m=itm[1])),
        key=lambda itm: itm[1]['event']
    )

    # Construct event series out of the grouped events
    event_series = []
    for event_name, events in grouped_events:
        events = list(events)
        event_series.append(
            EventSeries(
                event_name,
                [event for event, _ in events],
                [event_info['year'] for _, event_info in events]
            )
        )

    # Re-add the standalone categories to the series list so we can display them together and in
    # the correct order
    event_series.extend(standalone_events)
    generator.context['event_series'] = sorted(event_series, key=attrgetter('name'))
    log.debug("Grouped %d events into %d event series", len(initial_events), len(event_series))


def register():
    signals.article_generator_pretaxonomy.connect(group_event_series)
