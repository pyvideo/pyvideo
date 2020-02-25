import glob
import fnmatch
import json
import os

import pelican
from pelican import signals


# Monkey patch the ArticleGenerator to override specific method.
# We have to override the `_include_path` method because it does not
# filter files with enough specificity. If we wanted to filter a talk
# at `categories/jacksconf/videos/jacks-talk.json`, we could do so
# (without using this patch) by including `jacks-talk.json` in the
# list of IGNORE_FILES. However, if there are multiple `jacks-talk.json`
# files (maybe a bunch of different Jacks wanted to talk at a bunch of
# different conferences), we would exclude all `jacks-talk.json` files by
# including the single `jacks-talk.json` string in IGNORE_FILES. By checking
# the full path passed to `_include_path`, we can filter on a more granular
# level.
# Hopefully this patch can be removed by the merger of this PR:
# https://github.com/getpelican/pelican/pull/1975
class PyTubeArticlesGenerator(pelican.ArticlesGenerator):
    def _include_path(self, path, extensions=None):
        """Inclusion logic for .get_files(), returns True/False

        :param path: the path which might be including
        :param extensions: the list of allowed extensions (if False, all
            extensions are allowed)
        """
        if extensions is None:
            extensions = tuple(self.readers.extensions)

        #check IGNORE_FILES
        ignores = self.settings['IGNORE_FILES']
        if any(fnmatch.fnmatch(path, ignore) for ignore in ignores):
            return False

        basename = os.path.basename(path)
        if any(fnmatch.fnmatch(basename, ignore) for ignore in ignores):
            return False

        if extensions is False or basename.endswith(extensions):
            return True
        return False
pelican.ArticlesGenerator = PyTubeArticlesGenerator


def drop_no_publish(pelican_proj_obj):
    """
    Update IGNORE_FILES in pelicanconf with list of articles
    that should be excluded based on their ID. The list of article
    IDs that should be dropped is located in NO_PUBLISH_FILE.
    """
    excludes = pelican_proj_obj.settings.get('IGNORE_FILES', [])
    path = pelican_proj_obj.settings.get('PATH')
    data_dir = pelican_proj_obj.settings.get('DATA_DIR')

    no_publish_file = pelican_proj_obj.settings.get('NO_PUBLISH_FILE')
    if not no_publish_file:
        return

    no_publish_file_path = os.path.join(path, data_dir, no_publish_file)
    no_publish_ids = None
    if os.path.exists(no_publish_file_path):
        with open(no_publish_file_path, encoding='utf-8') as fp:
            no_publish_ids = set(json.load(fp))

    if not no_publish_ids:
        return

    paths = get_no_publish_paths(path, no_publish_ids)

    pelican_proj_obj.settings['IGNORE_FILES'] = excludes + paths


def get_no_publish_paths(pelican_path, no_publish_ids):
    search_pattern = os.path.join(pelican_path, '**/**/**/*.json')

    paths = []
    for file_path in glob.iglob(search_pattern):
        with open(file_path) as fp:
            try:
                blob = json.load(fp)
            except json.decoder.JSONDecodeError:
                print(f'Could not decode {file_path}', flush=True)
                continue
            if isinstance(blob, dict):
                file_id = blob.get('id')
                if file_id in no_publish_ids:
                    paths.append(file_path)

    no_publish_paths = []
    # strip paths so that all paths start with from inside of pelican PATH dir.
    for path in paths:
        path = path.replace(pelican_path, '')
        path = path.lstrip('/')
        no_publish_paths.append(path)

    return no_publish_paths


def register():
    signals.initialized.connect(drop_no_publish)

