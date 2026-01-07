import os
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from app.daily_emotion.daily_emotion_dataset import DataSets


# Emotion 라벨 정의
# 0: 중립 (Neutral)
# 1: 긍정 (Positive) 
# 2: 부정 (Negative)
EMOTION_LABELS = {
    0: "중립",
    1: "긍정",
    2: "부정"
}


class DailyEmotionMethod(object): 

    def __init__(self):
        # 데이터셋 객체 생성
        self.dataset = DataSets()
        self.dataset.fname = "효진이.csv"
        self.dataset.dname = os.path.join(os.path.dirname(__file__), "효진이.csv")
        self.dataset.id = "id"
        self.dataset.localdate = "localdate"
        self.dataset.title = "title"
        self.dataset.content = "content"
        self.dataset.userId = "userId"
        self.dataset.emotion = "emotion"  # label (0: 중립, 1: 긍정, 2: 부정)
        
        # ML 모델 관련 변수
        self.vectorizer = None
        self.model = None
        self.accuracy = None
        self.is_trained = False


    def new_model(self):
        # 효진이.csv 파일을 읽어와서 데이터프레임 작성
        try:
            if os.path.exists(self.dataset.dname):
                df = pd.read_csv(self.dataset.dname)
                # 빈 행 제거
                df = df.dropna(subset=['id', 'emotion'], how='all')
                # 빈 행이 있는 경우 제거
                df = df[df['id'].notna() & df['emotion'].notna()]
                self.dataset.data = df
                return df
            else:
                raise FileNotFoundError(f"파일을 찾을 수 없습니다: {self.dataset.dname}")
        except Exception as e:
            print(f"데이터 로드 실패: {str(e)}")
            raise


    def create_train(self):
        # emotion 값을 제거한 데이터프레임 작성 (학습용 특성 데이터)
        try:
            if self.dataset.data is None:
                self.new_model()
            
            # emotion(라벨)과 id를 제외한 특성 데이터
            train_df = self.dataset.data.drop(columns=[self.dataset.emotion, self.dataset.id], errors='ignore')
            return train_df
        except Exception as e:
            print(f"학습 데이터 생성 실패: {str(e)}")
            raise


    def create_label(self):
        # emotion 값만 가지는 답안지 데이터프레임 작성 (라벨 데이터)
        # 라벨: 0(중립), 1(긍정), 2(부정)
        try:
            if self.dataset.data is None:
                self.new_model()
            
            # emotion 라벨만 추출
            label_df = self.dataset.data[[self.dataset.emotion]].copy()
            
            # 라벨 분포 확인 (ML 학습 전 확인용)
            label_counts = label_df[self.dataset.emotion].value_counts().sort_index()
            print("\n[Emotion Label Distribution]")
            for label, count in label_counts.items():
                label_name = EMOTION_LABELS.get(label, f"Unknown({label})")
                print(f"  {label} ({label_name}): {count}개")
            
            return label_df
        except Exception as e:
            print(f"라벨 데이터 생성 실패: {str(e)}")
            raise
    
    def preprocess(self):
        """데이터 전처리 - 텍스트 결합 및 정제"""
        try:
            if self.dataset.data is None:
                self.new_model()
            
            df = self.dataset.data.copy()
            
            # title과 content 결합 (텍스트 분류를 위해)
            df['text'] = df['title'].fillna('') + ' ' + df['content'].fillna('')
            df['text'] = df['text'].str.strip()
            
            # 빈 텍스트 제거
            df = df[df['text'].str.len() > 0]
            
            self.dataset.data = df
            print(f"[전처리 완료] 총 {len(df)}개 데이터")
            return df
        except Exception as e:
            print(f"전처리 실패: {str(e)}")
            raise
    
    def modeling(self):
        """모델 초기화"""
        try:
            # TF-IDF 벡터화기 초기화
            self.vectorizer = TfidfVectorizer(
                max_features=1000,
                ngram_range=(1, 2),
                min_df=2,
                max_df=0.95
            )
            
            # RandomForest 분류기 초기화
            self.model = RandomForestClassifier(
                n_estimators=100,
                random_state=42,
                n_jobs=-1
            )
            
            print("[모델링 완료] TF-IDF + RandomForest 모델 초기화")
            return self.model
        except Exception as e:
            print(f"모델링 실패: {str(e)}")
            raise
    
    def learning(self):
        """모델 학습"""
        try:
            if self.dataset.data is None:
                self.preprocess()
            
            if self.model is None:
                self.modeling()
            
            # 학습 데이터 준비
            X = self.dataset.data['text'].values
            y = self.dataset.data[self.dataset.emotion].values.astype(int)
            
            # 텍스트 벡터화
            X_vectorized = self.vectorizer.fit_transform(X)
            
            # 학습/테스트 데이터 분할 (80:20)
            X_train, X_test, y_train, y_test = train_test_split(
                X_vectorized, y, test_size=0.2, random_state=42, stratify=y
            )
            
            # 모델 학습
            print(f"[학습 시작] 학습 데이터: {X_train.shape[0]}개, 테스트 데이터: {X_test.shape[0]}개")
            self.model.fit(X_train, y_train)
            
            # 학습 데이터로 정확도 계산 (참고용)
            train_pred = self.model.predict(X_train)
            train_accuracy = accuracy_score(y_train, train_pred)
            
            # 테스트 데이터로 정확도 계산
            test_pred = self.model.predict(X_test)
            test_accuracy = accuracy_score(y_test, test_pred)
            
            self.accuracy = {
                'train_accuracy': round(train_accuracy * 100, 2),
                'test_accuracy': round(test_accuracy * 100, 2),
                'train_count': len(y_train),
                'test_count': len(y_test)
            }
            
            self.is_trained = True
            print(f"[학습 완료] 학습 정확도: {self.accuracy['train_accuracy']}%, 테스트 정확도: {self.accuracy['test_accuracy']}%")
            
            return self.accuracy
        except Exception as e:
            print(f"학습 실패: {str(e)}")
            raise
    
    def evaluate(self):
        """모델 평가 및 상세 메트릭 계산"""
        try:
            if not self.is_trained:
                print("[경고] 모델이 학습되지 않았습니다. 먼저 learning()을 실행하세요.")
                return None
            
            if self.dataset.data is None:
                self.preprocess()
            
            # 전체 데이터로 평가
            X = self.dataset.data['text'].values
            y = self.dataset.data[self.dataset.emotion].values.astype(int)
            
            X_vectorized = self.vectorizer.transform(X)
            y_pred = self.model.predict(X_vectorized)
            
            # 정확도 계산
            accuracy = accuracy_score(y, y_pred)
            
            # 분류 리포트
            report = classification_report(y, y_pred, target_names=['중립', '긍정', '부정'], output_dict=True)
            
            # 혼동 행렬
            cm = confusion_matrix(y, y_pred)
            
            evaluation_result = {
                'accuracy': round(accuracy * 100, 2),
                'classification_report': report,
                'confusion_matrix': cm.tolist(),
                'total_samples': len(y)
            }
            
            print(f"[평가 완료] 전체 정확도: {evaluation_result['accuracy']}%")
            print(f"\n[분류 리포트]")
            print(classification_report(y, y_pred, target_names=['중립', '긍정', '부정']))
            
            return evaluation_result
        except Exception as e:
            print(f"평가 실패: {str(e)}")
            raise
    
    def get_accuracy(self):
        """학습된 모델의 정확도 반환"""
        if self.accuracy is None:
            return None
        return self.accuracy
    
    def predict(self, text: str):
        """
        텍스트 입력으로 감정 예측
        
        Args:
            text: 예측할 일기 텍스트 (title + content 결합 형태 권장)
            
        Returns:
            예측 결과 딕셔너리
            {
                'predicted_emotion': int,  # 예측된 감정 라벨 (0, 1, 2)
                'emotion_name': str,       # 감정 이름 (중립, 긍정, 부정)
                'probabilities': dict      # 각 감정별 확률
            }
        """
        try:
            if not self.is_trained or self.model is None or self.vectorizer is None:
                raise ValueError("모델이 학습되지 않았습니다. 먼저 learning()을 실행하세요.")
            
            # 텍스트 전처리
            if not text or len(text.strip()) == 0:
                raise ValueError("예측할 텍스트가 비어있습니다.")
            
            # 텍스트 벡터화
            text_vectorized = self.vectorizer.transform([text])
            
            # 예측
            predicted_label = self.model.predict(text_vectorized)[0]
            
            # 확률 계산
            probabilities = self.model.predict_proba(text_vectorized)[0]
            
            # 결과 구성
            result = {
                'predicted_emotion': int(predicted_label),
                'emotion_name': EMOTION_LABELS.get(predicted_label, f"Unknown({predicted_label})"),
                'probabilities': {
                    EMOTION_LABELS.get(i, f"Unknown({i})"): round(float(prob) * 100, 2)
                    for i, prob in enumerate(probabilities)
                }
            }
            
            print(f"[예측 완료] 입력 텍스트: {text[:50]}...")
            print(f"[예측 결과] 감정: {result['emotion_name']} (라벨: {result['predicted_emotion']})")
            print(f"[확률] {result['probabilities']}")
            
            return result
        except Exception as e:
            print(f"예측 실패: {str(e)}")
            raise

