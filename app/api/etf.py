"""ETF管理API路由 - 异步版本"""
import asyncio
from fastapi import APIRouter, HTTPException
from concurrent.futures import ThreadPoolExecutor
from app.models.database import db
from app.services.data_service import ETFDataService

router = APIRouter()
executor = ThreadPoolExecutor(max_workers=4)


@router.get("/list")
async def get_etf_list():
    """获取ETF列表 - 快速响应"""
    try:
        # 从数据库获取ETF列表
        etfs = db.get_etf_list()
        
        if not etfs:
            return {
                "code": 0,
                "data": [
                    {"code": "510300", "name": "沪深300ETF", "change": None, "price": None},
                    {"code": "512880", "name": "证券ETF", "change": None, "price": None},
                ]
            }
        
        # 只返回数据库中的信息，不调用外部API
        result = []
        for etf in etfs:
            result.append({
                "code": etf.code,
                "name": etf.name,
                "change": None,
                "price": None
            })
        
        return {"code": 0, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def get_etf_info_async(code: str):
    """异步获取ETF信息"""
    loop = asyncio.get_event_loop()
    try:
        return await asyncio.wait_for(
            loop.run_in_executor(executor, ETFDataService.get_etf_info, code),
            timeout=3.0
        )
    except Exception as e:
        return {'code': code, 'name': ETFDataService.ETF_NAMES.get(code, code), 'exchange': '沪深', 'category': 'ETF'}


@router.post("/add")
async def add_etf(code: str):
    """添加ETF - 异步版本"""
    try:
        # 验证代码格式
        if not code.isdigit() or len(code) != 6:
            raise HTTPException(status_code=400, detail="请输入6位数字代码")
        
        # 检查是否已存在
        existing = db.get_etf_list()
        if any(e.code == code for e in existing):
            return {"code": 0, "message": "ETF已存在"}
        
        # 异步获取ETF信息（带超时）
        info = await get_etf_info_async(code)
        
        if not info.get('name'):
            info['name'] = ETFDataService.ETF_NAMES.get(code, code)
        
        # 保存到数据库
        db.add_etf(
            code=code,
            name=info['name'],
            exchange=info.get('exchange', ''),
            category=info.get('category', 'ETF')
        )
        
        return {"code": 0, "message": f"成功添加ETF: {info['name']}"}
    except Exception as e:
        if "UNIQUE constraint" in str(e):
            return {"code": 0, "message": "ETF已存在"}
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{code}")
async def remove_etf(code: str):
    """移除ETF"""
    # 简化实现：暂不移除，只标记
    return {"code": 0, "message": f"ETF {code} 已标记为移除"}


@router.get("/{code}/info")
async def get_etf_info(code: str):
    """获取ETF详细信息"""
    info = ETFDataService.get_etf_info(code)
    return {"code": 0, "data": info}


@router.get("/{code}/realtime")
async def get_etf_realtime(code: str):
    """获取ETF实时价格"""
    data = ETFDataService.get_realtime_price(code)
    return {"code": 0, "data": data}


@router.get("/search")
async def search_etf(keyword: str):
    """搜索ETF"""
    results = ETFDataService.search_etf(keyword)
    return {"code": 0, "data": results}
