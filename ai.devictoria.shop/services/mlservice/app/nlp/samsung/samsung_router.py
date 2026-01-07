"""
삼성 보고서 워드클라우드 라우터
"""
import base64
import hashlib
import io
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from .samsung_wordcloud import SamsungWordcloud

# 라우터 생성
router = APIRouter(
    prefix="/samsung",
    tags=["samsung"],
    responses={404: {"description": "Not found"}}
)

# 싱글톤 인스턴스
_samsung_service: Optional[SamsungWordcloud] = None


def get_samsung_service() -> SamsungWordcloud:
    """Samsung 서비스 인스턴스 가져오기 (싱글톤)"""
    global _samsung_service
    if _samsung_service is None:
        _samsung_service = SamsungWordcloud()
    return _samsung_service


@router.get("/")
async def root():
    """루트 엔드포인트 - 워드클라우드 자동 생성"""
    try:
        service = get_samsung_service()
        
        # 워드클라우드 생성 (기본 설정)
        service.draw_wordcloud()
        
        # save 폴더에 저장된 파일 확인
        save_dir = Path(__file__).parent.parent / "save"
        output_file = save_dir / "samsung_wordcloud.png"
        
        return {
            "service": "Samsung Wordcloud Service",
            "description": "삼성 지속가능경영보고서 워드클라우드 생성 서비스",
            "status": "success",
            "message": "워드클라우드 이미지가 생성되었습니다.",
            "file_path": str(output_file),
            "endpoints": {
                "wordcloud": "/samsung/wordcloud - 워드클라우드 생성 (커스텀 설정)",
                "process": "/samsung/process - 텍스트 전처리 및 빈도 분석"
            }
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"워드클라우드 생성 중 오류 발생: {str(e)}")


@router.get("/wordcloud")
async def generate_samsung_wordcloud(
    width: int = Query(1000, description="워드클라우드 너비"),
    height: int = Query(600, description="워드클라우드 높이"),
    background_color: str = Query("white", description="배경색")
):
    """
    삼성 보고서 워드클라우드 생성
    
    Args:
        width: 워드클라우드 너비
        height: 워드클라우드 높이
        background_color: 배경색
        
    Returns:
        워드클라우드 이미지 (base64 인코딩) 및 분석 결과
    """
    try:
        service = get_samsung_service()
        
        # 텍스트 전처리 및 빈도 분석
        freq_txt = service.find_freq()
        
        # 워드클라우드 생성
        texts = service.remove_stopword()
        
        # 빈도 분석
        from nltk import FreqDist
        freq_dist = FreqDist(texts)
        freq_dict = dict(freq_dist)
        
        # "삼성전자"를 가장 크게 표시하기 위해 빈도를 최대값으로 설정
        if '삼성전자' in freq_dict:
            max_freq = max(freq_dict.values()) if freq_dict.values() else 100
            # "삼성전자"의 빈도를 최대값의 2배로 설정하여 가장 크게 표시
            freq_dict['삼성전자'] = max_freq * 2
        else:
            # "삼성전자"가 없으면 추가하고 높은 빈도 부여
            max_freq = max(freq_dict.values()) if freq_dict.values() else 100
            freq_dict['삼성전자'] = max_freq * 2
        
        # 폰트 경로 설정
        font_path = Path(__file__).parent.parent / "data" / "D2Coding.ttf"
        if not font_path.exists():
            # 폰트가 없으면 기본 폰트 사용
            font_path = None
        
        from wordcloud import WordCloud
        
        # 빈도 기반으로 워드클라우드 생성
        wcloud = WordCloud(
            font_path=str(font_path) if font_path and font_path.exists() else None,
            relative_scaling=0.2,
            width=width,
            height=height,
            background_color=background_color
        ).generate_from_frequencies(freq_dict)
        
        # save 폴더에 워드클라우드 이미지 저장
        save_dir = Path(__file__).parent.parent / "save"
        save_dir.mkdir(parents=True, exist_ok=True)
        
        # 파일명 생성
        params_str = f"{width}_{height}_{background_color}"
        params_hash = hashlib.md5(params_str.encode()).hexdigest()[:8]
        filename = f"samsung_wordcloud_{params_hash}.png"
        filepath = save_dir / filename
        
        # 이미 파일이 존재하면 재사용
        if filepath.exists():
            with open(filepath, 'rb') as f:
                img_data = f.read()
            img_base64 = base64.b64encode(img_data).decode('utf-8')
        else:
            # 새로 생성
            plt.figure(figsize=(width/100, height/100))
            plt.imshow(wcloud, interpolation='bilinear')
            plt.axis('off')
            plt.tight_layout(pad=0)
            
            # 파일로 저장
            plt.savefig(filepath, format='png', bbox_inches='tight', pad_inches=0, dpi=100)
            
            # base64 인코딩을 위한 버퍼
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', bbox_inches='tight', pad_inches=0, dpi=100)
            plt.close()
            
            img_buffer.seek(0)
            img_base64 = base64.b64encode(img_buffer.read()).decode('utf-8')
            img_buffer.close()
        
        # 빈도 데이터를 딕셔너리로 변환 (상위 30개)
        freq_dict = freq_txt.head(30).to_dict()
        
        return {
            "status": "success",
            "wordcloud_image": f"data:image/png;base64,{img_base64}",
            "wordcloud_file": str(filepath),
            "wordcloud_filename": filename,
            "wordcloud_width": width,
            "wordcloud_height": height,
            "top_words": {str(k): int(v) for k, v in freq_dict.items()},
            "total_words": len(freq_txt)
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"워드클라우드 생성 중 오류 발생: {str(e)}")


@router.get("/process")
async def process_samsung_text():
    """
    삼성 보고서 텍스트 전처리 및 빈도 분석
    
    Returns:
        전처리 결과 및 빈도 분석 데이터
    """
    try:
        # 싱글톤 인스턴스 강제 재생성 (코드 변경사항 반영)
        from .samsung_wordcloud import SamsungWordcloud
        import logging
        logger = logging.getLogger(__name__)
        logger.warning("[라우터] text_process() 호출 시작")
        service = SamsungWordcloud()
        logger.warning("[라우터] SamsungWordcloud 인스턴스 생성 완료")
        result = service.text_process()
        logger.warning(f"[라우터] text_process() 반환값 키: {list(result.keys())}")
        logger.warning(f"[라우터] saved_file 존재: {result.get('saved_file') is not None}")
        logger.warning(f"[라우터] 삼성전자_원본빈도: {result.get('삼성전자_원본빈도')}")
        
        # 빈도 데이터를 딕셔너리로 변환 (상위 50개)
        freq_txt = result.get('freq_txt')
        if freq_txt is not None:
            # pandas Series를 딕셔너리로 변환
            if hasattr(freq_txt, 'head'):
                freq_dict = freq_txt.head(50).to_dict()
            elif hasattr(freq_txt, 'to_dict'):
                freq_dict = freq_txt.to_dict()
            else:
                freq_dict = dict(freq_txt) if isinstance(freq_txt, dict) else {}
            
            # "삼성전자"가 상위 50개에 없어도 포함되도록 보장
            if '삼성전자' not in freq_dict and '삼성전자' in freq_txt.index if hasattr(freq_txt, 'index') else False:
                freq_dict['삼성전자'] = int(freq_txt['삼성전자'])
            
            result['freq_txt'] = {str(k): int(v) for k, v in freq_dict.items()}
            result['total_words'] = len(freq_txt) if hasattr(freq_txt, '__len__') else len(freq_dict)
            
            # 삼성전자 빈도 확인 (원본 빈도수 사용)
            if '삼성전자' in freq_dict:
                result['삼성전자_빈도'] = int(freq_dict['삼성전자'])
                # 순위 계산
                sorted_items = sorted(freq_dict.items(), key=lambda x: x[1], reverse=True)
                ranks = {k: i+1 for i, (k, v) in enumerate(sorted_items)}
                result['삼성전자_순위'] = ranks.get('삼성전자', '없음')
            elif '삼성전자_원본빈도' in result and result.get('삼성전자_원본빈도', 0) > 0:
                # 원본 빈도가 있으면 사용
                result['삼성전자_빈도'] = result.get('삼성전자_원본빈도', 0)
                # freq_txt에도 추가
                if '삼성전자' not in result['freq_txt']:
                    new_freq_txt = {'삼성전자': result.get('삼성전자_원본빈도', 0)}
                    new_freq_txt.update(result['freq_txt'])
                    result['freq_txt'] = new_freq_txt
        
        # result의 모든 키를 유지 (saved_file, 삼성전자_원본빈도 등)
        logger.warning(f"최종 반환값 키: {list(result.keys())}")
        logger.warning(f"최종 삼성전자_원본빈도 값: {result.get('삼성전자_원본빈도')} (타입: {type(result.get('삼성전자_원본빈도'))})")
        logger.warning(f"최종 최대빈도 값: {result.get('최대빈도')} (타입: {type(result.get('최대빈도'))})")
        
        return result
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"텍스트 처리 중 오류 발생: {str(e)}")


@router.get("/image")
async def get_samsung_wordcloud_image():
    """
    삼성 보고서 워드클라우드 이미지 반환
    
    Returns:
        워드클라우드 PNG 이미지 파일
    """
    try:
        # 이미지 파일 경로
        save_dir = Path(__file__).parent.parent / "save"
        image_path = save_dir / "samsung_wordcloud.png"
        
        # 이미지가 없으면 생성
        if not image_path.exists():
            service = SamsungWordcloud()
            service.draw_wordcloud()
            # 다시 확인
            if not image_path.exists():
                raise HTTPException(status_code=404, detail="워드클라우드 이미지를 생성할 수 없습니다.")
        
        return FileResponse(
            path=str(image_path),
            media_type="image/png",
            filename="samsung_wordcloud.png"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"이미지 로드 중 오류 발생: {str(e)}")

