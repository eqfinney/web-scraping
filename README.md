# Asynchronous Web Scraping
Author: Emily Quinn Finney
Version: 2.0

In this package I implemented an asynchronous breadth first search based web
crawler/scraper as part of my time at the Recurse Center 
(https://www.recurse.com/). The package relies primarily on Python's asyncio
and Beautiful Soup libraries. 


## Features/Details

While writing this code, I tested two different methods of object-oriented software design.

* web_crawler_dependency_injection.py: Creates a page loading object (URLoader) and uses this object within another object that scrapes a web page (PageScraper).
* web_crawler_main_class.py:  Creates a page loading object (URLoader) and a page scraping object (PageScraper) and integrates both objects into a main class (MainScraper) that controls all high-level logic. 

Version 1.0 was written recursively, and was not implemented asynchronously.


## Running Tests

To test the code, you will need pytest installed. Then type the following into the terminal: 

```
pytest -v -s test_web_crawler_{$TEST_MODULE}.py
```


Last edited 04/05/2017