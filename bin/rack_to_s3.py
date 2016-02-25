import concurrent.futures
import glob
import json
import math
import os
from urllib.parse import urlparse
from urllib.request import urlopen
import sys

from boto.s3.connection import S3Connection
from boto.s3.key import Key
from filechunkio import FileChunkIO


DATA_DIR = 'data'
KEYS = (
    'video_flv_url',
    'video_mp4_url',
    'video_ogv_url',
    'video_webm_url',
)
PYTUBE_BUCKET = 'pytube'
AWSID, AWSSECRET = os.environ.get('AWSID'), os.environ.get('AWSSECRET')
UP_CHUNK_SIZE = 52428800
TEMP_FILE = 'temp-media-file'


def generate_paths_to_copy(json_file_paths):
    for json_file_path in json_file_paths:

        with open(json_file_path) as fp:
            data = json.load(fp)

        if isinstance(data, dict):
            data = [data]

        for media_record in data:
            for key in KEYS:
                value = media_record.get(key)
                if value and 'rackcdn' in value:
                    yield value


def copy(args):
    bucket, source, dest = args
    sys.stdout.write('Downloading: {}\n'.format(source))
    sys.stdout.flush()
    
    try:
        response = urlopen(source)
        headers = {'Content-Type' : response.info().get_content_type()}
        with open(TEMP_FILE, 'wb') as fp:
            while True:
                chunk = response.read(16 * 1024)
                if not chunk:
                    break
                fp.write(chunk)
    except Exception as e:
        sys.stdout.write('Failed to download: {}\n'.format(source))
        sys.stdout.write('{}\n'.format(e.message))
        sys.stdout.flush()
        return

    source_size = os.stat(TEMP_FILE).st_size
    mp = bucket.initiate_multipart_upload(dest, headers=headers, reduced_redundancy=True)
    chunk_count = int(math.ceil(source_size / float(UP_CHUNK_SIZE)))

    try:
        sys.stdout.write('Uploading: {}\n'.format(source))
        sys.stdout.flush()
        for i in range(chunk_count):
            offset = UP_CHUNK_SIZE * i
            bytes = min(UP_CHUNK_SIZE, source_size - offset)
            with FileChunkIO(TEMP_FILE, 'r', offset=offset, bytes=bytes) as fp:
                mp.upload_part_from_file(fp, part_num=i + 1)

        mp.complete_upload()
    except Exception as e:
        mp.cancel_upload()
        sys.stdout.write('Failed to upload: {}\n'.format(source))
        sys.stdout.write('{}\n'.format(e))
        sys.stdout.flush()
        return


def main():
    conn = S3Connection(AWSID, AWSSECRET)
    bucket = conn.get_bucket(PYTUBE_BUCKET)

    pattern = '{}/**/*.json'.format(DATA_DIR)
    json_file_paths = glob.iglob(pattern, recursive=True)
    paths = sorted(generate_paths_to_copy(json_file_paths))

    args = ((bucket, path, urlparse(path).path) for path in paths)

    for arg_tup in args:
       copy(arg_tup) 

    print('Done.')


main()

