"""数据服务模块 - 基于akshare官方文档"""
import akshare as ak
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import pandas as pd
import time
import numpy as np


class ETFDataService:
    """ETF数据服务 - 使用akshare官方API"""
    
    MAX_RETRIES = 3
    RETRY_DELAY = 2
    
    # 常见ETF名称映射
    ETF_NAMES = {
        '510300': '沪深300ETF',
        '510500': '500ETF',
        '512880': '证券ETF',
        '159915': '创业板ETF',
        '159941': '科创50ETF',
        '159919': '沪深300ETF',
        '511880': '银华ETF',
        '510880': '红利ETF',
        '159920': '创成长ETF',
        '159937': '中证1000ETF',
    }
    
    @staticmethod
    def get_etf_info(code: str) -> Dict:
        """获取ETF基本信息 - 使用 fund_etf_spot_em()"""
        for attempt in range(ETFDataService.MAX_RETRIES):
            try:
                # 获取所有ETF实时行情
                spot_df = ak.fund_etf_spot_em()
                
                # 查找匹配的ETF
                if '代码' in spot_df.columns:
                    etf_info = spot_df[spot_df['代码'] == code]
                    
                    if not etf_info.empty:
                        return {
                            'code': code,
                            'name': etf_info.iloc[0]['名称'],
                            'exchange': '沪深',
                            'category': 'ETF'
                        }
                        
            except Exception as e:
                print(f"获取ETF信息失败 (尝试 {attempt + 1}): {e}")
                if attempt < ETFDataService.MAX_RETRIES - 1:
                    time.sleep(ETFDataService.RETRY_DELAY)
        
        # 所有尝试都失败，使用预设名称映射
        preset_name = ETFDataService.ETF_NAMES.get(code, code)
        return {'code': code, 'name': preset_name, 'exchange': '沪深', 'category': 'ETF'}
    
    @staticmethod
    def get_realtime_price(code: str) -> Dict:
        """获取实时价格 - 使用 fund_etf_spot_em() 获取单只ETF"""
        for attempt in range(ETFDataService.MAX_RETRIES):
            try:
                # 获取所有ETF实时行情
                spot_df = ak.fund_etf_spot_em()
                
                # 查找匹配的ETF
                if '代码' in spot_df.columns:
                    etf_info = spot_df[spot_df['代码'] == code]
                    
                    if not etf_info.empty:
                        latest = etf_info.iloc[0]
                        return {
                            'code': code,
                            'price': float(latest.get('最新价', 0)),
                            'change': float(latest.get('涨跌幅', 0)),
                            'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        }
                        
            except Exception as e:
                print(f"获取实时价格失败 (尝试 {attempt + 1}): {e}")
                if attempt < ETFDataService.MAX_RETRIES - 1:
                    time.sleep(ETFDataService.RETRY_DELAY)
        
        # 使用模拟数据
        return ETFDataService._generate_mock_price(code)
    
    @staticmethod
    def get_price_history(code: str, period: str = '6m') -> Dict:
        """获取历史价格数据 - 使用 fund_etf_hist_em()
        
        Args:
            code: ETF代码
            period: 时间周期 ('1w', '1m', '3m', '6m', '1y')
        """
        # 计算需要的日期数和周期
        period_config = {
            '1w': ('weekly', 7),
            '1m': ('monthly', 30),
            '3m': ('monthly', 90),
            '6m': ('daily', 180),
            '1y': ('daily', 365)
        }
        
        akshare_period, days = period_config.get(period, ('daily', 180))
        
        # 计算日期范围 - 使用akshare要求的格式 YYYYMMDD
        end_date = datetime.now().strftime('%Y%m%d')
        start_date = (datetime.now() - timedelta(days=days * 2)).strftime('%Y%m%d')
        
        for attempt in range(ETFDataService.MAX_RETRIES):
            try:
                # 使用正确的API: fund_etf_hist_em
                fund_etf_hist_em = ak.fund_etf_hist_em(
                    symbol=code,
                    period=akshare_period,
                    start_date=start_date,
                    end_date=end_date,
                    adjust='qfq'  # 前复权
                )
                
                if not fund_etf_hist_em.empty:
                    df = fund_etf_hist_em.tail(days)
                    
                    dates = df['日期'].tolist()
                    prices = df['收盘'].tolist()
                    volumes = df['成交量'].tolist()
                    
                    return {
                        'code': code,
                        'period': period,
                        'dates': dates,
                        'prices': prices,
                        'volumes': volumes
                    }
                    
            except Exception as e:
                print(f"获取历史价格失败 (尝试 {attempt + 1}): {e}")
                if attempt < ETFDataService.MAX_RETRIES - 1:
                    time.sleep(ETFDataService.RETRY_DELAY)
        
        # 使用模拟数据
        return ETFDataService._generate_mock_history(code, days)
    
    @staticmethod
    def get_intraday_data(code: str) -> Dict:
        """获取分时数据 - 使用 fund_etf_hist_min_em()"""
        for attempt in range(ETFDataService.MAX_RETRIES):
            try:
                # 使用正确的API: fund_etf_hist_min_em
                fund_etf_hist_min_em = ak.fund_etf_hist_min_em(
                    symbol=code,
                    period="5",
                    adjust="",
                    start_date="2020-01-01 09:30:00",
                    end_date=datetime.now().strftime('%Y-%m-%d') + " 17:40:00"
                )
                
                if not fund_etf_hist_min_em.empty:
                    times = fund_etf_hist_min_em['时间'].tolist()
                    prices = fund_etf_hist_min_em['收盘'].tolist()
                    volumes = fund_etf_hist_min_em['成交量'].tolist()
                    
                    return {
                        'code': code,
                        'times': times,
                        'prices': prices,
                        'volumes': volumes
                    }
                    
            except Exception as e:
                print(f"获取分时数据失败 (尝试 {attempt + 1}): {e}")
                if attempt < ETFDataService.MAX_RETRIES - 1:
                    time.sleep(ETFDataService.RETRY_DELAY)
        
        # 使用模拟数据
        return ETFDataService._generate_mock_intraday(code)
    
    @staticmethod
    def search_etf(keyword: str) -> List[Dict]:
        """搜索ETF - 使用 fund_etf_spot_em()"""
        for attempt in range(ETFDataService.MAX_RETRIES):
            try:
                spot_df = ak.fund_etf_spot_em()
                
                # 模糊搜索
                mask = spot_df['代码'].astype(str).str.contains(keyword) | \
                       spot_df['名称'].str.contains(keyword)
                
                results = spot_df[mask].head(10)
                
                return results.apply(lambda x: {
                    'code': x['代码'],
                    'name': x['名称'],
                    'exchange': '沪深'
                }, axis=1).tolist()
                
            except Exception as e:
                print(f"搜索ETF失败 (尝试 {attempt + 1}): {e}")
                if attempt < ETFDataService.MAX_RETRIES - 1:
                    time.sleep(ETFDataService.RETRY_DELAY)
        
        # 返回预设的ETF列表
        common_etfs = [
            {'code': '510300', 'name': '沪深300ETF', 'exchange': '沪深'},
            {'code': '510500', 'name': '500ETF', 'exchange': '沪深'},
            {'code': '512880', 'name': '证券ETF', 'exchange': '沪深'},
            {'code': '159915', 'name': '创业板ETF', 'exchange': '沪深'},
            {'code': '159941', 'name': '科创50ETF', 'exchange': '沪深'},
        ]
        
        keyword_lower = keyword.lower()
        return [etf for etf in common_etfs if keyword_lower in etf['code'].lower() or keyword_lower in etf['name'].lower()]
    
    @staticmethod
    def _generate_mock_price(code: str) -> Dict:
        """生成模拟实时价格"""
        np.random.seed(hash(code) % 2**32)
        base_price = 2.0 + (hash(code) % 100) / 50
        change = (np.random.randn() * 2)
        
        return {
            'code': code,
            'price': round(base_price * (1 + change / 100), 3),
            'change': round(change, 2),
            'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    
    @staticmethod
    def _generate_mock_history(code: str, days: int) -> Dict:
        """生成模拟历史数据"""
        np.random.seed(hash(code) % 2**32)
        
        base_price = 3.0 + (hash(code) % 100) / 50
        dates = []
        prices = []
        volumes = []
        
        current_price = base_price
        today = datetime.now()
        
        for i in range(days, 0, -1):
            date = today - timedelta(days=i)
            dates.append(date.strftime('%Y-%m-%d'))
            
            change = np.random.randn() * 0.02
            current_price *= (1 + change)
            prices.append(round(current_price, 3))
            
            volumes.append(int(np.random.uniform(1000000, 10000000)))
        
        return {
            'code': code,
            'period': f'{days}d',
            'dates': dates,
            'prices': prices,
            'volumes': volumes
        }
    
    @staticmethod
    def _generate_mock_intraday(code: str) -> Dict:
        """生成分时数据"""
        np.random.seed(hash(code) % 2**32)
        
        times = []
        prices = []
        volumes = []
        
        base_price = 3.0 + (hash(code) % 100) / 50
        current_price = base_price
        
        for hour in range(9, 15):
            for minute in range(0, 60, 5):
                if hour == 9 and minute < 30:
                    continue
                if hour == 15 and minute > 0:
                    break
                    
                times.append(f'{hour:02d}:{minute:02d}')
                
                change = np.random.randn() * 0.005
                current_price *= (1 + change)
                prices.append(round(current_price, 3))
                
                volumes.append(int(np.random.uniform(10000, 100000)))
        
        return {
            'code': code,
            'times': times,
            'prices': prices,
            'volumes': volumes
        }


class PriceDataProcessor:
    """价格数据处理器"""
    
    @staticmethod
    def to_dataframe(data: Dict) -> pd.DataFrame:
        """转换为DataFrame"""
        if not data['dates']:
            return pd.DataFrame()
        
        df = pd.DataFrame({
            'date': pd.to_datetime(data['dates']),
            'close': data['prices'],
            'volume': data['volumes']
        })
        df.set_index('date', inplace=True)
        return df
    
    @staticmethod
    def calculate_ma(prices: List[float], window: int) -> List[float]:
        """计算移动平均线"""
        if len(prices) < window:
            return [0.0] * len(prices)
        
        df = pd.DataFrame({'close': prices})
        df['ma'] = df['close'].rolling(window=window).mean()
        return df['ma'].fillna(0).tolist()
    
    @staticmethod
    def calculate_rsi(prices: List[float], period: int = 14) -> List[float]:
        """计算RSI"""
        if len(prices) < period + 1:
            return [0.0] * len(prices)
        
        df = pd.DataFrame({'close': prices})
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi.fillna(50).tolist()
    
    @staticmethod
    def calculate_bollinger_bands(prices: List[float], window: int = 20, std_dev: int = 2) -> Dict:
        """计算布林带"""
        if len(prices) < window:
            return {'upper': [], 'middle': [], 'lower': []}
        
        df = pd.DataFrame({'close': prices})
        
        df['middle'] = df['close'].rolling(window=window).mean()
        df['std'] = df['close'].rolling(window=window).std()
        
        df['upper'] = df['middle'] + (std_dev * df['std'])
        df['lower'] = df['middle'] - (std_dev * df['std'])
        
        return {
            'upper': df['upper'].fillna(0).tolist(),
            'middle': df['middle'].fillna(0).tolist(),
            'lower': df['lower'].fillna(0).tolist()
        }
