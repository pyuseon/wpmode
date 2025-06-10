from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime, timedelta
import csv
import time
import re


def debug_page_elements(driver, wait_time=3):
    """페이지의 모든 가능한 뉴스 요소들을 찾아서 출력하는 디버그 함수"""
    time.sleep(wait_time)

    print("\n=== 🔍 페이지 디버깅 시작 ===")

    # 1. 전체 페이지 구조 확인
    try:
        main_pack = driver.find_element(By.CSS_SELECTOR, "#main_pack")
        print("✅ #main_pack 존재")
    except:
        print("❌ #main_pack 없음")

    # 2. 뉴스 관련 div들 모두 찾기
    possible_selectors = [
        "div[class*='news']",
        "div[class*='group']",
        "div[class*='api']",
        "div[class*='subject']",
        "div[class*='area']",
        "div[class*='wrap']",
        "div[class*='item']",
        "div[class*='card']",
        "div[class*='list']",
        "div[class*='vertical']",
        "div[class*='horizontal']"
    ]

    for selector in possible_selectors:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            if elements:
                print(f"📦 {selector}: {len(elements)}개 발견")
                # 첫 번째 요소의 클래스명 출력
                if elements[0].get_attribute("class"):
                    print(f"    클래스: {elements[0].get_attribute('class')}")
        except:
            continue

    # 3. 링크 요소들 찾기
    print("\n=== 📎 링크 요소 분석 ===")
    link_selectors = [
        "a[href*='news.naver.com']",
        "a[href*='n.news.naver.com']",
        "a[class*='news']",
        "a[class*='tit']",
        "a[class*='title']",
        "a[class*='headline']"
    ]

    for selector in link_selectors:
        try:
            links = driver.find_elements(By.CSS_SELECTOR, selector)
            if links:
                print(f"🔗 {selector}: {len(links)}개")
                if links[0].text.strip():
                    print(f"    첫 번째 텍스트: {links[0].text.strip()[:50]}...")
        except:
            continue

    # 4. 모든 a 태그의 클래스명 수집
    print("\n=== 🏷️ 모든 링크 클래스명 분석 ===")
    all_links = driver.find_elements(By.TAG_NAME, "a")
    class_names = set()
    for link in all_links[:20]:  # 처음 20개만
        if link.get_attribute("class"):
            class_names.add(link.get_attribute("class"))
            if link.text.strip() and len(link.text.strip()) > 10:
                print(f"📰 클래스: {link.get_attribute('class')}")
                print(f"    텍스트: {link.text.strip()[:80]}...")
                print(f"    href: {link.get_attribute('href')[:80] if link.get_attribute('href') else 'None'}...")
                print("---")

    print(f"\n총 {len(all_links)}개의 링크 발견")
    return True


def find_elements_intelligently(driver, base_element=None):
    """지능적으로 뉴스 요소들을 찾는 함수"""
    search_base = base_element if base_element else driver

    # 1단계: 뉴스 컨테이너를 찾기 위한 패턴들
    container_patterns = [
        # 최신 컨테이너 패턴들
        "div.sds-comps-vertical-layout.sds-comps-full-layout.fender-news-item-list-tab"
        "div.fender-news-item-list-tab",
        "div[class*='fender-news-item-list']",
        # "div[class*='news-item-list']",
        # "div.group_news",
        # "div[class*='api_subject']",
        # "#main_pack"
    ]

    container = None
    for pattern in container_patterns:
        try:
            found_container = search_base.find_element(By.CSS_SELECTOR, pattern)
            if found_container:
                container = found_container
                print(f"🎯 뉴스 컨테이너 발견: {pattern}")
                break
        except:
            continue

    if not container:
        print("❌ 뉴스 컨테이너를 찾을 수 없습니다!")
        return []

        # 2단계: 컨테이너 안에서 개별 뉴스 카드들 찾기
    card_patterns = [
        # 정확한 개별 카드 패턴 (2024년 6월)
        "div.sds-comps-vertical-layout.sds-comps-full-layout._4zQ0QZWfn7bqZ_ul5OV",
        "div[class*='sds-comps-vertical-layout'][class*='sds-comps-full-layout'][class*='_4zQ0QZWfn7bqZ_ul5OV']",
        "div[class*='_4zQ0QZWfn7bqZ_ul5OV']",  # 고유 클래스로 찾기

        # 좀 더 일반적인 패턴들 (백업용)
        "div.sds-comps-vertical-layout.sds-comps-full-layout:not(.fender-news-item-list-tab)",
        "div[class*='sds-comps-vertical-layout'][class*='full-layout']:not([class*='fender'])",
        "div[class*='vertical-layout']:not([class*='fender']):not([class*='tab'])",
    ]

    found_cards = []
    for pattern in card_patterns:
        try:
            elements = container.find_elements(By.CSS_SELECTOR, pattern)
            if elements and len(elements) > 1:  # 여러 개의 카드가 있어야 함
                print(f"🎯 개별 뉴스 카드 패턴 '{pattern}'로 {len(elements)}개 발견")
                found_cards = elements
                break
            elif elements and len(elements) == 1:
                print(f"⚠️ 패턴 '{pattern}'로 1개만 발견 - 다음 패턴 시도")
        except Exception as e:
            print(f"❌ 패턴 '{pattern}' 시도 실패: {e}")
            continue

    # 3단계: 여전히 찾지 못했다면 더 포괄적으로 찾기
    if not found_cards:
        print("🔍 포괄적 검색 시작...")
        try:
            # 컨테이너의 모든 직접 자식들 중에서 텍스트가 있는 것들 찾기
            all_children = container.find_elements(By.XPATH, "./*")
            potential_cards = []

            for child in all_children:
                # 텍스트 길이가 충분하고 링크가 있는 요소들만 선택
                if child.text.strip() and len(child.text.strip()) > 10:
                    links = child.find_elements(By.CSS_SELECTOR, "a")
                    if links:  # 링크가 있으면 뉴스 카드일 가능성이 높음
                        potential_cards.append(child)

            if potential_cards:
                print(f"🎯 포괄적 검색으로 {len(potential_cards)}개 카드 발견")
                found_cards = potential_cards
        except Exception as e:
            print(f"❌ 포괄적 검색 실패: {e}")

    return found_cards




def find_news_cards_in_container(container):


        # 2단계: 컨테이너 안에서 개별 뉴스 카드들 찾기
    card_patterns = [
        # 정확한 개별 카드 패턴 (2024년 6월)
        "div.sds-comps-vertical-layout.sds-comps-full-layout._4zQ0QZWfn7bqZ_ul5OV",
        "div[class*='sds-comps-vertical-layout'][class*='sds-comps-full-layout'][class*='_4zQ0QZWfn7bqZ_ul5OV']",
        "div[class*='_4zQ0QZWfn7bqZ_ul5OV']",  # 고유 클래스로 찾기

        # 좀 더 일반적인 패턴들 (백업용)
        "div.sds-comps-vertical-layout.sds-comps-full-layout:not(.fender-news-item-list-tab)",
        "div[class*='sds-comps-vertical-layout'][class*='full-layout']:not([class*='fender'])",
        "div[class*='vertical-layout']:not([class*='fender']):not([class*='tab'])",
    ]

    found_cards = []
    for pattern in card_patterns:
        try:
            elements = container.find_elements(By.CSS_SELECTOR, pattern)
            if elements and len(elements) > 1:  # 여러 개의 카드가 있어야 함
                print(f"🎯 개별 뉴스 카드 패턴 '{pattern}'로 {len(elements)}개 발견")
                found_cards = elements
                break
            elif elements and len(elements) == 1:
                print(f"⚠️ 패턴 '{pattern}'로 1개만 발견 - 다음 패턴 시도")
        except Exception as e:
            print(f"❌ 패턴 '{pattern}' 시도 실패: {e}")
            continue

    # 3단계: 여전히 찾지 못했다면 더 포괄적으로 찾기
    if not found_cards:
        print("🔍 포괄적 검색 시작...")
        try:
            # 컨테이너의 모든 직접 자식들 중에서 텍스트가 있는 것들 찾기
            all_children = container.find_elements(By.XPATH, "./*")
            potential_cards = []

            for child in all_children:
                # 텍스트 길이가 충분하고 링크가 있는 요소들만 선택
                if child.text.strip() and len(child.text.strip()) > 10:
                    links = child.find_elements(By.CSS_SELECTOR, "a")
                    if links:  # 링크가 있으면 뉴스 카드일 가능성이 높음
                        potential_cards.append(child)

            if potential_cards:
                print(f"🎯 포괄적 검색으로 {len(potential_cards)}개 카드 발견")
                found_cards = potential_cards
        except Exception as e:
            print(f"❌ 포괄적 검색 실패: {e}")

    return found_cards


def extract_title_intelligently(card):
    """지능적으로 제목을 추출하는 함수"""
    title_patterns = [
        # 정확한 최신 패턴 (2024년 6월)
        "span.sds-comps-text.sds-comps-text-ellipsis.sds-comps-text-ellipsis-1.sds-comps-text-type-headline1",
        "span[class*='sds-comps-text-type-headline1']",
        "span[class*='sds-comps-text'][class*='headline1']",
    ]

    for pattern in title_patterns:
        try:
            elements = card.find_elements(By.CSS_SELECTOR, pattern)
            for element in elements:
                text = element.text.strip()
                if text and len(text) > 5:  # 최소 5글자 이상
                    print(f"    📰 제목 발견 (패턴: {pattern}): {text[:50]}...")
                    return text
        except:
            continue

    return ""


def find_expansion_link_from_spans(card):
    """카드에서 더보기 링크를 찾는 함수"""
    expansion_patterns = [
        "span.sds-comps-text.sds-comps-text-type-body2.sds-comps-text-weight-sm",
        "span[class*='sds-comps-text-type-body2'][class*='sds-comps-text-weight-sm']",
        "span[class*='sds-comps-text'][class*='body2'][class*='weight-sm']",
        "span.sds-comps-text-type-body2",
        "span.sds-comps-text-weight-sm",
    ]

    for pattern in expansion_patterns:
        try:
            span_elements = card.find_elements(By.CSS_SELECTOR, pattern)

            for i, span_elem in enumerate(span_elements):
                text = span_elem.text.strip() if span_elem.text else ""


                # 텍스트 조건 확인
                if "관련뉴스" in text and "전체보기" in text:
                    try:
                        # 부모 요소들을 확인해서 a 태그 찾기
                        parent = span_elem.find_element(By.XPATH, "..")
                        while parent and parent.tag_name.lower() != 'a':
                            parent = parent.find_element(By.XPATH, "..")

                        if parent and parent.tag_name.lower() == 'a':
                            href = parent.get_attribute("href")
                            if href:
                                print(f"      🎯 더보기 링크 발견!")
                                return href
                    except:
                        continue

        except Exception as e:
            continue

    print("      ⚠️ 더보기 링크를 찾을 수 없음")
    return ""


def process_related_news(driver, card, main_title, main_original_url, results):
    """관련 뉴스를 처리하는 함수 (더보기 페이지 + 내부 관련뉴스)"""
    related_added = 0

    expansion_link = find_expansion_link_from_spans(card)

    if not expansion_link:
        print("      ⚠️ 더보기 링크를 찾을 수 없음")

    # 2. 더보기 페이지가 있으면 처리
    if expansion_link:
        try:
            print(f"      📄 더보기 페이지 크롤링 시작...")
            related_added += crawl_expansion_page(driver, expansion_link, main_title, main_original_url, results)
        except Exception as e:
            print(f"      ❌ 더보기 페이지 처리 실패: {e}")

    # 3. 내부 관련 뉴스 처리 (더보기가 없거나 실패한 경우)
    if not expansion_link or related_added == 0:
        try:
            print(f"      📰 내부 관련뉴스 탐지 중...")
            related_added += crawl_internal_related_news(card, main_title, main_original_url, results)
        except Exception as e:
            print(f"      ❌ 내부 관련뉴스 처리 실패: {e}")

    return related_added


def find_original_link(card):
    """오리지널 뉴스 링크를 찾는 함수 - media.naver.com 제외"""

    # 방법 1: nocr='1' 속성을 가진 모든 링크 찾기
    try:
        links = card.find_elements(By.CSS_SELECTOR, "a[nocr='1']")
        print(f"      🔍 nocr='1' 링크 {len(links)}개 발견")

        for i, link in enumerate(links):
            href = link.get_attribute("href")
            text = link.text.strip() if link.text else ""
            print(f"         [{i + 1}] URL: {href}")

            # media.naver.com 제외하고 유효한 링크 체크
            if href and href.startswith('http') and "media.naver.com" not in href:
                print(f"      🎯 오리지널 링크 선택: {href}")
                return href
            elif href and "media.naver.com" in href:
                print(f"         [{i + 1}] ❌ media.naver.com 링크 제외")

    except Exception as e:
        print(f"      ❌ nocr='1' 링크 찾기 실패: {e}")

    # 방법 2: sds-comps-vertical-layout 컨테이너 안의 링크
    try:
        containers = card.find_elements(By.CSS_SELECTOR, "div[class*='sds-comps-vertical-layout']")
        print(f"      🔍 vertical-layout 컨테이너 {len(containers)}개 발견")

        for container in containers:
            links = container.find_elements(By.CSS_SELECTOR, "a[href]")
            for link in links:
                href = link.get_attribute("href")
                if href and href.startswith('http') and "media.naver.com" not in href:
                    print(f"      🎯 컨테이너에서 링크 발견: {href}")
                    return href

    except Exception as e:
        print(f"      ❌ 컨테이너 링크 찾기 실패: {e}")

    # 방법 3: 카드 내 모든 링크 중에서 선택
    try:
        all_links = card.find_elements(By.CSS_SELECTOR, "a[href]")
        print(f"      🔍 전체 링크 {len(all_links)}개 발견")

        exclude_patterns = ['search', 'cluster', 'google', 'media.naver.com']
        valid_links = []

        for link in all_links:
            href = link.get_attribute("href")
            if href and href.startswith('http'):
                is_excluded = any(pattern in href for pattern in exclude_patterns)
                if not is_excluded:
                    valid_links.append(href)
                else:
                    print(f"         ❌ 제외된 링크: {href}")

        if valid_links:
            print(f"      🎯 유효한 링크 선택: {valid_links[0]}")
            return valid_links[0]

    except Exception as e:
        print(f"      ❌ 전체 링크 찾기 실패: {e}")

    print("      ⚠️ 오리지널 링크를 찾을 수 없음")
    return ""



def crawl_expansion_page(driver, expansion_link, main_title, main_original_url, results):
    """더보기 페이지를 크롤링하는 함수"""
    added_count = 0
    original_window = driver.current_window_handle

    try:
        # 새 탭 열기
        driver.execute_script("window.open('');")
        driver.switch_to.window(driver.window_handles[1])

        start_page = 1
        max_pages = 5  # 최대 5페이지까지만

        while start_page <= max_pages * 10:
            paginated_url = f"{expansion_link}&start={start_page}"
            driver.get(paginated_url)
            time.sleep(2)

            # 확장 페이지의 뉴스 컨테이너 찾기
            container_patterns = [
                "div.sds-comps-vertical-layout.sds-comps-full-layout.fender-news-item-list-tab",
                "div.fender-news-item-list-tab",
                "div[class*='fender-news-item-list']",
                "div[class*='news-item-list']",
            ]

            container = None
            for pattern in container_patterns:
                try:
                    container = driver.find_element(By.CSS_SELECTOR, pattern)
                    break
                except:
                    continue

            if not container:
                print(f"        ❌ 확장 페이지 컨테이너 없음")
                break

            # 확장 페이지의 뉴스 카드들 찾기
            expanded_cards = find_news_cards_in_container(container)

            if not expanded_cards or len(expanded_cards) <= 1:
                print(f"        ⛔ 더 이상 관련뉴스 없음 (페이지 {start_page // 10 + 1})")
                break

            page_added = 0
            for i, related_card in enumerate(expanded_cards):
                if i == 0 and page_added == 0:  # 첫 번째는 원본 뉴스이므로 스킵
                    continue

                try:
                    # 관련 뉴스 제목 추출
                    related_title = extract_title_intelligently(related_card)
                    if not related_title :
                        continue

                    # URL 추출
                    related_naver_url = get_naver_url(related_card)
                    related_original_url = get_original_url(related_card)


                    print(f"        네이버 URL: {related_naver_url}")
                    print(f"        원본 URL: {related_original_url}")

                    # 언론사 추출
                    related_press = ""
                    press_patterns = [
                        "span[class*='profile'][class*='title']",
                        "span[class*='press']",
                        "span[class*='info']"
                    ]
                    for pattern in press_patterns:
                        try:
                            press_elem = related_card.find_element(By.CSS_SELECTOR, pattern)
                            related_press = press_elem.text.strip()
                            if related_press:
                                break
                        except:
                            continue

                    # 발행일 추출
                    related_published = ""
                    date_patterns = [
                        "span[class*='weight-sm']",
                        "span[class*='date']",
                        "span[class*='time']"
                    ]
                    for pattern in date_patterns:
                        try:
                            date_elem = related_card.find_element(By.CSS_SELECTOR, pattern)
                            text = date_elem.text.strip()
                            if any(x in text for x in ['시간', '분', '일', '월', '년', ':']):
                                related_published = text
                                break
                        except:
                            continue

                    # 결과에 추가
                    results.append({
                        "title": related_title,
                        "naver_url": related_naver_url,
                        "original_url": related_original_url,
                        "source": related_press,
                        "published": related_published,
                        "related_to": main_title,
                        "related_original_url": main_original_url
                    })

                    added_count += 1
                    page_added += 1
                    print(f"        ✅ 관련뉴스 추가: {related_title[:30]}...")

                except Exception as e:
                    print(f"        ❌ 관련뉴스 추출 실패: {e}")
                    continue

            print(f"        📄 페이지 {start_page // 10 + 1}: {page_added}건 추가")

            if page_added == 0:  # 이 페이지에서 아무것도 추출하지 못했으면 종료
                break

            start_page += 10

    except Exception as e:
        print(f"        ❌ 확장 페이지 처리 실패: {e}")

    finally:
        # 원래 탭으로 돌아가기
        try:
            driver.close()  # 현재 탭 닫기
            driver.switch_to.window(original_window)  # 원래 탭으로
        except:
            pass

    return added_count


def crawl_internal_related_news(card, main_title, main_original_url, results):
    """카드 내부의 관련 뉴스를 크롤링하는 함수"""
    added_count = 0

    # 내부 관련뉴스 컨테이너 찾기
    related_container_patterns = [
        "div.sds-comps-vertical-layout.sds-comps-full-layout",  # 새로운 패턴
        "div[class*='sds-comps-vertical-layout'][class*='sds-comps-full-layout']",
        "div[class*='sds-comps-vertical-layout']",
        "div[class*='sds-comps-full-layout']",
    ]

    related_container = None
    for pattern in related_container_patterns:
        try:
            related_container = card.find_element(By.CSS_SELECTOR, pattern)
            print(f"        🎯 내부 관련뉴스 컨테이너 발견: {pattern}")
            break
        except:
            continue

    if not related_container:
        print(f"        ❌ 내부 관련뉴스 컨테이너 없음")
        return 0

    # 관련뉴스 아이템들 찾기
    related_item_patterns = [
        "div.sds-comps-base-layout.sds-comps-full-layout",  # 새로운 패턴
        "div[class*='sds-comps-base-layout'][class*='sds-comps-full-layout']",
        "div[class*='sds-comps-base-layout']",
        "div[class*='sds-comps-full-layout']",
    ]

    related_items = []
    for pattern in related_item_patterns:
        try:
            items = related_container.find_elements(By.CSS_SELECTOR, pattern)
            if items:
                related_items = items
                print(f"        🎯 관련뉴스 아이템 {len(items)}개 발견: {pattern}")
                break
        except:
            continue

    if not related_items:
        print(f"        ❌ 관련뉴스 아이템 없음")
        return 0

    # 각 관련뉴스 아이템 처리
    for item in related_items[:10]:  # 최대 5개까지
        try:
            # 제목 추출
            related_title = ""
            title_patterns = [
                "span.sds-comps-text.sds-comps-text-ellipsis.sds-comps-text-ellipsis-1.sds-comps-text-type-body2",
                # 새로운 패턴
                "span[class*='sds-comps-text-type-body2'][class*='sds-comps-text-ellipsis']",
                "span[class*='sds-comps-text'][class*='body2'][class*='ellipsis']",
                "span.sds-comps-text-type-body2",
                "span[class*='sds-comps-text-type-body2']"
            ]

            for pattern in title_patterns:
                try:
                    title_elem = item.find_element(By.CSS_SELECTOR, pattern)
                    text = title_elem.text.strip()
                    if text and len(text) > 5 and text != main_title:
                        related_title = text
                        break
                except:
                    continue

            if not related_title:
                continue

            # URL 추출
            related_naver_url = ""
            related_original_url = ""
            try:
                links = item.find_elements(By.CSS_SELECTOR, "a")
                for link in links:
                    href = link.get_attribute("href")
                    if href:
                        if "news.naver.com" in href:
                            related_naver_url = href
                        elif "media.naver.com" not in href and "n.news.naver.com" not in href:
                                related_original_url = href
            except:
                pass

            # 언론사와 발행일 (간단하게)
            related_press = ""
            related_published = ""

            try:
                # profile-info 컨테이너 찾기
                profile_info = card.find_element(By.CSS_SELECTOR, ".sds-comps-profile-info")

                # 언론사명 추출
                press_patterns = [
                    "span.sds-comps-profile-info-title-text",
                    "span[class*='profile-info-title-text']",
                    "span[class*='title-text']",
                ]

                for pattern in press_patterns:
                    try:
                        press_elem = profile_info.find_element(By.CSS_SELECTOR, pattern)
                        related_press = press_elem.text.strip()
                        if related_press:
                            break
                    except:
                        continue

                # 발행시간 추출
                time_patterns = [
                    "span.sds-comps-profile-info-subtext",
                    "span[class*='profile-info-subtext']",
                    "span[class*='subtext']",
                ]

                for pattern in time_patterns:
                    try:
                        time_elem = profile_info.find_element(By.CSS_SELECTOR, pattern)
                        related_published = time_elem.text.strip()
                        if related_published:
                            break
                    except:
                        continue
            except:
                pass

            # 결과에 추가
            results.append({
                "title": related_title,
                "naver_url": related_naver_url,
                "original_url": related_original_url,
                "source": related_press,
                "published": related_published,
                "related_to": main_title,
                "related_original_url": main_original_url
            })

            added_count += 1
            print(f"        ✅ 내부 관련뉴스 추가: {related_title[:30]}...")

        except Exception as e:
            print(f"        ❌ 내부 관련뉴스 추출 실패: {e}")
            continue

    return added_count

def get_naver_url(card):
    """네이버 뉴스 URL을 추출하는 함수"""
    try:
        naver_container = card.find_element(By.CSS_SELECTOR, ".sds-comps-profile-info")
        naver_link = naver_container.find_element(By.CSS_SELECTOR, "a[href*='n.news.naver']")
        return naver_link.get_attribute("href")
    except:
        return ""

def get_original_url(card):
    """원본 뉴스 URL을 추출하는 함수"""
    try:
        headline_span = card.find_element(By.CSS_SELECTOR,
                                        "span.sds-comps-text.sds-comps-text-ellipsis.sds-comps-text-ellipsis-1.sds-comps-text-type-headline1")
        original_link = headline_span.find_element(By.XPATH, "..")  # 부모 a 태그

        # a 태그이고 nocr="1" 속성을 가지고 있는지 확인
        if (original_link.tag_name.lower() == 'a' and
                original_link.get_attribute("nocr") == "1"):
            href = original_link.get_attribute("href")
            if href and "media.naver.com" not in href:
                return href
    except:
        pass
    return ""


def crawl_with_intelligent_detection(keyword, start_date_str, end_date_str):
    """지능적 감지 기능이 있는 크롤링 함수 (관련뉴스 포함)"""
    # 현재 날짜와 시간으로 파일명 생성
    now = datetime.now()
    date_str = now.strftime("%y%m%d")  # yymmdd 형식
    time_str = now.strftime("%H%M")  # hhmm 형식
    output_filename = f"naver_news_{keyword}_{date_str}_{time_str}.csv"

    options = webdriver.ChromeOptions()
    options.add_argument("--window-size=1200,900")
    options.add_argument(
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    options.add_experimental_option("detach", True)

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    results = []
    start_date = datetime.strptime(start_date_str, "%Y%m%d")
    end_date = datetime.strptime(end_date_str, "%Y%m%d")

    try:
        current_date = start_date
        while current_date <= end_date:
            date_str = current_date.strftime("%Y%m%d")
            print(f"\n📅 {date_str} 날짜 뉴스 수집 시작")

            page = 1
            while True:
                start_num = (page - 1) * 10 + 1
                url = f"https://search.naver.com/search.naver?where=news&query={keyword}&nso=so:r,p:from{date_str}to{date_str},a:all&start={start_num}"
                print(f"🌐 접속 URL: {url}")
                driver.get(url)

                # 첫 페이지에서만 디버깅 실행
                if current_date == start_date and page == 1:
                    debug_page_elements(driver)
                else:
                    time.sleep(2)  # 일반적인 대기

                # 지능적으로 뉴스 카드 찾기
                print(f"\n=== 🎯 뉴스 카드 탐지 시작 (페이지 {page}) ===")
                news_cards = find_elements_intelligently(driver)

                if not news_cards or page > 3:
                    print(f"❌ 더 이상 뉴스가 없습니다 (페이지 {page})")
                    break

                print(f"✅ {len(news_cards)}개의 뉴스 카드 발견!")

                # 각 카드에서 정보 추출
                for i, card in enumerate(news_cards):
                    print(f"\n--- 📰 뉴스 {i + 1} 처리 중 (페이지 {page}) ---")

                    try:
                        # 제목 추출
                        title = extract_title_intelligently(card)
                        if not title:
                            print(f"    ❌ 제목 추출 실패")
                            continue

                        # URL 추출
                        naver_url = get_naver_url(card)
                        original_url = get_original_url(card)
                        print(f"        네이버 URL: {naver_url}")
                        print(f"        원본 URL: {original_url}")

                        # 언론사 추출 (간단히)
                        press = ""
                        press_patterns = [
                            "span[class*='press']",
                            "span[class*='info']",
                            "[class*='profile'] span"
                        ]
                        for pattern in press_patterns:
                            try:
                                press_elem = card.find_element(By.CSS_SELECTOR, pattern)
                                press = press_elem.text.strip()
                                if press:
                                    break
                            except:
                                continue

                        # 발행일 추출 (간단히)
                        published = ""
                        date_patterns = [
                            "span[class*='date']",
                            "span[class*='time']",
                            "[class*='info'] span"
                        ]
                        for pattern in date_patterns:
                            try:
                                date_elem = card.find_element(By.CSS_SELECTOR, pattern)
                                text = date_elem.text.strip()
                                if any(x in text for x in ['시간', '분', '일', '월', '년', ':']):
                                    published = text
                                    break
                            except:
                                continue



                        result = {
                            "title": title,
                            "naver_url": naver_url,
                            "original_url": original_url,
                            "source": press,
                            "published": published,
                            "related_to": "",
                            "related_original_url": ""
                        }

                        results.append(result)
                        print(f"    ✅ 추출 완료: {title[:30]}... | {press} | {published}")

                        # 🔄 관련 뉴스 처리
                        print(f"    🔗 관련 뉴스 탐지 중...")
                        related_count = process_related_news(driver, card, title, original_url, results)
                        if related_count > 0:
                            print(f"    ✅ 관련 뉴스 {related_count}건 추가")

                    except Exception as e:
                        print(f"    ❌ 뉴스 {i + 1} 처리 실패: {e}")
                        continue

                print(f"📄 페이지 {page} 완료")
                page += 1

            print(f"📅 {date_str} 날짜 수집 완료")
            current_date += timedelta(days=1)

        # 결과 저장
        if results:
            with open(output_filename, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.DictWriter(f, fieldnames=[
                    "title", "naver_url", "original_url", "source", "published",
                    "related_to", "related_original_url"
                ])
                writer.writeheader()
                writer.writerows(results)

            # 결과 요약
            main_news = [r for r in results if not r['related_to']]
            related_news = [r for r in results if r['related_to']]

            print(f"\n✅ 총 {len(results)}건 저장 완료 → {output_filename}")
            print(f"   📰 주요 뉴스: {len(main_news)}건")
            print(f"   🔗 관련 뉴스: {len(related_news)}건")
        else:
            print("\n❌ 추출된 뉴스가 없습니다.")

    except Exception as e:
        print(f"❌ 크롤링 실패: {e}")

    finally:
        driver.quit()

    return results


# 테스트 실행
if __name__ == "__main__":
    print("🚀 지능적 네이버 뉴스 크롤러 시작")


    # 날짜 범위 테스트 (예: 6월 1일 ~ 6월 6일)
    results = crawl_with_intelligent_detection("출산", "20240601", "20240601")

    if results:
        print(f"\n📊 최종 결과:")
        main_news = [r for r in results if not r['related_to']]
        related_news = [r for r in results if r['related_to']]

        print(f"📰 주요 뉴스: {len(main_news)}건")
        print(f"🔗 관련 뉴스: {len(related_news)}건")
        print(f"📈 총 뉴스: {len(results)}건")

        # 샘플 출력
        for i, result in enumerate(main_news[:3]):
            print(f"{i + 1}. {result['title'][:50]}...")
    else:
        print("\n🔧 현재 페이지 구조가 변경되었을 가능성이 있습니다.")
        print("   위의 디버깅 출력을 참고하여 새로운 셀렉터를 확인해주세요.")