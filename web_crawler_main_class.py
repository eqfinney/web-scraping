#
# An asynchronous web crawler, uses breadth-first search
# Author: Emily Quinn Finney
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


class PageScraper:

    def __init__(self, url, sequence, id_sequence):
        """
        Initializes the PageScraper class.
        :param sequence: the sequence to which all URLs must be matched if they are to be scraped, string
        :param id_sequence: the sequence used to identify a product ID, string regex
        """
        self.url = url
        self.sequence = sequence
        self.id_sequence = id_sequence
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

    # TODO: make sure these have docstrings
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


# TODO: worth making this more unit-testable?
def identify_duplicates(url, master_set, id_sequence):
    """
    Determines whether the product has already been included in a master set of products.
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


class URLoader:

    def __init__(self, url, session):
        self.url = url
        self.session = session

    async def fetch(self):
        with async_timeout.timeout(10):
            async with self.session.get(self.url) as response:
                return await response.text()

    # TODO: worth making this more unit-testable?
    async def open_page(self):
        """
        Opens a web page using the urllib.request library, and returns a Beautiful Soup object
        :return: structured_page, the BeautifulSoup object
        """
        page = await self.fetch()
        structured_page = BeautifulSoup(page, 'lxml')
        return structured_page


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


class MainScraper:

    def __init__(self, url_loader, page_scraper, filename):
        """
        Initializes the MainScraper class, which combines functionality of PageScraper and URLoader classes.
        :param url_loader: the object that loads URLs given to it
        :param page_scraper: the object that scrapes HTML from a given web page
        :param filename: the name of the file into which to write the HTML, string
        :return:
        """
        self.url_loader = url_loader
        self.page_scraper = page_scraper
        self.filename = filename

    async def update_queue(self, link):
        """
        Opens the URLoader and updates the queue with information retrieved
        :param link: the URL with which to update the queue
        :return:
        """
        self.page_scraper.add_link_to_master(link)
        self.url_loader.url = link
        result = await self.url_loader.open_page()
        write_page_to_file(result, self.filename)
        # gets all urls that haven't yet been seen
        self.page_scraper.locate_linked_pages(result)
        self.page_scraper.queue.remove(link)

    async def main(self):
        """
        Loads and scrapes pages.
        :return:
        """
        await self.update_queue(self.url_loader.url)

        while len(self.page_scraper.queue) > 0:
            # get the first link in the queue, will be removed at the end of self.update_queue()
            link = self.page_scraper.queue[0]
            if not identify_duplicates(link, self.page_scraper.master_set, self.page_scraper.id_sequence):
                await self.update_queue(link)
            else:
                self.page_scraper.queue.remove(link)


if __name__ == '__main__':

    loop = asyncio.get_event_loop()

    with aiohttp.ClientSession(loop=loop) as client_session:
        # initialize the objects
        TeaLoader = URLoader('http://shop.numitea.com/Tea-by-Type/c/NumiTeaStore@ByType', client_session)
        NumiTeaScraper = PageScraper('http://shop.numitea.com/Tea-by-Type/c/NumiTeaStore@ByType',
                                     'NumiTeaStore', 'NUMIS-[0-9]*')
        PrimaryScraper = MainScraper(TeaLoader, NumiTeaScraper, 'new_tea_corpus.html')

        loop.run_until_complete(PrimaryScraper.main())

    loop.close()
