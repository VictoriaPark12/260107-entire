#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
히트맵 데이터를 JSON으로 생성
"""
import sys
import pandas as pd
import numpy as np
import json
from pathlib import Path

# Windows 터미널 인코딩 설정
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

def generate_heatmap_json():
    """히트맵 데이터를 JSON으로 생성"""
    # 경로 설정
    current_file = Path(__file__)
    save_dir = current_file.parent  # save 폴더
    csv_file = save_dir / "crime_merged_by_gu.csv"
    output_file = save_dir / "heatmap_data.json"
    
    print("="*80)
    print("히트맵 데이터 JSON 생성")
    print("="*80)
    print(f"입력 파일: {csv_file}")
    print(f"출력 파일: {output_file}")
    print()
    
    # CSV 파일 읽기
    if not csv_file.exists():
        print(f"[ERROR] 파일을 찾을 수 없습니다: {csv_file}")
        return
    
    df = pd.read_csv(csv_file, encoding='utf-8-sig')
    print(f"[OK] 데이터 로드 완료: {len(df)} 행, {len(df.columns)} 컬럼")
    print()
    
    # 범죄율 데이터 계산
    crime_occurrence_cols = [col for col in df.columns if '발생' in col and '검거' not in col]
    crime_rate_data = {}
    
    # 범죄율 계산
    heatmap_data_crime = pd.DataFrame()
    heatmap_data_crime['자치구'] = df['자치구']
    
    for crime_type in crime_occurrence_cols:
        valid_mask = df['인구'].notna() & (df['인구'] > 0)
        crime_rate = np.where(
            valid_mask,
            (df[crime_type] / df['인구']) * 100000,
            np.nan
        )
        col_name = crime_type.replace(' 발생', '')
        heatmap_data_crime[col_name] = crime_rate
    
    heatmap_data_crime = heatmap_data_crime.set_index('자치구')
    
    # 정규화
    min_val = heatmap_data_crime.min().min()
    max_val = heatmap_data_crime.max().max()
    
    if max_val > min_val:
        heatmap_data_crime_normalized = (heatmap_data_crime - min_val) / (max_val - min_val)
    else:
        heatmap_data_crime_normalized = heatmap_data_crime.copy()
    
    # 범죄율 데이터 변환
    districts = heatmap_data_crime_normalized.index.tolist()
    crime_types = heatmap_data_crime_normalized.columns.tolist()
    
    crime_rate_dict = {}
    for district in districts:
        crime_rate_dict[district] = {}
        for crime_type in crime_types:
            value = heatmap_data_crime_normalized.loc[district, crime_type]
            crime_rate_dict[district][crime_type] = float(value) if not pd.isna(value) else 0.0
    
    # 검거율 데이터 계산
    crime_arrest_cols = [col for col in df.columns if '검거' in col]
    arrest_rate_data = {}
    
    # 검거율 계산
    heatmap_data_arrest = pd.DataFrame()
    heatmap_data_arrest['자치구'] = df['자치구']
    
    for crime_type in crime_arrest_cols:
        valid_mask = df['인구'].notna() & (df['인구'] > 0)
        arrest_rate = np.where(
            valid_mask,
            (df[crime_type] / df['인구']) * 100000,
            np.nan
        )
        col_name = crime_type.replace(' 검거', '')
        heatmap_data_arrest[col_name] = arrest_rate
    
    heatmap_data_arrest = heatmap_data_arrest.set_index('자치구')
    
    # 정규화
    min_val = heatmap_data_arrest.min().min()
    max_val = heatmap_data_arrest.max().max()
    
    if max_val > min_val:
        heatmap_data_arrest_normalized = (heatmap_data_arrest - min_val) / (max_val - min_val)
    else:
        heatmap_data_arrest_normalized = heatmap_data_arrest.copy()
    
    # 검거율 데이터 변환
    arrest_rate_dict = {}
    for district in districts:
        arrest_rate_dict[district] = {}
        for crime_type in crime_types:
            value = heatmap_data_arrest_normalized.loc[district, crime_type]
            arrest_rate_dict[district][crime_type] = float(value) if not pd.isna(value) else 0.0
    
    # JSON 생성
    result = {
        "crimeRate": {
            "districts": districts,
            "crimeTypes": crime_types,
            "data": crime_rate_dict
        },
        "arrestRate": {
            "districts": districts,
            "crimeTypes": crime_types,
            "data": arrest_rate_dict
        }
    }
    
    # JSON 파일 저장
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"[OK] JSON 파일 저장 완료: {output_file}")
    print()
    print("="*80)
    print("처리 완료!")
    print("="*80)
    print()

if __name__ == "__main__":
    generate_heatmap_json()

