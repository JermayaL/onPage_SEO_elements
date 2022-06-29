import csv
import os
import re
from bs4 import BeautifulSoup
from lxml import html
from slugify import slugify
from pathlib import Path
from playwright.sync_api import sync_playwright
import openpyxl
from dotenv import load_dotenv


def remove_headers_footers():
    invalid_tags = ["header", "footer"]
    value = page.content()
    soup = BeautifulSoup(value, features="lxml")

    for tag in invalid_tags:
        soup.find(tag).decompose()
    return soup


def sanitize_html(soup):
    invalid_tags = ["h1", "h2"]
    for tag in invalid_tags:
        soup.find(tag).decompose()
    regex = re.compile(".*breadcrumbs*")
    try:
        soup.find('div', {"class": regex}).decompose()
    except:
        print("Unable to locate breadcrumbs")
    return soup.find("body").text.replace("\n", "")


def hundredwords(kw, soup):
    try:
        kw = kw.lower().split()
        result = sanitize_html(soup)
        firsthundredwords = ' '.join(result.lower().split()[:100]).split('.')
        for sentence in firsthundredwords:
            for sub_kw in kw:
                if not re.search(rf"\b{sub_kw}\b", sentence, re.IGNORECASE):
                    return False
            return True
        else:
            return False
    except:
        return False


def prelog(xpath):
    try:
        page.locator(xpath).first.inner_html(timeout=5000)
        return True
    except:
        return False


def get_len_or_content(data, content=False, length=0):
    if not content:
        return len(data.split())
    data = data.lower().split()
    if len(data) > length:
        return data[-length:]
    return set(data)


def paragraph_search(kw, page):
    paragraph_content = ''
    try:
        for paragraph in page.xpath("//p"):
            para = paragraph.xpath('.')[0].text_content()
            if len(para) > paragraph_min_length:
                paragraph_content += para
        if paragraph_content:
            text = get_len_or_content(paragraph_content, True, 100).split('.')
            keywords_list = kw.lower().split()
            for sentence in text:
                for sub_kw in keywords_list:
                    if not re.search(rf"\b{sub_kw}\b", sentence, re.IGNORECASE):
                        return False
            return True
        else:
            return False
    except:
        return False


def check_keyword(kw, node):
    kw = set(kw.lower().split())

    text = node.text_content().lower().split('.')
    for sentence in text:
        for sub_kw in kw:
            if not re.search(rf"\b{sub_kw}\b", sentence, re.IGNORECASE):
                return False
        return True


def tagsearch(kw, tag, page):
    for t in page.xpath(f"//{tag}"):
        tagflag = check_keyword(kw, t)
        if tagflag:
            return True
    else:
        return False


def searchdescription(kw):
    try:
        kw = set(kw.lower().split())
        description = page.locator("//meta[@name='description']").inner_text(timeout=5000)
        for sentence in description:
            for sub_kw in kw:
                if not re.search(rf"\b{sub_kw}\b", sentence, re.IGNORECASE):
                    return False
        return True
    except:
        return False


def imagecheck():
    page.evaluate("""
           let nodes = document.querySelectorAll('img');
            for (let i = 0; i < nodes.length; i++) {
                let node = nodes[i]
                let alt = node.getAttribute('alt');
                let source = node.getAttribute('src')
                if ((alt && alt.toLowerCase().includes('logo'))
                    || (source && source.includes('logo'))
                    || !(node.offsetWidth || node.offsetHeight || node.getClientRects().length)) {
                    node.remove();
                }
            
            }
           """)
    if page.query_selector("img") is not None:
        return True
    return False


def lazyloading():
    try:
        page.locator("//img[@loading='lazy']").first.inner_text(timeout=5000)
        return True
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
            page.goto(row[0].value, wait_until="networkidle", timeout=60000)

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
            else:
                print("Unable to load URL, waited for 60 seconds. Now skipping...")
                continue
        soup = remove_headers_footers()

        page_content = html.fromstring(soup.prettify())
        page_text = page_content.xpath("//body")[0].text_content().strip()
        total_words = get_len_or_content(page_text)
        imgflag = imagecheck()
        titleflag = tagsearch(row[1].value, "title", page_content)
        keyword_density = str(round(page_text.lower().count(row[1].value.lower()) / total_words * 100, 2)) + "%"
        keywordone_density = str(
            round(page_text.lower().count(row[1].value.split()[0].lower()) / total_words * 100, 2)) + "%"
        keywordtwo_density = str(
            round(page_text.lower().count(row[1].value.split()[1].lower()) / total_words * 100, 2)) + "%"
        firsthundredflag = hundredwords(row[1].value, soup)
        h1flag = tagsearch(row[1].value, "h1", page_content)
        h2flag = tagsearch(row[1].value, "h2", page_content)
        paragraphflag = paragraph_search(row[1].value, page_content)
        slugflag = False

        if slugify(row[1].value) in row[0].value:
            slugflag = True

        descriptionflag = searchdescription(row[1].value)
        preloadflag = prelog("//link[contains(@rel, 'preload')]")
        prefetchflag = prelog("//link[contains(@rel, 'prefetch')]")
        preconnectflag = prelog("//link[contains(@rel, 'preconnect')]")

        lazyloadingflag = lazyloading()

        data = [row[0].value, row[1].value, h1flag, h2flag, firsthundredflag, slugflag, paragraphflag, titleflag,
                descriptionflag, preloadflag, prefetchflag,
                preconnectflag, imgflag, lazyloadingflag, keyword_density, keywordone_density, keywordtwo_density]
        print(data)
        with open("output.csv", mode="a+", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(data)


if __name__ == "__main__":
    headers = ["URL", "Keyword", "H1", "H2", "First 100 Words", "Slug", "Last Paragraph", "Title Tag",
               "Meta Description", "Preload", "Prefetch", "Preconnect", "Image", "Lazy Loading", "Keyword Density",
               "Keyword1 Density", "Keyword2 Density"]
    with open("output.csv", mode="a+", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(headers)

    firsthundredflag = False
    BASE_DIR = Path(__file__).resolve().parent
    load_dotenv(BASE_DIR / "vars.txt")
    input_file_path = os.environ['input_file']
    paragraph_min_length = int(os.environ['paragraph_length'])
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        readexcel()
