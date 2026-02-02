"""ETF量化助手 - FastAPI后端服务"""
import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from app.api import etf, strategy, data

app = FastAPI(
    title="ETF量化助手 API",
    description="提供ETF数据分析、策略建议和可视化数据",
    version="0.1.0"
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态文件目录
static_path = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_path):
    app.mount("/static", StaticFiles(directory=static_path), name="static")

# 注册路由
app.include_router(etf.router, prefix="/api/etf", tags=["ETF管理"])
app.include_router(strategy.router, prefix="/api/strategy", tags=["策略分析"])
app.include_router(data.router, prefix="/api/data", tags=["数据服务"])


@app.get("/")
async def root():
    """返回前端页面"""
    index_path = os.path.join(os.path.dirname(__file__), "static", "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "ETF量化助手", "static": "/static"}


@app.get("/health")
async def health():
    """健康检查"""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
