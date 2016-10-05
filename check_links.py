#!/usr/bin/env python3 
""" A script to check pyvideo.org for broken links. Takes a url in the form "http://www.pyvideo.org as argument in the command line. """

import argparse
from urllib.parse import urlparse, urljoin

from bs4 import BeautifulSoup
import requests

def collect_links(url):
  
    to_visit, found_links, visited_links, internal_urls, external_urls, malformed_urls = set(), set(), set(), set(), set(), set()

    found_links.add(url)
    to_visit.add(url)
    
    while to_visit:
        
        to_visit = set(el for el in found_links if "pyvideo" in urlparse(el).netloc and el not in visited_links.union(external_urls, malformed_urls))

        for address in to_visit: 

            try:
                r = requests.get(address)
                soup = BeautifulSoup(r.text, "lxml")
                
                for link in soup.find_all('a'):
                    extracted_link = link.get("href")
                    parsed_link = urlparse(extracted_link)
                    if extracted_link not in visited_links and extracted_link not in external_urls and extracted_link not in malformed_urls:
                        found_links.add(str(extracted_link)) 
                    if parsed_link.netloc == "":
                        joined_url = urljoin(address, extracted_link)
                        if urlparse(joined_url).scheme and urlparse(joined_url).netloc:
                            found_links.add(str(joined_url))
           
            except requests.exceptions.RequestException:
                pass

            internal_urls = set(el for el in found_links if urlparse(el).scheme and 
                "pyvideo" in urlparse(el).netloc)

            external_urls = set(el for el in found_links if urlparse(el).scheme and
                "pyvideo" not in urlparse(el).netloc)

            malformed_urls = set(el for el in found_links if urlparse(el).netloc and el not in internal_urls.union(external_urls))

            
            visited_links.add(address)
            


    return visited_links, external_urls, malformed_urls
  
def main(start_url):

    link_collection = collect_links(args.url)

    linkset, external_urls = link_collection[0], link_collection[1]

    try:

        checked = {a: requests.get(a).status_code for a in gathered_links}

    except requests.exceptions.RequestException as e:
        print("url {} generated exception {}".format(a,e))

  
    print("Number of pages checked: ", len(checked))

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('url')
    args = parser.parse_args()

    main(args.url)
