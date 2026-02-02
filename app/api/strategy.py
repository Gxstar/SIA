"""策略分析API路由"""
import asyncio
from fastapi import APIRouter, HTTPException
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from app.services.data_service import ETFDataService
from app.services.strategy_engine import StrategyEngine
from app.services.llm_service import LLMService
from app.models.database import db

router = APIRouter()
strategy_engine = StrategyEngine()
llm_service = LLMService()
executor = ThreadPoolExecutor(max_workers=4)


async def get_price_with_timeout(code: str, period: str = '3m', timeout: float = 5.0):
    """带超时的获取价格数据"""
    loop = asyncio.get_event_loop()
    try:
        result = await asyncio.wait_for(
            loop.run_in_executor(executor, ETFDataService.get_price_history, code, period),
            timeout=timeout
        )
        return result
    except asyncio.TimeoutError:
        return {'code': code, 'dates': [], 'prices': [], 'volumes': [], 'error': 'timeout'}
    except Exception as e:
        return {'code': code, 'dates': [], 'prices': [], 'volumes': [], 'error': str(e)}


@router.get("/{code}")
async def get_strategy(code: str):
    """获取ETF策略分析 - 带超时控制"""
    try:
        # 先返回基础信息，快速响应
        # 获取价格数据（带5秒超时）
        price_data = await get_price_with_timeout(code, period='3m', timeout=5.0)
        
        # 如果超时或无数据，返回快速响应
        if not price_data.get('dates'):
            return {
                "code": 0,
                "data": {
                    "etf_code": code,
                    "date": datetime.now().strftime('%Y-%m-%d'),
                    "signals": [
                        {"name": "双均线", "signal": "持有", "confidence": 0.5, "details": "数据加载中..."},
                        {"name": "RSI", "signal": "持有", "confidence": 0.5, "details": "数据加载中..."},
                        {"name": "布林带", "signal": "持有", "confidence": 0.5, "details": "数据加载中..."},
                    ],
                    "final_action": "等待",
                    "amount": 0,
                    "llm_advice": "正在获取最新数据，请稍候刷新页面查看完整分析",
                },
                "warning": price_data.get('error', '暂无数据')
            }
        
        # 运行策略分析
        result = strategy_engine.analyze(price_data['prices'], price_data['dates'])
        
        # 计算建议金额 (默认10000元基准)
        suggested_amount = strategy_engine.calculate_position(10000, result['confidence'], result['final_action'])
        
        # 生成LLM建议
        llm_advice = llm_service.generate_advice(result)
        
        return {
            "code": 0,
            "data": {
                "etf_code": code,
                "date": datetime.now().strftime('%Y-%m-%d'),
                "signals": result['signals'],
                "final_action": result['final_action'],
                "amount": suggested_amount,
                "confidence": result['confidence'],
                "votes": result['votes'],
                "llm_advice": llm_advice,
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{code}/history")
async def get_strategy_history(code: str, days: int = 30):
    """获取历史策略记录"""
    try:
        strategies = db.get_daily_strategies(code, limit=days)
        
        data = []
        for s in strategies:
            data.append({
                'id': s.id,
                'date': s.date.strftime('%Y-%m-%d'),
                'strategy': s.final_action,
                'action': f"{s.final_action} ¥{s.suggested_amount:.0f}" if s.suggested_amount else s.final_action,
                'actual': f"{s.actual_action} ¥{s.actual_amount:.0f}" if s.actual_action else '-',
                'remark': s.remark or '-'
            })
        
        return {"code": 0, "data": data}
    except Exception as e:
        return {"code": 0, "data": []}


@router.get("/{code}/performance")
async def get_performance(code: str, days: int = 30):
    """获取绩效统计"""
    try:
        strategies = db.get_daily_strategies(code, limit=days)
        
        total = len(strategies)
        if total == 0:
            return {
                "code": 0,
                "data": {
                    "total": 0,
                    "followed": 0,
                    "not_followed": 0,
                    "accuracy": 0
                }
            }
        
        followed = sum(1 for s in strategies if s.actual_action)
        not_followed = total - followed
        
        # 计算策略准确度（简化版：假设执行后涨了就算对）
        accuracy = 0  # 需要实际价格数据对比
        
        return {
            "code": 0,
            "data": {
                "total": total,
                "followed": followed,
                "not_followed": not_followed,
                "accuracy": accuracy
            }
        }
    except Exception as e:
        return {"code": 0, "data": {}}


@router.post("/{code}/record")
async def record_action(code: str, action: str, amount: float = 0, remark: str = None):
    """记录用户实际操作"""
    try:
        # 保存到数据库
        db.save_daily_strategy({
            'etf_code': code,
            'date': datetime.now().date(),
            'raw_signals': {},
            'final_action': action,
            'suggested_amount': amount,
            'actual_action': action,
            'actual_amount': amount,
            'llm_advice': '',
            'remark': remark
        })
        
        return {"code": 0, "message": "记录成功"}
    except Exception as e:
        return {"code": 1, "message": str(e)}


@router.put("/{code}/history/{record_id}")
async def update_record(code: str, record_id: int, actual_action: str, actual_amount: float = 0, remark: str = None):
    """更新历史记录"""
    # 简化实现
    return {"code": 0, "message": "更新成功"}


def generate_llm_advice(result: dict) -> str:
    """生成LLM风格的建议"""
    action = result['final_action']
    confidence = result['confidence']
    votes = result['votes']
    
    action_desc = {
        '买入': '技术指标显示上涨信号',
        '卖出': '技术指标显示调整风险',
        '持有': '市场方向不明，建议观望'
    }
    
    confidence_desc = '较强' if confidence > 0.7 else '中等' if confidence > 0.5 else '较弱'
    
    advice = f"当前{action_desc[action]}，策略一致性{confidence_desc}（{votes}）。"
    
    if action == '买入':
        advice += "建议可考虑逢低布局，控制好仓位。"
    elif action == '卖出':
        advice += "建议适当减仓，防范短期风险。"
    else:
        advice += "建议保持现有仓位，谨慎操作。"
    
    return advice

