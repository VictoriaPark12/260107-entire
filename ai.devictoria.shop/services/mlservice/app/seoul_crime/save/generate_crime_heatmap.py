#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
자치구별 인구수 대비 범죄율 히트맵 생성
"""
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# Windows 터미널 인코딩 설정
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 한글 폰트 설정
plt.rcParams['font.family'] = 'Malgun Gothic'  # Windows
plt.rcParams['axes.unicode_minus'] = False  # 마이너스 기호 깨짐 방지

def generate_crime_rate_heatmap():
    """자치구별 인구수 대비 범죄율 히트맵 생성"""
    # 경로 설정
    current_file = Path(__file__)
    save_dir = current_file.parent  # save 폴더
    csv_file = save_dir / "crime_merged_by_gu.csv"
    output_file = save_dir / "crime_rate_heatmap.png"
    
    print("="*80)
    print("자치구별 인구수 대비 범죄율 히트맵 생성")
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
    
    # 인구수와 범죄 발생 건수 확인
    if '인구' not in df.columns:
        print(f"[ERROR] '인구' 컬럼이 없습니다.")
        return
    
    # 범죄 발생 컬럼 추출 (발생 건수만)
    crime_occurrence_cols = [col for col in df.columns if '발생' in col and '검거' not in col]
    
    if len(crime_occurrence_cols) == 0:
        print(f"[ERROR] 범죄 발생 컬럼을 찾을 수 없습니다.")
        return
    
    print(f"[INFO] 범죄 유형: {crime_occurrence_cols}")
    print()
    
    # 인구수 대비 범죄율 계산 (10만명당 발생 건수)
    # 범죄율 = (범죄 발생 건수 / 인구수) * 100000
    heatmap_data = pd.DataFrame()
    heatmap_data['자치구'] = df['자치구']
    
    # 각 범죄 유형별 범죄율 계산
    for crime_type in crime_occurrence_cols:
        # 인구수가 있는 행만 계산 (NaN 제외)
        valid_mask = df['인구'].notna() & (df['인구'] > 0)
        crime_rate = np.where(
            valid_mask,
            (df[crime_type] / df['인구']) * 100000,
            np.nan
        )
        # 범죄 유형명에서 ' 발생' 제거하여 컬럼명 생성
        col_name = crime_type.replace(' 발생', '')
        heatmap_data[col_name] = crime_rate
    
    # 자치구를 인덱스로 설정
    heatmap_data = heatmap_data.set_index('자치구')
    
    print(f"[INFO] 범죄율 계산 완료 (10만명당 발생 건수)")
    print(f"   범죄율 통계 (정규화 전):")
    print(heatmap_data.describe())
    print()
    
    # 정규화 적용 (Min-Max 정규화: 0-1 범위로 스케일링)
    print(f"[INFO] 정규화 적용 중...")
    # NaN 값을 제외한 최소값과 최대값 계산
    min_val = heatmap_data.min().min()
    max_val = heatmap_data.max().max()
    
    print(f"   최소값: {min_val:.6f}, 최대값: {max_val:.6f}")
    
    # 정규화: (x - min) / (max - min)
    if max_val > min_val:  # 0으로 나누기 방지
        heatmap_data_normalized = (heatmap_data - min_val) / (max_val - min_val)
    else:
        heatmap_data_normalized = heatmap_data.copy()
        print(f"   [경고] 최소값과 최대값이 같아 정규화를 건너뜁니다.")
    
    print(f"   정규화 후 통계:")
    print(heatmap_data_normalized.describe())
    print()
    
    # 정규화된 데이터를 히트맵에 사용
    heatmap_data = heatmap_data_normalized
    
    # 히트맵 생성
    print(f"[INFO] 히트맵 생성 중...")
    
    # 그림 크기 설정
    fig, ax = plt.subplots(figsize=(10, 12))
    
    # ==================== 색상 진하기 조절 설정 ====================
    # 1. 컬러맵 (cmap) 선택 - 연한 빨강에서 진한 빨강 그라데이션
    # "Reds"를 사용하면 밝은 빨강(연한 빨강)에서 진한 빨강으로
    # 하지만 더 연하게 하기 위해 커스텀 컬러맵 사용
    from matplotlib.colors import LinearSegmentedColormap
    
    # 연한 빨강(핑크)에서 진한 빨강까지의 커스텀 컬러맵 생성
    colors = ['#FFE5E5', '#FFB3B3', '#FF8080', '#FF4D4D', '#FF1A1A', '#E60000', '#CC0000', '#B30000', '#990000', '#800000']
    cmap = LinearSegmentedColormap.from_list('light_reds', colors, N=256)
    
    # 다른 옵션:
    # - "Reds": 기본 빨강 그라데이션 (밝은 빨강 → 진한 빨강)
    # - "pink": 핑크 계열
    # - "Reds_r": 역순
    
    # 2. 값 범위 설정 (vmin, vmax) - 색상 스케일 조절
    # 설정하지 않으면 자동으로 최소/최대값 사용
    # vmin = 0          # 최소값 설정 (이 값 이하는 가장 밝은 색)
    # vmax = None       # 최대값 설정 (None이면 자동, 또는 특정 값 지정)
    
    # 예시: 범죄율을 0~2000 사이로 제한하여 색상 대비 강화
    # vmin = 0
    # vmax = 2000
    
    # 3. robust 설정 - 이상치 제거로 색상 분포 조절 (색상을 더 연하게 만듦)
    robust = True     # 1사분위수와 3사분위수를 기반으로 색상 범위 설정 (이상치 영향 줄임, 색상 더 연함)
    # robust = False    # 전체 데이터 범위 사용 (기본값)
    
    # 4. center 설정 - 특정 값을 중심으로 색상 배치
    # center = None     # 중심값 없음 (기본값)
    # center = 500      # 500을 중심으로 색상 분포 (양수/음수 구분 시 유용)
    
    # 5. 컬러바 조절 (cbar_kws)
    cbar_kws = {
        'label': '정규화된 범죄율 (0-1)',
        # 'shrink': 0.8,  # 컬러바 크기 조절 (0~1)
        # 'aspect': 20,   # 컬러바 종횡비
    }
    # ==============================================================
    
    # 히트맵 그리기 (정규화된 데이터 사용)
    sns.heatmap(
        heatmap_data,
        annot=True,  # 숫자 표시
        fmt='.6f',   # 소수점 6자리
        cmap=cmap,
        vmin=0,      # 정규화된 최소값
        vmax=1,      # 정규화된 최대값
        robust=robust,  # 이상치 제거로 색상 더 연하게
        cbar_kws=cbar_kws,
        linewidths=0.5,
        linecolor='white',
        square=False,
        ax=ax
    )
    
    # 제목 및 레이블 설정
    ax.set_title('서울시 자치구별 인구수 대비 범죄율 (정규화)', 
                 fontsize=16, fontweight='bold', pad=20)
    ax.set_xlabel('범죄 유형', fontsize=12, fontweight='bold')
    ax.set_ylabel('자치구', fontsize=12, fontweight='bold')
    
    # x축 레이블 회전
    plt.xticks(rotation=45, ha='right')
    plt.yticks(rotation=0)
    
    # 레이아웃 조정
    plt.tight_layout()
    
    # 파일 저장
    output_file.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"[OK] 히트맵 저장 완료: {output_file}")
    
    # 화면에도 표시
    plt.show()
    
    print()
    print("="*80)
    print("처리 완료!")
    print("="*80)
    print()
    
    # 데이터 미리보기
    print("[범죄율 데이터 미리보기]")
    print(heatmap_data.head(10))
    print()

if __name__ == "__main__":
    generate_crime_rate_heatmap()

