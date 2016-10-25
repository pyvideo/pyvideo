#!/usr/bin/env python3
"""
Check pyvideo.org for broken links.
"""
import argparse
import sys
from urllib.parse import urlparse, urljoin

from bs4 import BeautifulSoup
import requests

def collect_links(url):
    site = urlparse(url).netloc.split(".")[1]
    to_visit = set()
    found_links = set()
    visited_links = set()
    internal_urls = set()
    external_urls = set() 
    malformed_urls = set()

    found_links.add(url)
    to_visit.add(url)
    
    while to_visit:

        seen = visited_links.union(external_urls, malformed_urls)
        to_visit = set()
        for el in found_links:
            if site in urlparse(el).netloc and el not in seen:
                to_visit.add(el)

        for address in to_visit: 

            try:
                r = requests.get(address)
                soup = BeautifulSoup(r.text, "html.parser")
                
                for link in soup.find_all('a'):
                    extracted_link = link.get("href")
                    parsed_link = urlparse(extracted_link)
                    if extracted_link not in seen:
                        found_links.add(str(extracted_link)) 
                    if parsed_link.netloc == "":
                        joined = urljoin(address, extracted_link)
                        if urlparse(joined).scheme and urlparse(joined).netloc:
                            found_links.add(str(joined))
           
            except requests.exceptions.RequestException:
                pass
            for el in found_links:
                if urlparse(el).scheme and site in urlparse(el).netloc:
                    internal_urls.add(el)
                elif urlparse(el).scheme and site not in urlparse(el).netloc:
                    external_urls.add(el)
                else:
                    malformed_urls.add(el)

            visited_links.add(address)          
    return visited_links, external_urls, malformed_urls
  
def main(start_url):
    visited_links, external_urls, malformed_urls = collect_links(args.url)
    gathered_links = visited_links.union(external_urls)
    
    errors = {}
    for a in gathered_links: 
        try:
            requests.get(a).status_code
        except requests.exceptions.RequestException as e:
            errors[a] = e
    if errors:
        for i in errors: 
            print(i,":", errors[i])
        sys.exit("Exit 1")
    else:
        sys.exit() 

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('url', type=str, help="Enter a url in the form http://www.pyvideo.org")
    args = parser.parse_args()

    main(args.url)
