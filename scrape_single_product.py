from bs4 import BeautifulSoup
import requests
from requests.exceptions import RequestException
import logging
import sys
import csv


# set up logging
logging.basicConfig(#filename = "log.txt",
                    level = logging.DEBUG, format = "%(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


# start scraping
## load the page
logger.info("App started.")
page_url = "http://www.shahrvand.ir/fa/product/cat/144.html#/pagesize-32/stock-1"
try:
    logger.info("Downloading page...")
    ##html_doc = requests.get(page_url).text
    with open("prod.html") as f:
        html_doc = f.read()
    logger.info("Page downloaded.")
except RequestException as ex:
    logger.error(ex)
    sys.exit(1)

## setup Beautiful Soup
logger.info("Parsing page...")
soup = BeautifulSoup(html_doc, "html.parser")

## setup output file
try:
    csvfile = open("prod.csv", "w", newline = "")
    csv_writer = csv.writer(csvfile)
    csv_writer.writerow(["title", "orig_price", "current_price"])
except Exception as e:
    logger.error(e)
    sys.exit(1)

## helper functions
def clean_price(price_text):
    if price_text:
        return price_text.string.replace("تومان", "").replace(",", "").strip()
    else:
        return ""

## actually parse html and save into csv
parent_tag = soup.find("div", class_ = "single_page_center")
raw_title = parent_tag.find("div", class_ = "title").string
final_price = clean_price(parent_tag.find("li", id = "price").contents[1])
description = parent_tag.find("div", class_ = "description")
brand = ""
for attr in description.find_all("li"):
    if (attr.contents[0].string.strip() == "برند :"):
        brand = attr.contents[1].string

logger.debug("title = " + raw_title)
logger.debug("brand = " + brand)
logger.debug("price = " + final_price)

# for tag in tags:
#     title = tag.find("a", class_ = "title").string
#     orig_price = tag.find("div", class_ = "old_price").span
#     orig_price = clean_price(orig_price)
#     cur_price = tag.find("div", class_ = "new_price")
#     cur_price = clean_price(cur_price)
#     logger.debug("title = {} \t\t orig price = {} \t cur price = {}\n".format(title, orig_price, cur_price))
#     csv_writer.writerow([title, orig_price, cur_price])
    #desc = tag.find("div", class_ = "description")
    #product_attrs = {}
    # for attr in desc("li"):
    #     spans = [s.string.strip() for s in attr.find_all("span")]
    #     key = spans[0]
    #     value = spans[1]
    #     product_attrs[key] = value
    

csvfile.close()

logger.info("Done.")


