#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
동일한 자치구를 합친 범죄 데이터 CSV 파일 생성
"""
import sys
import pandas as pd
from pathlib import Path

# Windows 터미널 인코딩 설정
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 경찰서명과 자치구 매핑
POLICE_STATION_TO_GU = {
    '중부서': '중구',
    '종로서': '종로구',
    '남대문서': '중구',
    '서대문서': '서대문구',
    '혜화서': '종로구',
    '용산서': '용산구',
    '성북서': '성북구',
    '동대문서': '동대문구',
    '마포서': '마포구',
    '영등포서': '영등포구',
    '성동서': '성동구',
    '동작서': '동작구',
    '광진서': '광진구',
    '서부서': '은평구',
    '강북서': '강북구',
    '금천서': '금천구',
    '중랑서': '중랑구',
    '강남서': '강남구',
    '관악서': '관악구',
    '강서서': '강서구',
    '강동서': '강동구',
    '종암서': '성북구',
    '구로서': '구로구',
    '서초서': '서초구',
    '양천서': '양천구',
    '송파서': '송파구',
    '노원서': '노원구',
    '방배서': '서초구',
    '은평서': '은평구',
    '도봉서': '도봉구',
    '수서서': '강남구'
}

def convert_station_name(station_name):
    """경찰서명을 '서울00경찰서' 형식으로 변환"""
    # '서' 제거하고 '서울' + 이름 + '경찰서' 형식으로 변경
    if station_name.endswith('서'):
        name = station_name[:-1]  # '서' 제거
        return f'서울{name}경찰서'
    return station_name

def generate_merged_crime_csv():
    """경찰서별 범죄 데이터 + 자치구 + 인구 정보 CSV 파일 생성"""
    # 경로 설정
    current_file = Path(__file__)
    save_dir = current_file.parent  # save 폴더
    data_dir = save_dir.parent / "data"  # data 폴더
    crime_file = data_dir / "crime.csv"
    pop_file = data_dir / "pop.csv"
    output_file = save_dir / "crime_merged_by_gu.csv"
    
    print("="*80)
    print("경찰서별 범죄 데이터 + 자치구 + 인구 정보 CSV 파일 생성")
    print("="*80)
    print(f"원본 범죄 파일: {crime_file}")
    print(f"원본 인구 파일: {pop_file}")
    print(f"출력 파일: {output_file}")
    print()
    
    # 범죄 데이터 읽기
    if not crime_file.exists():
        print(f"[ERROR] 파일을 찾을 수 없습니다: {crime_file}")
        return
    
    df = pd.read_csv(crime_file, encoding='utf-8')
    print(f"[OK] 범죄 데이터 로드 완료: {len(df)} 행, {len(df.columns)} 컬럼")
    print(f"   컬럼: {list(df.columns)}")
    print()
    
    # 인구 데이터 읽기
    if not pop_file.exists():
        print(f"[ERROR] 파일을 찾을 수 없습니다: {pop_file}")
        return
    
    pop_df = pd.read_csv(pop_file, encoding='utf-8')
    print(f"[OK] 인구 데이터 로드 완료: {len(pop_df)} 행, {len(pop_df.columns)} 컬럼")
    
    # 인구 데이터 전처리: 자치구와 인구 컬럼만 선택
    # pop.csv 구조: 기간, 자치구, 세대, 인구(계), ... 중에서 자치구와 인구(계) 선택
    # 좌로부터 2번째 컬럼(자치구), 4번째 컬럼(인구 계)
    if len(pop_df.columns) >= 4:
        pop_df_processed = pop_df.iloc[:, [1, 3]].copy()  # 자치구와 인구(계) 컬럼
        pop_df_processed.columns = ['자치구', '인구']
        # 위로부터 2, 3, 4번째 행 제거 (인덱스 1, 2, 3)
        pop_df_processed = pop_df_processed.drop(pop_df_processed.index[1:4])
        # 빈 행 및 합계 행 제거
        pop_df_processed = pop_df_processed[pop_df_processed['자치구'].notna() & (pop_df_processed['자치구'] != '')]
        pop_df_processed = pop_df_processed[pop_df_processed['자치구'] != '합계']
        pop_df_processed = pop_df_processed.reset_index(drop=True)
        
        # 인구 컬럼 숫자 변환 (콤마 제거)
        if pop_df_processed['인구'].dtype == 'object':
            pop_df_processed['인구'] = pop_df_processed['인구'].astype(str).str.replace(',', '').str.replace('"', '')
            pop_df_processed['인구'] = pd.to_numeric(pop_df_processed['인구'], errors='coerce')
        
        print(f"[OK] 인구 데이터 전처리 완료: {len(pop_df_processed)} 행")
        print()
    else:
        print(f"[WARNING] 인구 데이터 형식이 예상과 다릅니다. 인구 정보를 추가하지 않습니다.")
        pop_df_processed = None
    
    # 관서명을 '서울00경찰서' 형식으로 변경
    if '관서명' in df.columns:
        # 원본 관서명 저장 (자치구 매핑용)
        original_station_names = df['관서명'].copy()
        df['관서명'] = df['관서명'].apply(convert_station_name)
        print(f"[OK] 관서명 형식 변경 완료 (예: 중부서 → 서울중부경찰서)")
        print()
    
    # 자치구 컬럼 추가
    if '관서명' in df.columns:
        # 원본 관서명으로 자치구 매핑
        df['자치구'] = original_station_names.map(POLICE_STATION_TO_GU)
        
        # 매핑되지 않은 관서명 확인
        unmapped = df[df['자치구'].isna()]['관서명'].unique()
        if len(unmapped) > 0:
            print(f"[WARNING] 매핑되지 않은 관서명: {list(unmapped)}")
            print()
        
        # 매핑 실패한 행 제거
        before_drop = len(df)
        df = df[df['자치구'].notna()]
        after_drop = len(df)
        if before_drop != after_drop:
            print(f"[WARNING] 자치구 매핑 실패한 {before_drop - after_drop}개 행 제거됨")
            print()
        
        print(f"[OK] 자치구 컬럼 추가 완료")
        print(f"   처리된 행 수: {len(df)}")
        print(f"   고유 자치구 수: {df['자치구'].nunique()}")
        print()
    else:
        print("[ERROR] '관서명' 컬럼을 찾을 수 없습니다.")
        return
    
    # 숫자 컬럼 선택 (자치구, 관서명 제외)
    numeric_cols = [col for col in df.columns if col not in ['자치구', '관서명']]
    
    # 숫자 문자열에서 콤마 및 따옴표 제거 후 숫자 변환
    print(f"[INFO] 숫자 데이터 전처리 중...")
    for col in numeric_cols:
        if df[col].dtype == 'object':
            df[col] = df[col].astype(str).str.replace(',', '').str.replace('"', '')
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # 인구 데이터 머지
    if pop_df_processed is not None:
        print(f"[INFO] 인구 데이터 머지 중...")
        df = df.merge(pop_df_processed, on='자치구', how='left')
        
        # 종로구 인구가 누락된 경우 직접 채워넣기
        jongno_mask = df['자치구'] == '종로구'
        if jongno_mask.any() and df.loc[jongno_mask, '인구'].isna().any():
            print(f"[INFO] 종로구 인구 데이터가 누락되어 직접 채워넣는 중...")
            df.loc[jongno_mask, '인구'] = 162820.0
        
        # 인구가 누락된 자치구 확인
        missing_pop = df[df['인구'].isna()]['자치구'].unique()
        if len(missing_pop) > 0:
            print(f"[WARNING] 인구 데이터가 누락된 자치구: {list(missing_pop)}")
        
        print(f"[OK] 인구 데이터 머지 완료")
        print()
    
    # 자치구별로 집계 (합계) - 관서명은 소계가 가장 큰 경찰서 하나만 표시
    print(f"[INFO] 자치구별 집계 중...")
    print(f"   집계 전: {len(df)} 행 (경찰서별)")
    
    # 발생 건수 컬럼: 살인 발생, 강도 발생, 강간 발생, 절도 발생, 폭력 발생
    occurrence_cols = [col for col in numeric_cols if '발생' in col]
    
    # 범죄 발생 건수 합계를 소계로 계산 (개별 경찰서별로)
    if occurrence_cols:
        df['소계'] = df[occurrence_cols].sum(axis=1)
    
    # 숫자 컬럼들 집계 (소계는 제외하고 먼저 집계)
    numeric_cols_for_groupby = [col for col in numeric_cols if col != '소계']
    grouped_numeric = df.groupby('자치구')[numeric_cols_for_groupby].sum().reset_index()
    
    # 자치구별 소계 합계 계산 (집계된 값)
    if occurrence_cols:
        grouped_numeric['소계'] = grouped_numeric[occurrence_cols].sum(axis=1)
    
    # 자치구별로 소계가 가장 큰 경찰서 하나만 선택
    representative_stations = df.loc[df.groupby('자치구')['소계'].idxmax()][['자치구', '관서명']].reset_index(drop=True)
    
    # 인구 컬럼이 있으면 추가 (집계하지 않고 첫 번째 값 사용 - 자치구별로 동일하므로)
    if '인구' in df.columns:
        population = df.groupby('자치구')['인구'].first().reset_index()
        grouped_df = representative_stations.merge(grouped_numeric, on='자치구', how='inner')
        grouped_df = grouped_df.merge(population, on='자치구', how='left')
        
        # 종로구 인구가 여전히 누락된 경우 직접 채워넣기
        if '종로구' in grouped_df['자치구'].values:
            jongno_idx = grouped_df[grouped_df['자치구'] == '종로구'].index
            if len(jongno_idx) > 0 and pd.isna(grouped_df.loc[jongno_idx[0], '인구']):
                print(f"[INFO] 종로구 인구 데이터를 최종적으로 채워넣는 중...")
                grouped_df.loc[jongno_idx[0], '인구'] = 162820.0
    else:
        grouped_df = representative_stations.merge(grouped_numeric, on='자치구', how='inner')
    
    print(f"   집계 후: {len(grouped_df)} 행 (자치구별)")
    print(f"   집계된 자치구: {sorted(grouped_df['자치구'].tolist())}")
    print()
    
    # 컬럼 순서 정렬: 자치구, 관서명, 소계, 인구
    column_order = ['자치구', '관서명']
    if '소계' in grouped_df.columns:
        column_order.append('소계')
    if '인구' in grouped_df.columns:
        column_order.append('인구')
    
    # 존재하는 컬럼만 선택
    existing_cols = [col for col in column_order if col in grouped_df.columns]
    remaining_cols = [col for col in grouped_df.columns if col not in column_order]
    final_column_order = existing_cols + remaining_cols
    grouped_df = grouped_df[final_column_order]
    
    # save 폴더에 저장
    output_file.parent.mkdir(parents=True, exist_ok=True)
    grouped_df.to_csv(output_file, index=False, encoding='utf-8-sig')
    
    print(f"[OK] 파일 저장 완료: {output_file}")
    print(f"   - 저장된 행 수: {len(grouped_df)}")
    print(f"   - 저장된 컬럼 수: {len(grouped_df.columns)}")
    print(f"   - 컬럼: {', '.join(grouped_df.columns.tolist())}")
    print()
    
    # 파일 존재 확인
    if output_file.exists():
        print(f"[OK] 파일 생성 확인됨: {output_file}")
    else:
        print(f"[ERROR] 파일 생성 실패: {output_file}")
    
    print()
    print("="*80)
    print("처리 완료!")
    print("="*80)
    
    # 집계 결과 요약 출력
    print()
    print("[집계 결과 요약]")
    print(f"   총 자치구 수: {len(grouped_df)}")
    print()
    print("   처음 10개 자치구 데이터:")
    print(grouped_df.head(10).to_string(index=False))
    print()

if __name__ == "__main__":
    generate_merged_crime_csv()

