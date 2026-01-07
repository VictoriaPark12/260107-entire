from pathlib import Path
import pandas as pd
import numpy as np
from typing import Tuple
import sys
from sklearn.model_selection import KFold, cross_val_score
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.svm import SVC

# 공통 모듈 경로 추가
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

try:
    from common.utils import setup_logging
    logger = setup_logging("titanic_method")
except ImportError:
    import logging
    logger = logging.getLogger("titanic_method")

class TitanicMethod(object):
    
    def __init__(self):
        pass

    def read_csv(self, fname: str) -> pd.DataFrame:
        return pd.read_csv(fname)

    def create_df(self, df:pd.DataFrame, label:str) -> pd.DataFrame:
        """Survived 컬럼을 제거한 학습 데이터(특성) DataFrame 반환"""
        return df.drop(columns=[label])
    
    def create_label(self, df:pd.DataFrame, label:str) -> pd.DataFrame:
        return df[label]
    
    def drop_features(self, this, *feature: str) -> object:
        """피처를 삭제하는 메서드"""
        [i.drop(j, axis=1, inplace=True) for j in feature for i in [this.train,this.test ] ]

        # for i in [this.train, this.test]:
        #     for j in feature:
        #         i.drop(j, axis=1, inplace=True)
 
        return this
        

    
    def check_null(self, this) -> int:
        """널 값을 확인하는 메서드"""
        train_null = this.train.isnull().sum()
        test_null = this.test.isnull().sum()
        
        train_null_sum = int(train_null.sum())
        test_null_sum = int(test_null.sum())
        
        logger.info(f"  Train Null 상세:")
        for col, count in train_null.items():
            if count > 0:
                logger.info(f"    {col}: {int(count)}개")
        logger.info(f"  Train Null 총합: {train_null_sum}개")
        
        logger.info(f"  Test Null 상세:")
        for col, count in test_null.items():
            if count > 0:
                logger.info(f"    {col}: {int(count)}개")
        logger.info(f"  Test Null 총합: {test_null_sum}개")
        
        return train_null_sum + test_null_sum
        


    #nominal , ordinal, interval, ratio
    def pclass_ordinal(self, this) -> object:
        """
        Pclass: 객실 등급 (1, 2, 3)
        - 서열형 척도(ordinal)로 처리합니다.
        - 1등석 > 2등석 > 3등석이므로, 생존률 관점에서 1이 가장 좋고 3이 가장 안 좋습니다.
        """
        this.train['Pclass'] = this.train['Pclass'].astype(int)
        this.test['Pclass'] = this.test['Pclass'].astype(int)
        return this

    def title_nominal(self, this) -> object:
        """
        Title: 명칭 (Mr, Mrs, Miss, Master, Dr, etc.)
        - Name 컬럼에서 추출한 타이틀입니다.
        - nominal 척도입니다.
        """
        for idx, df in enumerate([this.train, this.test]):
            if 'Name' not in df.columns:
                continue
            
            # Name에서 Title 추출 (예: "Braund, Mr. Owen Harris" -> "Mr")
            df['Title'] = df['Name'].str.extract(r',\s*([^\.]+)\.', expand=False)
            df['Title'] = df['Title'].str.strip()
            
            # 희소한 타이틀을 "Rare" 그룹으로 묶기
            title_counts = df['Title'].value_counts()
            rare_titles = title_counts[title_counts < 10].index.tolist()
            df['Title'] = df['Title'].replace(rare_titles, 'Rare')
            
            # 결측치 처리 (Title이 없는 경우 "Unknown"으로)
            df['Title'] = df['Title'].fillna('Unknown')
            
            # One-hot encoding
            title_dummies = pd.get_dummies(df['Title'], prefix='Title', dtype=int)
            df = pd.concat([df, title_dummies], axis=1)
            logger.info(f"Title one-hot encoding: {list(title_dummies.columns)}")
            
            # 원본 Title 컬럼 제거
            if 'Title' in df.columns:
                df = df.drop(columns=['Title'])
            
            # 원본 DataFrame에 반영
            if idx == 0:
                this.train = df
            else:
                this.test = df
        
        return this

    def gender_nominal(self, this) -> object:
        """
        gender: 성별 (male, female)
        - nominal 척도입니다.
        """
        for idx, df in enumerate([this.train, this.test]):
            # 'Sex' 컬럼이 있으면 'gender'로 rename
            if 'Sex' in df.columns and 'gender' not in df.columns:
                df['gender'] = df['Sex']
            
            if 'gender' not in df.columns:
                continue
            
            # One-hot encoding
            gender_dummies = pd.get_dummies(df['gender'], prefix='gender', dtype=int)
            df = pd.concat([df, gender_dummies], axis=1)
            logger.info(f"Gender one-hot encoding: {list(gender_dummies.columns)}")
            
            # 원본 문자열 컬럼 제거 (Sex와 gender 모두)
            cols_to_drop = []
            if 'Sex' in df.columns:
                cols_to_drop.append('Sex')
            if 'gender' in df.columns:
                cols_to_drop.append('gender')
            
            if cols_to_drop:
                df = df.drop(columns=cols_to_drop)
            
            # 원본 DataFrame에 반영
            if idx == 0:
                this.train = df
            else:
                this.test = df
        
        return this

    def age_ratio(self, this) -> object:
        """
        Age: 나이
        - 원래는 ratio 척도지만, 여기서는 나이를 구간으로 나눈 ordinal 피처를 만들고자 합니다.
        - bins: [-1, 0, 5, 12, 18, 24, 35, 60, np.inf] (9개 엣지 = 8개 구간)
        - labels: ['Unknown', 'Baby', 'Child', 'Teenager', 'Young Adult', 'Adult', 'Senior', 'Elderly'] (8개 라벨)
        """
        for df in [this.train, this.test]:
            if 'Age' not in df.columns:
                continue
            
            # 결측치 처리: 중앙값으로 채우기
            if df['Age'].isnull().any():
                median_age = df['Age'].median()
                df['Age'] = df['Age'].fillna(median_age)
                logger.info(f"Age 결측치를 중앙값 {median_age}으로 채웠습니다.")
            
            # 나이 구간화
            bins = [-1, 0, 5, 12, 18, 24, 35, 60, np.inf]
            labels = ['Unknown', 'Baby', 'Child', 'Teenager', 'Young Adult', 'Adult', 'Senior', 'Elderly']
            df['Age_band'] = pd.cut(df['Age'], bins=bins, labels=labels, include_lowest=True)
            
            # Age_band를 ordinal로 변환 (숫자 인코딩)
            df['Age_band_ordinal'] = df['Age_band'].cat.codes
        
        return this

    def ticket_nominal(self, df:pd.DataFrame) -> pd.DataFrame:
        """
        Ticket: 티켓 번호
        - nominal 척도입니다.
        - 티켓 번호는 고유 식별자이므로, 일반적으로 그룹화하거나 삭제하는 것이 좋습니다.
        """
        df = df.copy()
        if 'Ticket' not in df.columns:
            return df
        
        # 티켓 번호의 접두사 추출 (예: "PC 17755" -> "PC")
        df['Ticket_prefix'] = df['Ticket'].str.extract(r'^([A-Za-z]+)', expand=False)
        df['Ticket_prefix'] = df['Ticket_prefix'].fillna('Numeric')
        
        # 희소한 접두사를 "Rare"로 묶기
        prefix_counts = df['Ticket_prefix'].value_counts()
        rare_prefixes = prefix_counts[prefix_counts < 5].index.tolist()
        df['Ticket_prefix'] = df['Ticket_prefix'].replace(rare_prefixes, 'Rare')
        
        # One-hot encoding
        ticket_dummies = pd.get_dummies(df['Ticket_prefix'], prefix='Ticket')
        df = pd.concat([df, ticket_dummies], axis=1)
        
        # 원본 Ticket 컬럼은 유지 (필요시 삭제 가능)
        return df

    def fare_ratio(self, this) -> object:
        """
        Fare: 요금
        - 원래는 ratio 척도이지만, 여기서는 구간화하여 서열형(ordinal)으로 사용합니다.
        """
        for df in [this.train, this.test]:
            if 'Fare' not in df.columns:
                continue
            
            # 결측치 처리: 중앙값으로 채우기
            if df['Fare'].isnull().any():
                median_fare = df['Fare'].median()
                df['Fare'] = df['Fare'].fillna(median_fare)
                logger.info(f"Fare 결측치를 중앙값 {median_fare}으로 채웠습니다.")
            
            # Fare를 사분위수로 구간화하여 ordinal 피처 생성
            try:
                df['Fare_band'] = pd.qcut(df['Fare'], q=4, labels=[0, 1, 2, 3], duplicates='drop')
                if pd.api.types.is_categorical_dtype(df['Fare_band']):
                    df['Fare_band'] = df['Fare_band'].cat.codes
                else:
                    df['Fare_band'] = df['Fare_band'].astype(int)
            except ValueError as e:
                logger.warning(f"qcut 실패, quantile 사용: {e}")
                df['Fare_band'] = pd.cut(df['Fare'], bins=4, labels=[0, 1, 2, 3], duplicates='drop')
                if pd.api.types.is_categorical_dtype(df['Fare_band']):
                    df['Fare_band'] = df['Fare_band'].cat.codes
                else:
                    df['Fare_band'] = df['Fare_band'].astype(int)
        
        return this

    def embarked_nominal(self, this) -> object:
        """
        Embarked: 탑승 항구 (C, Q, S)
        - 본질적으로는 nominal(명목) 척도입니다.
        - one-hot encoding을 사용합니다.
        """
        for idx, df in enumerate([this.train, this.test]):
            if 'Embarked' not in df.columns:
                continue
            
            # 결측치 처리: 가장 많이 등장하는 값(mode)으로 채우기
            if df['Embarked'].isnull().any():
                mode_embarked = df['Embarked'].mode()[0] if not df['Embarked'].mode().empty else 'S'
                df['Embarked'] = df['Embarked'].fillna(mode_embarked)
                logger.info(f"Embarked 결측치를 최빈값 {mode_embarked}으로 채웠습니다.")
            
            # One-hot encoding
            embarked_dummies = pd.get_dummies(df['Embarked'], prefix='Embarked', dtype=int)
            df = pd.concat([df, embarked_dummies], axis=1)
            logger.info(f"Embarked one-hot encoding: {list(embarked_dummies.columns)}")
            
            # 원본 Embarked 컬럼 제거
            if 'Embarked' in df.columns:
                df = df.drop(columns=['Embarked'])
            
            # 원본 DataFrame에 반영
            if idx == 0:
                this.train = df
            else:
                this.test = df
        
        return this
    
    def create_k_fold(self):
        """K-Fold 교차 검증 생성"""
        k_fold = KFold(n_splits=10, shuffle=True, random_state=0)
        return k_fold
    
    def accuracy_by_knn(self, model, dummy) -> float:
        """KNN 방식으로 정확도 계산"""
        logger.info('>>> KNN 방식 검증')
        clf = KNeighborsClassifier(n_neighbors=13)
        scoring = 'accuracy'
        k_fold = self.create_k_fold()
        score = cross_val_score(clf, model, dummy, cv=k_fold, n_jobs=1, scoring=scoring)
        accuracy = round(np.mean(score) * 100, 2)
        return accuracy
    
    def accuracy_by_dtree(self, model, dummy) -> float:
        """결정트리 방식으로 정확도 계산"""
        logger.info('>>> 결정트리 방식 검증')
        k_fold = self.create_k_fold()
        clf = DecisionTreeClassifier()
        scoring = 'accuracy'
        score = cross_val_score(clf, model, dummy, cv=k_fold, n_jobs=1, scoring=scoring)
        accuracy = round(np.mean(score) * 100, 2)
        return accuracy
    
    def accuracy_by_rforest(self, model, dummy) -> float:
        """랜덤포레스트 방식으로 정확도 계산"""
        logger.info('>>> 랜덤포레스트 방식 검증')
        k_fold = self.create_k_fold()
        clf = RandomForestClassifier(n_estimators=13)
        scoring = 'accuracy'
        score = cross_val_score(clf, model, dummy, cv=k_fold, n_jobs=1, scoring=scoring)
        accuracy = round(np.mean(score) * 100, 2)
        return accuracy
    
    def accuracy_by_nb(self, model, dummy) -> float:
        """나이브베이즈 방식으로 정확도 계산"""
        logger.info('>>> 나이브베이즈 방식 검증')
        clf = GaussianNB()
        k_fold = self.create_k_fold()
        scoring = 'accuracy'
        score = cross_val_score(clf, model, dummy, cv=k_fold, n_jobs=1, scoring=scoring)
        accuracy = round(np.mean(score) * 100, 2)
        return accuracy
    
    def accuracy_by_svm(self, model, dummy) -> float:
        """SVM 방식으로 정확도 계산"""
        logger.info('>>> SVM 방식 검증')
        k_fold = self.create_k_fold()
        clf = SVC()
        scoring = 'accuracy'
        score = cross_val_score(clf, model, dummy, cv=k_fold, n_jobs=1, scoring=scoring)
        accuracy = round(np.mean(score) * 100, 2)
        return accuracy
