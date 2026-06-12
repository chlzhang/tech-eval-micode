"""
FastAPI 应用入口
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core.config import settings
from .core.database import init_db, AsyncSessionLocal
from .core.security import get_password_hash
from .api import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时初始化数据库
    await init_db()
    
    # 创建默认管理员账号
    await create_default_admin()
    
    yield
    # 关闭时清理


async def create_default_admin():
    """创建默认管理员账号"""
    from .models.user import User
    from sqlalchemy import select
    
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.username == settings.ADMIN_USERNAME))
        admin = result.scalar_one_or_none()
        
        if not admin:
            admin = User(
                username=settings.ADMIN_USERNAME,
                password_hash=get_password_hash(settings.ADMIN_PASSWORD),
                display_name="管理员",
                department="技术部",
                role="admin",
                is_active=True
            )
            db.add(admin)
            await db.commit()
            print(f"已创建默认管理员账号: {settings.ADMIN_USERNAME}")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(api_router)


@app.get("/")
async def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running"
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}
