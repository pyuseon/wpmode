from selenium.webdriver.common.by import By


def find_elements_intelligently(driver, base_element=None):
    """지능적으로 뉴스 요소들을 찾는 함수"""
    search_base = base_element if base_element else driver

    # 1단계: 뉴스 컨테이너를 찾기 위한 패턴들
    container_patterns = [
        # 최신 컨테이너 패턴들
        "div.sds-comps-vertical-layout.sds-comps-full-layout.fender-news-item-list-tab"
        "div.fender-news-item-list-tab",
        "div[class*='fender-news-item-list']",
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
         # 정확한 개별 카드 패턴 (2024년 6월)
        "div.sds-comps-vertical-layout.sds-comps-full-layout._4zQ0QZWfn7bqZ_ul5OV",
        "div[class*='sds-comps-vertical-layout'][class*='sds-comps-full-layout'][class*='_4zQ0QZWfn7bqZ_ul5OV']",
        "div[class*='_4zQ0QZWfn7bqZ_ul5OV']",  # 고유 클래스로 찾기
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

def extract_naver_url(card):
    """네이버 뉴스 URL을 추출하는 함수"""
    try:
        naver_container = card.find_element(By.CSS_SELECTOR, ".sds-comps-profile-info")
        naver_link = naver_container.find_element(By.CSS_SELECTOR, "a[href*='n.news.naver']")
        return naver_link.get_attribute("href")
    except:
        return ""

def extract_original_url(card):
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


def extract_press(card):
    press = ""
    press_patterns = [
        # 주어진 구조에 맞는 구체적인 셀렉터
        "div.sds-comps-horizontal-layout.sds-comps-inline-layout.sds-comps-profile-info span.sds-comps-text.sds-comps-text-ellipsis.sds-comps-text-ellipsis-1.sds-comps-text-type-body2.sds-comps-text-weight-sm",

        # 좀 더 간단한 버전들 (백업용)
        ".sds-comps-profile-info span.sds-comps-text-ellipsis",
        ".sds-comps-profile-info .sds-comps-text-type-body2",
        "div[class*='profile-info'] span[class*='text-ellipsis']",
    ]

    for pattern in press_patterns:
        try:
            press_elem = card.find_element(By.CSS_SELECTOR, pattern)
            press = press_elem.text.strip()
            if press:
                break
        except:
            continue

    return press

def extract_published(card):
    published = ""
    date_patterns = [
        # 정확한 구조 패턴
        ".sds-comps-horizontal-layout.sds-comps-inline-layout.sds-comps-profile-info span.sds-comps-text.sds-comps-text-type-body2.sds-comps-text-weight-sm",
        ".sds-comps-profile-info span.sds-comps-text-type-body2.sds-comps-text-weight-sm",
        ".sds-comps-profile-info span.sds-comps-text-type-body2",
        ".sds-comps-profile-info span[class*='sds-comps-text-weight-sm']",
    ]
    for pattern in date_patterns:
        try:
            date_elems = card.find_elements(By.CSS_SELECTOR, pattern)
            for date_elem in date_elems:
                text = date_elem.text.strip()
                # 2024.06.15 형식 또는 다른 날짜 형식 확인
                import re
                if text and (
                        # YYYY.MM.DD 형식
                        re.match(r'\d{4}\.\d{1,2}\.\d{1,2}', text)
                ):
                    if len(text) < 50:  # 너무 긴 텍스트 제외
                        published = text
                        print(f"        📅 발행일 발견 (패턴: {pattern}): {text}")
                        break
            if published:
                break
        except:
            continue
    return published



def extract_img_url(card):
    image_url = ""
    image_patterns = [
        ".sds-comps-base-layout .sds-comps-inline-layout .sds-comps-image img",
        ".sds-rego-thumb-overlay img",
        ".fit-contain img",
        ".forced-ratio img",
        "img"
    ]
    for pattern in image_patterns:
        try:
            img_elem = card.find_element(By.CSS_SELECTOR, pattern)
            src = img_elem.get_attribute('src')
            if src and src.startswith('http'):
                image_url = src
                break
            # data-src나 다른 속성도 확인
            data_src = img_elem.get_attribute('data-src')
            if data_src and data_src.startswith('http'):
                image_url = data_src
                break
        except:
            continue
    return image_url

