"""数据库模型"""
from sqlalchemy import create_engine, Column, String, Float, Date, DateTime, Text, JSON, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

Base = declarative_base()


class ETFFund(Base):
    """ETF基本信息表"""
    __tablename__ = 'etf_funds'
    
    code = Column(String(20), primary_key=True)  # ETF代码
    name = Column(String(100))  # 基金名称
    exchange = Column(String(20))  # 交易所
    category = Column(String(50))  # 类别
    added_date = Column(Date, default=datetime.now().date)  # 添加日期
    config = Column(JSON)  # 配置（资金比例、策略参数等）
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class DailyStrategy(Base):
    """每日策略记录表"""
    __tablename__ = 'daily_strategies'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    etf_code = Column(String(20), index=True)  # ETF代码
    date = Column(Date, index=True)  # 策略日期
    raw_signals = Column(JSON)  # 原始信号
    final_action = Column(String(20))  # 最终操作
    suggested_amount = Column(Float)  # 建议金额
    llm_advice = Column(Text)  # LLM建议
    actual_action = Column(String(20))  # 用户实际执行
    actual_amount = Column(Float)  # 实际金额
    remark = Column(Text)  # 备注
    created_at = Column(DateTime, default=datetime.now)


class PriceHistory(Base):
    """历史价格数据表"""
    __tablename__ = 'price_history'
    
    etf_code = Column(String(20), primary_key=True)
    date = Column(Date, primary_key=True)
    open = Column(Float)
    close = Column(Float)
    high = Column(Float)
    low = Column(Float)
    volume = Column(Float)
    change_pct = Column(Float)  # 涨跌幅


class LLMCache(Base):
    """LLM响应缓存表"""
    __tablename__ = 'llm_cache'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    signal_key = Column(String(200), unique=True)  # 信号唯一标识
    prompt = Column(Text)  # 请求prompt
    response = Column(Text)  # LLM响应
    created_at = Column(DateTime, default=datetime.now)
    expires_at = Column(DateTime)  # 过期时间


class Database:
    """数据库管理器"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_db()
        return cls._instance
    
    def _init_db(self):
        """初始化数据库"""
        db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'etf_quant.db')
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        self.engine = create_engine(f'sqlite:///{db_path}', echo=False)
        self.Session = sessionmaker(bind=self.engine)
        Base.metadata.create_all(self.engine)
    
    def get_session(self):
        """获取数据库会话"""
        return self.Session()
    
    def add_etf(self, code: str, name: str, exchange: str = '', category: str = '', config: dict = None):
        """添加ETF"""
        session = self.get_session()
        try:
            etf = ETFFund(
                code=code,
                name=name,
                exchange=exchange,
                category=category,
                config=config or {}
            )
            session.add(etf)
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def get_etf_list(self):
        """获取ETF列表"""
        session = self.get_session()
        try:
            return session.query(ETFFund).all()
        finally:
            session.close()
    
    def save_price_history(self, etf_code: str, prices: list):
        """保存价格历史"""
        session = self.get_session()
        try:
            for p in prices:
                price = PriceHistory(
                    etf_code=etf_code,
                    date=p['date'],
                    open=p['open'],
                    close=p['close'],
                    high=p['high'],
                    low=p['low'],
                    volume=p['volume'],
                    change_pct=p.get('change_pct', 0)
                )
                session.merge(price)
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def get_price_history(self, etf_code: str, days: int = 180):
        """获取价格历史"""
        session = self.get_session()
        try:
            from datetime import timedelta
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days)
            
            return session.query(PriceHistory).filter(
                PriceHistory.etf_code == etf_code,
                PriceHistory.date >= start_date
            ).order_by(PriceHistory.date).all()
        finally:
            session.close()
    
    def save_daily_strategy(self, strategy: dict):
        """保存每日策略"""
        session = self.get_session()
        try:
            daily = DailyStrategy(
                etf_code=strategy['etf_code'],
                date=strategy['date'],
                raw_signals=strategy['raw_signals'],
                final_action=strategy['final_action'],
                suggested_amount=strategy['suggested_amount'],
                llm_advice=strategy.get('llm_advice', '')
            )
            session.add(daily)
            session.commit()
            return daily.id
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def get_daily_strategies(self, etf_code: str, limit: int = 30):
        """获取历史策略"""
        session = self.get_session()
        try:
            return session.query(DailyStrategy).filter(
                DailyStrategy.etf_code == etf_code
            ).order_by(DailyStrategy.date.desc()).limit(limit).all()
        finally:
            session.close()


# 全局数据库实例
db = Database()
