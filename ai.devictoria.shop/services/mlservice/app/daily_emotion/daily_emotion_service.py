import os
import logging
from typing import List, Optional
import pandas as pd
from icecream import ic
from app.daily_emotion.daily_emotion_model import DailyEmotion
from app.daily_emotion.daily_emotion_method import DailyEmotionMethod

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Emotion 라벨 정의
# 0: 중립 (Neutral)
# 1: 긍정 (Positive)
# 2: 부정 (Negative)
EMOTION_LABELS = {
    0: "중립",
    1: "긍정",
    2: "부정"
}


class DailyEmotionService:
    """일기 감정 데이터 서비스 클래스"""
    
    def __init__(self):
        """서비스 초기화"""
        self.data_path = os.path.join(os.path.dirname(__file__), "효진이.csv")
        self._emotions_cache: Optional[List[DailyEmotion]] = None
        self._ml_method = DailyEmotionMethod()
        self._load_data()
    
    def _load_data(self):
        """CSV 파일에서 데이터 로드"""
        try:
            if os.path.exists(self.data_path):
                logger.info(f"[DailyEmotionService] 데이터 로드 시작: {self.data_path}")
                # 여러 줄 필드를 처리하기 위해 quotechar와 escapechar 설정
                # on_bad_lines='skip'으로 잘못된 형식의 행 건너뛰기
                df = pd.read_csv(
                    self.data_path,
                    quotechar='"',
                    skipinitialspace=True,
                    on_bad_lines='skip',
                    encoding='utf-8',
                    engine='python'  # python 엔진이 복잡한 CSV를 더 잘 처리
                )
                
                # 마지막 빈 컬럼 제거 (trailing comma 때문에 생기는 빈 컬럼)
                df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
                
                # 빈 행 제거 (id나 emotion이 없는 행)
                df = df.dropna(subset=['id', 'emotion'], how='all')
                df = df[df['id'].notna() & df['emotion'].notna()]
                
                # 숫자로 변환 가능한지 확인
                df['id'] = pd.to_numeric(df['id'], errors='coerce')
                df['userId'] = pd.to_numeric(df['userId'], errors='coerce')
                df['emotion'] = pd.to_numeric(df['emotion'], errors='coerce')
                
                # 변환 실패한 행 제거
                df = df.dropna(subset=['id', 'emotion'])
                
                logger.info(f"[DailyEmotionService] CSV 파싱 완료: {len(df)}개 행")
                
                self._emotions_cache = []
                for idx, row in df.iterrows():
                    try:
                        emotion = self._dataframe_to_emotion(row)
                        self._emotions_cache.append(emotion)
                    except Exception as e:
                        logger.warning(f"[DailyEmotionService] 행 변환 실패 (ID: {row.get('id', 'unknown')}): {str(e)}")
                        continue
                
                logger.info(f"[DailyEmotionService] 데이터 로드 완료: {len(self._emotions_cache)}개")
            else:
                logger.warning(f"[DailyEmotionService] 데이터 파일을 찾을 수 없습니다: {self.data_path}")
                self._emotions_cache = []
        except Exception as e:
            logger.error(f"[DailyEmotionService] 데이터 로드 실패: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            self._emotions_cache = []
    
    def _dataframe_to_emotion(self, row: pd.Series) -> DailyEmotion:
        """
        DataFrame 행을 DailyEmotion 모델로 변환
        
        Args:
            row: pandas Series 객체
            
        Returns:
            DailyEmotion 모델 객체
        """
        try:
            return DailyEmotion(
                id=int(row['id']),
                localdate=str(row['localdate']).strip() if pd.notna(row['localdate']) else "",
                title=str(row['title']).strip() if pd.notna(row['title']) else "",
                content=str(row['content']).strip() if pd.notna(row['content']) else "",
                userId=int(row['userId']) if pd.notna(row['userId']) else 0,
                emotion=int(row['emotion']) if pd.notna(row['emotion']) else 0
            )
        except Exception as e:
            logger.error(f"[DailyEmotionService] DailyEmotion 변환 실패: {str(e)}")
            raise ValueError(f"DailyEmotion 변환 실패: {str(e)}")
    
    def get_emotion_by_id(self, emotion_id: int) -> Optional[DailyEmotion]:
        """
        일기 ID로 일기 정보 조회
        
        Args:
            emotion_id: 조회할 일기 ID
            
        Returns:
            DailyEmotion 객체 (없으면 None)
        """
        try:
            if self._emotions_cache is None:
                self._load_data()
            
            for emotion in self._emotions_cache:
                if emotion.id == emotion_id:
                    return emotion
            
            return None
        except Exception as e:
            logger.error(f"[DailyEmotionService] 일기 조회 실패 (ID: {emotion_id}): {str(e)}")
            raise
    
    def get_top_emotions(self, limit: int = 10) -> List[DailyEmotion]:
        """
        상위 N개의 일기 정보 조회
        
        Args:
            limit: 조회할 일기 수 (기본값: 10)
            
        Returns:
            DailyEmotion 객체 리스트
        """
        try:
            if self._emotions_cache is None:
                self._load_data()
            
            return self._emotions_cache[:limit] if self._emotions_cache else []
        except Exception as e:
            logger.error(f"[DailyEmotionService] 상위 일기 조회 실패: {str(e)}")
            raise
    
    def get_emotions_by_user_id(self, user_id: int) -> List[DailyEmotion]:
        """
        사용자 ID로 일기 목록 조회
        
        Args:
            user_id: 조회할 사용자 ID
            
        Returns:
            DailyEmotion 객체 리스트
        """
        try:
            if self._emotions_cache is None:
                self._load_data()
            
            return [emotion for emotion in self._emotions_cache if emotion.userId == user_id]
        except Exception as e:
            logger.error(f"[DailyEmotionService] 사용자별 일기 조회 실패 (UserID: {user_id}): {str(e)}")
            raise
    
    def get_emotions_by_emotion_label(self, emotion_label: int) -> List[DailyEmotion]:
        """
        감정 라벨로 일기 목록 조회
        
        Args:
            emotion_label: 조회할 감정 라벨
            
        Returns:
            DailyEmotion 객체 리스트
        """
        try:
            if self._emotions_cache is None:
                self._load_data()
            
            return [emotion for emotion in self._emotions_cache if emotion.emotion == emotion_label]
        except Exception as e:
            logger.error(f"[DailyEmotionService] 감정별 일기 조회 실패 (Emotion: {emotion_label}): {str(e)}")
            raise
    
    def get_label_distribution(self) -> dict:
        """
        라벨링 분포 통계 조회 (각 라벨의 개수와 비율 %)
        
        Returns:
            라벨 분포 통계 딕셔너리
        """
        try:
            if self._emotions_cache is None:
                self._load_data()
            
            total_count = len(self._emotions_cache)
            if total_count == 0:
                return {
                    "total": 0,
                    "labels": {}
                }
            
            # 각 라벨별 개수 계산
            label_counts = {0: 0, 1: 0, 2: 0}
            for emotion in self._emotions_cache:
                label = emotion.emotion
                if label in label_counts:
                    label_counts[label] += 1
            
            # 비율 계산 및 결과 구성
            label_stats = {}
            for label, count in label_counts.items():
                percentage = round((count / total_count) * 100, 2) if total_count > 0 else 0.0
                label_stats[label] = {
                    "label": label,
                    "labelName": EMOTION_LABELS.get(label, f"Unknown({label})"),
                    "count": count,
                    "percentage": percentage
                }
            
            return {
                "total": total_count,
                "labels": label_stats
            }
        except Exception as e:
            logger.error(f"[DailyEmotionService] 라벨 분포 조회 실패: {str(e)}")
            raise

    def train_model(self):
        """ML 모델 학습 실행"""
        try:
            logger.info("[DailyEmotionService] ML 모델 학습 시작")
            self._ml_method.preprocess()
            self._ml_method.modeling()
            accuracy = self._ml_method.learning()
            logger.info(f"[DailyEmotionService] ML 모델 학습 완료: {accuracy}")
            return accuracy
        except Exception as e:
            logger.error(f"[DailyEmotionService] ML 모델 학습 실패: {str(e)}")
            raise
    
    def evaluate_model(self):
        """ML 모델 평가 실행"""
        try:
            logger.info("[DailyEmotionService] ML 모델 평가 시작")
            evaluation = self._ml_method.evaluate()
            logger.info(f"[DailyEmotionService] ML 모델 평가 완료")
            return evaluation
        except Exception as e:
            logger.error(f"[DailyEmotionService] ML 모델 평가 실패: {str(e)}")
            raise
    
    def get_model_accuracy(self):
        """학습된 모델의 정확도 조회"""
        try:
            accuracy = self._ml_method.get_accuracy()
            if accuracy is None:
                return {
                    "status": "not_trained",
                    "message": "모델이 아직 학습되지 않았습니다. /api/daily-emotion/train 엔드포인트를 호출하여 학습하세요."
                }
            return {
                "status": "trained",
                "accuracy": accuracy
            }
        except Exception as e:
            logger.error(f"[DailyEmotionService] 정확도 조회 실패: {str(e)}")
            raise

    def preprocess(self):
        ic("😎😎 전처리 시작")
        ic("😎😎 전처리 완료")

    def modeling(self):
        ic("😎😎 모델링 시작")
        ic("😎😎 모델링 완료")

    def learning(self):
        ic("😎😎 학습 시작")
        ic("😎😎 학습 완료")

    def evaluate(self):
        ic("😎😎 평가 시작")
        ic("😎😎 평가 완료")

    def submit(self):
        ic("😎😎 제출 시작")
        ic("😎😎 제출 완료")

