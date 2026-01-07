from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import json
import time

def crawl_danawa_tv():
    """
    다나와 TV 상품 목록 Selenium 크롤링
    
    크롤링 전략:
    1. Selenium으로 페이지 로드
    2. 상품 목록이 로드될 때까지 대기
    3. <li class="prod_item"> 요소들 찾기
    4. 각 상품에서 다음 정보 추출:
       - 상품명: <p class="prod_name"> 안의 <a> 태그 텍스트
       - 상품 링크: <a> 태그의 href 속성
       - 가격 정보: 가격 관련 요소
       - 쇼핑몰 정보: 쇼핑몰 이름
    5. JSON 형태로 반환
    """
    
    url = "https://prod.danawa.com/list/?cate=10248425&15main_10_02="
    
    # Chrome 옵션 설정
    chrome_options = Options()
    chrome_options.add_argument('--headless')  # 헤드리스 모드 (브라우저 창 없이)
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    driver = None
    try:
        print("=" * 80)
        print("📺 다나와 TV 상품 목록 크롤링 시작")
        print("=" * 80)
        
        # 1단계: Selenium WebDriver 초기화
        print("\n[1단계] Selenium WebDriver 초기화 중...")
        # webdriver-manager를 사용하여 ChromeDriver 자동 관리
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        print("✓ WebDriver 초기화 완료")
        
        # 2단계: 페이지 로드
        print("\n[2단계] 페이지 로드 중...")
        driver.get(url)
        print(f"✓ 페이지 로드 완료: {url}")
        
        # 3단계: 상품 목록이 로드될 때까지 대기
        print("\n[3단계] 상품 목록 로딩 대기 중...")
        wait = WebDriverWait(driver, 10)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "li.prod_item")))
        time.sleep(2)  # 추가 로딩 대기
        print("✓ 상품 목록 로드 완료")
        
        # 4단계: 상품 목록 찾기
        print("\n[4단계] 상품 정보 추출 중...")
        product_items = driver.find_elements(By.CSS_SELECTOR, "li.prod_item")
        print(f"✓ 총 {len(product_items)}개의 상품 발견")
        
        # 결과 저장 리스트
        products = []
        
        # 각 상품 파싱
        for idx, item in enumerate(product_items[:20], 1):  # 상위 20개만
            try:
                # 상품명 추출
                product_name = "N/A"
                try:
                    name_elem = item.find_element(By.CSS_SELECTOR, "p.prod_name a")
                    product_name = name_elem.text.strip()
                except:
                    pass
                
                # 상품 링크 추출
                product_link = "N/A"
                try:
                    link_elem = item.find_element(By.CSS_SELECTOR, "p.prod_name a")
                    product_link = link_elem.get_attribute("href")
                except:
                    pass
                
                # 가격 정보 추출
                price = "N/A"
                try:
                    price_elem = item.find_element(By.CSS_SELECTOR, "p.price_sect")
                    price = price_elem.text.strip()
                except:
                    pass
                
                # 쇼핑몰 정보 추출
                mall = "N/A"
                try:
                    mall_elem = item.find_element(By.CSS_SELECTOR, "a.mall_name")
                    mall = mall_elem.text.strip()
                except:
                    pass
                
                # 상품 이미지 추출
                image_url = "N/A"
                try:
                    img_elem = item.find_element(By.CSS_SELECTOR, "div.thumb_image img")
                    image_url = img_elem.get_attribute("src")
                except:
                    pass
                
                # 데이터 추가
                products.append({
                    "rank": idx,
                    "product_name": product_name,
                    "product_link": product_link,
                    "price": price,
                    "mall": mall,
                    "image_url": image_url
                })
                
                # 상위 5개는 즉시 출력
                if idx <= 5:
                    print(f"  {idx}. {product_name} - {price} ({mall})")
                
            except Exception as e:
                print(f"⚠ 상품 {idx} 파싱 중 오류: {str(e)}")
                continue
        
        print(f"\n✓ {len(products)}개의 상품 정보 추출 완료")
        
        # 5단계: JSON 형태로 반환
        print("\n[5단계] 결과 반환")
        print("=" * 80)
        
        result = {
            "status": "success",
            "source": "다나와 TV 상품 목록",
            "url": url,
            "total_count": len(products),
            "data": products
        }
        
        # JSON 출력
        print(json.dumps(result, ensure_ascii=False, indent=2))
        
        return result
        
    except Exception as e:
        error_result = {
            "status": "error",
            "error": f"크롤링 실패: {str(e)}"
        }
        print(json.dumps(error_result, ensure_ascii=False, indent=2))
        return error_result
        
    finally:
        # WebDriver 종료
        if driver:
            print("\n[종료] WebDriver 종료 중...")
            driver.quit()
            print("✓ WebDriver 종료 완료")

if __name__ == "__main__":
    crawl_danawa_tv()

