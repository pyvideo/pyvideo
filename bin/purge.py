import os
import shutil
import sys


CONTENT_DIR = 'content'
CONTENT_DIR_KEEP = set(('pages', 'images', 'extra'))


def purge_content():
    contents = os.listdir(CONTENT_DIR)

    dirs_to_keep = CONTENT_DIR_KEEP.copy()
    if sys.argv[1].strip():
        dirs = (dir_.strip() for dir_ in sys.argv[1].strip().split(','))
        dirs_to_keep.update(dirs)
    for dir_ in contents:
        if dir_ not in dirs_to_keep:
            shutil.rmtree(os.path.join(CONTENT_DIR, dir_))


purge_content()

