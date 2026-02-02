"""LLM服务模块"""
import hashlib
import json
from datetime import datetime, timedelta
from typing import Dict, Optional
from abc import ABC, abstractmethod
import requests

from app.models.database import db, LLMCache


class BaseLLMProvider(ABC):
    """LLM提供商基类"""
    
    @abstractmethod
    def generate(self, prompt: str) -> str:
        pass


class DeepSeekProvider(BaseLLMProvider):
    """DeepSeek API提供商"""
    
    def __init__(self, api_key: str = None, base_url: str = "https://api.deepseek.com"):
        self.api_key = api_key
        self.base_url = base_url
        self.model = "deepseek-chat"
    
    def generate(self, prompt: str) -> str:
        """调用DeepSeek API"""
        if not self.api_key:
            return None
        
        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": "你是一个专业的ETF量化投资助手，请用简洁清晰的语言分析投资策略。"},
                        {"role": "user", "content": prompt}
                    ],
                    "max_tokens": 500,
                    "temperature": 0.7
                },
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"]
            else:
                print(f"DeepSeek API错误: {response.status_code}")
                return None
        except Exception as e:
            print(f"DeepSeek调用失败: {e}")
            return None


class OpenAIProvider(BaseLLMProvider):
    """OpenAI API提供商"""
    
    def __init__(self, api_key: str = None, model: str = "gpt-3.5-turbo"):
        self.api_key = api_key
        self.model = model
    
    def generate(self, prompt: str) -> str:
        """调用OpenAI API"""
        if not self.api_key:
            return None
        
        try:
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": "你是一个专业的ETF量化投资助手，请用简洁清晰的语言分析投资策略。"},
                        {"role": "user", "content": prompt}
                    ],
                    "max_tokens": 500,
                    "temperature": 0.7
                },
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"]
            else:
                print(f"OpenAI API错误: {response.status_code}")
                return None
        except Exception as e:
            print(f"OpenAI调用失败: {e}")
            return None


class MockLLMProvider(BaseLLMProvider):
    """模拟LLM提供商（用于测试）"""
    
    def generate(self, prompt: str) -> str:
        """返回模拟响应"""
        if "买入" in prompt:
            return ("技术指标综合显示短期上涨动能较强。"
                   "双均线形成金叉，RSI处于偏强区域，价格在布林带中轨上方运行。"
                   "建议可考虑逢低布局，建议仓位控制在30%-50%。")
        elif "卖出" in prompt:
            return ("技术指标显示短期存在调整风险。"
                   "RSI进入超买区域，需警惕回调风险。"
                   "建议适当减仓锁定利润，仓位建议控制在20%以下。")
        else:
            return ("市场方向暂不明确，各技术指标出现分歧。"
                   "建议保持现有仓位，谨慎追涨杀跌，等待更明确的信号。")


class LLMService:
    """LLM服务"""
    
    def __init__(self):
        import os
        from dotenv import load_dotenv
        
        # 加载环境变量
        load_dotenv()
        
        api_key = os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENAI_API_KEY")
        provider_type = os.getenv("LLM_PROVIDER", "mock")
        
        if provider_type == "deepseek" and api_key:
            self.provider = DeepSeekProvider(api_key)
        elif provider_type == "openai" and api_key:
            self.provider = OpenAIProvider(api_key)
        else:
            self.provider = MockLLMProvider()
    
    def _generate_cache_key(self, prompt: str) -> str:
        """生成缓存key"""
        return hashlib.md5(prompt.encode()).hexdigest()
    
    def _get_cached_response(self, cache_key: str) -> Optional[str]:
        """获取缓存的响应"""
        try:
            session = db.get_session()
            cached = session.query(LLMCache).filter(
                LLMCache.signal_key == cache_key
            ).first()
            session.close()
            
            if cached and cached.expires_at > datetime.now():
                return cached.response
        except Exception as e:
            print(f"查询缓存失败: {e}")
        return None
    
    def _save_to_cache(self, cache_key: str, prompt: str, response: str):
        """保存到缓存"""
        try:
            session = db.get_session()
            cache = LLMCache(
                signal_key=cache_key,
                prompt=prompt,
                response=response,
                expires_at=datetime.now() + timedelta(hours=24)
            )
            session.add(cache)
            session.commit()
            session.close()
        except Exception as e:
            print(f"保存缓存失败: {e}")
    
    def generate_advice(self, strategy_result: Dict) -> str:
        """生成策略建议"""
        
        # 构建prompt
        signals = strategy_result.get('signals', [])
        final_action = strategy_result.get('final_action', '持有')
        confidence = strategy_result.get('confidence', 0.5)
        
        prompt = f"""
请分析以下ETF策略信号并给出投资建议：

最终操作建议：{final_action}
综合置信度：{confidence:.0%}

各策略信号：
"""
        for s in signals:
            prompt += f"- {s['name']}: {s['signal']} (置信度{s['confidence']:.0%}) - {s.get('details', '')}\n"
        
        prompt += """
请用简洁清晰的语句总结：
1. 当前市场状态
2. 操作理由
3. 风险提示
4. 建议仓位

回复控制在100字以内。
"""
        
        # 检查缓存
        cache_key = self._generate_cache_key(prompt)
        cached = self._get_cached_response(cache_key)
        if cached:
            print("使用缓存的LLM响应")
            return cached
        
        # 调用LLM
        response = self.provider.generate(prompt)
        
        if response:
            self._save_to_cache(cache_key, prompt, response)
            return response
        else:
            # 返回基于规则的建议
            return self._rule_based_advice(strategy_result)
    
    def _rule_based_advice(self, strategy_result: Dict) -> str:
        """基于规则的建议（降级方案）"""
        final_action = strategy_result.get('final_action', '持有')
        confidence = strategy_result.get('confidence', 0.5)
        votes = strategy_result.get('votes', {})
        
        action_desc = {
            '买入': '技术指标显示上涨信号，建议适度建仓',
            '卖出': '技术指标显示调整风险，建议适当减仓',
            '持有': '市场方向不明，建议观望等待'
        }
        
        advice = action_desc.get(final_action, '建议观望')
        
        if confidence > 0.75:
            advice += '，信号较强。'
        elif confidence < 0.55:
            advice += '，信号较弱，谨慎操作。'
        else:
            advice += '。'
        
        # 添加风险提示
        if final_action == '买入':
            advice += '注意控制仓位，设置止损位。'
        elif final_action == '卖出':
            advice += '可考虑分批减仓，回调后择机接回。'
        
        return advice


# 测试
if __name__ == "__main__":
    from app.services.strategy_engine import StrategyEngine
    import numpy as np
    
    # 模拟价格数据
    np.random.seed(42)
    prices = list(np.cumsum(np.random.randn(100) * 0.01) + 4)
    
    # 策略分析
    engine = StrategyEngine()
    result = engine.analyze(prices)
    
    # LLM建议
    llm = LLMService()
    advice = llm.generate_advice(result)
    
    print("策略结果:", result)
    print("\nLLM建议:", advice)
