#
# Testing asynchronous web crawler
# Author: Emily Quinn Finney
#

from bs4 import BeautifulSoup
import os
import pytest
import requests
import web_crawler_dependency_injection as websclass


@pytest.fixture
def link():
    return 'http://shop.numitea.com/Mate-Lemon/p/NUMIS-10250&c=NumiTeaStore@Teabag@Green'


@pytest.fixture
def structured_page(link):
    page = requests.get(link).text
    return BeautifulSoup(page, 'lxml')


@pytest.fixture
@pytest.mark.asyncio
def loader(event_loop, link):
    import aiohttp
    with aiohttp.ClientSession(loop=event_loop) as client_session:
        # initialize the objects
        yield websclass.URLoader(link, client_session)


@pytest.fixture
def filename():
    filename = 'test_file.txt'
    yield filename
    print("commence filename teardown")
    if os.path.isfile(filename):
        os.remove(filename)


@pytest.fixture
def crawler(link, loader, filename):
    return websclass.PageScraper(link, 'NumiTeaStore', 'NUMIS-[0-9]*', loader, filename)


@pytest.mark.asyncio
async def test_fetch(loader):
    response = await loader.fetch()
    print(response)


@pytest.mark.asyncio
async def test_open_page(loader):
    structured_page = await loader.open_page()
    print(structured_page)


def test_locate_linked_pages(crawler, structured_page):
    set_of_links = crawler.locate_linked_pages(structured_page)
    for thing in set_of_links:
        assert crawler.sequence in thing


def test_add_link_to_master(crawler, link):
    master_list_before = len(crawler.master_set)
    result = crawler.add_link_to_master(link)
    assert result
    master_list_after = len(crawler.master_set)
    assert master_list_after == master_list_before + 1


@pytest.mark.asyncio
async def test_update_queue(crawler, link):
    count_before = crawler.queue.count(link)
    await crawler.update_queue(link)
    # test that it changed url loader
    assert crawler.page_loader.url == link
    # TODO: test that it removed link from queue


def test_find_id(link, id_sequence='NUMIS-[0-9]*'):
    number = websclass.find_id(link, id_sequence)
    assert number == 'NUMIS-10250'


def test_identify_duplicates(link, master_list=set(), id_sequence='NUMIS-[0-9]*'):
    result = websclass.identify_duplicates(link, master_list, id_sequence)
    assert not result
    master_list.add('NUMIS-10250')
    next_result = websclass.identify_duplicates(link, master_list, id_sequence)
    assert next_result


def test_write_page_to_file(filename, structured_page):
    websclass.write_page_to_file(structured_page, filename)
    assert os.path.isfile(filename)
