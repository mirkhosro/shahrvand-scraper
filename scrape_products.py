from bs4 import BeautifulSoup
import requests
from requests.exceptions import RequestException
import logging
import sys
import csv
import re
import time

zwnj_ptrn = re.compile("\u200c+")
white_ptrn = re.compile("[\u200c\u200f ]+")
size_ptrn = re.compile("\d+([\.،]\d+)? (گرمی|عددی|میلی لیتری|کیلویی|عدد) ")

# set up logging
logging.basicConfig(#filename = "log.txt",
                    level = logging.DEBUG, format = "%(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

## helper functions
def get_id(tag):
    # e.g. <div class = "product product1495">
    # product id is included in the second value of class atribute
    # so look for the second item (index 1) and after the word 'product' (length 7)
    return(tag["class"][1][7:])

    
def clean_price(price_text):
    "Cleans price tags by removing currency units and thousand separators."
    if price_text:
        return price_text.string.replace("تومان", "").replace(",", "").strip()
    else:
        return ""


def normalize_text(some_text):
    ## replace extra white spaces and ZWNJ with just one space
    some_text = white_ptrn.sub(" ", some_text)
    ## remove accents
    some_text = re.sub("[\u064e-\u0651]", "", some_text)
    ## use Persian letters
    some_text = some_text.replace("ي", "ی").replace("ك", "ک")
    return some_text.strip()


def clean_title(a_title):
    "Remove unnecessary stuff from a product title."
    clean_title = normalize_text(a_title)
    clean_title = re.sub("-", " ", clean_title)
    clean_title = size_ptrn.sub("", clean_title)
    return clean_title.strip()


def fix_brand(brand, all_brands):
    fixed = None
    if fixed is None:
        for good_brand in all_brands:
            if good_brand.replace(" ", "") == brand.replace(" ", ""):
                fixed = good_brand
    if fixed is None:
        for good_brand in all_brands:
            if brand in good_brand.split(" "):
                fixed = good_brand
                #logger.debug(f"{brand} found in {good_brand}")
    if fixed is None:
        for good_brand in all_brands:
            if brand.replace(" ", "") in good_brand.replace(" ", ""):
                fixed = good_brand
                #logger.debug(f"{brand} found in {good_brand}")
    return fixed

    
def get_brand(title: str, all_brands: set) -> str:
    # replace ZWNJ with space so we have better search keywords
    brand = title.split(" ")[-1]
    brand = normalize_text(brand)
    if all_brands is None or brand in all_brands:
        return brand
    else:
        fixed = fix_brand(brand, all_brands)
        if fixed is None:
            logger.info(f"The brand {brand} not found in brands.")
            return brand
        else:
            #logger.info(f"The brand {brand} replaced with {fixed}.")
            return fixed


def get_image_file_name(tag):
    image_file = tag.find("img")["src"]
    m = re.search(".*/(.+\.jpg)$", image_file)
    return m.group(1)


def get_keywords(title, brand):
    filtered = title
    filtered = re.sub(" (ها|ای|با|و|در|شده) ", " ", filtered)
    filtered = re.sub("\d+((\.|،)\d+)? \w+ ", "", filtered)
    filtered = filtered.replace(brand, "").strip()
    keywords = filtered.split(" ")
    keywords.append(brand)
    return keywords


def augment_keywords(keywords):
    """Augment keywords to generate all possible combinations."""
    stack = []
    full_kw = []
    def gen_for(k : int):
        stack.append(keywords[k])
        full_kw.append(" ".join(reversed(stack)))
        if (k > 0):
            for i in reversed(range(0, k)):
                gen_for(i)
        stack.pop()

    gen_for(len(keywords) - 1)
    return("-".join(full_kw))

if len(sys.argv) < 2:
    print("Input file path is required as the first argument.")
    sys.exit(1)
elif len(sys.argv) < 3:
    print("Output file path is required as the second argument.")
    sys.exit(1)
elif len(sys.argv) < 4:
    logger.warning("Supplying a brands.csv file as a third argument is highly recommended. Using plain extracted brands instead.")
    brands_file_path = None
else:
    brands_file_path = sys.argv[3]
    
logger.info(f"{sys.argv[0]} app started...")
html_file_path = sys.argv[1]
output_file_path = sys.argv[2]
all_brands = None
if brands_file_path is not None:
    all_brands = set()
    with open(brands_file_path, newline = "") as f:
        csv_r = csv.reader(f)
        header = next(csv_r)
        title_index = header.index("title")
        for row in csv_r:
            all_brands.add(normalize_text(row[title_index]))

# infile = open(html_file_path, newline = "")
# outfile = open(output_file_path, "w", newline = "")
# csv_r = csv.reader(infile)
# csv_w = csv.writer(outfile)
# csv_w.writerow(next(csv_r))
# for row in csv_r:
#     fixed = fix_brand(normalize_text(row[3]), all_brands)
#     if fixed is None:
#         print(f"Couldn't fix {row[3]}")
#     else:
#         row[3] = fixed
#     csv_w.writerow(row)
# infile.close()
# outfile.close()
# sys.exit(0)
    

logger.info("Loading files...")
## load the page or html file
with open(html_file_path) as f:
    html_doc = f.read()

## setup Beautiful Soup
logger.info("Parsing HTML page...")
soup = BeautifulSoup(html_doc, "html.parser")

    
logger.info("Processing data...")
## setup output file
try:
    csvfile = open(output_file_path, "w", newline = "")
    fields = ["shahrvand_id", "raw_title", "title", "brand", "orig_price", "current_price",
              "weight_g", "volume_ml", "image_file", "keywords"]
    csv_writer = csv.DictWriter(csvfile, fieldnames = fields, extrasaction = "ignore")
    csv_writer.writeheader()
except Exception as e:
    logger.error(e)
    sys.exit(1)

## actually parse html and save into csv
tags = soup("div", class_ = "product")
for tag in tags:
    shahrvand_id = get_id(tag)
    url_tag = tag.find("a", class_ = "title")
    raw_title = url_tag.string.strip()
    title = clean_title(raw_title)
    #logger.debug(title)
    current_price = clean_price(tag.find("div", class_ = "new_price"))
    orig_price = clean_price(tag.find("div", class_ = "old_price").span)
    if orig_price == "":
        orig_price = current_price
    brand = get_brand(raw_title, all_brands)        
    keywords = get_keywords(title, brand)
    full_keywords = augment_keywords(keywords)
    image_file = get_image_file_name(tag)
    row_dict = {"shahrvand_id": shahrvand_id, "raw_title": raw_title, "title": title,
                "brand": brand, "orig_price": orig_price, "current_price": current_price,
                "image_file": image_file, "keywords": full_keywords}
    desc = tag.find("div", class_ = "description")
    #product_attrs = {}
    for attr in desc("li"):
        spans = [s.string.strip() for s in attr.find_all("span") if s.string is not None]
        if len(spans) > 1:
            key = spans[0]
            value = spans[1]
            value = "|".join([s.strip() for s in value.split("|")])
            # if (key == "نوع :"):
            #     key = "type"            
            if (key == "وزن (گرم) :"):
                key = "weight_g"
            if (key == "حجم (میلی‌لیتر) :"):
                key = "volume_ml"
            # if (key == "کشور تولیدکننده :" or key == "کشور تولید کننده :" or key == "کشور سازنده :"):
            #     key = "made_in"
            # if (key == "طعم :"):
            #     key = "flavor"
            # if (key == "تعداد در بسته :" or key == "تعداد :"):
            #     key = "count"
            row_dict[key] = value
            
    #logger.debug("title = {} \t\t orig price = {} \t cur price = {}\t type = {}\t weight = {}".format(title, orig_price, cur_price, prod_type, weight))
    csv_writer.writerow(row_dict)
    #csv_writer.writerow([raw_title, title, brand, orig_price, cur_price, prod_type, weight])
    
csvfile.close()

logger.info("Done.")


