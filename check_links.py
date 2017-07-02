#!/usr/bin/env python3
"""
Check a site and report broken links.
"""
import asyncio 
import aiohttp 
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin, urlunparse
from queue import Queue
from sys import exit 
from argparse import ArgumentParser

async def get_page(url):
    try:
        conn = aiohttp.TCPConnector(verify_ssl=False)
        async with aiohttp.ClientSession(loop=loop, connector=conn) as session:
            async with session.get(url, timeout=60) as response:
                return await response.text() 
    except:
        pass

async def extract_links(url):
    urls = set() 
    with await asyncio.Semaphore(10): 
        html = await get_page(url)
        soup = BeautifulSoup(html, "html.parser")
        for link in soup.find_all('a'):
            extracted_link = link.get("href")
            parsed_link = urlparse(extracted_link)
            if parsed_link.scheme == "https":
                extracted_link = urlunparse(("http",) + parsed_link[1:])
            urls.add(extracted_link)
    return urls

async def collect_links(url):
    """gathers links, returns sets of internal and external links"""
    site = urlparse(url).netloc.split(".")[1]
    #move this to Argparse? 
    if site == "com" or site =="org":
        exit("exit 1 {}.com or {}.org is not a valid url.".format(site, site))
    
    to_visit = Queue()
    visited_links = set()
    external_urls = set()
    malformed_urls = set()
    seen = set()
    to_visit.put(url)
    
    while not to_visit.empty():
        address = to_visit.get() 
        extracted = await extract_links(address)
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

async def check_links(url): 
    errors = {}
    try:
        with await asyncio.Semaphore(10): 
            conn = aiohttp.TCPConnector(verify_ssl=False)
            async with aiohttp.ClientSession(loop=loop, connector=conn) as session:
                async with session.get(url, timeout=60) as resp:
                    if not resp.status == 200:
                        errors[url] = resp.status
               
    except Exception as e:
        errors[url] = e
    return errors 

async def main(start_url, loop):
    visited_links, external_urls, malformed_urls = await collect_links(args.url)
    if args.external:
        gathered_links = external_urls
    else:
        gathered_links = visited_links.union(external_urls)
    
    for url in gathered_links:
        errors = await check_links(url)

    if errors:
        for i in errors:
            print(i, ":", errors[i])
        exit("Exit 1")
    else:
        exit()

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('url', type=str, help="Enter a url in the form http://www.pyvideo.org")
    parser.add_argument("--external", action="store_true", help="Check only links to external sites")
    args = parser.parse_args()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(args.url, loop))
