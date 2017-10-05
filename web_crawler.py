#
# A synchronous web crawler, uses breadth-first search
# Author: Emily Quinn Finney
#
# Fixes:
# Make it asynchronous!
#


import urllib.request as urq
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import re

try:
    import psyco
    psyco.full()
except ImportError:
    pass


class PageScraper:

    def __init__(self, url, sequence, id_sequence, filename):
        """
        Initializes the PageScraper class.
        :param url: the base URL from which to scrape, string
        :param sequence: the sequence to which all URLs must be matched if they are to be scraped, string
        :param id_sequence: the sequence used to identify a product ID, string
        :param filename: the filename into which to scrape the website information, string
        """
        self.url = url
        self.sequence = sequence
        self.id_sequence = id_sequence
        self.filename = filename
        # keeps track of all URLs that have been visited so far
        self.master_list = set()

    def scrape_page(self):
        """
        Scrapes a page and all underlying page whose titles match a certain sequence, writing
        the text results into a text file.
        :return: set_of_links, a set of the pages successfully scraped
        """

        # find urls in layer 0
        undiscovered = locate_linked_pages(self.url, self.sequence)
        # all urls that haven't yet been seen, which should be everything
        self.master_list.update(self.scrape_layer(undiscovered))

    def scrape_layer(self, undiscovered):
        """
        Examines each of the pages matching a given sequence on a layer, writing the results to a text file.
        :param undiscovered: the URLs that have not yet been searched
        :return:
        """
        print('we have', len(undiscovered), 'objects!')
        url_list = set()

        # return master list if undiscovered is empty
        if not undiscovered:
            return self.master_list

        else:
            # we want to discover new URLs on each page
            for link in undiscovered:
                id_number = find_id(link, self.id_sequence)
                if not identify_duplicates(link, self.master_list, self.id_sequence):
                    self.master_list.add(id_number)
                    print(link)
                    open_page(link, self.filename, write=True, inspect=False)
                    url_list.update(locate_linked_pages(link, self.sequence))

            # recurse to the next layer, looking at only undiscovered links
            undiscovered = (url_list - self.master_list)
            self.master_list.update(self.scrape_layer(undiscovered))

            return self.master_list


def open_page(url, filename=None, write=True, inspect=False):
    """
    Opens a web page using the urllib.request library, and returns a Beautiful Soup object
    :param url: string, the URL of the web page of interest.
    :param filename: string, the file name to which the page should be written
    :param write: boolean, determines whether or not to write the prettified HTML page
    :param inspect: boolean, determines whether or not to print the prettified nested HTML page
    :return: structured_page, the BeautifulSoup object
    """
    page = urq.urlopen(url)
    structured_page = BeautifulSoup(page, 'lxml')
    page_string = structured_page.prettify()
    if inspect:
        print(page_string)
    if write:
        with open(filename, 'a') as f:
            f.write(page_string)
    return structured_page


def locate_linked_pages(url, sequence):
    """
    Given a page structured in a Beautiful Soup format, returns all the pages linked
    that contain a given sequence of characters in their URLs.
    :param url: a url for a web page, string
    :param sequence: the sequence to match in each of the chosen URLs
    :return: linked_pages, a list of strings containing linked URLs
    """
    structured_page = open_page(url)
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

"""
if __name__ == '__main__':
    NumiTeaScraper = PageScraper('http://shop.numitea.com/Tea-by-Type/c/NumiTeaStore@ByType',
                                 'c=NumiTeaStore@ByType', 'NUMIS-[0-9]*', 'tea_corpus.txt')
    NumiTeaScraper.scrape_page()
"""
