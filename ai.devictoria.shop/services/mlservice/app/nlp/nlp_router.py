"""
NLTK 자연어 처리 라우터
"""
import base64
import hashlib
import io
from datetime import datetime
from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse, Response
from typing import List, Dict, Optional
from pydantic import BaseModel
import matplotlib
matplotlib.use('Agg')  # GUI 백엔드 사용 안 함
import matplotlib.pyplot as plt

from app.nlp.emma.emma_wordcloud import NLTKService

# 라우터 생성
router = APIRouter(
    prefix="/nlp",
    tags=["nlp"],
    responses={404: {"description": "Not found"}}
)

# 서비스 인스턴스
_nltk_service: Optional[NLTKService] = None


def get_nltk_service() -> NLTKService:
    """서비스 인스턴스 싱글톤 패턴"""
    global _nltk_service
    if _nltk_service is None:
        _nltk_service = NLTKService()
    return _nltk_service


# 요청 모델
class TokenizeRequest(BaseModel):
    text: str
    method: str = "word"  # "word", "sentence", "regex"


class StemRequest(BaseModel):
    words: List[str]
    method: str = "porter"  # "porter", "lancaster", "lemmatize"
    pos: Optional[str] = None


class AnalyzeTextRequest(BaseModel):
    text: str
    text_name: str = "Text"
    plot_frequency: bool = False
    plot_dispersion_words: Optional[List[str]] = None
    extract_names: bool = False
    create_wordcloud: bool = False


@router.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "service": "NLTK Natural Language Processing Service",
        "description": "NLTK를 사용한 자연어 처리 서비스",
        "endpoints": {
            "corpus": "/nlp/corpus - 말뭉치 파일 목록",
            "tokenize": "/nlp/tokenize - 토큰화",
            "stem": "/nlp/stem - 형태소 분석",
            "pos_tag": "/nlp/pos-tag - 품사 태깅",
            "analyze": "/nlp/analyze - 텍스트 종합 분석",
            "emma": "/nlp/emma - 엠마 텍스트 분석 및 워드클라우드 생성 (GET)"
        }
    }


@router.get("/corpus")
async def get_corpus_fileids():
    """말뭉치 파일 ID 목록 조회"""
    try:
        service = get_nltk_service()
        fileids = service.get_corpus_fileids()
        return {
            "status": "success",
            "count": len(fileids),
            "fileids": fileids
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"말뭉치 조회 중 오류 발생: {str(e)}")


@router.get("/corpus/{fileid}")
async def get_corpus_text(fileid: str, length: Optional[int] = None):
    """말뭉치 텍스트 조회"""
    try:
        service = get_nltk_service()
        text = service.load_corpus_text(fileid)
        if length:
            text = text[:length]
        return {
            "status": "success",
            "fileid": fileid,
            "text_length": len(text),
            "text": text
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"말뭉치 텍스트 조회 중 오류 발생: {str(e)}")


@router.post("/tokenize")
async def tokenize_text(request: TokenizeRequest):
    """텍스트 토큰화"""
    try:
        service = get_nltk_service()
        
        if request.method == "word":
            tokens = service.tokenize_words(request.text)
        elif request.method == "sentence":
            tokens = service.tokenize_sentences(request.text)
        elif request.method == "regex":
            tokens = service.tokenize_regex(request.text)
        else:
            raise HTTPException(status_code=400, detail="지원하지 않는 토큰화 방법입니다.")
        
        return {
            "status": "success",
            "method": request.method,
            "token_count": len(tokens),
            "tokens": tokens
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"토큰화 중 오류 발생: {str(e)}")


@router.post("/stem")
async def stem_words(request: StemRequest):
    """형태소 분석 (어간 추출 또는 원형 복원)"""
    try:
        service = get_nltk_service()
        
        if request.method == "porter":
            result = service.stem_porter(request.words)
        elif request.method == "lancaster":
            result = service.stem_lancaster(request.words)
        elif request.method == "lemmatize":
            result = service.lemmatize(request.words, request.pos)
        else:
            raise HTTPException(status_code=400, detail="지원하지 않는 형태소 분석 방법입니다.")
        
        return {
            "status": "success",
            "method": request.method,
            "pos": request.pos,
            "input_words": request.words,
            "output_words": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"형태소 분석 중 오류 발생: {str(e)}")


@router.post("/pos-tag")
async def pos_tag_text(text: str):
    """품사 태깅"""
    try:
        service = get_nltk_service()
        tagged = service.tag_pos(text)
        
        return {
            "status": "success",
            "tagged_tokens": tagged,
            "nouns": service.extract_nouns(text)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"품사 태깅 중 오류 발생: {str(e)}")


@router.post("/analyze")
async def analyze_text(request: AnalyzeTextRequest):
    """텍스트 종합 분석"""
    try:
        service = get_nltk_service()
        result = service.analyze_text(
            text=request.text,
            text_name=request.text_name,
            plot_frequency=request.plot_frequency,
            plot_dispersion_words=request.plot_dispersion_words,
            extract_names=request.extract_names,
            create_wordcloud=request.create_wordcloud
        )
        
        # Text 객체와 WordCloud 객체는 JSON 직렬화 불가능하므로 제외
        response = {
            "status": "success",
            "text_name": result["text_name"],
            "total_tokens": result["total_tokens"],
            "vocabulary_size": result["vocabulary_size"],
            "most_common_words": result["most_common_words"]
        }
        
        if "names_freq_dist" in result:
            response["most_common_names"] = result["most_common_names"]
        
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"텍스트 분석 중 오류 발생: {str(e)}")


@router.get("/freq-dist")
async def get_frequency_distribution(text: str, word: Optional[str] = None):
    """빈도 분포 조회"""
    try:
        service = get_nltk_service()
        tokens = service.tokenize_regex(text)
        freq_dist = service.create_freq_dist(tokens)
        
        result = {
            "status": "success",
            "total_words": freq_dist.N(),
            "vocabulary_size": len(freq_dist),
            "most_common": service.get_most_common(freq_dist, 20)
        }
        
        if word:
            word_count = freq_dist[word]
            word_freq = freq_dist.freq(word)
            result["word_stats"] = {
                "word": word,
                "count": word_count,
                "frequency": word_freq
            }
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"빈도 분포 조회 중 오류 발생: {str(e)}")


@router.get("/emma")
async def analyze_emma_with_wordcloud(
    text_length: Optional[int] = None,
    extract_names: bool = True,
    width: int = 1000,
    height: int = 600,
    background_color: str = "white"
):
    """
    엠마 텍스트 분석 및 워드클라우드 생성
    
    Args:
        text_length: 분석할 텍스트 길이 (None이면 전체)
        extract_names: 고유명사 추출 여부
        width: 워드클라우드 너비
        height: 워드클라우드 높이
        background_color: 배경색
        
    Returns:
        분석 결과 및 워드클라우드 이미지 (base64 인코딩)
    """
    try:
        service = get_nltk_service()
        
        # 엠마 텍스트 로드
        if text_length:
            emma_text = service.get_emma_text(text_length)
        else:
            emma_text = service.load_corpus_text("austen-emma.txt")
        
        # 텍스트 분석 (워드클라우드 생성 포함)
        tokens = service.tokenize_regex(emma_text)
        text_obj = service.create_text_object(tokens, "Emma")
        freq_dist = service.create_freq_dist(tokens)
        
        # 고유명사 추출 (선택적)
        names_freq = None
        most_common_names = None
        if extract_names:
            names_freq = service.extract_names_from_text(emma_text)
            most_common_names = service.get_most_common(names_freq, 10)
        
        # 워드클라우드에 사용할 빈도 분포 선택
        wordcloud_freq = names_freq if (extract_names and names_freq) else freq_dist
        
        # emma_wordcloud.py의 create_wordcloud 메서드 활용
        wc = service.create_wordcloud(
            freq_dist=wordcloud_freq,
            width=width,
            height=height,
            background_color=background_color,
            random_state=0,
            show=False  # 파일로만 저장, 화면에 표시하지 않음
        )
        
        # save 폴더에 워드클라우드 이미지 저장
        # nlp_router.py는 app/nlp/에 있으므로 save 폴더는 app/nlp/save/
        save_dir = Path(__file__).parent / "save"
        save_dir.mkdir(parents=True, exist_ok=True)
        
        # 파일명 생성 (파라미터 기반, 타임스탬프 제거하여 같은 파라미터면 같은 파일명)
        params_str = f"{extract_names}_{width}_{height}_{background_color}_{text_length or 'full'}"
        params_hash = hashlib.md5(params_str.encode()).hexdigest()[:8]
        if extract_names and names_freq:
            filename = f"emma_names_wordcloud_{params_hash}.png"
        else:
            filename = f"emma_wordcloud_{params_hash}.png"
        filepath = save_dir / filename
        
        # 이미 파일이 존재하면 재사용
        if filepath.exists():
            # 기존 파일을 읽어서 base64 인코딩
            with open(filepath, 'rb') as f:
                img_data = f.read()
            img_base64 = base64.b64encode(img_data).decode('utf-8')
        else:
            # 새로 생성
            # 워드클라우드를 이미지로 변환 (파일 저장 및 base64 인코딩)
            plt.figure(figsize=(width/100, height/100))
            plt.imshow(wc, interpolation='bilinear')
            plt.axis("off")
            plt.tight_layout(pad=0)
            
            # 먼저 파일로 저장
            plt.savefig(filepath, format='png', bbox_inches='tight', pad_inches=0, dpi=100)
            
            # base64 인코딩을 위한 버퍼
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', bbox_inches='tight', pad_inches=0, dpi=100)
            plt.close()
            
            # base64 인코딩
            img_buffer.seek(0)
            img_base64 = base64.b64encode(img_buffer.read()).decode('utf-8')
            img_buffer.close()
        
        # 결과 반환
        result = {
            "status": "success",
            "text_name": "Emma",
            "text_length": len(emma_text),
            "total_tokens": len(tokens),
            "vocabulary_size": len(freq_dist),
            "most_common_words": service.get_most_common(freq_dist, 20),
            "wordcloud_image": f"data:image/png;base64,{img_base64}",
            "wordcloud_file": str(filepath),
            "wordcloud_filename": filename,
            "wordcloud_width": width,
            "wordcloud_height": height
        }
        
        if extract_names and names_freq:
            result["most_common_names"] = most_common_names
            result["names_count"] = names_freq.N()
        
        return result
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"엠마 텍스트 분석 중 오류 발생: {str(e)}")

