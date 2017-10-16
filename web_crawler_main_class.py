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

logging.basicConfig(level=logging.DEBUG)


class PageScraper:

    def __init__(self, url, sequence, id_sequence):
        """
        Initializes the PageScraper class.
        :param sequence: the sequence to which all URLs must be matched if they are to be scraped, string
        :param id_sequence: the sequence used to identify a product ID, string regex
        :param filename: the filename into which to scrape the website information, string
        """
        self.url = url
        self.sequence = sequence
        self.id_sequence = id_sequence
        # keeps track of all IDs that have been seen so far
        self.master_list = set()
        # keeps track of all URLs that have been seen so far, per level
        self.url_list = set()

    async def scrape_page(self, page):
        """
        Scrapes a page and all underlying page whose titles match a certain sequence, writing
        the text results into a text file.
        :return: set_of_links, a set of the pages successfully scraped
        """

        # find urls in layer 0
        undiscovered = locate_linked_pages(first_page, self.sequence, self.url)
        # handle the futures asynchronously
        # gets all urls that haven't yet been seen, which should be everything
        all_urls = await self.scrape_layer(undiscovered)
        self.master_list.update(all_urls)

    async def scrape_layer(self, undiscovered, recursive=True):
        """
        Examines each of the pages matching a given sequence on a layer, writing the results to a text file.
        :param undiscovered: the URLs that have not yet been searched
        :return:
        """
        print('we have', len(undiscovered), 'objects!')

        # return master list if undiscovered is empty
        if len(undiscovered) > 0:
            # we want to discover new URLs on each page
            linked_pages = set()
            for link in undiscovered:
                id_number = find_id(link, self.id_sequence)
                if not identify_duplicates(link, self.master_list, self.id_sequence):
                    self.master_list.add(id_number)
                    #TODO: make eliminate page_loader and make this totally independent
                    self.page_loader.url = link
                    structured_page = await self.page_loader.open_page()
                    linked_pages = locate_linked_pages(structured_page, self.sequence, self.url)

            self.url_list.update(linked_pages)

            if recursive:
                await self.recurse_layer()

        return self.master_list

    async def recurse_layer(self):
        """
        Implements recursion in lower layers, looking only at undiscovered links
        :param undiscovered: the URLs that have not yet been searched
        :return:
        """
        # make sure the links aren't duplicates before labelling them undiscovered
        undiscovered = { x for x in self.url_list
                         if not identify_duplicates(x, self.master_list, self.id_sequence) }
        print('undiscovered: ', undiscovered)
        #import ipdb; ipdb.set_trace()
        if len(undiscovered) > 0:
            # define a set of recursive tasks, but do not yet complete them
            tasks = [ self.scrape_layer(undiscovered) ]
            # gather the tasks and run the recursion asynchronously
            # as you do, update the master list with findings
            self.master_list.update(await asyncio.gather(*tasks))


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


def locate_linked_pages(structured_page, sequence, url):
    """
    Given a page structured in a Beautiful Soup format, returns all the pages linked
    that contain a given sequence of characters in their URLs.
    :param structured_page: a page structured in Beautiful Soup format
    :param sequence: the sequence to which to match to return a link
    :param url: the base url from which to scrape, string
    :return: linked_pages, a list of strings containing linked URLs
    """
    all_links = structured_page.find_all('a')
    set_of_links = set()
    for link in all_links:
        address = str(link.get('href'))
        if sequence in address:
            if not urlparse(address).netloc:
                scheme = urlparse(url).scheme
                base_url = urlparse(url).netloc
                address = ''.join([scheme, '://', base_url, address])
            set_of_links.add(address)

    return set_of_links


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


def identify_duplicates(url, master_list, id_sequence):
    """
    Determines whether the product has already been included in a master list of products.
    :param url: a URL from which to draw a product ID number
    :param master_list: the master list of products with which to compare the product ID
    :param id_sequence: the ID sequence used to ID products in a URL
    :return: a Boolean showing whether the product has been seen (T) or not (F)
    """
    id_number = find_id(url, id_sequence)
    if id_number:
        # check that ID against the master_list
        if id_number in master_list:
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
        # initialize the objects
        TeaLoader = URLoader('http://shop.numitea.com/Tea-by-Type/c/NumiTeaStore@ByType', client_session)
        NumiTeaScraper = PageScraper('http://shop.numitea.com/Tea-by-Type/c/NumiTeaStore@ByType',
                                     'c=NumiTeaStore@ByType', 'NUMIS-[0-9]*')

        while len(NumiTeaScraper.undiscovered) > 0:
            NumiTeaScraper.scrape_page(result)
            next_link = NumiTeaScraper.undiscovered[0]
            result = TeaLoader.open_page(next_link, client_session)
            write_page_to_file(result, 'new_tea_corpus.html')

        loop.run_until_complete(NumiTeaScraper.scrape_page())

    loop.close()
