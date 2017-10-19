#
# An asynchronous web crawler, uses breadth-first search recursively
# Also, it doesn't work yet
# Author: Emily Quinn Finney
#
# TODO: Rewrite the web crawler tests
#

import aiohttp
import asyncio
import async_timeout
from bs4 import BeautifulSoup
import logging
import re
from urllib.parse import urlparse


try:
    import psyco
    psyco.full()
except ImportError:
    pass

#logging.basicConfig(level=logging.DEBUG)


class URLoader:

    def __init__(self, url, session):
        self.url = url
        self.session = session

    async def fetch(self):
        with async_timeout.timeout(10):
            async with self.session.get(self.url) as response:
                return await response.text()

    async def open_page(self):
        """
        Opens a web page using the urllib.request library, and returns a Beautiful Soup object
        :return: structured_page, the BeautifulSoup object
        """
        page = await self.fetch()
        structured_page = BeautifulSoup(page, 'lxml')
        return structured_page


class PageScraper:

    def __init__(self, url, sequence, id_sequence, page_loader, filename=None):
        """
        Initializes the PageScraper class.
        :param sequence: the sequence to which all URLs must be matched if they are to be scraped, string
        :param id_sequence: the sequence used to identify a product ID, string regex
        :param filename: the filename into which to scrape the website information, string
        """
        self.url = url
        self.sequence = sequence
        self.id_sequence = id_sequence
        self.filename = filename
        self.page_loader = page_loader
        # keeps track of all IDs that have been seen so far
        self.master_set = set()
        # keeps track of all URLs that have been seen so far, per level
        self.queue = [url]

    def locate_linked_pages(self, structured_page):
        """
        Given a page structured in a Beautiful Soup format, returns all the pages linked
        that contain a given sequence of characters in their URLs.
        :param structured_page: a page structured in Beautiful Soup format
        :return: linked_pages, a list of strings containing linked URLs
        """
        all_links = structured_page.find_all('a')
        for link in all_links:
            address = str(link.get('href'))
            if self.sequence in address:
                if not urlparse(address).netloc:
                    scheme = urlparse(self.url).scheme
                    base_url = urlparse(self.url).netloc
                    address = ''.join([scheme, '://', base_url, address])
                self.queue.append(address)

        return self.queue

    def add_link_to_master(self, link):

        id_number = find_id(link, self.id_sequence)
        if not identify_duplicates(link, self.master_set, self.id_sequence):
            #print(id_number)
            self.master_set.add(id_number)
            return True

        return False

    def find_undiscovered(self):
        undiscovered = list()
        for link in self.queue:
            if not identify_duplicates(link, self.master_set, self.id_sequence):
                undiscovered.append(link)

        return undiscovered

    async def update_queue(self, link):
        """
        Opens the URLoader and updates the queue with information retrieved
        :param link: the URL with which to update the queue
        :return:
        """
        self.add_link_to_master(link)
        self.page_loader.url = link
        result = await self.page_loader.open_page()
        write_page_to_file(result, self.filename)
        # gets all urls that haven't yet been seen
        self.locate_linked_pages(result)
        self.queue.remove(link)

    async def main(self):
        """
        Loads and scrapes pages.
        :return:
        """
        await self.update_queue(self.page_loader.url)

        while len(self.queue) > 0:
            # get the first link in the queue, will be removed at the end of self.update_queue()
            link = self.queue[0]
            if not identify_duplicates(link, self.master_set, self.id_sequence):
                await self.update_queue(link)
            else:
                self.queue.remove(link)


def find_id(url, id_sequence):
    """
    Matches the identification sequence in a URL, returning the ID number in the URL
    :param url: a URL from which to draw a product ID number
    :param id_sequence: the identification sequence used to ID products in a URL
    :return: id_number, the ID number of the product referenced in the URL
    """
    # find the parts of the string that match id_sequence
    if re.search(id_sequence, url):
        id_number = re.search(id_sequence, url).group()
    else:
        id_number = None
    return id_number


def identify_duplicates(url, master_set, id_sequence):
    """
    Determines whether the product has already been included in a master list of products.
    :param url: a URL from which to draw a product ID number
    :param master_set: the master set of products with which to compare the product ID
    :param id_sequence: the ID sequence used to ID products in a URL
    :return: a Boolean showing whether the product has been seen (T) or not (F)
    """
    id_number = find_id(url, id_sequence)
    if id_number:
        # check that ID against the master_set
        if id_number in master_set:
            return True
        else:
            return False
    # if no ID number, treat the page as a duplicate and don't add it to the list
    else:
        return True


def write_page_to_file(structured_page, filename, inspect=False):
    """
    Writes a page to file.
    :param structured_page: a page structured in Beautiful Soup format
    :param filename: the name of a file into which to write the HTML
    :param inspect: Boolean, a parameter indicating whether to print he page before writing
    :return:
    """
    page_string = structured_page.prettify()
    if inspect:
        print(page_string)
    with open(filename, 'a') as f:
        f.write(page_string)


if __name__ == '__main__':

    loop = asyncio.get_event_loop()

    with aiohttp.ClientSession(loop=loop) as client_session:
        TeaLoader = URLoader('http://shop.numitea.com/Tea-by-Type/c/NumiTeaStore@ByType', client_session)
        NumiTeaScraper = PageScraper('http://shop.numitea.com/Tea-by-Type/c/NumiTeaStore@ByType',
                                     'NumiTeaStore', 'NUMIS-[0-9]*', TeaLoader, 'new_tea_corpus.html')
        loop.run_until_complete(NumiTeaScraper.main())

    loop.close()
