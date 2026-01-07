"""
타이타닉 데이터 서비스
판다스, 넘파이, 사이킷런을 사용한 데이터 처리 및 머신러닝 서비스
"""
import sys
from pathlib import Path
from typing import List, Dict, Optional, Any, ParamSpecArgs
import pandas as pd
import numpy as np
import pickle
import os
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import GaussianNB
from sklearn.tree import DecisionTreeClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.svm import SVC
from app.titanic.titanic_dataset import TitanicDataSet

# 공통 모듈 경로 추가
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

try:
    from common.utils import setup_logging
    logger = setup_logging("titanic_service")
except ImportError:
    import logging
    logger = logging.getLogger("titanic_service")

from app.titanic.titanic_method import TitanicMethod


class TitanicService:
    """타이타닉 데이터 처리 및 머신러닝 서비스"""
    
    def __init__(self):
        self.processed_data = None
        self.X_train = None
        self.X_test = None
        self.y_train = None
        self.y_test = None
        self.y_train_full = None  # Survived 라벨 저장
        self.models = {}
        self.evaluation_results = {}


    def preprocess(self) -> Dict[str, Any]:
        """데이터 전처리 및 정보 반환"""
        def clean_for_json(obj):
            """DataFrame의 NaN, inf 값을 None으로 변환하고 boolean을 int로 변환하여 JSON 직렬화 가능하게 함"""
            if isinstance(obj, bool):
                return 1 if obj else 0
            elif isinstance(obj, (np.integer, np.floating)):
                if np.isnan(obj) or np.isinf(obj):
                    return None
                return float(obj) if isinstance(obj, np.floating) else int(obj)
            elif isinstance(obj, dict):
                return {k: clean_for_json(v) for k, v in obj.items()}
            elif isinstance(obj, (list, tuple)):
                return [clean_for_json(item) for item in obj]
            elif isinstance(obj, pd.Series):
                return clean_for_json(obj.to_dict())
            elif isinstance(obj, pd.DataFrame):
                return clean_for_json(obj.to_dict('records'))
            return obj
        
        try:
            logger.info("\n" + "="*80)
            logger.info("전처리 시작")
            logger.info("="*80)
            the_method = TitanicMethod()
            
            # CSV 파일 경로 설정
            base_path = Path(__file__).parent
            train_csv_path = base_path / 'train.csv'
            test_csv_path = base_path / 'test.csv'
            
            # 파일 존재 확인
            if not train_csv_path.exists():
                raise FileNotFoundError(f"Train CSV 파일을 찾을 수 없습니다: {train_csv_path}")
            if not test_csv_path.exists():
                raise FileNotFoundError(f"Test CSV 파일을 찾을 수 없습니다: {test_csv_path}")
            
            # Train 데이터 로드
            df_train = the_method.read_csv(str(train_csv_path))
            
            # Test 데이터 로드
            df_test = the_method.read_csv(str(test_csv_path))
            
            # 원본 데이터 요약 정보 출력
            if 'Survived' in df_train.columns:
                total_passengers = len(df_train)
                survived_count = int(df_train['Survived'].sum())
                death_count = total_passengers - survived_count
                survived_rate = (survived_count / total_passengers * 100) if total_passengers > 0 else 0
                death_rate = (death_count / total_passengers * 100) if total_passengers > 0 else 0
                
                logger.info("\n" + "="*80)
                logger.info("타이타닉 데이터셋 전체 요약")
                logger.info("="*80)
                logger.info(f"전체 승객 수: {total_passengers}명")
                logger.info(f"생존자: {survived_count}명 ({survived_rate:.2f}%)")
                logger.info(f"사망자: {death_count}명 ({death_rate:.2f}%)")
                logger.info(f"컬럼 수: {len(df_train.columns)}개")
                logger.info(f"컬럼 목록: {', '.join(df_train.columns.tolist())}")
            
            # DataFrame 생성
            this_train = the_method.create_df(df_train, 'Survived')
            if 'Survived' in df_test.columns:
                this_test = the_method.create_df(df_test, 'Survived')
            else:
                this_test = df_test.copy()
            
            # this 객체 초기화
            this = TitanicDataSet()
            this.train = this_train
            this.test = this_test
            
            # 전처리 파이프라인 (고정 로직)
            drop_features = ['SibSp', 'Parch', 'Cabin', 'Ticket']
            this = the_method.drop_features(this, *drop_features)
            this = the_method.pclass_ordinal(this)
            this = the_method.fare_ratio(this)
            this = the_method.embarked_nominal(this)
            this = the_method.gender_nominal(this)
            this = the_method.age_ratio(this)
            this = the_method.title_nominal(this)
            drop_name = ['Name']
            this = the_method.drop_features(this, *drop_name)
            
            # boolean과 문자열 컬럼을 int로 변환하고 원본 문자열 컬럼 제거
            def convert_to_int(df: pd.DataFrame) -> pd.DataFrame:
                """boolean과 문자열 컬럼을 int로 변환하고 원본 문자열 컬럼 제거"""
                df = df.copy()
                
                # 제거할 원본 문자열 컬럼 목록
                cols_to_drop = []
                converted_cols = []
                
                # boolean 컬럼들을 int로 변환
                for col in df.columns:
                    if df[col].dtype == bool or df[col].dtype == 'bool':
                        df[col] = df[col].astype(int)
                        converted_cols.append(f"{col} (bool->int)")
                    elif df[col].dtype == object or pd.api.types.is_categorical_dtype(df[col]):
                        # 문자열 컬럼 처리 (object 타입 또는 categorical 타입)
                        if col == 'gender' or col == 'Sex':
                            cols_to_drop.append(col)
                        elif col == 'Age_band':
                            cols_to_drop.append(col)
                        elif col == 'Embarked':
                            cols_to_drop.append(col)
                        elif col == 'Title':
                            cols_to_drop.append(col)
                        elif col not in ['PassengerId', 'Pclass', 'Age', 'Fare']:  # 기본 숫자 컬럼 제외
                            # 기타 문자열 컬럼도 제거
                            cols_to_drop.append(col)
                
                # 원본 문자열 컬럼 제거
                if cols_to_drop:
                    df = df.drop(columns=[col for col in cols_to_drop if col in df.columns])
                
                return df
            
            # Train과 Test 데이터를 int로 변환
            this.train = convert_to_int(this.train)
            this.test = convert_to_int(this.test)
            
            # 최종 null 개수 계산
            train_null_count = int(this.train.isnull().sum().sum())
            test_null_count = int(this.test.isnull().sum().sum())
            
            # Train 정보 출력
            logger.info(" 😎😎😎트레인 전처리 완료")
            logger.info(f"\n1. Train 의 type \n {type(this.train)}")
            logger.info(f"\n2. Train 의 column \n {this.train.columns}")
            logger.info(f"\n3. Train 의 상위 5개 행\n {this.train.head(5)}")
            logger.info(f"\n4. Train 의 null 의 갯수\n {train_null_count}개")
            
            # Test 정보 출력
            logger.info("🤢🤢🤢 테스트 전처리 완료")
            logger.info(f"\n1. Test 의 type \n {type(this.test)}")
            logger.info(f"\n2. Test 의 column \n {this.test.columns}")
            logger.info(f"\n3. Test 의 상위 5개 행\n {this.test.head(5)}")
            logger.info(f"\n4. Test 의 null 의 갯수\n {test_null_count}개")
            
            # 결과 반환
            result = {
                "train": {
                    "type": str(type(this.train)),
                    "columns": this.train.columns.tolist(),
                    "head": clean_for_json(this.train.head(5).to_dict('records')),
                    "null_count": train_null_count
                },
                "test": {
                    "type": str(type(this.test)),
                    "columns": this.test.columns.tolist(),
                    "head": clean_for_json(this.test.head(5).to_dict('records')),
                    "null_count": test_null_count
                }
            }
            
            logger.info("\n" + "="*80)
            logger.info("전처리 완료")
            logger.info("="*80 + "\n")
            
            # 전처리된 데이터 저장 (모델링/학습/평가용)
            self.processed_data = this
            if 'Survived' in df_train.columns:
                self.y_train_full = df_train['Survived']
            
            return result
            
        except FileNotFoundError as e:
            logger.error(f"파일을 찾을 수 없음: {e}")
            raise
        except Exception as e:
            logger.error(f"전처리 중 에러 발생: {type(e).__name__}: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            raise

    def modeling(self):
        logger.info("😎😎 모델링 시작")
        
        if self.processed_data is None:
            raise ValueError("전처리된 데이터가 없습니다. preprocess()를 먼저 실행하세요.")
        
        try:
            # 모델 생성 (모든 모델)
            self.models = {
                'DecisionTree': DecisionTreeClassifier(random_state=42),
                'RandomForest': RandomForestClassifier(n_estimators=13, random_state=42),
                'NaiveBayes': GaussianNB(),
                'KNN': KNeighborsClassifier(n_neighbors=13),
                'SVM': SVC(random_state=42)
            }
            logger.info(f"모델 생성 완료: {list(self.models.keys())}")
            logger.info("😎😎 모델링 완료")
        except Exception as e:
            logger.error(f"모델 생성 실패: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            raise

    def learning(self):
        logger.info("😎😎 학습 시작")
        
        if self.processed_data is None:
            raise ValueError("전처리된 데이터가 없습니다. preprocess()를 먼저 실행하세요.")
        
        if not self.models:
            raise ValueError("모델이 없습니다. modeling()을 먼저 실행하세요.")
        
        # 전처리된 데이터 준비
        X = self.processed_data.train.copy()
        
        # Survived 라벨 확인
        if self.y_train_full is None:
            raise ValueError("Survived 라벨이 없습니다. preprocess()를 먼저 실행하세요.")
        
        y = self.y_train_full.copy()
        
        # 문자열 컬럼 확인 및 제거 (모델 학습을 위해)
        object_cols = [col for col in X.columns if X[col].dtype == object]
        if object_cols:
            logger.warning(f"문자열 컬럼 발견 및 제거: {object_cols}")
            X = X.drop(columns=object_cols)
        
        # 데이터 크기 확인
        logger.info(f"전체 데이터 크기: X={X.shape}, y={y.shape}")
        logger.info(f"Survived 라벨 분포: 생존={int(y.sum())}명, 사망={int((y == 0).sum())}명")
        logger.info(f"피처 컬럼: {list(X.columns)}")
        
        # Train/Validation 분할
        self.X_train, self.X_test, self.y_train, self.y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        logger.info(f"훈련 데이터 크기: {self.X_train.shape}, 라벨 크기: {self.y_train.shape}")
        logger.info(f"검증 데이터 크기: {self.X_test.shape}, 라벨 크기: {self.y_test.shape}")
        
        # 모델 저장 디렉토리 생성
        models_dir = Path(__file__).parent / 'models'
        models_dir.mkdir(exist_ok=True)
        
        # 각 모델 학습 및 저장
        for name, model in self.models.items():
            logger.info(f"{name} 모델 학습 중...")
            try:
                model.fit(self.X_train, self.y_train)
                logger.info(f"{name} 모델 학습 완료")
                
                # 모델 저장
                model_path = models_dir / f'{name}_model.pkl'
                with open(model_path, 'wb') as f:
                    pickle.dump(model, f)
                logger.info(f"{name} 모델 저장 완료: {model_path}")
            except Exception as e:
                logger.error(f"{name} 모델 학습 실패: {str(e)}")
                import traceback
                logger.error(traceback.format_exc())
                raise
        
        logger.info("😎😎 학습 완료")

    def evaluate(self):
        logger.info("😎😎 평가 시작")
        
        if self.processed_data is None:
            raise ValueError("전처리된 데이터가 없습니다. preprocess()를 먼저 실행하세요.")
        
        if self.y_train_full is None:
            raise ValueError("Survived 라벨이 없습니다. preprocess()를 먼저 실행하세요.")
        
        # 전처리된 데이터 준비
        X = self.processed_data.train.copy()
        y = self.y_train_full.copy()
        
        # 문자열 컬럼 확인 및 제거 (모델 학습을 위해)
        object_cols = [col for col in X.columns if X[col].dtype == object or pd.api.types.is_categorical_dtype(X[col])]
        if object_cols:
            logger.warning(f"문자열 컬럼 발견 및 제거: {object_cols}")
            X = X.drop(columns=object_cols)
        
        the_method = TitanicMethod()
        self.evaluation_results = {}
        
        # K-Fold 교차 검증으로 각 모델 평가
        try:
            # 결정트리
            accuracy_dtree = the_method.accuracy_by_dtree(X, y)
            self.evaluation_results['DecisionTree'] = accuracy_dtree / 100
            logger.info(f'결정트리 활용한 검증 정확도 {accuracy_dtree}%')
            print(f'결정트리 활용한 검증 정확도 {accuracy_dtree}%')
        except Exception as e:
            logger.error(f"결정트리 평가 실패: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
        
        try:
            # 랜덤포레스트
            accuracy_rforest = the_method.accuracy_by_rforest(X, y)
            self.evaluation_results['RandomForest'] = accuracy_rforest / 100
            logger.info(f'랜덤포레스트 활용한 검증 정확도 {accuracy_rforest}%')
            print(f'랜덤포레스트 활용한 검증 정확도 {accuracy_rforest}%')
        except Exception as e:
            logger.error(f"랜덤포레스트 평가 실패: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
        
        try:
            # 나이브베이즈
            accuracy_nb = the_method.accuracy_by_nb(X, y)
            self.evaluation_results['NaiveBayes'] = accuracy_nb / 100
            logger.info(f'나이브베이즈 활용한 검증 정확도 {accuracy_nb}%')
            print(f'나이브베이즈 활용한 검증 정확도 {accuracy_nb}%')
        except Exception as e:
            logger.error(f"나이브베이즈 평가 실패: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
        
        try:
            # KNN
            accuracy_knn = the_method.accuracy_by_knn(X, y)
            self.evaluation_results['KNN'] = accuracy_knn / 100
            logger.info(f'KNN 활용한 검증 정확도 {accuracy_knn}%')
            print(f'KNN 활용한 검증 정확도 {accuracy_knn}%')
        except Exception as e:
            logger.error(f"KNN 평가 실패: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
        
        try:
            # SVM
            accuracy_svm = the_method.accuracy_by_svm(X, y)
            self.evaluation_results['SVM'] = accuracy_svm / 100
            logger.info(f'SVM 활용한 검증 정확도 {accuracy_svm}%')
            print(f'SVM 활용한 검증 정확도 {accuracy_svm}%')
        except Exception as e:
            logger.error(f"SVM 평가 실패: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
        
        logger.info("😎😎 평가 완료")
        return self.evaluation_results


    def submit(self):
        """Kaggle 제출용 모델 생성 및 저장"""
        logger.info("😎😎 제출 시작")
        
        if self.processed_data is None:
            raise ValueError("전처리된 데이터가 없습니다. preprocess()를 먼저 실행하세요.")
        
        if self.y_train_full is None:
            raise ValueError("Survived 라벨이 없습니다. preprocess()를 먼저 실행하세요.")
        
        # 전체 train 데이터 준비
        X_train_full = self.processed_data.train.copy()
        y_train_full = self.y_train_full.copy()
        
        # 문자열 컬럼 확인 및 제거
        object_cols = [col for col in X_train_full.columns if X_train_full[col].dtype == object or pd.api.types.is_categorical_dtype(X_train_full[col])]
        if object_cols:
            logger.warning(f"문자열 컬럼 발견 및 제거: {object_cols}")
            X_train_full = X_train_full.drop(columns=object_cols)
        
        # test 데이터 준비
        X_test = self.processed_data.test.copy()
        object_cols_test = [col for col in X_test.columns if X_test[col].dtype == object or pd.api.types.is_categorical_dtype(X_test[col])]
        if object_cols_test:
            X_test = X_test.drop(columns=object_cols_test)
        
        # train과 test의 컬럼을 동일하게 맞추기
        common_cols = [col for col in X_train_full.columns if col in X_test.columns]
        X_train_full = X_train_full[common_cols]
        X_test = X_test[common_cols]
        
        logger.info(f"전체 학습 데이터 크기: X={X_train_full.shape}, y={y_train_full.shape}")
        logger.info(f"테스트 데이터 크기: X={X_test.shape}")
        logger.info(f"피처 컬럼: {list(X_train_full.columns)}")
        
        # 모델 저장 디렉토리 생성
        models_dir = Path(__file__).parent / 'models'
        models_dir.mkdir(exist_ok=True)
        
        # 모든 모델 생성 및 학습
        kaggle_models = {
            'DecisionTree': DecisionTreeClassifier(random_state=42),
            'RandomForest': RandomForestClassifier(n_estimators=13, random_state=42),
            'NaiveBayes': GaussianNB(),
            'KNN': KNeighborsClassifier(n_neighbors=13),
            'SVM': SVC(random_state=42)
        }
        
        results = {}
        
        # 각 모델별로 학습, 저장, 예측 수행
        for model_name, model in kaggle_models.items():
            try:
                logger.info(f"Kaggle 제출용 {model_name} 모델 학습 중...")
                model.fit(X_train_full, y_train_full)
                logger.info(f"{model_name} 모델 학습 완료")
                
                # 모델 저장
                kaggle_model_path = models_dir / f'{model_name}_kaggle_model.pkl'
                with open(kaggle_model_path, 'wb') as f:
                    pickle.dump(model, f)
                logger.info(f"{model_name} Kaggle 제출용 모델 저장 완료: {kaggle_model_path}")
                
                # Test 데이터에 대한 예측
                predictions = model.predict(X_test)
                logger.info(f"{model_name} 예측 완료: {len(predictions)}개 샘플")
                
                # Submission 파일 생성
                submission_path = Path(__file__).parent / f'submission_{model_name}.csv'
                submission_df = pd.DataFrame({
                    'PassengerId': self.processed_data.test['PassengerId'].values,
                    'Survived': predictions
                })
                submission_df.to_csv(submission_path, index=False)
                logger.info(f"{model_name} Submission 파일 생성 완료: {submission_path}")
                
                results[model_name] = {
                    "model_path": str(kaggle_model_path),
                    "submission_path": str(submission_path),
                    "predictions_count": len(predictions),
                    "survival_count": int(predictions.sum()),
                    "death_count": int((predictions == 0).sum())
                }
            except Exception as e:
                logger.error(f"{model_name} 모델 처리 실패: {str(e)}")
                import traceback
                logger.error(traceback.format_exc())
        
        # 기본 submission.csv는 랜덤포레스트 결과로 생성
        if 'RandomForest' in results:
            import shutil
            rf_submission = Path(__file__).parent / 'submission_RandomForest.csv'
            default_submission = Path(__file__).parent / 'submission.csv'
            if rf_submission.exists():
                shutil.copy(rf_submission, default_submission)
                logger.info(f"기본 submission.csv 생성 완료 (RandomForest 결과)")
        
        logger.info("😎😎 제출 완료")
        return {
            "models": results,
            "default_submission": "submission.csv (RandomForest 결과)"
        }