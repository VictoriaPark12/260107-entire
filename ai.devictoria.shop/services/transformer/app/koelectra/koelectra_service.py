#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
KoELECTRA 감성 분석 서비스
로컬 모델을 사용한 감성 분석
"""
import torch
import torch.nn.functional as F
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    AutoConfig,
    ElectraForSequenceClassification
)
from pathlib import Path
import logging
from typing import Dict, Optional
import time

logger = logging.getLogger(__name__)


class KoELECTRAService:
    """KoELECTRA 감성 분석 서비스 클래스"""
    
    # 레이블 매핑
    LABEL_MAP = {
        0: "부정",
        1: "긍정"
    }
    
    def __init__(
        self,
        model_path: Optional[Path] = None,
        device: str = "cpu",
        max_length: int = 512
    ):
        """
        Args:
            model_path: 모델 경로 (None이면 기본 경로 사용)
            device: 실행 장치 (cpu/cuda)
            max_length: 최대 시퀀스 길이
        """
        self.device = device
        self.max_length = max_length
        
        # 모델 경로 설정
        if model_path is None:
            model_path = Path(__file__).parent / "koelectra_model"
        
        self.model_path = Path(model_path)
        
        # 모델 및 토크나이저 초기화
        self.tokenizer = None
        self.model = None
        
        logger.info(f"KoELECTRA 서비스 초기화 (모델 경로: {self.model_path})")
    
    def load_model(self) -> None:
        """모델 및 토크나이저 로드"""
        try:
            logger.info("모델 로드 시작...")
            
            # 모델 경로 확인
            if not self.model_path.exists():
                raise FileNotFoundError(f"모델 경로를 찾을 수 없습니다: {self.model_path}")
            
            config_path = self.model_path / "config.json"
            model_path = self.model_path / "pytorch_model.bin"
            vocab_path = self.model_path / "vocab.txt"
            tokenizer_config_path = self.model_path / "tokenizer_config.json"
            
            # 파일 존재 확인
            if not config_path.exists():
                raise FileNotFoundError(f"config.json을 찾을 수 없습니다: {config_path}")
            if not model_path.exists():
                raise FileNotFoundError(f"pytorch_model.bin을 찾을 수 없습니다: {model_path}")
            if not vocab_path.exists():
                raise FileNotFoundError(f"vocab.txt을 찾을 수 없습니다: {vocab_path}")
            
            # Config 로드
            logger.info("Config 로드 중...")
            config = AutoConfig.from_pretrained(
                str(config_path.parent),
                local_files_only=True
            )
            
            # 시퀀스 분류를 위한 설정 수정
            if not hasattr(config, 'num_labels'):
                config.num_labels = 2  # 긍정/부정
            
            # Tokenizer 로드
            logger.info("Tokenizer 로드 중...")
            self.tokenizer = AutoTokenizer.from_pretrained(
                str(self.model_path),
                local_files_only=True,
                use_fast=False  # 로컬 모델은 fast tokenizer가 없을 수 있음
            )
            
            # 모델 로드 시도
            logger.info("Model 로드 중...")
            try:
                # ElectraForSequenceClassification으로 시도
                self.model = ElectraForSequenceClassification.from_pretrained(
                    str(self.model_path),
                    config=config,
                    local_files_only=True
                )
            except Exception as e:
                logger.warning(f"ElectraForSequenceClassification 로드 실패: {e}")
                logger.info("ElectraModel로 로드 후 분류 헤드 추가...")
                # 기본 Electra 모델로 로드 후 분류 헤드 추가
                from transformers import ElectraModel
                base_model = ElectraModel.from_pretrained(
                    str(self.model_path),
                    config=config,
                    local_files_only=True
                )
                # 분류 헤드 추가
                from torch import nn
                
                class ElectraClassifier(nn.Module):
                    """Electra 모델에 분류 헤드를 추가한 커스텀 모델"""
                    def __init__(self, base_model, num_labels=2):
                        super().__init__()
                        self.electra = base_model
                        self.dropout = nn.Dropout(0.1)
                        self.classifier = nn.Linear(base_model.config.hidden_size, num_labels)
                    
                    def forward(self, input_ids, attention_mask=None, token_type_ids=None):
                        outputs = self.electra(
                            input_ids=input_ids,
                            attention_mask=attention_mask,
                            token_type_ids=token_type_ids
                        )
                        # [CLS] 토큰 사용 (첫 번째 토큰)
                        pooled_output = outputs.last_hidden_state[:, 0]
                        pooled_output = self.dropout(pooled_output)
                        logits = self.classifier(pooled_output)
                        
                        # 표준 출력 형식으로 반환
                        class ModelOutput:
                            def __init__(self, logits):
                                self.logits = logits
                        
                        return ModelOutput(logits=logits)
                
                self.model = ElectraClassifier(base_model, num_labels=2)
            
            # 장치로 이동
            self.model.to(self.device)
            self.model.eval()
            
            logger.info("모델 로드 완료!")
            logger.info(f"  - Vocab Size: {config.vocab_size}")
            logger.info(f"  - Hidden Size: {config.hidden_size}")
            logger.info(f"  - Num Layers: {config.num_hidden_layers}")
            logger.info(f"  - Device: {self.device}")
            
        except Exception as e:
            logger.error(f"모델 로드 실패: {e}")
            raise RuntimeError(f"모델 로드 중 오류 발생: {e}")
    
    def preprocess(self, text: str) -> Dict:
        """
        입력 텍스트 전처리 및 토큰화
        
        Args:
            text: 입력 텍스트
        
        Returns:
            토큰화된 입력 딕셔너리
        """
        if self.tokenizer is None:
            raise RuntimeError("토크나이저가 로드되지 않았습니다. load_model()을 먼저 호출하세요.")
        
        # 토큰화
        encoded = self.tokenizer(
            text,
            padding=True,
            truncation=True,
            max_length=self.max_length,
            return_tensors="pt"
        )
        
        # 장치로 이동
        encoded = {k: v.to(self.device) for k, v in encoded.items()}
        
        return encoded
    
    def predict(
        self,
        text: str,
        return_probabilities: bool = False
    ) -> Dict:
        """
        감성 분석 예측
        
        Args:
            text: 입력 텍스트
            return_probabilities: 확률값 반환 여부
        
        Returns:
            예측 결과 딕셔너리
        """
        if self.model is None:
            raise RuntimeError("모델이 로드되지 않았습니다. load_model()을 먼저 호출하세요.")
        
        start_time = time.time()
        
        try:
            # 전처리
            inputs = self.preprocess(text)
            
            # 추론
            with torch.no_grad():
                # 모델 타입에 따라 추론
                if hasattr(self.model, 'electra'):
                    # 커스텀 ElectraClassifier 모델인 경우
                    outputs = self.model(
                        input_ids=inputs['input_ids'],
                        attention_mask=inputs.get('attention_mask'),
                        token_type_ids=inputs.get('token_type_ids')
                    )
                    logits = outputs.logits
                else:
                    # 표준 모델인 경우
                    outputs = self.model(**inputs)
                    logits = outputs.logits
            
            # Softmax로 확률 계산
            probabilities = F.softmax(logits, dim=-1)
            
            # CPU로 이동 및 numpy 변환
            probs = probabilities.detach().cpu().numpy()[0]
            
            # 최대 확률의 레이블
            pred_label = int(probs.argmax())
            pred_score = float(probs[pred_label])
            
            # 결과 구성
            result = {
                "text": text,
                "sentiment": self.LABEL_MAP.get(pred_label, "알 수 없음"),
                "score": pred_score,
                "label_id": pred_label
            }
            
            # 확률값 추가
            if return_probabilities:
                result["probabilities"] = {
                    self.LABEL_MAP[i]: float(probs[i])
                    for i in range(len(probs))
                }
            
            # 처리 시간
            elapsed_ms = (time.time() - start_time) * 1000
            result["processing_time_ms"] = elapsed_ms
            
            logger.info(f"감성 분석 완료: {result['sentiment']} (신뢰도: {pred_score:.4f}, {elapsed_ms:.2f}ms)")
            
            return result
            
        except Exception as e:
            logger.error(f"추론 중 오류: {e}")
            raise RuntimeError(f"감성 분석 실패: {e}")


# 싱글톤 인스턴스
_service_instance: Optional[KoELECTRAService] = None


def get_service(
    model_path: Optional[Path] = None,
    device: str = "cpu",
    max_length: int = 512
) -> KoELECTRAService:
    """
    KoELECTRAService 싱글톤 인스턴스 반환
    
    Args:
        model_path: 모델 경로
        device: 실행 장치
        max_length: 최대 시퀀스 길이
    
    Returns:
        KoELECTRAService 인스턴스
    """
    global _service_instance
    
    if _service_instance is None:
        _service_instance = KoELECTRAService(
            model_path=model_path,
            device=device,
            max_length=max_length
        )
        _service_instance.load_model()
    
    return _service_instance

