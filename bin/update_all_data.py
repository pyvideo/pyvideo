"""
This module can be used to make changes to all data in the
data directory.
"""
import glob
import json


DATA_DIR = 'data'


def change_data(file_path, data):
    print(file_path)
    data['status'] = 'published'


def main():
    pattern = '{}/**/*.json'.format(DATA_DIR)
    json_file_paths = glob.iglob(pattern, recursive=True)

    for file_path in json_file_paths:
        with open(file_path) as fp:
            data = json.load(fp)

        change_data(file_path, data)

        with open(file_path, 'w') as fp:
            json.dump(data, fp, sort_keys=True, indent=4)

main()

