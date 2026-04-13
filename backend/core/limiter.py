from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import FastAPI
from config import settings

# 初始化限流组件（按IP限流）
limiter = Limiter(key_func=get_remote_address, default_limits=[settings.RATE_LIMIT])

def add_limiter(app: FastAPI):
    """给FastAPI应用添加限流中间件"""
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
