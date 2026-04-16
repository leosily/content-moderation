import os

# Pydantic v2 将 BaseSettings 移到了 pydantic-settings。
# 这里做兼容：优先使用 pydantic-settings；若环境仍是 pydantic v1，则回退。
try:
    from pydantic_settings import BaseSettings
except Exception:  # pragma: no cover
    from pydantic import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./content_moderation.db"
    
    REDIS_CONFIG: dict = {
        "host": "localhost",
        "port": 6379,
        "db": 0
    }
    
    SECRET_KEY: str = "your-secret-key-123456" 
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 300  
    
    # 百度智能云AI接口配置
    AI_CONFIG: dict = {
        "access_token": "your-baidu-ai-access-token",  # 手动获取或用SDK获取
        "authorization": "Bearer bce-v3/ALTAK-aT0WpQ6nZOM0lSEf4lmXT/ffc0b4411b30bce5cde68b88e4c8755412995db4",  # 兼容示例中的 Authorization 头写法（可留空）
        "strategy_id": "1",   # 可选：命中百度侧自定义策略
        "audit_url": "https://aip.baidubce.com/rest/2.0/solution/v1/text_censor/v2/user_defined"
    }
    
    RATE_LIMIT: str = "10/minute"  # 每分钟最多10次请求

settings = Settings()
