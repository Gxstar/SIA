# ETF量化助手 (ETF Quant Assistant)

一个为个人投资者设计的ETF量化分析工具，结合技术指标分析和LLM智能解读，提供明确的操作建议。

## ✨ 功能特性

### 📊 ETF管理
- **添加ETF**：输入ETF代码（如510300）自动获取基金信息
- **ETF列表**：展示自选ETF，实时涨跌幅和价格
- **持仓配置**：设置资金比例和风险偏好

### 📈 策略分析
- **双均线策略**：MA5/MA20金叉死叉判断买卖时机
- **RSI策略**：识别超买超卖区域
- **布林带策略**：价格波动区间分析
- **投票机制**：综合多策略信号生成最终建议

### 🤖 LLM智能解读
- 技术指标转化为通俗易懂的投资逻辑
- 个性化风险提示和市场分析
- 缓存机制避免重复调用API

### 📉 数据可视化
- 历史价格走势图（支持1-6个月）
- 技术指标叠加显示
- ECharts交互式图表

### 💾 数据管理
- SQLite本地数据库持久化存储
- 历史策略记录查询
- 策略绩效跟踪

## 🚀 快速开始

### 1. 安装依赖

```bash
cd /home/gxstar123/编程/SIA
.venv/bin/pip install -r requirements.txt
# 或使用uv
uv sync
```

### 2. 启动服务

```bash
cd /home/gxstar123/编程/SIA
.venv/bin/python main.py
```

服务运行在：http://localhost:8000

### 3. 访问界面

在浏览器打开 **http://localhost:8000**

## 📡 API接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/` | GET | 前端页面 |
| `/api/etf/list` | GET | 获取ETF列表 |
| `/api/etf/add?code=xxx` | POST | 添加ETF |
| `/api/etf/search?keyword=xxx` | GET | 搜索ETF |
| `/api/data/{code}/price?period=1m` | GET | 获取价格历史 |
| `/api/strategy/{code}` | GET | 策略分析 |
| `/api/strategy/{code}/history` | GET | 历史策略记录 |
| `/health` | GET | 健康检查 |

## ⚙️ 配置LLM（可选）

创建 `.env` 文件启用LLM智能解读：

```env
# DeepSeek API（推荐）
DEEPSEEK_API_KEY=your_api_key
LLM_PROVIDER=deepseek

# 或 OpenAI API
OPENAI_API_KEY=your_api_key
LLM_PROVIDER=openai

# 或本地Mock模式
LLM_PROVIDER=mock
```

重启服务后生效。

## 📁 项目结构

```
/home/gxstar123/编程/SIA/
├── app/
│   ├── main.py              # FastAPI入口
│   ├── api/
│   │   ├── etf.py           # ETF管理API
│   │   ├── strategy.py      # 策略分析API
│   │   └── data.py          # 数据服务API
│   ├── models/
│   │   └── database.py      # SQLite数据库模型
│   ├── services/
│   │   ├── data_service.py      # 数据获取服务
│   │   ├── strategy_engine.py   # 量化策略引擎
│   │   └── llm_service.py       # LLM解释服务
│   └── static/
│       ├── index.html       # 主页面
│       ├── css/style.css    # 样式
│       └── js/
│           ├── app.js       # 前端逻辑
│           └── echarts.min.js
├── data/
│   └── etf_quant.db         # SQLite数据库
├── .env                     # LLM配置（可选）
├── main.py                  # 启动入口
└── pyproject.toml           # 项目配置
```

## 🛠️ 技术栈

- **后端**：FastAPI + Python 3.12
- **前端**：HTML5 + CSS3 + Vanilla JS
- **数据源**：akshare（免费金融数据）
- **数据库**：SQLite
- **图表**：ECharts
- **量化计算**：Pandas + NumPy

## 📝 使用说明

1. 在输入框输入ETF代码（如 `510300`）
2. 点击"添加"按钮
3. 点击ETF卡片查看详细分析
4. 右侧面板展示策略建议和AI解读

## ⚠️ 风险提示

- 本工具仅供学习和研究，不构成投资建议
- 免费数据源可能存在延迟
- 量化策略无法适应所有市场环境
- 投资有风险，请谨慎决策

## 📄 许可证

MIT License
