# testing web crawler

import asyncio
import web_crawler as webs

async def test_open_page(url='http://shop.numitea.com/Tea-by-Type/c/NumiTeaStore@ByType'):
    loop = asyncio.get_event_loop()
    loop.run_until_complete(webs.open_page(url))
    loop.close()


async def test_locate_linked_pages(url='http://shop.numitea.com/Tea-by-Type/c/NumiTeaStore@ByType',
                             sequence='c=NumiTeaStore@ByType'):
    loop = asyncio.get_event_loop()
    set_of_links = await webs.locate_linked_pages(url, sequence)
    loop.close()
    for thing in set_of_links:
        assert sequence in thing


def test_find_id(url='http://shop.numitea.com/NUMIS-10430&c=NumiTeaStore@ByType@Puerh',
                 id_sequence='NUMIS-[0-9]*'):
    value = webs.find_id(url, id_sequence)
    assert value == 'NUMIS-10430'


def test_identify_duplicates(url='http://shop.numitea.com/NUMIS-10430&c=NumiTeaStore@ByType@Puerh',
                             master_list={'NUMIS-10430'}, id_sequence='NUMIS-[0-9]*'):
    truefalse = webs.identify_duplicates(url, master_list, id_sequence)
    assert truefalse
