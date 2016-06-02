import os
import shutil


CONTENT_DIR = 'content'
CONTENT_DIR_KEEP = set(('pages', 'images', 'extra'))


def purge_content():
    contents = os.listdir(CONTENT_DIR)
    for dir_ in contents:
        if dir_ not in CONTENT_DIR_KEEP:
            shutil.rmtree(os.path.join(CONTENT_DIR, dir_))


purge_content()

