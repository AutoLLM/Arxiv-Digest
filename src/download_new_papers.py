# encoding: utf-8
import os
import re
from urllib.error import HTTPError

import tqdm
from bs4 import BeautifulSoup as bs
import urllib.request
import json
import datetime
import pytz

#Linh - add new def crawl_html_version(html_link) here
def crawl_html_version(html_link):
    main_content = []
    try:
        html = urllib.request.urlopen(html_link)
    except HTTPError as e:
        return ["None"]
    soup = bs(html)
    content = soup.find('div', attrs={'class': 'ltx_page_content'})
    para_list = content.find_all("div", attrs={'class': 'ltx_para'})

    for each in para_list:
        main_content.append(each.text.strip())
    return ' '.join(main_content)[:10000]
    #if len(main_content >)
    #return ''.join(main_content) if len(main_content) < 20000 else ''.join(main_content[:20000])

#Linh - add because cs sub does not have abstract displayed, will revert if it comes back
def crawl_abstract(html_link):
    main_content = []
    try:
        html = urllib.request.urlopen(html_link)
    except HTTPError as e:
        return ["None"]
    soup = bs(html)
    content = soup.find('blockquote', attrs={'class': 'abstract'}).text.replace("Abstract:", "").strip()
    return content
def _download_new_papers(field_abbr):
    NEW_SUB_URL = f'https://arxiv.org/list/{field_abbr}/recent'  # https://arxiv.org/list/cs/new
    print(NEW_SUB_URL)
    page = urllib.request.urlopen(NEW_SUB_URL)

    soup = bs(page)
    content = soup.body.find("div", {'id': 'content'})

    # find the first h3 element in content
    h3 = content.find("h3").text   # e.g: New submissions for Wed, 10 May 23
    date = h3.replace("New submissions for", "").strip()

    dt_list = content.dl.find_all("dt")
    dd_list = content.dl.find_all("dd")
    arxiv_base = "https://arxiv.org/abs/"
    arxiv_html = "https://arxiv.org/html/"

    assert len(dt_list) == len(dd_list)
    new_paper_list = []
    for i in tqdm.tqdm(range(len(dt_list))):
        paper = {}
        ahref = dt_list[i].find('a', href = re.compile(r'[/]([a-z]|[A-Z])\w+')).attrs['href']
        paper_number = ahref.strip().replace("/abs/", "")

        paper['main_page'] = arxiv_base + paper_number
        paper['pdf'] = arxiv_base.replace('abs', 'pdf') + paper_number

        paper['title'] = dd_list[i].find("div", {"class": "list-title mathjax"}).text.replace("Title:\n", "").strip()
        paper['authors'] = dd_list[i].find("div", {"class": "list-authors"}).text \
                            .replace("Authors:\n", "").replace("\n", "").strip()
        paper['subjects'] = dd_list[i].find("div", {"class": "list-subjects"}).text.replace("Subjects:\n", "").strip()
        #print(dd_list[i].find("div", {"class": "list-subjects"}).text.replace("Subjects:\n", "").strip())

        #TODO: edit the abstract part - it is currently moved

        #paper['abstract'] = dd_list[i].find("p", {"class": "mathjax"}).text.replace("\n", " ").strip()
        paper['abstract'] = crawl_abstract( arxiv_base + paper_number)
        paper['content'] = crawl_html_version(arxiv_html + paper_number + "v1")
        new_paper_list.append(paper)


    #  check if ./data exist, if not, create it
    if not os.path.exists("./data"):
        os.makedirs("./data")

    # save new_paper_list to a jsonl file, with each line as the element of a dictionary
    date = datetime.date.fromtimestamp(datetime.datetime.now(tz=pytz.timezone("America/New_York")).timestamp())
    date = date.strftime("%a, %d %b %y")
    with open(f"./data/{field_abbr}_{date}.jsonl", "w") as f:
        for paper in new_paper_list:
            f.write(json.dumps(paper) + "\n")


def get_papers(field_abbr, limit=None):
    date = datetime.date.fromtimestamp(datetime.datetime.now(tz=pytz.timezone("America/New_York")).timestamp())
    date = date.strftime("%a, %d %b %y")
    if not os.path.exists(f"./data/{field_abbr}_{date}.jsonl"):
        _download_new_papers(field_abbr)
    results = []
    with open(f"./data/{field_abbr}_{date}.jsonl", "r") as f:
        for i, line in enumerate(f.readlines()):
            if limit and i == limit:
                return results
            results.append(json.loads(line))
    return results

#crawl_html_version("https://arxiv.org/html/2404.11972v1")