# ETF量化助手项目上下文

## 项目概述

**ETF量化助手 (ETF Quant Assistant)** 是一个为个人投资者设计的ETF量化分析工具，结合技术指标分析和LLM智能解读，提供明确的操作建议。项目采用 FastAPI 后端 + 原生 HTML/JS 前端的架构，使用 akshare 获取免费金融数据，支持多种量化策略（双均线、RSI、布林带）和智能投资建议生成。

### 核心特性
- **ETF管理**: 添加、搜索、管理自选ETF
- **策略分析**: 双均线、RSI、布林带多策略并行，投票机制生成综合信号
- **LLM智能解读**: 支持DeepSeek/OpenAI API，将技术指标转化为自然语言建议
- **数据可视化**: ECharts交互式图表展示历史价格走势
- **本地持久化**: SQLite数据库存储ETF信息、策略记录和价格历史

---

## 技术栈

### 后端
- **Python**: 3.12+
- **Web框架**: FastAPI (0.109.0+)
- **ASGI服务器**: Uvicorn (0.27.0+)
- **数据源**: akshare (1.11.0+) - 免费金融数据API
- **数据处理**: pandas (2.1.0+) + numpy (1.26.0+)
- **数据库**: SQLAlchemy (2.0.46+) + SQLite
- **环境配置**: python-dotenv (1.0.0+)

### 前端
- **基础**: HTML5 + CSS3 + Vanilla JavaScript
- **图表库**: ECharts (echarts.min.js)
- **样式**: Material Design风格

### 包管理
- **工具**: uv (快速Python包管理器)
- **配置**: pyproject.toml

---

## 项目结构

```
/home/gxstar123/Program/SIA/
├── main.py                      # 项目入口 (启动FastAPI服务)
├── pyproject.toml               # 项目配置和依赖定义
├── README.md                    # 用户文档
├── 开发文档.md                  # 详细开发文档（中文）
├── AGENTS.md                    # 本文件 - 上下文文档
│
├── app/
│   ├── main.py                  # FastAPI应用实例，路由配置
│   │
│   ├── api/                     # API路由层
│   │   ├── etf.py               # ETF管理API (list, add, remove, search)
│   │   ├── strategy.py          # 策略分析API
│   │   └── data.py              # 数据服务API
│   │
│   ├── models/                  # 数据模型层
│   │   └── database.py          # SQLAlchemy模型和数据库管理器
│   │       - ETFFund: ETF基本信息
│   │       - DailyStrategy: 每日策略记录
│   │       - PriceHistory: 历史价格数据
│   │       - LLMCache: LLM响应缓存
│   │
│   ├── services/                # 业务逻辑层
│   │   ├── data_service.py      # ETF数据获取服务 (akshare封装)
│   │   ├── strategy_engine.py   # 量化策略引擎
│   │   └── llm_service.py       # LLM解释服务
│   │
│   └── static/                  # 前端静态资源
│       ├── index.html           # 主页面
│       ├── css/
│       │   └── style.css        # 样式文件
│       └── js/
│           ├── app.js           # 前端逻辑
│           └── echarts.min.js   # ECharts库
│
└── data/
    └── etf_quant.db             # SQLite数据库文件
```

---

## 构建和运行

### 环境准备

**使用 uv (推荐):**
```bash
# 同步依赖
uv sync

# 运行项目
uv run python main.py
```

**使用虚拟环境:**
```bash
# 创建并激活虚拟环境
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# 安装依赖
pip install -r requirements.txt

# 运行项目
python main.py
```

### 启动服务

```bash
# 方式1: 直接运行入口文件
python main.py

# 方式2: 使用uvicorn直接运行FastAPI
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

服务启动后访问: http://localhost:8000

### API端点

| 端点 | 方法 | 描述 |
|------|------|------|
| `/` | GET | 前端页面 |
| `/health` | GET | 健康检查 |
| `/api/etf/list` | GET | 获取ETF列表 |
| `/api/etf/add?code=xxx` | POST | 添加ETF |
| `/api/etf/search?keyword=xxx` | GET | 搜索ETF |
| `/api/etf/{code}/info` | GET | 获取ETF详细信息 |
| `/api/etf/{code}/realtime` | GET | 获取实时价格 |
| `/api/data/{code}/price?period=1m` | GET | 获取价格历史 |
| `/api/strategy/{code}` | GET | 策略分析 |
| `/api/strategy/{code}/history` | GET | 历史策略记录 |

---

## 开发约定

### 代码风格
- **Python**: 遵循PEP 8规范
- **注释**: 使用中文注释，清晰说明业务逻辑
- **类型提示**: 使用Python类型提示 (`typing` 模块)
- **文档字符串**: 使用三引号文档字符串说明函数功能

### 命名约定
- **类名**: PascalCase (如 `ETFDataService`)
- **函数/方法**: snake_case (如 `get_etf_info`)
- **常量**: UPPER_SNAKE_CASE (如 `MAX_RETRIES`)
- **数据库表**: snake_case (如 `etf_funds`)

### 异步处理
- API路由使用 `async/await` 模式
- 阻塞IO操作（如akshare调用）使用 `ThreadPoolExecutor` 包装
- 设置合理的超时时间（通常3-5秒）

### 错误处理
- 使用 `try-except` 捕获异常
- API层抛出 `HTTPException` 返回合适的HTTP状态码
- 外部API调用失败时提供fallback（如使用模拟数据）

### 数据库操作
- 使用单例模式的 `Database` 类
- 每次操作获取新session，完成后关闭
- 使用 `session.commit()` 提交事务
- 异常时使用 `session.rollback()` 回滚

---

## 关键模块说明

### 1. 数据服务 (`app/services/data_service.py`)

**ETFDataService**: 封装akshare API，提供ETF数据获取
- `get_etf_info(code)`: 获取ETF基本信息
- `get_realtime_price(code)`: 获取实时价格
- `get_price_history(code, period)`: 获取历史价格 (1w/1m/3m/6m/1y)
- `get_intraday_data(code)`: 获取分时数据
- `search_etf(keyword)`: 搜索ETF

**重试机制**: 所有外部API调用都有重试机制（最多3次，间隔2秒）

**Fallback**: API失败时返回模拟数据，确保系统可用性

### 2. 策略引擎 (`app/services/strategy_engine.py`)

**策略类型**:
- `MovingAverageStrategy`: 双均线策略 (MA5/MA20)
- `RSIStrategy`: RSI指标策略 (周期14, 超买70/超卖30)
- `BollingerBandStrategy`: 布林带策略 (20日, 2倍标准差)

**StrategyEngine**: 综合策略引擎
- 运行所有策略生成信号
- 投票机制决定最终操作（买入/卖出/持有）
- 基于置信度计算建议仓位（10%-50%）

### 3. 数据库模型 (`app/models/database.py`)

**表结构**:
- `ETFFund`: ETF基本信息 (code, name, exchange, category, config)
- `DailyStrategy`: 每日策略记录 (etf_code, date, raw_signals, final_action, llm_advice)
- `PriceHistory`: 历史价格数据 (etf_code, date, open, close, high, low, volume)
- `LLMCache`: LLM响应缓存 (signal_key, prompt, response, expires_at)

**数据库路径**: `app/data/etf_quant.db`

### 4. API路由 (`app/api/`)

- `etf.py`: ETF管理相关API
- `strategy.py`: 策略分析相关API
- `data.py`: 数据服务相关API

所有API返回统一格式:
```json
{
  "code": 0,
  "message": "success",
  "data": {...}
}
```

---

## LLM配置（可选）

创建 `.env` 文件启用LLM功能:

```env
# DeepSeek API（推荐）
DEEPSEEK_API_KEY=your_api_key
LLM_PROVIDER=deepseek

# 或 OpenAI API
OPENAI_API_KEY=your_api_key
LLM_PROVIDER=openai

# 本地Mock模式（无API调用）
LLM_PROVIDER=mock
```

---

## 注意事项

1. **数据延迟**: akshare免费数据可能有15分钟延迟
2. **重试机制**: 外部API调用失败时自动重试3次
3. **模拟数据**: API失败时返回模拟数据，不影响系统可用性
4. **数据库**: SQLite文件位于 `app/data/etf_quant.db`
5. **静态文件**: 前端文件位于 `app/static/`
6. **包管理**: 使用 `uv sync` 同步依赖，或手动 `pip install`
7. **端口**: 默认使用8000端口，可通过修改启动命令更改

---

## 常见任务

### 添加新的量化策略
1. 在 `app/services/strategy_engine.py` 创建策略类，继承基础接口
2. 实现 `analyze(prices, dates)` 方法返回 `Signal` 对象
3. 在 `StrategyEngine.__init__()` 的 `self.strategies` 列表中注册

### 添加新的API端点
1. 在 `app/api/` 目录下创建或编辑路由文件
2. 使用 `APIRouter` 定义路由
3. 在 `app/main.py` 中注册路由

### 添加新的数据模型
1. 在 `app/models/database.py` 创建SQLAlchemy模型类
2. 在 `Database` 类中添加对应的CRUD方法
3. 重启应用，SQLAlchemy会自动创建新表

---

## 项目状态

- **当前分支**: master
- **最新提交**: "Refactor code structure for improved readability and maintainability"
- **未跟踪文件**: AGENTS.md (本文件)