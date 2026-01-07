"""
한국어 자연어 처리 라우터
"""
import base64
import hashlib
import io
from pathlib import Path
from typing import List, Dict, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from wordcloud import WordCloud

from .korean_nlp_service import get_korean_nlp_service

# 라우터 생성
router = APIRouter(
    prefix="/korean",
    tags=["korean-nlp"],
    responses={404: {"description": "Not found"}}
)


# 요청 모델
class TokenizeRequest(BaseModel):
    text: str
    pos_tags: Optional[List[str]] = None
    min_length: int = 2
    remove_stopwords: bool = True


class BowRequest(BaseModel):
    text: str
    pos_tags: Optional[List[str]] = None
    min_length: int = 2
    remove_stopwords: bool = True
    top_n: Optional[int] = None


class KeywordRequest(BaseModel):
    text: str
    top_n: int = 20
    pos_tags: Optional[List[str]] = None


class WordCloudRequest(BaseModel):
    text: str
    pos_tags: Optional[List[str]] = None
    min_length: int = 2
    remove_stopwords: bool = True
    top_n: Optional[int] = 100
    width: int = 1000
    height: int = 600
    background_color: str = "white"
    font_path: Optional[str] = None


@router.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "service": "Korean NLP Service",
        "description": "kiwipiepy를 사용한 한국어 자연어 처리 서비스",
        "library": "kiwipiepy (Kiwi)",
        "endpoints": {
            "tokenize": "/korean/tokenize - 토큰화",
            "bow": "/korean/bow - Bag of Words 생성",
            "keywords": "/korean/keywords - 키워드 추출",
            "pos": "/korean/pos - 품사 태깅",
            "wordcloud": "/korean/wordcloud - 워드클라우드 생성",
            "corpus": "/korean/corpus - 말뭉치 분석"
        }
    }


@router.post("/tokenize")
async def tokenize_text(request: TokenizeRequest):
    """한국어 텍스트 토큰화"""
    try:
        service = get_korean_nlp_service()
        tokens = service.tokenize(
            text=request.text,
            pos_tags=request.pos_tags,
            min_length=request.min_length,
            remove_stopwords=request.remove_stopwords
        )
        
        return {
            "status": "success",
            "token_count": len(tokens),
            "tokens": tokens,
            "pos_tags_used": request.pos_tags or ['NNG', 'NNP', 'NNB']
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"토큰화 중 오류 발생: {str(e)}")


@router.post("/bow")
async def create_bow(request: BowRequest):
    """Bag of Words (BoW) 생성"""
    try:
        service = get_korean_nlp_service()
        bow = service.create_bow(
            text=request.text,
            pos_tags=request.pos_tags,
            min_length=request.min_length,
            remove_stopwords=request.remove_stopwords,
            top_n=request.top_n
        )
        
        return {
            "status": "success",
            "vocabulary_size": len(bow),
            "bow": bow,
            "pos_tags_used": request.pos_tags or ['NNG', 'NNP', 'NNB']
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"BoW 생성 중 오류 발생: {str(e)}")


@router.post("/keywords")
async def extract_keywords(request: KeywordRequest):
    """키워드 추출"""
    try:
        service = get_korean_nlp_service()
        keywords = service.extract_keywords(
            text=request.text,
            top_n=request.top_n,
            pos_tags=request.pos_tags
        )
        
        return {
            "status": "success",
            "keyword_count": len(keywords),
            "keywords": [{"word": word, "frequency": freq} for word, freq in keywords],
            "pos_tags_used": request.pos_tags or ['NNG', 'NNP', 'NNB']
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"키워드 추출 중 오류 발생: {str(e)}")


@router.post("/pos")
async def analyze_pos(text: str):
    """품사 태깅 분석"""
    try:
        service = get_korean_nlp_service()
        pos_result = service.analyze_pos(text=text)
        
        return {
            "status": "success",
            "token_count": len(pos_result),
            "pos_analysis": pos_result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"품사 태깅 중 오류 발생: {str(e)}")


@router.post("/wordcloud")
async def create_wordcloud(request: WordCloudRequest):
    """한국어 워드클라우드 생성"""
    try:
        service = get_korean_nlp_service()
        
        # BoW 생성
        bow = service.create_bow(
            text=request.text,
            pos_tags=request.pos_tags,
            min_length=request.min_length,
            remove_stopwords=request.remove_stopwords,
            top_n=request.top_n
        )
        
        if not bow:
            raise HTTPException(status_code=400, detail="추출된 단어가 없습니다.")
        
        # 한글 폰트 경로 설정 (없으면 기본 폰트 사용)
        font_path = request.font_path
        if not font_path:
            # Windows: Malgun Gothic
            # Linux: Nanum Gothic (설치 필요)
            import platform
            if platform.system() == 'Windows':
                font_path = 'C:\\Windows\\Fonts\\malgun.ttf'
            else:
                # Docker 컨테이너 내부라면 사전에 설치된 폰트 사용
                font_path = '/usr/share/fonts/truetype/nanum/NanumGothic.ttf'
        
        # 워드클라우드 생성
        wc = WordCloud(
            width=request.width,
            height=request.height,
            background_color=request.background_color,
            font_path=font_path,
            relative_scaling=0.2,
            min_font_size=10,
            random_state=42
        ).generate_from_frequencies(bow)
        
        # save 폴더에 워드클라우드 이미지 저장
        save_dir = Path(__file__).parent.parent / "save"
        save_dir.mkdir(parents=True, exist_ok=True)
        
        # 파일명 생성
        params_str = f"{request.top_n}_{request.width}_{request.height}_{request.background_color}"
        params_hash = hashlib.md5(params_str.encode()).hexdigest()[:8]
        filename = f"korean_wordcloud_{params_hash}.png"
        filepath = save_dir / filename
        
        # 이미 파일이 존재하면 재사용
        if filepath.exists():
            with open(filepath, 'rb') as f:
                img_data = f.read()
            img_base64 = base64.b64encode(img_data).decode('utf-8')
        else:
            # 새로 생성
            plt.figure(figsize=(request.width/100, request.height/100))
            plt.imshow(wc, interpolation='bilinear')
            plt.axis("off")
            plt.tight_layout(pad=0)
            
            # 파일로 저장
            plt.savefig(filepath, format='png', bbox_inches='tight', pad_inches=0, dpi=100)
            
            # base64 인코딩
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', bbox_inches='tight', pad_inches=0, dpi=100)
            plt.close()
            
            img_buffer.seek(0)
            img_base64 = base64.b64encode(img_buffer.read()).decode('utf-8')
            img_buffer.close()
        
        return {
            "status": "success",
            "vocabulary_size": len(bow),
            "wordcloud_image": f"data:image/png;base64,{img_base64}",
            "wordcloud_file": str(filepath),
            "wordcloud_filename": filename,
            "wordcloud_width": request.width,
            "wordcloud_height": request.height
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"워드클라우드 생성 중 오류 발생: {str(e)}")


@router.get("/corpus")
async def analyze_corpus(
    filename: str = Query(..., description="말뭉치 파일명 (예: kr-Report_2018.txt)"),
    text_length: Optional[int] = Query(None, description="분석할 텍스트 길이 (None이면 전체)"),
    top_n: int = Query(20, description="상위 N개 키워드 추출")
):
    """말뭉치 파일 분석"""
    try:
        service = get_korean_nlp_service()
        
        # 말뭉치 파일 로드
        corpus_file = Path(__file__).parent.parent / "data" / filename
        if not corpus_file.exists():
            raise HTTPException(status_code=404, detail=f"파일을 찾을 수 없습니다: {filename}")
        
        text = service.load_corpus(corpus_file)
        
        if text_length:
            text = text[:text_length]
        
        # 키워드 추출
        keywords = service.extract_keywords(text=text, top_n=top_n)
        
        # 토큰화
        tokens = service.tokenize(text=text)
        
        # BoW 생성
        bow = service.create_bow(text=text, top_n=top_n)
        
        return {
            "status": "success",
            "filename": filename,
            "text_length": len(text),
            "total_tokens": len(tokens),
            "vocabulary_size": len(bow),
            "keywords": [{"word": word, "frequency": freq} for word, freq in keywords]
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"말뭉치 분석 중 오류 발생: {str(e)}")

