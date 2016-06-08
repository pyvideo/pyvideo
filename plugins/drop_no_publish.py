import glob
import json
import os

from pelican import signals


def drop_no_publish(pelican):
    """
    Update ARTICLE_EXCLUDES in pelicanconf with list of articles
    that should be excluded based on their ID. The list of article
    IDs that should be dropped is located in NO_PUBLISH_FILE.
    """
    excludes = pelican.settings.get('ARTICLE_EXCLUDES') or []
    path = pelican.settings.get('PATH')
    data_dir = pelican.settings.get('DATA_DIR')

    no_publish_file = pelican.settings.get('NO_PUBLISH_FILE')
    if not no_publish_file:
        return

    with open(os.path.join(path, data_dir, no_publish_file)) as fp:
        no_publish_ids = set(json.load(fp))

    if not no_publish_ids:
        return

    paths = get_no_publish_paths(path, no_publish_ids)

    pelican.settings['ARTICLE_EXCLUDES'] = excludes + paths


def get_no_publish_paths(pelican_path, no_publish_ids):
    search_pattern = os.path.join(pelican_path, '**/**/**/*.json')

    paths = []
    for file_path in glob.iglob(search_pattern):
        with open(file_path) as fp:
            blob = json.load(fp)
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

