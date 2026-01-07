import requests
from bs4 import BeautifulSoup
import json

def crawl_bugs_chart():
    """
    Bugs Music 실시간 차트 정적 크롤링
    
    크롤링 전략:
    1. requests로 HTML 페이지 가져오기
    2. BeautifulSoup으로 HTML 파싱
    3. 차트 테이블(table.list.tracklist.byChart) 찾기
    4. 각 행(tr)에서 다음 정보 추출:
       - title: <p class="title"> 안의 <a> 태그 텍스트
       - artist: <p class="artist"> 안의 모든 <a> 태그 텍스트 (쉼표로 연결)
       - album: <a class="album"> 태그 텍스트
    5. JSON 형태로 터미널에 출력
    """
    
    # URL 설정
    url = "https://music.bugs.co.kr/chart/track/realtime/total"
    
    # User-Agent 헤더 설정 (크롤링 차단 방지)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "Referer": "https://music.bugs.co.kr/"
    }
    
    try:
        print("=" * 50)
        print("Bugs Music 실시간 차트 크롤링 시작")
        print("=" * 50)
        
        # HTTP 요청
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        response.encoding = 'utf-8'
        
        print(f"✓ HTTP 요청 성공 (상태 코드: {response.status_code})")
        
        # HTML 파싱
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 차트 테이블 찾기 (클래스명: list, tracklist, byChart)
        table = soup.find('table', class_='list')
        
        if not table:
            error_result = {"error": "차트 테이블을 찾을 수 없습니다"}
            print(json.dumps(error_result, ensure_ascii=False, indent=2))
            return error_result
        
        print(f"✓ 차트 테이블 발견")
        
        # tbody 찾기
        tbody = table.find('tbody')
        if not tbody:
            error_result = {"error": "tbody를 찾을 수 없습니다"}
            print(json.dumps(error_result, ensure_ascii=False, indent=2))
            return error_result
        
        # 모든 tr (행) 가져오기
        rows = tbody.find_all('tr')
        print(f"✓ 총 {len(rows)}개의 곡 발견")
        
        # 결과 저장 리스트
        chart_data = []
        
        # 각 행 파싱
        for idx, row in enumerate(rows, 1):
            try:
                # 순위
                rank_div = row.find('div', class_='ranking')
                rank = rank_div.get_text(strip=True) if rank_div else str(idx)
                
                # 곡명 (title) - <p class="title"> 안의 <a> 태그
                title_p = row.find('p', class_='title')
                title = "N/A"
                if title_p:
                    title_a = title_p.find('a')
                    if title_a:
                        title = title_a.get_text(strip=True)
                
                # 아티스트 (artist) - <p class="artist"> 안의 모든 <a> 태그
                artist_p = row.find('p', class_='artist')
                artist = "N/A"
                if artist_p:
                    artist_links = artist_p.find_all('a')
                    if artist_links:
                        artist = ', '.join([a.get_text(strip=True) for a in artist_links])
                
                # 앨범 (album) - <a class="album"> 태그
                album_a = row.find('a', class_='album')
                album = album_a.get_text(strip=True) if album_a else "N/A"
                
                # 데이터 추가
                chart_data.append({
                    "rank": rank,
                    "title": title,
                    "artist": artist,
                    "album": album
                })
                
            except Exception as e:
                print(f"⚠ 순위 {idx} 파싱 중 오류: {str(e)}")
                continue
        
        print(f"✓ {len(chart_data)}개의 곡 정보 추출 완료")
        print("=" * 50)
        
        # JSON 형태로 출력
        result = {
            "status": "success",
            "chart_type": "Bugs Music 실시간 차트",
            "url": url,
            "total_count": len(chart_data),
            "data": chart_data[:10]  # 상위 10개만 출력
        }
        
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return result
        
    except requests.exceptions.Timeout:
        error_result = {"error": "요청 시간 초과"}
        print(json.dumps(error_result, ensure_ascii=False, indent=2))
        return error_result
    except requests.exceptions.RequestException as e:
        error_result = {"error": f"HTTP 요청 실패: {str(e)}"}
        print(json.dumps(error_result, ensure_ascii=False, indent=2))
        return error_result
    except Exception as e:
        error_result = {"error": f"크롤링 실패: {str(e)}"}
        print(json.dumps(error_result, ensure_ascii=False, indent=2))
        return error_result

if __name__ == "__main__":
    crawl_bugs_chart()

