from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime, timedelta
import csv
import time
import extract_factor_util as extract_util
import os
import logging


def setup_logging():
    """로깅 설정 함수"""
    # 현재 시간으로 로그 파일명 생성
    now = datetime.now()
    log_filename = f"logs/naver_crawl_{now.strftime('%y%m%d_%H%M')}.log"

    # logs 디렉토리 생성
    os.makedirs("logs", exist_ok=True)

    # 로거 설정
    logger = logging.getLogger('naver_crawler')
    logger.setLevel(logging.INFO)

    # 기존 핸들러 제거 (중복 방지)
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # 파일 핸들러 (UTF-8 인코딩으로 한글 지원)
    file_handler = logging.FileHandler(log_filename, encoding='utf-8')
    file_handler.setLevel(logging.INFO)

    # 콘솔 핸들러
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # 로그 포맷 설정
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # 핸들러 추가
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


class ImprovedRateLimiter:
    """개선된 요청 속도 제한 클래스"""

    def __init__(self, max_requests=10, time_window=60, min_delay=2, logger=None):
        self.max_requests = max_requests  # 시간 윈도우당 최대 요청 수
        self.time_window = time_window  # 시간 윈도우 (초)
        self.min_delay = min_delay  # 요청 간 최소 대기 시간 (초)
        self.requests = []  # 요청 시간을 저장하는 리스트
        self.last_request_time = 0  # 마지막 요청 시간
        self.logger = logger or logging.getLogger('naver_crawler')

        # 통계
        self.total_requests = 0
        self.total_wait_time = 0

    def wait_if_needed(self, request_type="일반"):
        """필요시 대기하는 메서드"""
        current_time = time.time()
        self.total_requests += 1

        # 1. 최소 대기 시간 체크 (연속 요청 방지)
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.min_delay:
            min_wait = self.min_delay - time_since_last
            self.logger.info(f"⏱️  최소 대기: {min_wait:.1f}초 ({request_type} 요청)")
            time.sleep(min_wait)
            current_time = time.time()
            self.total_wait_time += min_wait

        # 2. 시간 윈도우를 벗어난 오래된 요청들 제거
        self.requests = [req_time for req_time in self.requests
                         if current_time - req_time < self.time_window]

        # 3. 최대 요청 수 체크
        if len(self.requests) >= self.max_requests:
            oldest_request = min(self.requests)
            window_wait = self.time_window - (current_time - oldest_request)
            if window_wait > 0:
                self.logger.info(f"⏰ 윈도우 제한: {window_wait:.1f}초 대기 중... "
                                 f"({self.time_window}초에 {self.max_requests}회 제한)")
                time.sleep(window_wait + 0.5)  # 여유 시간 추가
                current_time = time.time()
                self.total_wait_time += window_wait + 0.5

        # 4. 현재 요청 시간 기록
        self.requests.append(current_time)
        self.last_request_time = current_time

        # 5. 진행 상황 로깅
        if self.total_requests % 10 == 0:
            avg_wait = self.total_wait_time / self.total_requests
            self.logger.info(f"📊 요청 통계: {self.total_requests}회 완료, "
                             f"평균 대기: {avg_wait:.1f}초")

    def get_stats(self):
        """통계 반환"""
        return {
            'total_requests': self.total_requests,
            'total_wait_time': self.total_wait_time,
            'avg_wait_time': self.total_wait_time / max(self.total_requests, 1),
            'current_window_requests': len(self.requests)
        }


def debug_page_elements(driver, logger, wait_time=3):
    """페이지의 모든 가능한 뉴스 요소들을 찾아서 출력하는 디버그 함수"""
    time.sleep(wait_time)

    logger.info("=== 🔍 페이지 디버깅 시작 ===")

    # 1. 전체 페이지 구조 확인
    try:
        main_pack = driver.find_element(By.CSS_SELECTOR, "#main_pack")
        logger.info("✅ #main_pack 존재")
    except:
        logger.info("❌ #main_pack 없음")

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
                logger.info(f"📦 {selector}: {len(elements)}개 발견")
                # 첫 번째 요소의 클래스명 출력
                if elements[0].get_attribute("class"):
                    logger.info(f"    클래스: {elements[0].get_attribute('class')}")
        except:
            continue

    # 3. 링크 요소들 찾기
    logger.info("=== 📎 링크 요소 분석 ===")
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
                logger.info(f"🔗 {selector}: {len(links)}개")
                if links[0].text.strip():
                    logger.info(f"    첫 번째 텍스트: {links[0].text.strip()[:50]}...")
        except:
            continue

    # 4. 모든 a 태그의 클래스명 수집
    logger.info("=== 🏷️ 모든 링크 클래스명 분석 ===")
    all_links = driver.find_elements(By.TAG_NAME, "a")
    class_names = set()
    for link in all_links[:20]:  # 처음 20개만
        if link.get_attribute("class"):
            class_names.add(link.get_attribute("class"))
            if link.text.strip() and len(link.text.strip()) > 10:
                logger.info(f"📰 클래스: {link.get_attribute('class')}")
                logger.info(f"    텍스트: {link.text.strip()[:80]}...")
                logger.info(f"    href: {link.get_attribute('href')[:80] if link.get_attribute('href') else 'None'}...")
                logger.info("---")

    logger.info(f"총 {len(all_links)}개의 링크 발견")
    return True


def crawl_with_intelligent_detection(keyword, start_date_str, end_date_str, logger):
    # 속도 제한기 초기화 (1분에 10회)
    rate_limiter = ImprovedRateLimiter(max_requests=10, time_window=60, logger=logger)

    # 현재 날짜와 시간으로 파일명 생성
    now = datetime.now()
    start_str = now.strftime("%y%m%d")  # yymmdd 형식
    time_str = now.strftime("%H%M")  # hhmm 형식
    output_filename = f"naver_news_{keyword}_{start_str}_{time_str}_({start_date_str}to{end_date_str}).csv"

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
            start_str = current_date.strftime("%Y%m%d")
            logger.info("================================")

            # 7일 단위로 날짜 문자열 생성
            current_plus_6day = current_date + timedelta(days=6)

            if current_plus_6day <= end_date:
                end_str = (current_date + timedelta(days=6)).strftime("%Y%m%d")
            else:
                end_str = end_date.strftime("%Y%m%d")

            page = 1

            logger.info(f"📄 {start_str}부터 {end_str}까지의 뉴스 수집 시작")

            finished = False

            while True:
                if finished:
                    logger.info(f"✅ {start_str} to {end_str} 뉴스 수집 완료")
                    break

                # 속도 제한 적용
                rate_limiter.wait_if_needed()

                start_num = (page - 1) * 10 + 1

                office_category = "3"  # 1: 일간지, 2: 방송통신, 3: 경제IT, 4: 인터넷신문
                url = f"https://search.naver.com/search.naver?where=news&query={keyword}&nso=so:r,p:from{start_str}to{end_str},a:all&start={start_num}&service_area=1&office_category={office_category}"
                logger.info(f"🌐 접속 URL: {url}")
                driver.get(url)

                # 첫 페이지에서만 디버깅 실행
                if current_date == start_date and page == 1:
                    debug_page_elements(driver, logger)
                else:
                    time.sleep(3)

                # 지능적으로 뉴스 카드 찾기
                logger.info(f"=== 🎯 뉴스 카드 탐지 시작 (페이지 {page}) ===")
                news_cards = extract_util.find_elements_intelligently(driver)

                if not news_cards:
                    logger.info(f"❌ 더 이상 뉴스가 없습니다 (페이지 {page})")
                    break

                logger.info(f"✅ {len(news_cards)}개의 뉴스 카드 발견!")

                if len(news_cards) < 8:
                    finished = True

                # 각 카드에서 정보 추출
                for i, card in enumerate(news_cards):
                    logger.info(f"--- 📰 뉴스 {i + 1} 처리 중 (페이지 {page}) ---")

                    try:
                        # 제목 추출
                        title = extract_util.extract_title_intelligently(card)
                        if not title:
                            logger.warning(f"    ❌ 제목 추출 실패")
                            continue

                        # URL 추출
                        naver_url = extract_util.extract_naver_url(card)
                        original_url = extract_util.extract_original_url(card)
                        logger.info(f"        네이버 URL: {naver_url}")
                        logger.info(f"        원본 URL: {original_url}")

                        # 언론사 추출 (간단히)
                        press = extract_util.extract_press(card)
                        # 발행일 추출
                        published = extract_util.extract_published(card)
                        # 이미지 URL 추출
                        image_url = extract_util.extract_img_url(card)

                        result = {
                            "title": title,
                            "naver_url": naver_url,
                            "original_url": original_url,
                            "source": press,
                            "published": published,
                            "image_url": image_url,
                            "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "scraped_url": url
                        }

                        results.append(result)
                        logger.info(f"    ✅ 추출 완료: {title[:30]}... | {press} | {published}")

                    except Exception as e:
                        logger.error(f"    ❌ 뉴스 {i + 1} 처리 실패: {e}")
                        continue

                logger.info(f"📄 페이지 {page} 완료")
                time.sleep(2)
                page += 1

            logger.info(f"📅 {start_str} to {end_str} 수집 완료")

            current_date = datetime.strptime(end_str, "%Y%m%d") + timedelta(days=1)

        save_results(output_filename, results, logger)

        # 최종 통계 출력
        stats = rate_limiter.get_stats()
        logger.info(f"📊 레이트 리미터 최종 통계:")
        logger.info(f"   총 요청: {stats['total_requests']}회")
        logger.info(f"   총 대기 시간: {stats['total_wait_time']:.1f}초")
        logger.info(f"   평균 대기 시간: {stats['avg_wait_time']:.1f}초")

    except Exception as e:
        logger.error(f"❌ 크롤링 실패: {e}")

    finally:
        driver.quit()

    return results


def save_results(output_filename, results, logger):
    # 결과 저장
    if results:
        output_directory = "results/"
        os.makedirs(output_directory, exist_ok=True)

        # ID 추가 및 중복 제거
        processed_results = []
        seen_urls = set()  # 중복 체크용 (URL 기준)

        for result in results:  # enumerate 제거
            # URL 기준으로 중복 체크 (naver_url 또는 original_url)
            url_key = result.get('naver_url') or result.get('original_url')
            if url_key and url_key in seen_urls:
                logger.info(f"🔄 중복 뉴스 발견: {url_key} (건너뜀)")
                logger.info(f"    제목: {result.get('title')}")
                continue  # 중복이면 건너뛰기

            if url_key:
                seen_urls.add(url_key)

            # published 여부 체크
            result['has_published'] = 'Y' if result.get('published') else 'N'

            processed_results.append(result)

        # 중복 제거 후 ID 부여
        for idx, result in enumerate(processed_results, 1):
            result['id'] = idx

        filepath = os.path.join(output_directory, output_filename)

        try:
            with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.DictWriter(f, fieldnames=[
                    "id", "title", "naver_url", "original_url", "source",
                    "published", "has_published", "image_url", "scraped_at", "scraped_url"
                ])
                writer.writeheader()
                writer.writerows(processed_results)

            # 결과 요약
            original_count = len(results)
            final_count = len(processed_results)
            duplicate_count = original_count - final_count
            no_published_count = sum(1 for r in processed_results if r['has_published'] == 'N')

            logger.info(f"   📰 전체 뉴스: {original_count}건")
            logger.info(f"   🔄 중복 제거: {duplicate_count}건")
            logger.info(f"   ✅ 최종 저장: {final_count}건")
            logger.info(f"   ⚠️  발행일 없음: {no_published_count}건")
            logger.info(f"   💾 저장 위치: {filepath}")

        except Exception as e:
            logger.error(f"❌ 파일 저장 중 오류 발생: {e}")

    else:
        logger.warning("❌ 추출된 뉴스가 없습니다.")


def format_duration(seconds):
    """초를 시:분:초 형식으로 변환"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60

    if hours > 0:
        return f"{hours}시간 {minutes}분 {secs:.1f}초"
    elif minutes > 0:
        return f"{minutes}분 {secs:.1f}초"
    else:
        return f"{secs:.2f}초"


if __name__ == "__main__":
    # 로깅 설정
    logger = setup_logging()

    # 시작 시간 기록
    start_time = time.time()
    start_datetime = datetime.now()

    logger.info("🚀 네이버 뉴스 크롤러 시작")
    logger.info(f"⏰ 시작 시간: {start_datetime.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("-" * 50)

    results = crawl_with_intelligent_detection("\"육아휴직\"", "20240601", "20250531", logger)

    # crawl_target_dates = ["20240701", "20240901", "20241201", "20250201"]
    # keyword = "\"아동\""
    # all_results = []
    #
    # for i in range(len(crawl_target_dates)):
    #     start_date = crawl_target_dates[i]
    #     if i < len(crawl_target_dates) - 1:
    #         end_date = datetime.strptime(crawl_target_dates[i + 1], "%Y%m%d") + timedelta(days=-1)
    #         end_date = end_date.strftime("%Y%m%d")
    #     else:
    #         end_date = "20250531"
    #     logger.info(f"🔍 크롤링 시작: {start_date} ~ {end_date}")
    #     results = crawl_with_intelligent_detection(keyword, start_date, end_date, logger)
    #     all_results.extend(results)

    # 종료 시간 기록
    end_time = time.time()
    end_datetime = datetime.now()
    execution_time = end_time - start_time

    logger.info("-" * 50)
    logger.info(f"⏰ 종료 시간: {end_datetime.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"⌛ 총 실행 시간: {format_duration(execution_time)}")

    # if all_results:
    #     logger.info(f"📊 최종 결과:")
    #     logger.info(f"📈 총 뉴스: {len(all_results)}건")
    #     logger.info(f"⚡ 평균 처리 속도: {len(all_results) / execution_time:.2f}건/초")
    # else:
    #     logger.warning("🔧 현재 페이지 구조가 변경되었을 가능성이 있습니다.")
    #     logger.warning("   위의 디버깅 출력을 참고하여 새로운 셀렉터를 확인해주세요.")