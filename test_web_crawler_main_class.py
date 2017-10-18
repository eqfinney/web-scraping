#
# Testing asynchronous web crawler
# Author: Emily Quinn Finney
#

from bs4 import BeautifulSoup
import os
import pytest
import requests
import unittest
import web_crawler_main_class as websclass


# TODO: figure out what's up with pytest-asyncio event_loop fixture
@pytest.fixture
@pytest.mark.asyncio
def loader(event_loop):
    import aiohttp
    with aiohttp.ClientSession(loop=event_loop) as client_session:
        # initialize the objects
        return websclass.URLoader('http://shop.numitea.com/Tea-by-Type/c/NumiTeaStore@ByType', client_session)


@pytest.mark.asyncio
async def test_fetch(loader):
    response = await loader.fetch()
    print(response.text)


@pytest.mark.asyncio
async def test_open_page(loader):
    structured_page = await loader.open_page()
    print(structured_page)


class TestPageScraper(unittest.TestCase):

    def setUp(self):
        self.crawler = websclass.PageScraper('http://shop.numitea.com/Tea-by-Type/c/NumiTeaStore@ByType',
                                             'NumiTeaStore@ByType', 'NUMIS-[0-9]*')
        page = requests.get(self.crawler.url).text
        self.structured_page = BeautifulSoup(page, 'lxml')

    def test_locate_linked_pages(self):
        set_of_links = self.crawler.locate_linked_pages(self.structured_page)
        for thing in set_of_links:
            assert self.crawler.sequence in thing

    def test_add_link_to_master(self,
                                link='http://shop.numitea.com/Mate-Lemon/p/NUMIS-10250&c=NumiTeaStore@Teabag@Green'):
        master_list_before = len(self.crawler.master_set)
        result = self.crawler.add_link_to_master(link)
        assert result
        master_list_after = len(self.crawler.master_set)
        assert master_list_after == master_list_before + 1


class TestWritePage(unittest.TestCase):

    def setUp(self):
        self.filename = 'test_file.txt'
        page = requests.get('http://shop.numitea.com/Mate-Lemon/p/NUMIS-10250&c=NumiTeaStore@Teabag@Green').text
        self.structured_page = BeautifulSoup(page, 'lxml')

    def test_write_page_to_file(self):
        websclass.write_page_to_file(self.structured_page, self.filename)
        # assert filename exists
        assert os.path.isfile(self.filename)

    def tearDown(self):
        os.remove(self.filename)


def test_find_id(url='http://shop.numitea.com/Mate-Lemon/p/NUMIS-10250&c=NumiTeaStore@Teabag@Green',
                 id_sequence='NUMIS-[0-9]*'):
    number = websclass.find_id(url, id_sequence)
    assert number == 'NUMIS-10250'


def test_identify_duplicates(url='http://shop.numitea.com/Mate-Lemon/p/NUMIS-10250&c=NumiTeaStore@Teabag@Green',
                             master_list=set(), id_sequence='NUMIS-[0-9]*'):
    result = websclass.identify_duplicates(url, master_list, id_sequence)
    assert not result
    master_list.add('NUMIS-10250')
    next_result = websclass.identify_duplicates(url, master_list, id_sequence)
    assert next_result

"""
class TestMainScraper:

    def setUp(self):
        pass

    async def test_update_queue(self, link):
        pass

    async def test_main(self):
        pass
"""
