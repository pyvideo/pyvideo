import subprocess

from pelican import signals
from pelican.writers import Writer


class PyVideoWriter(Writer):
    """
    This class exists so that elements in a feed can be sorted.
    """
    def write_feed(self, elements, *args, **kwargs):
        elements = self.sort_elements(elements)
        return super().write_feed(elements, *args, **kwargs)

    def sort_elements(self, elements):
        return sorted(elements, key=self.key_func)

    def key_func(self, element):
        path = element.data_path  # eg. pydata-dc-2016/videos/closing-session.json
        event_dir = path.split('/')[0]
        cmp_key = self.sorted_events.index(event_dir)
        return cmp_key

    @property
    def sorted_events(self):
        if not hasattr(self, '_sorted_events'):
            output = subprocess.run(["./sort_events.sh"], stdout=subprocess.PIPE)
            self._sorted_events = output.stdout.decode().strip().split('\n')
        return self._sorted_events


def get_writer(pelican_object):
    return PyVideoWriter


def register():
    signals.get_writer.connect(get_writer)

