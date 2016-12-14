#!/usr/bin/env python3
"""
Check a site and report broken links.
"""
from argparse import ArgumentParser
import sys
from queue import Queue
from urllib.parse import urlparse, urljoin

from bs4 import BeautifulSoup
import requests

def extract_links(address):
    """extracts links from a web page"""
    try:
        r = requests.get(address)
        soup = BeautifulSoup(r.text, "html.parser")
        for link in soup.find_all('a'):
            extracted_link = link.get("href")
            yield extracted_link
    except requests.exceptions.RequestException:
        pass

def collect_links(url):
    """gathers links, returns sets of internal and external links"""
    site = urlparse(url).netloc.split(".")[1]
    to_visit = Queue()
    visited_links = set()
    external_urls = set()
    malformed_urls = set()
    seen = set()
    to_visit.put(url)
    
    while not to_visit.empty():

        address = to_visit.get() 
        extracted = extract_links(address)
        visited_links.add(address)

        for ext_link in extracted:
            parsed_link = urlparse(ext_link)
            if parsed_link.netloc == "":
                ext_link = urljoin(address, ext_link)
            netloc = str(urlparse(ext_link).netloc)
            scheme = str(urlparse(ext_link).scheme)
            if site in netloc and ext_link not in seen:
                to_visit.put(ext_link)
                seen.add(ext_link)
            if "http" in scheme and site not in netloc and ext_link not in seen:
                external_urls.add(ext_link)
                seen.add(ext_link)
            if "http" not in scheme:
                malformed_urls.add(ext_link)
                seen.add(ext_link)
                    
    return visited_links, external_urls, malformed_urls
  
def main(start_url):
    visited_links, external_urls, malformed_urls = collect_links(args.url)
    if args.external:
        gathered_links = external_urls
    else:
        gathered_links = visited_links.union(external_urls)
    
    errors = {}
    for a in gathered_links:
        try:
            requests.get(a).status_code
        except requests.exceptions.RequestException as e:
            errors[a] = e

    if errors:
        for i in errors:
            print(i, ":", errors[i])
        sys.exit("Exit 1")
    else:
        sys.exit()

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('url', type=str, help="Enter a url in the form http://www.pyvideo.org")
    parser.add_argument("--external", action="store_true", help="Check only links to external sites")
    args = parser.parse_args()

    main(args.url)
