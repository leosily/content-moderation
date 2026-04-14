from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import redis
from config import settings


engine = create_engine(
    settings.DATABASE_URL, connect_args={"check_same_thread": False}  # SQLite必填参数
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()  

redis_client = redis.Redis(
    host=settings.REDIS_CONFIG["host"],
    port=settings.REDIS_CONFIG["port"],
    db=settings.REDIS_CONFIG["db"],
    decode_responses=True 
)
