from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base
from api import api_router
from core.limiter import add_limiter

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AI内容审核系统",
    description="基于FastAPI+SQLAlchemy+Redis+Celery的自媒体文本审核系统",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

add_limiter(app)

app.include_router(api_router)

@app.get("/", tags=["测试"])
def root():
    return {"message": "AI内容审核系统（基础版）已启动，访问/api/docs查看接口文档"}