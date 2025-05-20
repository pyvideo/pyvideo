import datetime
import glob
import operator
import os
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
        if event_dir not in self.sorted_events:
            return len(self.sorted_events)
        else:
            cmp_key = self.sorted_events.index(event_dir)
            return cmp_key

    @property
    def sorted_events(self):
        if not hasattr(self, '_sorted_events'):
            events = []
            old_wd = os.getcwd()
            os.chdir('data')
            for path in glob.iglob('**/category.json'):
                directory = os.path.dirname(path)
                command = "git log --diff-filter=A --follow --format=%ai -1 --".split()
                command.append(path)
                output = subprocess.check_output(
                    command, universal_newlines=True)
                if output:
                    dt = datetime.datetime.strptime(
                        output.strip(), "%Y-%m-%d %H:%M:%S %z")
                else:
                    dt = datetime.datetime.now(tz=datetime.timezone.utc)
                events.append((dt, directory))
            os.chdir(old_wd)
            events.sort(key=operator.itemgetter(1))
            events.sort(key=operator.itemgetter(0), reverse=True)
            self._sorted_events = [event[1] for event in events]
        return self._sorted_events


def get_writer(pelican_object):
    return PyVideoWriter


def register():
    signals.get_writer.connect(get_writer)
