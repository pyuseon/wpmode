from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime, timedelta
import csv
import time

def crawl_sds_news_over_period(keyword, start_date_str, end_date_str):
    # 현재 시각 기반 파일명 생성
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    output_filename = f"naver_news_{keyword}_{timestamp}.csv"

    # 크롬 드라이버 설정
    options = webdriver.ChromeOptions()
    options.add_experimental_option("detach", True)
    options.add_argument("--window-size=1200,900")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    results = []

    # 날짜 범위 설정
    start_date = datetime.strptime(start_date_str, "%Y%m%d")
    end_date = datetime.strptime(end_date_str, "%Y%m%d")

    current = start_date
    while current <= end_date:
        date_str = current.strftime("%Y%m%d")
        print(f"\n📅 {date_str} 날짜 뉴스 수집 시작")
        # for page in range(max_pages_per_day):
        #     start = page * 10 + 1
        #     # URL 생성부 (ds/de → nso 파라미터로 교체)
        #
        #     url = (
        #         f"https://search.naver.com/search.naver?"
        #         f"where=news&query={keyword}&start={start}"
        #         f"&nso=so:r,p:from{date_str}to{date_str},a:all"
        #     )
        #     driver.get(url)
        #     time.sleep(2)

        page = 1
        while True:
            start = (page - 1) * 10 + 1
            url = (
                f"https://search.naver.com/search.naver?where=news&query={keyword}"
                f"&nso=so:r,p:from{date_str}to{date_str},a:all&start={start}"
            )
            driver.get(url)
            time.sleep(1.5)

            cards = driver.find_elements(By.CSS_SELECTOR,
                                         "#main_pack div.group_news div.fender-news-item-list-tab > div.sds-comps-vertical-layout")

            if not cards:
                print(f"  ⛔ 더 이상 뉴스 없음 (페이지 {page})")
                break

            print(f"  ✅ 페이지 {page} - 뉴스 {len(cards)}건")
            page += 1

            try:
                cards = driver.find_elements(By.CSS_SELECTOR, "#main_pack div.group_news div.fender-news-item-list-tab > div.sds-comps-vertical-layout")
                print(f"  - [{page + 1}페이지] 뉴스 카드 {len(cards)}건 탐색됨")

                for card in cards:
                    try:
                        # 제목
                        title_link = card.find_element(By.CSS_SELECTOR, "div.HyuoyN_3xv7CrtOc6W9S a")
                        title = title_link.text.strip()

                        # 네이버 뉴스 링크
                        naver_url = ""
                        try:
                            naver_link_tag = card.find_element(By.CSS_SELECTOR,
                                                               "span.sds-comps-profile-info-subtext a[href*='n.news.naver.com']")
                            naver_url = naver_link_tag.get_attribute("href")
                        except:
                            pass

                        # ✅ 언론사 원문 링크
                        original_url = ""
                        try:
                            original_link_tag = card.find_element(By.CSS_SELECTOR, "div.MO3Wlu3b2IM2fbhzxx5r a")
                            original_url = original_link_tag.get_attribute("href")
                        except:
                            pass

                        # 언론사명
                        press = card.find_element(By.CSS_SELECTOR,
                                                  "div.sds-comps-profile-info-title span a span").text.strip()

                        # 발행일
                        published = card.find_element(By.CSS_SELECTOR,
                                                      "span.sds-comps-profile-info-subtext span").text.strip()

                        results.append({
                            "title": title,
                            "naver_url": naver_url,
                            "original_url": original_url,
                            "source": press,
                            "published": published,
                            "related_to": "",
                            "related_original_url": ""
                        })
                        related_block = card.find_elements(By.CSS_SELECTOR, "div.JT4g6KsELnSY85CYAym9")
                        if related_block:
                            related_cards = related_block[0].find_elements(By.CSS_SELECTOR, "div.Eb67Vg8smoO6HeVy39Y9")

                            for related in related_cards:
                                try:
                                    # ✅ 제목 추출
                                    related_title = related.find_element(
                                        By.CSS_SELECTOR,
                                        "span.sds-comps-text.sds-comps-text-ellipsis-1.sds-comps-text-type-body2.XFo8_NV9Mn6G9z_wh_S9"
                                    ).text.strip()

                                    related_naver_url = ""
                                    related_original_url = ""
                                    try:
                                        related_naver_url = related.find_element(By.CSS_SELECTOR,
                                                                                 "a[href*='n.news.naver.com']").get_attribute(
                                            "href")
                                    except:
                                        pass
                                    try:
                                        related_original_url = related.find_element(By.CSS_SELECTOR,
                                                                                    "div.MO3Wlu3b2IM2fbhzxx5r a").get_attribute(
                                            "href")
                                    except:
                                        pass

                                    related_press = related.find_element(By.CSS_SELECTOR,"span.sds-comps-profile-info-title-text").text.strip()

                                    related_published = related.find_element(
                                        By.CSS_SELECTOR,
                                        "span.sds-comps-text.sds-comps-text-type-body2.sds-comps-text-weight-sm"
                                    ).text.strip()

                                    results.append({
                                        "title": related_title,
                                        "naver_url": related_naver_url,
                                        "original_url": related_original_url,
                                        "source": related_press,
                                        "published": related_published,
                                        "related_to": title,
                                        "related_original_url": original_url
                                    })
                                except Exception as e:
                                    print("    ❗ 관련 뉴스 파싱 실패:", e)
                                    continue

                    except Exception as e:
                        print("    ❗ 카드 파싱 실패:", e)
                        continue

            except Exception as e:
                print("    ❗ 뉴스 리스트 파싱 실패:", e)
                break

        current += timedelta(days=1)

    driver.quit()

    # CSV 저장
    with open(output_filename, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=["title", "naver_url","original_url", "source", "published", "related_to", "related_original_url"])
        writer.writeheader()
        writer.writerows(results)

    print(f"\n✅ 총 {len(results)}건 저장 완료 → {output_filename}")

# 실행
if __name__ == "__main__":
    crawl_sds_news_over_period("출산", "20240601","20240601")