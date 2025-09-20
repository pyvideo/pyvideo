import glob
import fnmatch
import json
import os

import pelican
from pelican import signals
import six


# Monkey patch the ArticleGenerator to override two specific methods.
# 
# 1. We have to override the `_include_path` method because it does not
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
#
# 2. Override the `get_files` method to use the pre-4.0.0 behavior. This is
# required to maintain consistent rendering with the behavior of PyVideo when
# built using Pelican 3.7.1. In Pelican >=4.0.0, the `files` variable in this
# method is a set rather than a list, which manifests as PyVideo tags
# seemingly changing their case and formatting between renders due to file
# ordering and name collisions after the tag names are run through Pelican's
# `slugify` process. As a next step to remove this method override, the data
# repository should be updated to ensure consistency with tags (e.g. "Data
# Science" vs. "data science" vs. "data-science"), and a check should be added
# to prevent future tag duplication.
class PyVideoArticlesGenerator(pelican.ArticlesGenerator):
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

    def get_files(self, paths, exclude=[], extensions=None):
        """Return a list of files to use, based on rules
        :param paths: the list pf paths to search (relative to self.path)
        :param exclude: the list of path to exclude
        :param extensions: the list of allowed extensions (if False, all
            extensions are allowed)
        """
        # backward compatibility for older generators
        if isinstance(paths, six.string_types):
            paths = [paths]
        # group the exclude dir names by parent path, for use with os.walk()
        exclusions_by_dirpath = {}
        for e in exclude:
            parent_path, subdir = os.path.split(os.path.join(self.path, e))
            exclusions_by_dirpath.setdefault(parent_path, set()).add(subdir)

        files = []
        ignores = self.settings['IGNORE_FILES']
        for path in paths:
            # careful: os.path.join() will add a slash when path == ''.
            root = os.path.join(self.path, path) if path else self.path
            if os.path.isdir(root):
                for dirpath, dirs, temp_files in os.walk(
                        root, followlinks=True):
                    drop = []
                    excl = exclusions_by_dirpath.get(dirpath, ())
                    for d in dirs:
                        if (d in excl or
                            any(fnmatch.fnmatch(d, ignore)
                                for ignore in ignores)):
                            drop.append(d)
                    for d in drop:
                        dirs.remove(d)
                    reldir = os.path.relpath(dirpath, self.path)
                    for f in temp_files:
                        fp = os.path.join(reldir, f)
                        if self._include_path(fp, extensions):
                            files.append(fp)
            elif os.path.exists(root) and self._include_path(path, extensions):
                files.append(path)  # can't walk non-directories
        return files

pelican.ArticlesGenerator = PyVideoArticlesGenerator


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

