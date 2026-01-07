import sys
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Tuple, Optional
import logging
from app.seoul_crime.save.seoul_method import SeoulCrimeMethod
from app.seoul_crime.save.seoul_data import SeoulCrimeData

logger = logging.getLogger(__name__)

class SeoulCrimeService:
    """서울 범죄 데이터 서비스"""
    
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
        '종암서': '성북구',  # 종암동은 성북구
        '구로서': '구로구',
        '서초서': '서초구',
        '양천서': '양천구',
        '송파서': '송파구',
        '노원서': '노원구',
        '방배서': '서초구',  # 방배동은 서초구
        '은평서': '은평구',
        '도봉서': '도봉구',
        '수서서': '강남구'  # 수서동은 강남구
    }
    
    def __init__(self):
        self.method = SeoulCrimeMethod()
        self.data = SeoulCrimeData()
        self.crime_rate_columns = ['살인검거율', '강도검거율', '강간검거율', '절도검거율', '폭력검거율']
        self.crime_columns = ['살인', '강도', '강간', '절도', '폭력']
        self.merged_df: Optional[pd.DataFrame] = None

    def preprocess(self) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        데이터 전처리 및 머지 (CCTV + 인구 + 범죄)
        
        Returns:
        --------
        Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]
            (cctv_df, crime_df, pop_df, final_merged_df)
            final_merged_df: CCTV, 인구, 범죄 데이터가 자치구 기준으로 머지된 최종 DataFrame
        """
        print("\n" + "="*60)
        print("서울 범죄 데이터 전처리 시작")
        print("="*60)
        
        # 데이터 로드
        data_dir = Path(self.data.dname)
        cctv_path = data_dir / "cctv.csv"
        crime_path = data_dir / "crime.csv"
        pop_path = data_dir / "pop.csv"
        
        print(f"\n[1/4] CSV 파일 로드 중...")
        cctv_df = self.method.csv_to_df(str(cctv_path))
        # CCTV 컬럼 드롭: '2013년도 이전', '2014년', '2015년', '2016년' 제거
        cctv_df = cctv_df.drop(['2013년도 이전', '2014년', '2015년', '2016년'], axis=1)
        
        crime_df = self.method.csv_to_df(str(crime_path))
        # pop 파일은 CSV이므로 csv_to_df 사용 (원래 xlsx_to_df였지만 실제 파일은 csv)
        pop_df = self.method.csv_to_df(str(pop_path))
        
        print(f"   ✅ CCTV: {len(cctv_df)} 행, {len(cctv_df.columns)} 컬럼")
        print(f"   ✅ 범죄: {len(crime_df)} 행, {len(crime_df.columns)} 컬럼")
        print(f"   ✅ 인구: {len(pop_df)} 행, {len(pop_df.columns)} 컬럼")
        
        # pop 컬럼 편집 
        # axis = 1 방향으로 자치구와 좌로부터 4번째 컬럼만 남기고 모두 삭제 
        # axis = 0 방향으로 위로부터 2, 3, 4 번째 행을 제거
        print(f"\n[2/4] 인구 데이터 전처리 중...")
        
        # 컬럼 편집: 자치구(인덱스 1)와 좌로부터 4번째 컬럼(인덱스 3)만 남기기
        columns_to_keep = [pop_df.columns[1], pop_df.columns[3]]  # 자치구와 좌로부터 4번째 컬럼
        pop_df = pop_df[columns_to_keep]
        pop_df.columns = ['자치구', '인구']  # 컬럼명 재설정
        print(f"   ✅ 컬럼 선택 완료: 자치구, 인구만 남김")
        
        # 행 편집: 위로부터 2, 3, 4 번째 행 제거 (인덱스 1, 2, 3)
        pop_df = pop_df.drop(pop_df.index[1:4])  # 인덱스 1, 2, 3 제거
        print(f"   ✅ 행 제거 완료: 인덱스 1, 2, 3 제거됨")
        
        # 빈 행 제거
        pop_df = pop_df[pop_df['자치구'].notna() & (pop_df['자치구'] != '')]
        pop_df = pop_df[pop_df['자치구'] != '합계']  # 합계 행 제거
        # 인덱스 리셋
        pop_df = pop_df.reset_index(drop=True)
        print(f"   ✅ 전처리 완료: {len(pop_df)} 행, {len(pop_df.columns)} 컬럼")
        
        # 로그 출력
        logger.info(f"  cctv 탑  : {cctv_df.head(1).to_string()}")
        logger.info(f"  crime 탑  : {crime_df.head(1).to_string()}")
        logger.info(f"  pop 탑  : {pop_df.head(1).to_string()}")
        
        # CCTV 데이터 전처리
        print(f"\n[3/4] CCTV 데이터 전처리 중...")
        # 기관명 컬럼 정리 (따옴표 제거)
        if '기관명' in cctv_df.columns:
            cctv_df['기관명'] = cctv_df['기관명'].str.strip().str.replace('"', '')
        print(f"   ✅ 전처리 완료: {len(cctv_df)} 행")
        
        # 머지 전 중복 컬럼 확인
        print(f"\n[4/4] CCTV-인구 데이터 머지 중...")
        print(f"   머지 키: cctv['기관명'] = pop['자치구']")
        
        # 머지 실행
        merged_df = self.method.df_merge(
            left=cctv_df,
            right=pop_df,
            left_on='기관명',
            right_on='자치구',
            how='inner',
            remove_duplicate_columns=True
        )
        
        # 머지 후 "기관명"을 "자치구"로 변경 (통일된 컬럼명 사용)
        if '기관명' in merged_df.columns and '자치구' in merged_df.columns:
            # 값이 동일한지 확인
            if merged_df['기관명'].equals(merged_df['자치구']):
                # 기존 자치구 컬럼 제거 후 기관명을 자치구로 변경
                merged_df = merged_df.drop(columns=['자치구'])
                merged_df = merged_df.rename(columns={'기관명': '자치구'})
                print(f"\n   ✅ '기관명' 컬럼을 '자치구'로 변경됨 (기존 자치구 컬럼 제거)")
            else:
                # 값이 다르면 기존 자치구를 다른 이름으로 변경 후 기관명을 자치구로 변경
                merged_df = merged_df.rename(columns={'자치구': '자치구_원본', '기관명': '자치구'})
                print(f"\n   ⚠️  '기관명'을 '자치구'로 변경, 기존 '자치구'는 '자치구_원본'으로 변경됨")
        elif '기관명' in merged_df.columns:
            # 자치구 컬럼이 없으면 기관명을 자치구로 변경
            merged_df = merged_df.rename(columns={'기관명': '자치구'})
            print(f"\n   ✅ '기관명' 컬럼을 '자치구'로 변경됨")
        
        # 범죄 데이터 전처리: 자치구별로 집계 (같은 구에 여러 경찰서가 있을 수 있음)
        print(f"\n[5/5] 범죄 데이터 자치구별 집계 중...")
        print(f"   원본 범죄 데이터: {len(crime_df)} 행 (경찰서별)")
        
        # 숫자 문자열에서 콤마 제거 및 숫자 변환
        crime_df_processed = crime_df.copy()
        
        # '자치구' 컬럼이 없으면 '구' 컬럼이 있는지 확인하고, 없으면 관서명을 기반으로 추가
        if '자치구' not in crime_df_processed.columns:
            # '구' 컬럼이 있으면 '자치구'로 이름 변경
            if '구' in crime_df_processed.columns:
                crime_df_processed['자치구'] = crime_df_processed['구']
                print(f"   ✅ '구' 컬럼을 '자치구'로 변경")
            # '구'도 없으면 관서명을 기반으로 '자치구' 추가
            elif '관서명' in crime_df_processed.columns:
                crime_df_processed['자치구'] = crime_df_processed['관서명'].map(self.POLICE_STATION_TO_GU)
                # 매핑되지 않은 관서명 확인
                unmapped = crime_df_processed[crime_df_processed['자치구'].isna()]['관서명'].unique()
                if len(unmapped) > 0:
                    print(f"   ⚠️  매핑되지 않은 관서명: {list(unmapped)}")
                    logger.warning(f"매핑되지 않은 관서명: {list(unmapped)}")
            else:
                raise ValueError("'자치구' 컬럼과 '관서명' 컬럼이 모두 없습니다. 범죄 데이터에 필요한 컬럼이 없습니다.")
        
        # '자치구' 컬럼이 None인 행 제거 (매핑 실패한 데이터)
        before_drop = len(crime_df_processed)
        crime_df_processed = crime_df_processed[crime_df_processed['자치구'].notna()]
        after_drop = len(crime_df_processed)
        if before_drop != after_drop:
            print(f"   ⚠️  '자치구' 컬럼이 None인 {before_drop - after_drop}개 행 제거됨")
        
        # '자치구' 컬럼이 없으면 에러
        if '자치구' not in crime_df_processed.columns:
            raise ValueError("'자치구' 컬럼을 추가할 수 없습니다. 데이터를 확인해주세요.")
        
        print(f"   ✅ '자치구' 컬럼 확인: {crime_df_processed['자치구'].nunique()}개 자치구")
        
        # 숫자 컬럼만 선택 (자치구, 구, 관서명 제외)
        numeric_cols = [col for col in crime_df_processed.columns if col not in ['자치구', '구', '관서명']]
        
        # 숫자 문자열에서 콤마 제거 및 숫자 변환
        for col in numeric_cols:
            if crime_df_processed[col].dtype == 'object':
                crime_df_processed[col] = crime_df_processed[col].astype(str).str.replace(',', '').str.replace('"', '')
                crime_df_processed[col] = pd.to_numeric(crime_df_processed[col], errors='coerce')
        
        # 자치구별로 집계 (합계)
        crime_by_gu = crime_df_processed.groupby('자치구')[numeric_cols].sum().reset_index()
        print(f"   ✅ 집계 완료: {len(crime_by_gu)} 행 (자치구별)")
        print(f"   집계된 자치구: {list(crime_by_gu['자치구'].values)}")
        
        # CCTV-인구 머지 결과와 범죄 데이터 머지
        print(f"\n[6/6] CCTV-인구-범죄 데이터 머지 중...")
        print(f"   머지 키: merged_df['자치구'] = crime_by_gu['자치구']")
        
        # merged_df의 '자치구'와 범죄 데이터의 '자치구'를 기준으로 머지
        final_merged_df = self.method.df_merge(
            left=merged_df,
            right=crime_by_gu,
            left_on='자치구',
            right_on='자치구',
            how='inner',
            remove_duplicate_columns=True
        )
        
        # 머지 후 '구' 컬럼이 있으면 제거 (자치구와 동일한 값인 경우)
        if '구' in final_merged_df.columns and '자치구' in final_merged_df.columns:
            if final_merged_df['자치구'].equals(final_merged_df['구']):
                final_merged_df = final_merged_df.drop(columns=['구'])
                print(f"\n   ✅ '구' 컬럼 제거됨 (자치구와 동일한 값)")
            else:
                print(f"\n   ⚠️  '구' 컬럼 유지됨 (자치구와 다른 값 존재)")
        
        self.merged_df = final_merged_df
        
        print(f"\n" + "="*60)
        print(f"전처리 완료!")
        print(f"   - CCTV: {len(cctv_df)} 행")
        print(f"   - 범죄: {len(crime_df)} 행 (경찰서별) → {len(crime_by_gu)} 행 (자치구별 집계)")
        print(f"   - 인구: {len(pop_df)} 행")
        print(f"   - 최종 머지: {len(final_merged_df)} 행, {len(final_merged_df.columns)} 컬럼")
        print(f"\n최종 머지된 컬럼:")
        for i, col in enumerate(final_merged_df.columns, 1):
            print(f"   {i:2d}. {col}")
        print("="*60 + "\n")
        
        # crime를 save 폴더에 csv 파일로 저장 (자치구 컬럼 추가 및 컬럼 순서 정렬)
        # save 폴더 경로 설정 (sname이 없으면 자동으로 현재 save 폴더 사용)
        if self.data.sname and str(self.data.sname).strip():
            save_path = Path(self.data.sname)
        else:
            # save 폴더 자동 설정: 현재 파일이 있는 save 폴더 사용
            # seoul_service.py가 있는 폴더가 save 폴더
            save_path = Path(__file__).parent
        
        save_path.mkdir(parents=True, exist_ok=True)
        crime_save_df = crime_df.copy()
        
        # 자치구 컬럼 추가 (관서명을 기반으로 매핑)
        if '관서명' in crime_save_df.columns:
            crime_save_df['자치구'] = crime_save_df['관서명'].map(self.POLICE_STATION_TO_GU)
            
            # 매핑되지 않은 관서명 확인
            unmapped = crime_save_df[crime_save_df['자치구'].isna()]['관서명'].unique()
            if len(unmapped) > 0:
                print(f"⚠️  매핑되지 않은 관서명: {list(unmapped)}")
        
        # 같은 자치구는 하나로 합치기 (자치구별 집계)
        print(f"\n[범죄 데이터 저장] 자치구별 집계 중...")
        print(f"   원본 범죄 데이터: {len(crime_save_df)} 행 (경찰서별)")
        
        # 숫자 컬럼만 선택 (자치구, 관서명, 구 제외)
        numeric_cols = [col for col in crime_save_df.columns if col not in ['자치구', '관서명', '구']]
        
        # 숫자 문자열에서 콤마 제거 및 숫자 변환
        for col in numeric_cols:
            if crime_save_df[col].dtype == 'object':
                crime_save_df[col] = crime_save_df[col].astype(str).str.replace(',', '').str.replace('"', '')
                crime_save_df[col] = pd.to_numeric(crime_save_df[col], errors='coerce')
        
        # 자치구별로 집계 (합계) - 관서명은 제거하고 자치구만 남김
        crime_save_df = crime_save_df.groupby('자치구')[numeric_cols].sum().reset_index()
        print(f"   ✅ 집계 완료: {len(crime_save_df)} 행 (자치구별)")
        print(f"   집계된 자치구: {list(crime_save_df['자치구'].values)}")
        
        # 컬럼 순서 정렬: 자치구, 나머지 컬럼들
        # 순서: 자치구, 살인 발생, 살인 검거, 강도 발생, 강도 검거, 강간 발생, 강간 검거, 절도 발생, 절도 검거, 폭력 발생, 폭력 검거
        original_column_order = [
            '자치구',
            '살인 발생', '살인 검거', 
            '강도 발생', '강도 검거', 
            '강간 발생', '강간 검거', 
            '절도 발생', '절도 검거', 
            '폭력 발생', '폭력 검거'
        ]
        # 원본 순서에 있는 컬럼만 선택하고 순서대로 정렬
        existing_cols = [col for col in original_column_order if col in crime_save_df.columns]
        # 원본 순서에 없는 컬럼이 있다면 뒤에 추가
        remaining_cols = [col for col in crime_save_df.columns if col not in original_column_order]
        final_column_order = existing_cols + remaining_cols
        crime_save_df = crime_save_df[final_column_order]
        
        crime_file_path = save_path / "crime.csv"
        try:
            crime_save_df.to_csv(crime_file_path, index=False, encoding='utf-8-sig')
            print(f"✅ 범죄 데이터 저장 완료: {crime_file_path}")
            print(f"   - 저장 경로: {save_path}")
            print(f"   - 저장된 행 수: {len(crime_save_df)}")
            print(f"   - 저장된 컬럼 수: {len(crime_save_df.columns)}")
            print(f"   - 컬럼 순서: {', '.join(crime_save_df.columns.tolist())}")
            # 파일이 실제로 생성되었는지 확인
            if crime_file_path.exists():
                print(f"   ✅ 파일 생성 확인됨: {crime_file_path}")
            else:
                print(f"   ❌ 파일 생성 실패: {crime_file_path}")
        except Exception as e:
            print(f"❌ 파일 저장 중 오류 발생: {e}")
            import traceback
            traceback.print_exc()
        
        # 최종 머지된 데이터를 save 폴더에 csv 파일로 저장 (자치구별로 합쳐진 데이터)
        print(f"\n[최종 머지 데이터 저장] 자치구별 집계 및 저장 중...")
        
        # final_merged_df 복사
        merged_save_df = final_merged_df.copy()
        
        # 자치구 컬럼이 있는지 확인
        if '자치구' in merged_save_df.columns:
            # 숫자 컬럼만 선택 (자치구 제외)
            merged_numeric_cols = [col for col in merged_save_df.columns if col != '자치구']
            
            # 숫자 컬럼을 숫자 타입으로 변환 (이미 숫자일 수 있지만 확실하게)
            for col in merged_numeric_cols:
                if merged_save_df[col].dtype == 'object':
                    merged_save_df[col] = merged_save_df[col].astype(str).str.replace(',', '').str.replace('"', '')
                    merged_save_df[col] = pd.to_numeric(merged_save_df[col], errors='coerce')
            
            # 자치구별로 집계 (같은 자치구가 여러 행일 경우 합치기)
            print(f"   저장 전 데이터: {len(merged_save_df)} 행")
            merged_save_df = merged_save_df.groupby('자치구')[merged_numeric_cols].sum().reset_index()
            print(f"   ✅ 집계 완료: {len(merged_save_df)} 행 (자치구별)")
            
            # 자치구를 첫 번째 컬럼으로 정렬
            merged_column_order = ['자치구'] + [col for col in merged_save_df.columns if col != '자치구']
            merged_save_df = merged_save_df[merged_column_order]
        else:
            print(f"   ⚠️  '자치구' 컬럼이 없어 집계하지 않음")
        
        merged_file_path = save_path / "merged_data.csv"
        try:
            merged_save_df.to_csv(merged_file_path, index=False, encoding='utf-8-sig')
            print(f"✅ 최종 머지 데이터 저장 완료: {merged_file_path}")
            print(f"   - 저장 경로: {save_path}")
            print(f"   - 저장된 행 수: {len(merged_save_df)}")
            print(f"   - 저장된 컬럼 수: {len(merged_save_df.columns)}")
            print(f"   - 컬럼: {', '.join(merged_save_df.columns.tolist())}")
            # 파일이 실제로 생성되었는지 확인
            if merged_file_path.exists():
                print(f"   ✅ 파일 생성 확인됨: {merged_file_path}")
            else:
                print(f"   ❌ 파일 생성 실패: {merged_file_path}")
        except Exception as e:
            print(f"❌ 최종 머지 데이터 저장 중 오류 발생: {e}")
            import traceback
            traceback.print_exc()
        
        return cctv_df, crime_df, pop_df, final_merged_df

    def preprocess_to_dict(self) -> dict:
        """
        데이터 전처리 및 머지를 딕셔너리 형식으로 반환 (포스트맨용)
        
        Returns:
        --------
        dict: 전처리된 데이터 정보를 딕셔너리로 반환
        """
        from pathlib import Path
        
        # 원본 데이터 먼저 로드 (드롭된 내용 추적용)
        data_dir = Path(self.data.dname)
        original_pop = pd.read_csv(data_dir / "pop.csv", encoding='utf-8')
        original_cctv = pd.read_csv(data_dir / "cctv.csv", encoding='utf-8')
        original_crime = pd.read_csv(data_dir / "crime.csv", encoding='utf-8')
        
        # 전처리 실행
        cctv, crime, pop, cctv_pop = self.preprocess()
        
        # 드롭된 컬럼 추적
        pop_dropped_columns = [col for col in original_pop.columns if col not in pop.columns]
        # CCTV에서 드롭된 컬럼: '2013년도 이전', '2014년', '2015년', '2016년'
        cctv_dropped_columns = ['2013년도 이전', '2014년', '2015년', '2016년']
        
        # 드롭된 행 추적 (pop 데이터)
        pop_dropped_rows_count = len(original_pop) - len(pop)
        
        # 머지 후 드롭된 컬럼 (기관명 → 자치구 변경, 구 컬럼 제거)
        merged_dropped_columns = []
        if '기관명' in cctv.columns and '자치구' in cctv_pop.columns:
            merged_dropped_columns.append('기관명 (→ 자치구로 변경)')
        if '구' in cctv_pop.columns:
            merged_dropped_columns.append('구 (자치구와 동일하여 제거)')
        
        # crime.csv 파일 저장 경로 확인
        save_path = Path(__file__).parent if not (self.data.sname and str(self.data.sname).strip()) else Path(self.data.sname)
        crime_file_path = save_path / "crime.csv"
        crime_file_exists = crime_file_path.exists()
        
        return {
            "status": "success",
            "cctv_rows": len(cctv),
            "cctv_columns": cctv.columns.tolist(),
            "cctv_original_columns": original_cctv.columns.tolist(),
            "cctv_dropped_columns": cctv_dropped_columns,
            "cctv_changes": [
                f"컬럼 드롭: {len(cctv_dropped_columns)}개 컬럼 제거 ({', '.join(cctv_dropped_columns)})",
                "'기관명' 컬럼에서 따옴표(\") 제거"
            ],
            "crime_rows": len(crime),
            "crime_columns": crime.columns.tolist(),
            "crime_original_columns": original_crime.columns.tolist(),
            "crime_changes": ["경찰서별 데이터 → 자치구별 집계 (groupby)", "숫자 문자열에서 콤마 및 따옴표 제거"],
            "crime_saved": {
                "file_path": str(crime_file_path),
                "exists": crime_file_exists,
                "save_directory": str(save_path)
            },
            "pop_rows": len(pop),
            "pop_columns": pop.columns.tolist(),
            "pop_original_columns": original_pop.columns.tolist(),
            "pop_dropped_columns": pop_dropped_columns,
            "pop_dropped_rows": pop_dropped_rows_count,
            "pop_changes": [
                f"컬럼 드롭: {len(pop_dropped_columns)}개 컬럼 제거 (자치구, 인구만 남김)",
                f"행 드롭: 인덱스 1, 2, 3 행 제거 및 빈 행, '합계' 행 제거 (총 {pop_dropped_rows_count}개 행 제거)"
            ],
            "cctv_pop_rows": len(cctv_pop),
            "cctv_pop_columns": cctv_pop.columns.tolist(),
            "cctv_pop_dropped_columns": merged_dropped_columns,
            "cctv_pop_changes": [
                "'기관명' → '자치구'로 컬럼명 변경",
                "'구' 컬럼 제거 (자치구와 동일한 값)"
            ],
            "cctv_preview": cctv.head(3).to_dict(orient='records'),
            "crime_preview": crime.head(3).to_dict(orient='records'),
            "pop_preview": pop.head(3).to_dict(orient='records'),
            "cctv_pop_preview": cctv_pop.head(3).to_dict(orient='records'),
            "message": "데이터 전처리 및 머지가 완료되었습니다"
        }
