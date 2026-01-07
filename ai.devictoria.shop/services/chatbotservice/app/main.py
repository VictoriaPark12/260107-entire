from fastapi import FastAPI, APIRouter
import uvicorn

app = FastAPI()

# 서브라우터 생성
chatbot_router = APIRouter()

@chatbot_router.get("/")
async def chatbot_root():
    return {"message": "Chatbot Service API", "version": "0.1.0"}

# 라우터를 앱에 포함
app.include_router(chatbot_router)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=9002)

