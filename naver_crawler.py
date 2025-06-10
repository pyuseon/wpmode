import requests
from bs4 import BeautifulSoup
import csv
import time

import requests
from bs4 import BeautifulSoup
import csv
import time

def crawl_naver_news_precise(keyword, max_pages=3):
    base_url = "https://search.naver.com/search.naver"
    results = []

    for page in range(1, max_pages * 10, 10):  # 1, 11, 21...
        params = {
            "where": "news",
            "sm": "tab_jum",
            "query": keyword,
            "start": page
        }

        headers = {
            "User-Agent": "Mozilla/5.0"
        }

        resp = requests.get(base_url, params=params, headers=headers)
        soup = BeautifulSoup(resp.text, "html.parser")

        news_list = soup.select("div.group_news > ul.list_news > li")

        if not news_list:
            print("뉴스 항목이 없습니다. 구조가 변경되었을 수 있습니다.")
            break

        for li in news_list:
            title_tag = li.select_one("a.news_tit")
            press_tag = li.select_one("a.info.press")
            date_tag = li.select_one("div.info_group > span.info")

            results.append({
                "title": title_tag["title"] if title_tag else "",
                "naver_url": title_tag["href"] if title_tag else "",
                "press_url": press_tag["href"] if press_tag and press_tag.has_attr("href") else "",
                "source": press_tag.get_text(strip=True) if press_tag else "",
                "published": date_tag.get_text(strip=True) if date_tag else ""
            })

        time.sleep(1)

    return results

# div id="container" > div id="main_pack" > div class="group_news" > div class "sds-comps-vertical-layout sds-comps-full-layout fender-news-item-list-tab"