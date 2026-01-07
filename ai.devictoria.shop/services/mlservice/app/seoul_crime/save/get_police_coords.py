#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
경찰서 주소 및 위도/경도 조회 스크립트
도커 터미널에서 실행: python -m app.seoul_crime.save.get_police_coords
"""
import sys
from pathlib import Path
import pandas as pd
from app.seoul_crime.save.kakao_map_singleton import KakaoMapSingleton
from app.seoul_crime.save.seoul_data import SeoulCrimeData

# Windows 터미널 인코딩 설정
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

def get_police_station_coordinates():
    """경찰서 주소와 위도/경도 조회"""
    print("="*80)
    print("서울 경찰서 주소 및 위도/경도 조회")
    print("="*80)
    
    # 데이터 로드
    data = SeoulCrimeData()
    crime_path = Path(data.dname) / "crime.csv"
    
    if not crime_path.exists():
        print(f"[ERROR] 범죄 데이터 파일을 찾을 수 없습니다: {crime_path}")
        return
    
    # CSV 파일 읽기
    crime_df = pd.read_csv(crime_path, encoding='utf-8')
    print(f"\n[OK] 범죄 데이터 로드 완료: {len(crime_df)} 행")
    
    # 카카오맵 API 인스턴스 생성
    try:
        kakao = KakaoMapSingleton()
        print(f"[OK] 카카오맵 API 연결 완료")
    except Exception as e:
        print(f"[ERROR] 카카오맵 API 연결 실패: {e}")
        return
    
    # 결과 저장용 리스트
    results = []
    
    # 각 경찰서에 대해 주소 및 좌표 조회
    print(f"\n{'='*80}")
    print(f"{'관서명':<15} {'자치구':<10} {'주소':<50} {'위도':<15} {'경도':<15} {'상태'}")
    print(f"{'='*80}")
    
    # 경찰서명과 자치구 매핑
    POLICE_STATION_TO_GU = {
        '중부서': '중구', '종로서': '종로구', '남대문서': '중구', '서대문서': '서대문구',
        '혜화서': '종로구', '용산서': '용산구', '성북서': '성북구', '동대문서': '동대문구',
        '마포서': '마포구', '영등포서': '영등포구', '성동서': '성동구', '동작서': '동작구',
        '광진서': '광진구', '서부서': '은평구', '강북서': '강북구', '금천서': '금천구',
        '중랑서': '중랑구', '강남서': '강남구', '관악서': '관악구', '강서서': '강서구',
        '강동서': '강동구', '종암서': '성북구', '구로서': '구로구', '서초서': '서초구',
        '양천서': '양천구', '송파서': '송파구', '노원서': '노원구', '방배서': '서초구',
        '은평서': '은평구', '도봉서': '도봉구', '수서서': '강남구'
    }
    
    for idx, row in crime_df.iterrows():
        station_name = row['관서명']
        gu = POLICE_STATION_TO_GU.get(station_name, '')
        
        # 검색 쿼리: 여러 형태로 시도
        station_name_full = station_name.replace('서', '경찰서') if station_name.endswith('서') else f"{station_name}경찰서"
        
        # 특정 경찰서에 대한 특별한 검색어 추가
        queries = []
        if station_name == '서대문서':
            queries = [
                '서울 서대문경찰서',
                '서대문경찰서',
                '서울 서대문구 경찰서',
                '서대문구 경찰서',
                '서울 서대문',
                '서울 서대문구',
            ]
        elif station_name == '강서서':
            queries = [
                '서울 강서경찰서',
                '강서경찰서',
                '서울 강서구 경찰서',
                '강서구 경찰서',
                '서울 강서',
                '서울 강서구',
            ]
        elif station_name == '수서서':
            queries = [
                '서울 수서경찰서',
                '수서경찰서',
                '서울 강남구 수서경찰서',
                '강남구 수서경찰서',
                '서울 수서 파출소',
                '서울 강남구 수서',
            ]
        else:
            queries = [
                f"서울 {station_name_full}",
                f"{station_name_full}",
                f"서울특별시 {station_name_full}",
                f"서울 {gu} {station_name_full}",
                f"{gu} {station_name_full}",
            ]
        
        response = None
        query_used = None
        
        for query in queries:
            try:
                response = kakao.geocode(query)
                if response.get('documents') and len(response['documents']) > 0:
                    # 경찰서 관련 결과 우선 검색
                    for doc in response['documents']:
                        place_name = doc.get('place_name', '')
                        category = doc.get('category_name', '')
                        category_group = doc.get('category_group_name', '')
                        category_code = doc.get('category_group_code', '')
                        
                        # 경찰서 관련 키워드 확인
                        is_police = ('경찰' in place_name or '경찰' in category or '경찰' in category_group or 
                                    category_code == 'PO3')
                        
                        if is_police:
                            query_used = query
                            response = {'documents': [doc], 'meta': response.get('meta', {})}
                            break
                    
                    # 경찰서 관련 결과가 없으면 주소 기반으로 필터링
                    if not query_used and len(response.get('documents', [])) > 0:
                        for doc in response['documents']:
                            address = doc.get('road_address_name', '') or doc.get('address_name', '')
                            place_name = doc.get('place_name', '')
                            
                            # 주소나 장소명에 구 이름이 포함되어 있으면 사용
                            if gu and (gu in address or gu.replace('구', '') in address or gu in place_name):
                                query_used = query
                                response = {'documents': [doc], 'meta': response.get('meta', {})}
                                break
                    
                    # 여전히 없으면 첫 번째 결과 사용 (서대문서, 강서서, 수서서의 경우)
                    if not query_used and len(response.get('documents', [])) > 0:
                        if station_name in ['서대문서', '강서서', '수서서']:
                            query_used = query
                            response = {'documents': [response['documents'][0]], 'meta': response.get('meta', {})}
                    
                    if query_used:
                        break
            except:
                continue
        
        try:
            if response and response.get('documents') and len(response['documents']) > 0:
                doc = response['documents'][0]
                address = doc.get('road_address_name', '') or doc.get('address_name', '') or doc.get('place_name', '')
                x = doc.get('x', '')
                y = doc.get('y', '')
                
                results.append({
                    '관서명': station_name,
                    '자치구': gu,
                    '주소': address,
                    '위도': y,
                    '경도': x,
                    '상태': '[OK] 성공'
                })
                
                print(f"{station_name:<15} {gu:<10} {address:<50} {y:<15} {x:<15} [OK]")
            else:
                results.append({
                    '관서명': station_name,
                    '자치구': gu,
                    '주소': '',
                    '위도': '',
                    '경도': '',
                    '상태': '[FAIL] 결과 없음'
                })
                print(f"{station_name:<15} {gu:<10} {'결과 없음':<50} {'':<15} {'':<15} [FAIL]")
        except Exception as e:
            results.append({
                '관서명': station_name,
                '자치구': gu,
                '주소': '',
                '위도': '',
                '경도': '',
                '상태': f'[ERROR] {str(e)[:30]}'
            })
            print(f"{station_name:<15} {gu:<10} {'오류 발생':<50} {'':<15} {'':<15} [ERROR]")
    
    # 결과를 DataFrame으로 변환
    result_df = pd.DataFrame(results)
    
    # 요약 출력
    print(f"\n{'='*80}")
    print("조회 결과 요약")
    print(f"{'='*80}")
    success_count = len(result_df[result_df['상태'].str.contains('[OK]', na=False)])
    fail_count = len(result_df) - success_count
    print(f"[OK] 성공: {success_count}개")
    print(f"[FAIL] 실패: {fail_count}개")
    print(f"총: {len(result_df)}개")
    
    return result_df

if __name__ == "__main__":
    try:
        get_police_station_coordinates()
    except KeyboardInterrupt:
        print("\n\n[INTERRUPT] 사용자에 의해 중단되었습니다.")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

