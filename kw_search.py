import csv
import os
from bs4 import BeautifulSoup
from lxml import html
from slugify import slugify
from pathlib import Path
from playwright.sync_api import sync_playwright
import openpyxl
from lxml import etree
from dotenv import load_dotenv


def sanitize_html():
    invalid_tags = ["h1", "h2"]
    value = page.content()
    soup = BeautifulSoup(value)

    for tag in soup.findAll(True):
        if tag.name in invalid_tags:
            tag.hidden = True
    return soup.find("body").text.replace("\n", "")


def hundredwords(kw):
    try:
        result = sanitize_html()
        firsthundredwords = ' '.join(result.split()[
                                     :100])
        if kw.lower() in firsthundredwords.lower():
            return True
        return False
    except:
        return False


def prelog(xpath):
    try:
        page.locator(xpath).first.inner_html(timeout=5000)
        return True
    except:
        return False


def tagsearch(kw, tag, index=0):
    if index:
        try:
            page.locator(
                f"//{tag}[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{kw.lower()}')].nth({index})").inner_text(
                timeout=5000)
            return True
        except:
            return False
    try:
        page.locator(
            f"//{tag}[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{kw.lower()}')]").inner_text(
            timeout=5000)
        return True
    except:
        return False


def searchdescription(kw):
    try:
        description = page.locator("//meta[@name='description']").inner_text(timeout=5000)
        if kw.lower() in description.lower():
            return True
        return False
    except:
        return False


def readexcel():
    wb_obj = openpyxl.load_workbook(input_file_path)
    sheet_obj = wb_obj.active
    count = 0
    for row in sheet_obj.iter_rows():
        if count == 0:
            count += 1
            continue
        try:
            page.goto(row[0].value)
        except Exception as e:
            if 'ERR_CONNECTION_TIMED_OUT' in e.args[0]:
                option = input(
                    f"Current URL {row[0].value} is not working, It seems Website is not working. Do you want to continue with next URL or you want to quit? Y/N")
                if option.lower() == 'y':
                    print("User Selected to continue. So, Moving to next URL")
                    continue
                else:
                    print("User Selected to quit. So, Quiting...")
                    return

        result = html.fromstring(page.content())

        slugflag = False

        h1flag = tagsearch(row[1].value, "h1")
        h2flag = tagsearch(row[1].value, "h2")
        firsthundredflag = hundredwords(row[1].value)
        if slugify(row[1].value) in row[0].value:
            slugflag = True
        pflag = tagsearch(row[1].value, "p", -1)
        titleflag = tagsearch(row[1].value, "title")
        descriptionflag = searchdescription(row[1].value)
        preloadflag = prelog("//link[contains(@rel, 'preload')]")
        prefetchflag = prelog("//link[contains(@rel, 'prefetch')]")
        preconnectflag = prelog("//link[contains(@rel, 'preconnect')]")
        data = [row[0].value, row[1].value, h1flag, h2flag, firsthundredflag, slugflag, pflag, titleflag,
                descriptionflag, preloadflag, prefetchflag,
                preconnectflag]
        print(data)
        with open("output.csv", mode="a+", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(data)


if __name__ == "__main__":
    headers = ["URL", "Keyword", "H1", "H2", "First 100 Words", "Slug", "Last Paragraph", "Title Tag",
               "Meta Description", "Preload", "Prefetch", "Preconnect"]
    with open("output.csv", mode="a+", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(headers)

    firsthundredflag = False
    BASE_DIR = Path(__file__).resolve().parent
    load_dotenv(BASE_DIR / "vars.txt")
    input_file_path = os.environ['input_file']
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        readexcel()
