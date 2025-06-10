from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import csv
import time

def crawl_sds_news(keyword, max_pages=1, output="naver_sds_news.csv"):
    options = webdriver.ChromeOptions()
    options.add_experimental_option("detach", True)  # 브라우저 꺼지지 않도록
    options.add_argument("--window-size=1200,900")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    base_url = "https://search.naver.com/search.naver?where=news&query={}&start={}&ds=2024.06.01&de=2025.06.04"
    results = []

    for page in range(max_pages):
        start = page * 10 + 1
        url = base_url.format(keyword, start)
        driver.get(url)
        time.sleep(2)

        try:
            cards = driver.find_elements(By.CSS_SELECTOR, "#main_pack div.group_news div.fender-news-item-list-tab > div.sds-comps-vertical-layout")

            print(f"[{page + 1}페이지] 뉴스 카드 {len(cards)}건 탐색됨")

            for card in cards:
                try:
                    # 제목 및 네이버 링크
                    title_link = card.find_element(By.CSS_SELECTOR, "div.HyuoyN_3xv7CrtOc6W9S a")
                    title = title_link.text.strip()
                    article_url = title_link.get_attribute("href")

                    # 언론사
                    press_span = card.find_element(By.CSS_SELECTOR, "div.sds-comps-profile-info-title span a span")
                    press = press_span.text.strip()

                    # 등록 시간
                    time_span = card.find_element(By.CSS_SELECTOR, "span.sds-comps-profile-info-subtext span")
                    published = time_span.text.strip()

                    results.append({
                        "title": title,
                        "naver_url": article_url,
                        "source": press,
                        "published": published
                    })
                except Exception as e:
                    print("❗ 카드 파싱 실패:", e)
                    continue

        except Exception as e:
            print("❗ 뉴스 리스트 파싱 실패:", e)
            break

    driver.quit()

    with open(output, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=["title", "naver_url", "source", "published"])
        writer.writeheader()
        writer.writerows(results)

    print(f"\n✅ 총 {len(results)}건 저장 완료 → {output}")

# 실행
if __name__ == "__main__":
    crawl_sds_news("출산", max_pages=2)