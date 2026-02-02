"""数据服务API路由"""
import asyncio
from fastapi import APIRouter
from concurrent.futures import ThreadPoolExecutor
from app.services.data_service import ETFDataService, PriceDataProcessor
from app.models.database import db
from datetime import datetime

router = APIRouter()
executor = ThreadPoolExecutor(max_workers=4)


async def get_data_with_timeout(func, code: str, period: str = None, timeout: float = 5.0):
    """带超时的数据获取"""
    loop = asyncio.get_event_loop()
    try:
        if period:
            result = await asyncio.wait_for(
                loop.run_in_executor(executor, func, code, period),
                timeout=timeout
            )
        else:
            result = await asyncio.wait_for(
                loop.run_in_executor(executor, func, code),
                timeout=timeout
            )
        return result
    except asyncio.TimeoutError:
        return {'code': code, 'dates': [], 'prices': [], 'volumes': [], 'error': 'timeout'}
    except Exception as e:
        return {'code': code, 'dates': [], 'prices': [], 'volumes': [], 'error': str(e)}


@router.get("/{code}/price")
async def get_price_history(code: str, period: str = "6m"):
    """获取价格历史数据 - 带超时控制"""
    data = await get_data_with_timeout(ETFDataService.get_price_history, code, period, timeout=5.0)
    return {"code": 0, "data": data}


@router.get("/{code}/intraday")
async def get_intraday_data(code: str):
    """获取分时数据 - 带超时控制"""
    loop = asyncio.get_event_loop()
    try:
        data = await asyncio.wait_for(
            loop.run_in_executor(executor, ETFDataService.get_intraday_data, code),
            timeout=5.0
        )
        return {"code": 0, "data": data}
    except Exception as e:
        return {"code": 0, "data": {'code': code, 'times': [], 'prices': [], 'volumes': [], 'error': str(e)}}


@router.get("/{code}/realtime")
async def get_realtime_price(code: str):
    """获取实时价格 - 带超时控制"""
    loop = asyncio.get_event_loop()
    try:
        data = await asyncio.wait_for(
            loop.run_in_executor(executor, ETFDataService.get_realtime_price, code),
            timeout=3.0
        )
        return {"code": 0, "data": data}
    except Exception as e:
        return {"code": 0, "data": {'code': code, 'price': None, 'change': None, 'error': str(e)}}


@router.get("/{code}/indicators")
async def get_indicators(code: str, period: str = "3m"):
    """获取技术指标数据 - 带超时控制"""
    price_data = await get_data_with_timeout(ETFDataService.get_price_history, code, period, timeout=5.0)
    
    if not price_data.get('dates'):
        return {"code": 0, "data": {}, "warning": "数据加载超时"}
    
    # 计算技术指标
    ma5 = PriceDataProcessor.calculate_ma(price_data['prices'], 5)
    ma20 = PriceDataProcessor.calculate_ma(price_data['prices'], 20)
    rsi = PriceDataProcessor.calculate_rsi(price_data['prices'], 14)
    bb = PriceDataProcessor.calculate_bollinger_bands(price_data['prices'], 20, 2)
    
    return {
        "code": 0,
        "data": {
            "code": code,
            "period": period,
            "dates": price_data['dates'],
            "ma5": ma5,
            "ma20": ma20,
            "rsi": rsi,
            "bollinger_upper": bb['upper'],
            "bollinger_middle": bb['middle'],
            "bollinger_lower": bb['lower']
        }
    }


@router.post("/sync")
async def sync_data():
    """同步所有ETF数据"""
    try:
        etfs = db.get_etf_list()
        for etf in etfs:
            price_data = ETFDataService.get_price_history(etf.code)
            if price_data['dates']:
                # 转换数据格式
                prices = []
                for i, date in enumerate(price_data['dates']):
                    prices.append({
                        'date': date,
                        'open': price_data['prices'][i],
                        'close': price_data['prices'][i],
                        'high': price_data['prices'][i],
                        'low': price_data['prices'][i],
                        'volume': price_data['volumes'][i]
                    })
                db.save_price_history(etf.code, prices)
        return {"code": 0, "message": f"已同步 {len(etfs)} 只ETF数据"}
    except Exception as e:
        return {"code": 1, "message": str(e)}
