"""量化策略引擎"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from dataclasses import dataclass


@dataclass
class Signal:
    """交易信号"""
    name: str
    signal: str  # '买入' | '卖出' | '持有'
    confidence: float  # 0-1
    details: str = ''


class MovingAverageStrategy:
    """双均线策略"""
    
    def __init__(self, short_window: int = 5, long_window: int = 20):
        self.short_window = short_window
        self.long_window = long_window
    
    def analyze(self, prices: List[float], dates: List[str] = None) -> Signal:
        """分析并返回信号"""
        if len(prices) < self.long_window + 5:
            return Signal(
                name="双均线",
                signal="持有",
                confidence=0.5,
                details="数据不足"
            )
        
        df = pd.DataFrame({'close': prices})
        df['ma_short'] = df['close'].rolling(window=self.short_window).mean()
        df['ma_long'] = df['close'].rolling(window=self.long_window).mean()
        
        # 当前状态
        current_price = prices[-1]
        current_ma_short = df['ma_short'].iloc[-1]
        current_ma_long = df['ma_long'].iloc[-1]
        prev_ma_short = df['ma_short'].iloc[-2]
        prev_ma_long = df['ma_long'].iloc[-2]
        
        # 趋势判断
        short_trend = df['ma_short'].iloc[-1] / df['ma_short'].iloc[-5] - 1 if len(df) >= 5 else 0
        long_trend = df['ma_long'].iloc[-1] / df['ma_long'].iloc[-10] - 1 if len(df) >= 10 else 0
        
        # 交叉信号
        golden_cross = prev_ma_short <= prev_ma_long and current_ma_short > current_ma_long
        death_cross = prev_ma_short >= prev_ma_long and current_ma_short < current_ma_long
        
        # 位置判断
        price_above_ma = current_price > current_ma_short
        
        # 综合判断
        if golden_cross and price_above_ma:
            signal = "买入"
            confidence = 0.85
            details = "金叉形成，价格站上均线"
        elif death_cross:
            signal = "卖出"
            confidence = 0.80
            details = "死叉形成，注意风险"
        elif current_ma_short > current_ma_long and short_trend > 0:
            signal = "买入"
            confidence = 0.70
            details = "短期均线在上且上升趋势"
        elif current_ma_short < current_ma_long and long_trend < -0.02:
            signal = "卖出"
            confidence = 0.70
            details = "中长期趋势向下"
        elif price_above_ma:
            signal = "持有"
            confidence = 0.60
            details = "价格暂稳，均线整理中"
        else:
            signal = "持有"
            confidence = 0.55
            details = "观望为主"
        
        return Signal(
            name="双均线",
            signal=signal,
            confidence=confidence,
            details=details
        )


class RSIStrategy:
    """RSI策略"""
    
    def __init__(self, period: int = 14, overbought: float = 70, oversold: float = 30):
        self.period = period
        self.overbought = overbought
        self.oversold = oversold
    
    def analyze(self, prices: List[float], dates: List[str] = None) -> Signal:
        """分析并返回信号"""
        if len(prices) < self.period + 5:
            return Signal(
                name="RSI",
                signal="持有",
                confidence=0.5,
                details="数据不足"
            )
        
        df = pd.DataFrame({'close': prices})
        
        # 计算RSI
        delta = df['close'].diff()
        gain = delta.where(delta > 0, 0).rolling(window=self.period).mean()
        loss = -delta.where(delta < 0, 0).rolling(window=self.period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        current_rsi = rsi.iloc[-1]
        
        # 趋势RSI
        rsi_trend = rsi.iloc[-1] - rsi.iloc[-5] if len(rsi) >= 5 else 0
        
        # 信号判断
        if current_rsi >= self.overbought:
            signal = "卖出"
            confidence = 0.85
            details = f"RSI={current_rsi:.1f}，超买区域"
        elif current_rsi <= self.oversold:
            signal = "买入"
            confidence = 0.80
            details = f"RSI={current_rsi:.1f}，超卖区域"
        elif current_rsi > 60 and rsi_trend < -5:
            signal = "卖出"
            confidence = 0.65
            details = "RSI拐头向下，可能调整"
        elif current_rsi < 40 and rsi_trend > 5:
            signal = "买入"
            confidence = 0.65
            details = "RSI拐头向上，可能反弹"
        elif current_rsi > 50:
            signal = "持有"
            confidence = 0.55
            details = f"RSI={current_rsi:.1f}，偏强区域"
        else:
            signal = "持有"
            confidence = 0.55
            details = f"RSI={current_rsi:.1f}，偏弱区域"
        
        return Signal(
            name="RSI",
            signal=signal,
            confidence=confidence,
            details=details
        )


class BollingerBandStrategy:
    """布林带策略"""
    
    def __init__(self, window: int = 20, std_dev: int = 2):
        self.window = window
        self.std_dev = std_dev
    
    def analyze(self, prices: List[float], dates: List[str] = None) -> Signal:
        """分析并返回信号"""
        if len(prices) < self.window + 5:
            return Signal(
                name="布林带",
                signal="持有",
                confidence=0.5,
                details="数据不足"
            )
        
        df = pd.DataFrame({'close': prices})
        
        # 计算布林带
        df['middle'] = df['close'].rolling(window=self.window).mean()
        df['std'] = df['close'].rolling(window=self.window).std()
        df['upper'] = df['middle'] + (self.std_dev * df['std'])
        df['lower'] = df['middle'] - (self.std_dev * df['std'])
        
        current_price = prices[-1]
        current_upper = df['upper'].iloc[-1]
        current_lower = df['lower'].iloc[-1]
        current_middle = df['middle'].iloc[-1]
        
        # 位置判断
        position = (current_price - current_lower) / (current_upper - current_lower) if current_upper != current_lower else 0.5
        
        # 波动性
        bandwidth = (current_upper - current_lower) / current_middle
        prev_bandwidth = (df['upper'].iloc[-2] - df['lower'].iloc[-2]) / df['middle'].iloc[-2]
        volatility_change = bandwidth / prev_bandwidth if prev_bandwidth > 0 else 1
        
        # 信号判断
        if current_price >= current_upper:
            signal = "卖出"
            confidence = 0.85
            details = "价格触及上轨，警惕回调"
        elif current_price <= current_lower:
            signal = "买入"
            confidence = 0.80
            details = "价格触及下轨，可能反弹"
        elif position > 0.8 and volatility_change > 1.1:
            signal = "卖出"
            confidence = 0.70
            details = "价格接近上轨且波动放大"
        elif position < 0.2 and volatility_change > 1.1:
            signal = "买入"
            confidence = 0.70
            details = "价格接近下轨且波动放大"
        elif position > 0.5:
            signal = "持有"
            confidence = 0.55
            details = "价格在中轨上方运行"
        else:
            signal = "持有"
            confidence = 0.55
            details = "价格在中轨下方运行"
        
        return Signal(
            name="布林带",
            signal=signal,
            confidence=confidence,
            details=details
        )


class StrategyEngine:
    """策略引擎 - 综合多个策略"""
    
    def __init__(self):
        self.strategies = [
            MovingAverageStrategy(short_window=5, long_window=20),
            RSIStrategy(period=14, overbought=70, oversold=30),
            BollingerBandStrategy(window=20, std_dev=2)
        ]
    
    def analyze(self, prices: List[float], dates: List[str] = None) -> Dict:
        """综合分析并返回最终信号"""
        
        # 运行所有策略
        signals = []
        for strategy in self.strategies:
            signal = strategy.analyze(prices, dates)
            signals.append({
                'name': signal.name,
                'signal': signal.signal,
                'confidence': signal.confidence,
                'details': signal.details
            })
        
        # 投票机制
        votes = {'买入': 0, '卖出': 0, '持有': 0}
        total_confidence = {'买入': 0, '卖出': 0, '持有': 0}
        
        for s in signals:
            votes[s['signal']] += 1
            total_confidence[s['signal']] += s['confidence']
        
        # 选择票数最多的
        final_action = max(votes, key=lambda x: (votes[x], total_confidence[x]))
        
        # 计算最终置信度
        avg_confidence = total_confidence[final_action] / votes[final_action] if votes[final_action] > 0 else 0.5
        
        return {
            'signals': signals,
            'final_action': final_action,
            'confidence': avg_confidence,
            'votes': votes
        }
    
    def calculate_position(self, total_capital: float, confidence: float, final_action: str) -> float:
        """计算建议仓位"""
        if final_action != "买入":
            return 0
        
        # 基于置信度计算仓位 (10%-50%)
        position_pct = 0.1 + (confidence - 0.5) * 0.8
        position_pct = max(0.1, min(0.5, position_pct))
        
        return round(total_capital * position_pct, 2)


# 测试
if __name__ == "__main__":
    # 模拟价格数据
    np.random.seed(42)
    prices = list(np.cumsum(np.random.randn(100) * 0.01) + 4)
    
    engine = StrategyEngine()
    result = engine.analyze(prices)
    
    print("策略分析结果:")
    print(f"信号: {result['signals']}")
    print(f"最终操作: {result['final_action']}")
    print(f"置信度: {result['confidence']:.2f}")
    print(f"投票: {result['votes']}")
    print(f"建议金额: ¥{engine.calculate_position(10000, result['confidence'], result['final_action'])}")
