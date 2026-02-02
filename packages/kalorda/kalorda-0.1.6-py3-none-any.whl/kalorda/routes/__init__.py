# 导出所有路由模块，方便在主应用中注册
from fastapi import APIRouter

from .admin import router as users_router
from .auth import router as auth_router
from .dataset import router as dataset_router
from .finetune import router as finetune_router
from .home import router as home_router
from .modeltest import router as modeltest_router
from .stream import router as stream_router
from .system import router as system_router

# 创建主路由器并设置/api前缀
api_router = APIRouter(prefix="/api")  # /api

# 注册所有子路由到主路由器
api_router.include_router(home_router)
api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(system_router)
api_router.include_router(dataset_router)
api_router.include_router(finetune_router)
api_router.include_router(stream_router)
api_router.include_router(modeltest_router)
