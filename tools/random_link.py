import datetime
import random
import re
import urllib

import bs4
import requests


SITEMAP_URL = 'https://pyvideo.org/sitemap.xml'
PATTERN = re.compile(r'^/(?!speaker)(?!tag)(?!events)(?!pages).*/.+$')


def get_video_links():
    response = requests.get(SITEMAP_URL)
    soup = bs4.BeautifulSoup(response.content, 'lxml')

    one_year_ago = (datetime.datetime.now() - datetime.timedelta(days=365)).date()
    links = set()
    for url in soup.find_all('url'):
        loc = url.find('loc').string
        path = urllib.parse.urlparse(loc).path
        if PATTERN.match(path):
            mod_string = url.find('lastmod').string
            if datetime.datetime.strptime(mod_string, '%Y-%m-%d').date() > one_year_ago:
                links.add(path)

    return links


def get_used_links(used_links_file):
    try:
        with open(used_links_file) as fp:
            lines = fp.readlines()
            return set(line.strip() for line in lines)

    except FileNotFoundError:
        return set()


def save_newly_used_links(used_links_file, newly_used_links):
    with open(used_links_file, 'a') as fp:
        for link in newly_used_links:
            fp.write(link + '\n')


def main(used_links_file):
    links = get_video_links()
    used_links = get_used_links(used_links_file)

    unused_links = links - used_links

    newly_used_links = random.sample(unused_links, 3)

    save_newly_used_links(used_links_file, newly_used_links)

    for link in newly_used_links:
        print(f'https://pyvideo.org{link}')


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('used_links_file', help='TXT with on link per line')
    args = parser.parse_args()

    main(args.used_links_file)

