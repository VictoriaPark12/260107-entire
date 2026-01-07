from fastapi import FastAPI, APIRouter
import uvicorn
import sys
from pathlib import Path

# bs_demo 디렉토리를 Python 경로에 추가
sys.path.append(str(Path(__file__).parent / "bs_demo"))
from bugsmusic import crawl_bugs_chart

# sel_demo 디렉토리를 Python 경로에 추가
sys.path.append(str(Path(__file__).parent / "sel_demo"))
from danawa import crawl_danawa_tv

app = FastAPI()

# 서브라우터 생성
crawler_router = APIRouter()

@crawler_router.get("/")
async def crawler_root():
    return {"message": "Crawler Service API", "version": "0.1.0"}

@crawler_router.get("/bugsmusic")
async def get_bugs_music_chart():
    """Bugs Music 실시간 차트 크롤링"""
    result = crawl_bugs_chart()
    return result

@crawler_router.get("/danawa")
async def get_danawa_tv():
    """다나와 TV 상품 목록 크롤링"""
    result = crawl_danawa_tv()
    return result

# 라우터를 앱에 포함
app.include_router(crawler_router)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=9001)

