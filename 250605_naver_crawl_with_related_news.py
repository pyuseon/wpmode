from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime, timedelta
import csv
import time

def crawl_sds_news_over_period(keyword, start_date_str, end_date_str):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    output_filename = f"naver_news_{keyword}_{timestamp}.csv"

    options = webdriver.ChromeOptions()
    options.add_argument("--window-size=1200,900")
    options.add_experimental_option("detach", True)
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    results = []
    start_date = datetime.strptime(start_date_str, "%Y%m%d")
    end_date = datetime.strptime(end_date_str, "%Y%m%d")

    current = start_date
    while current <= end_date:
        date_str = current.strftime("%Y%m%d")
        print(f"\n📅 {date_str} 날짜 뉴스 수집 시작")
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

            if not cards or page > 3 :
                print(f"  ⛔ 더 이상 뉴스 없음 (페이지 {page})")
                break

            print(f"  ✅ 페이지 {page} - 뉴스 {len(cards)}건")
            page += 1

            for card in cards:
                try:
                    title = card.find_element(By.CSS_SELECTOR, "div.HyuoyN_3xv7CrtOc6W9S a").text.strip()
                    naver_url = ""
                    original_url = ""
                    try:
                        naver_url = card.find_element(By.CSS_SELECTOR, "a[href*='n.news.naver.com']").get_attribute("href")
                    except: pass
                    try:
                        original_url = card.find_element(By.CSS_SELECTOR, "div.MO3Wlu3b2IM2fbhzxx5r a").get_attribute("href")
                    except: pass
                    press = card.find_element(By.CSS_SELECTOR, "div.sds-comps-profile-info-title span a span").text.strip()
                    published = card.find_element(By.CSS_SELECTOR, "span.sds-comps-profile-info-subtext span").text.strip()

                    results.append({
                        "title": title,
                        "naver_url": naver_url,
                        "original_url": original_url,
                        "source": press,
                        "published": published,
                        "related_to": "",
                        "related_original_url": ""
                    })

                    # 🔁 관련 뉴스 더보기 (별도 페이지) 우선 확인
                    has_expansion = False
                    try:
                        expansion_block = card.find_element(By.CSS_SELECTOR, "div.smft2gmdyMSZNXp7mPCu")
                        base_expansion_link = expansion_block.find_element(By.CSS_SELECTOR, "a").get_attribute("href")
                        has_expansion = True

                        start = 1
                        while True:
                            paginated_link = f"{base_expansion_link}&start={start}"

                            driver.execute_script("window.open('');")
                            driver.switch_to.window(driver.window_handles[1])
                            driver.get(paginated_link)
                            time.sleep(5)

                            try:
                                expanded_section = driver.find_element(By.CSS_SELECTOR,
                                                                       "div.gSjvQ1lhW6CA0uVcUdvz.desktop_mode.api_subject_bx")
                                expanded_cards = expanded_section.find_elements(By.CSS_SELECTOR,
                                                                                "div.sds-comps-vertical-layout.sds-comps-full-layout.UC1lc0LnKWszTX7CYO7K")

                                # 결과 없으면 종료
                                if not expanded_cards or len(expanded_cards) == 1:
                                    driver.close()
                                    driver.switch_to.window(driver.window_handles[0])
                                    break

                                for i, related in enumerate(expanded_cards):
                                    if i == 0:
                                        continue
                                    try:
                                        related_title = related.find_element(By.CSS_SELECTOR,
                                                                             "span.sds-comps-text-type-headline1").text.strip()
                                        related_naver_url = ""
                                        related_original_url = ""
                                        try:
                                            for a in related.find_elements(By.CSS_SELECTOR, "a"):
                                                href = a.get_attribute("href")
                                                if "n.news.naver.com" in href:
                                                    related_naver_url = href
                                                else:
                                                    related_original_url = href
                                        except:
                                            pass
                                        related_press = related.find_element(By.CSS_SELECTOR,
                                                                             "span.sds-comps-profile-info-title-text").text.strip()
                                        related_published = related.find_element(By.CSS_SELECTOR,
                                                                                 "span.sds-comps-text-weight-sm").text.strip()

                                        results.append({
                                            "title": related_title,
                                            "naver_url": related_naver_url,
                                            "original_url": related_original_url,
                                            "source": related_press,
                                            "published": related_published,
                                            "related_to": title,
                                            "related_original_url": original_url
                                        })
                                    except:
                                        continue
                                driver.close()
                                driver.switch_to.window(driver.window_handles[0])
                                start += 10
                            except:
                                driver.close()
                                driver.switch_to.window(driver.window_handles[0])
                                break

                        driver.close()
                        driver.switch_to.window(driver.window_handles[0])
                    except:
                        pass

                    # 🔁 관련 뉴스 내부 수집 (확장 링크가 없을 때만)
                    if not has_expansion:
                        related_block = card.find_elements(By.CSS_SELECTOR, "div.JT4g6KsELnSY85CYAym9")
                        if related_block:
                            related_cards = related_block[0].find_elements(By.CSS_SELECTOR, "div.Eb67Vg8smoO6HeVy39Y9")
                            for related in related_cards:
                                try:
                                    related_title = related.find_element(By.CSS_SELECTOR, "span.XFo8_NV9Mn6G9z_wh_S9").text.strip()
                                    related_naver_url = ""
                                    related_original_url = ""
                                    try:
                                        for a in related.find_elements(By.CSS_SELECTOR, "a"):
                                            href = a.get_attribute("href")
                                            if "n.news.naver.com" in href:
                                                related_naver_url = href
                                            else:
                                                related_original_url = href
                                    except: pass
                                    related_press = related.find_element(By.CSS_SELECTOR, "span.sds-comps-profile-info-title-text").text.strip()
                                    related_published = related.find_element(By.CSS_SELECTOR, "span.sds-comps-text-weight-sm").text.strip()

                                    results.append({
                                        "title": related_title,
                                        "naver_url": related_naver_url,
                                        "original_url": related_original_url,
                                        "source": related_press,
                                        "published": related_published,
                                        "related_to": title,
                                        "related_original_url": original_url
                                    })
                                except: continue

                except Exception as e:
                    print("  ❗ 대표 뉴스 파싱 실패:", e)
                    continue


        current += timedelta(days=1)

    driver.quit()

    with open(output_filename, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "title", "naver_url", "original_url", "source", "published",
            "related_to", "related_original_url"
        ])
        writer.writeheader()
        writer.writerows(results)

    print(f"\n✅ 총 {len(results)}건 저장 완료 → {output_filename}")

if __name__ == "__main__":
    crawl_sds_news_over_period("출산", "20240601", "20240601")
