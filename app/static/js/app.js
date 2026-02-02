/**
 * ETF量化助手 - 主应用逻辑
 */

class ETFQuantApp {
    constructor() {
        this.selectedEtf = null;
        this.chart = null;
        this.loading = false;
        this.loadingProgress = 0;
        this.init();
    }

    init() {
        this.bindEvents();
        this.loadEtfList();
        this.initChart();
    }

    // 显示/隐藏全局加载状态
    setLoading(loading, message = '加载中...') {
        this.loading = loading;
        
        let overlay = document.getElementById('loadingOverlay');
        if (loading) {
            if (!overlay) {
                overlay = document.createElement('div');
                overlay.id = 'loadingOverlay';
                overlay.innerHTML = `
                    <div class="loading-spinner"></div>
                    <div class="loading-message">${message}</div>
                    <div class="loading-progress-bar">
                        <div class="loading-progress-fill" id="loadingProgress"></div>
                    </div>
                `;
                overlay.style.cssText = `
                    position: fixed;
                    top: 0;
                    left: 0;
                    right: 0;
                    bottom: 0;
                    background: rgba(255, 255, 255, 0.9);
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    justify-content: center;
                    z-index: 9999;
                `;
                document.body.appendChild(overlay);
            }
            overlay.style.display = 'flex';
            document.body.style.cursor = 'wait';
        } else {
            if (overlay) {
                overlay.style.display = 'none';
            }
            document.body.style.cursor = 'default';
        }
        
        // 禁用/启用按钮
        document.querySelectorAll('.btn').forEach(btn => {
            btn.disabled = loading;
        });
    }

    // 更新加载进度
    setLoadingProgress(progress) {
        this.loadingProgress = progress;
        const progressBar = document.getElementById('loadingProgress');
        if (progressBar) {
            progressBar.style.width = `${progress}%`;
        }
    }

    // 显示通知
    showNotification(message, type = 'info') {
        // 创建通知元素
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 12px 20px;
            border-radius: 8px;
            color: white;
            font-size: 14px;
            z-index: 10000;
            animation: slideIn 0.3s ease;
            background: ${type === 'success' ? '#10b981' : type === 'error' ? '#ef4444' : '#2563eb'};
        `;
        
        document.body.appendChild(notification);
        
        // 3秒后移除
        setTimeout(() => {
            notification.style.opacity = '0';
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }

    // 绑定事件
    bindEvents() {
        // 添加ETF
        document.getElementById('addEtfBtn').addEventListener('click', () => {
            this.addEtf();
        });

        document.getElementById('etfCodeInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.addEtf();
        });

        // 刷新数据
        document.getElementById('syncBtn').addEventListener('click', () => {
            this.syncData();
        });

        // 图表切换
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.switchChart(e.target.dataset.tab);
            });
        });
    }

    // 加载ETF列表
    async loadEtfList() {
        try {
            this.setLoadingProgress(10);
            const response = await fetch('/api/etf/list');
            const result = await response.json();
            
            if (result.code === 0 && result.data.length > 0) {
                this.renderEtfList(result.data);
            } else {
                this.renderEmptyEtfList();
            }
            this.setLoadingProgress(30);
        } catch (error) {
            console.error('加载ETF列表失败:', error);
            this.renderEmptyEtfList();
        }
    }

    // 渲染空ETF列表
    renderEmptyEtfList() {
        const container = document.getElementById('etfList');
        container.innerHTML = `
            <div class="empty-state" style="padding: 20px;">
                <p>暂无ETF</p>
                <p style="font-size: 12px; color: #999;">在上方输入框添加ETF代码</p>
            </div>
        `;
    }

    // 渲染ETF列表
    renderEtfList(etfList) {
        const container = document.getElementById('etfList');
        container.innerHTML = etfList.map(etf => `
            <div class="etf-card" data-code="${etf.code}">
                <div class="etf-card-header">
                    <span class="etf-card-code">${etf.code}</span>
                    <span class="etf-card-change ${etf.change >= 0 ? 'change-positive' : 'change-negative'}">
                        ${etf.change !== null ? (etf.change >= 0 ? '+' : '') + etf.change.toFixed(2) + '%' : '-'}
                    </span>
                </div>
                <div class="etf-card-name">${etf.name || etf.code}</div>
                <div class="etf-card-price">${etf.price !== null ? '¥' + etf.price.toFixed(3) : '-'}</div>
            </div>
        `).join('');

        // 绑定点击事件
        container.querySelectorAll('.etf-card').forEach(card => {
            card.addEventListener('click', () => {
                this.selectEtf(card.dataset.code);
            });
        });
        this.setLoadingProgress(50);
    }

    // 选择ETF - 优化加载体验
    async selectEtf(code) {
        this.selectedEtf = code;
        
        // 更新选中状态
        document.querySelectorAll('.etf-card').forEach(card => {
            card.classList.toggle('active', card.dataset.code === code);
        });

        // 更新ETF信息头部
        document.getElementById('selectedEtfCode').textContent = code;
        
        // 显示加载状态
        this.setLoading(true, '正在加载数据...');
        this.setLoadingProgress(0);
        
        try {
            // 分步加载，避免一次性请求太多
            this.setLoadingProgress(10);
            
            // 先加载基础信息
            const infoRes = await fetch(`/api/etf/${code}/info`);
            const infoResult = await infoRes.json();
            this.setLoadingProgress(20);
            
            if (infoResult.code === 0) {
                document.getElementById('selectedEtfName').textContent = infoResult.data.name || code;
            }
            
            // 并行加载策略和图表数据
            this.setLoadingProgress(30);
            const [strategyRes, chartRes] = await Promise.all([
                fetch(`/api/strategy/${code}`),
                fetch(`/api/data/${code}/price?period=6m`)
            ]);
            
            this.setLoadingProgress(60);
            
            const strategyResult = await strategyRes.json();
            const chartResult = await chartRes.json();
            
            // 更新策略建议
            if (strategyResult.code === 0) {
                this.renderStrategy(strategyResult.data);
            }
            
            this.setLoadingProgress(80);
            
            // 渲染图表
            if (chartResult.code === 0 && chartResult.data.dates?.length > 0) {
                this.renderChart(chartResult.data);
            } else {
                this.renderEmptyChart(code);
            }
            
            this.setLoadingProgress(100);
            
            // 异步加载历史记录（不阻塞主界面）
            this.loadHistoryAsync(code);
            
        } catch (error) {
            console.error('加载ETF数据失败:', error);
            this.showNotification('部分数据加载失败', 'error');
        } finally {
            setTimeout(() => {
                this.setLoading(false);
            }, 300);
        }
    }

    // 异步加载历史记录（不阻塞）
    async loadHistoryAsync(code) {
        try {
            const [historyRes, perfRes] = await Promise.all([
                fetch(`/api/strategy/${code}/history?days=30`),
                fetch(`/api/strategy/${code}/performance?days=30`)
            ]);
            
            const historyResult = await historyRes.json();
            const perfResult = await perfRes.json();
            
            if (historyResult.code === 0 && historyResult.data.length > 0) {
                this.renderHistory(historyResult.data);
            }
            
            if (perfResult.code === 0) {
                this.renderPerformance(perfResult.data);
            }
        } catch (error) {
            console.error('加载历史记录失败:', error);
        }
    }

    // 渲染策略建议
    renderStrategy(data) {
        const container = document.getElementById('strategyCards');
        
        if (!data || !data.signals) {
            container.innerHTML = '<div class="empty-state">选择ETF查看策略建议</div>';
            return;
        }
        
        const signalMap = {
            '买入': 'buy',
            '卖出': 'sell',
            '持有': 'hold',
            '等待': 'hold'
        };

        const cardsHtml = data.signals.map(signal => `
            <div class="strategy-card ${signalMap[signal.signal] || 'hold'}">
                <div class="strategy-card-header">
                    <span class="strategy-name">${signal.name}</span>
                    <span class="strategy-signal signal-${signalMap[signal.signal] || 'hold'}">${signal.signal}</span>
                </div>
                <div class="strategy-confidence">置信度: ${((signal.confidence || 0) * 100).toFixed(0)}%</div>
            </div>
        `).join('');

        const finalAdvice = `
            <div class="final-advice">
                <div class="final-advice-header">📋 最终操作建议: ${data.final_action || '观望'} ${data.amount ? '¥' + data.amount : ''}</div>
                <div class="llm-advice">
                    <strong>🤖 AI分析:</strong> ${data.llm_advice || '暂无分析'}
                </div>
            </div>
        `;

        container.innerHTML = cardsHtml + finalAdvice;
    }

    // 添加ETF
    async addEtf() {
        const codeInput = document.getElementById('etfCodeInput');
        const code = codeInput.value.trim().toUpperCase();
        
        if (!code) {
            this.showNotification('请输入ETF代码', 'error');
            return;
        }

        // 验证代码格式
        if (!/^\d{6}$/.test(code)) {
            this.showNotification('请输入6位数字代码，如510300', 'error');
            return;
        }

        this.setLoading(true, '正在添加ETF...');
        this.setLoadingProgress(0);
        
        try {
            this.setLoadingProgress(30);
            const response = await fetch(`/api/etf/add?code=${code}`, {
                method: 'POST'
            });
            const result = await response.json();
            this.setLoadingProgress(80);
            
            if (result.code === 0) {
                codeInput.value = '';
                this.showNotification(result.message, 'success');
                this.loadEtfList();
            } else {
                this.showNotification(result.message || '添加失败', 'error');
            }
            this.setLoadingProgress(100);
        } catch (error) {
            console.error('添加ETF失败:', error);
            this.showNotification('添加失败，请检查网络', 'error');
        } finally {
            setTimeout(() => {
                this.setLoading(false);
            }, 300);
        }
    }

    // 同步数据
    async syncData() {
        this.setLoading(true, '正在同步数据...');
        this.setLoadingProgress(0);
        this.showNotification('正在同步数据...', 'info');
        
        try {
            this.setLoadingProgress(50);
            const response = await fetch('/api/data/sync', { method: 'POST' });
            const result = await response.json();
            this.setLoadingProgress(100);
            
            if (result.code === 0) {
                this.showNotification('数据同步完成', 'success');
                this.loadEtfList();
                if (this.selectedEtf) {
                    this.selectEtf(this.selectedEtf);
                }
            } else {
                this.showNotification(result.message || '同步失败', 'error');
            }
        } catch (error) {
            console.error('同步失败:', error);
            this.showNotification('同步失败，请检查网络', 'error');
        } finally {
            setTimeout(() => {
                this.setLoading(false);
            }, 300);
        }
    }

    // 初始化图表
    initChart() {
        const chartDom = document.getElementById('mainChart');
        this.chart = echarts.init(chartDom);
        
        const option = {
            title: {
                text: '选择ETF查看走势图',
                left: 'center',
                top: 'center',
                textStyle: {
                    color: '#64748b'
                }
            },
            tooltip: {
                trigger: 'axis',
                axisPointer: { type: 'cross' }
            },
            legend: {
                data: ['价格'],
                bottom: 10
            },
            grid: {
                left: 50,
                right: 50,
                top: 60,
                bottom: 60
            },
            xAxis: { type: 'category', data: [] },
            yAxis: [
                { type: 'value', scale: true, axisLabel: { formatter: '¥{value}' } },
                { type: 'value', scale: true, show: false }
            ],
            series: []
        };
        
        this.chart.setOption(option);
        
        // 响应式
        window.addEventListener('resize', () => {
            this.chart.resize();
        });
    }

    // 切换图表
    switchChart(type) {
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.tab === type);
        });
        
        if (this.selectedEtf) {
            if (type === 'intraday') {
                this.loadIntradayData(this.selectedEtf);
            } else {
                this.loadChartData(this.selectedEtf, '6m');
            }
        }
    }

    // 加载分时数据
    async loadIntradayData(code) {
        try {
            const response = await fetch(`/api/data/${code}/intraday`);
            const result = await response.json();
            
            if (result.code === 0 && result.data.times?.length > 0) {
                this.renderIntradayChart(result.data);
            } else {
                this.renderEmptyChart(code, '暂无分时数据');
            }
        } catch (error) {
            console.error('加载分时数据失败:', error);
            this.renderEmptyChart(code, '分时数据加载失败');
        }
    }

    // 渲染分时图
    renderIntradayChart(data) {
        const option = {
            title: {
                text: `${data.code} 分时走势`,
                left: 20,
                top: 10
            },
            tooltip: {
                trigger: 'axis',
                axisPointer: { type: 'cross' }
            },
            legend: {
                data: ['价格', '成交量'],
                bottom: 10
            },
            grid: {
                left: 50,
                right: 50,
                top: 60,
                bottom: 60
            },
            xAxis: {
                type: 'category',
                data: data.times,
                axisLabel: {
                    formatter: (value) => value.substring(0, 5)
                }
            },
            yAxis: [
                { type: 'value', scale: true, axisLabel: { formatter: '¥{value}' } },
                { type: 'value', scale: true, show: false }
            ],
            series: [
                {
                    name: '价格',
                    type: 'line',
                    data: data.prices,
                    smooth: true,
                    lineStyle: { width: 2, color: '#2563eb' },
                    itemStyle: { color: '#2563eb' },
                    areaStyle: {
                        color: {
                            type: 'linear',
                            x: 0, y: 0, x2: 0, y2: 1,
                            colorStops: [
                                { offset: 0, color: 'rgba(37, 99, 235, 0.3)' },
                                { offset: 1, color: 'rgba(37, 99, 235, 0.05)' }
                            ]
                        }
                    }
                },
                {
                    name: '成交量',
                    type: 'bar',
                    yAxisIndex: 1,
                    data: data.volumes,
                    itemStyle: { color: 'rgba(37, 99, 235, 0.3)' }
                }
            ]
        };
        
        this.chart.setOption(option, true);
    }

    // 加载图表数据
    async loadChartData(code, period = '6m') {
        try {
            const response = await fetch(`/api/data/${code}/price?period=${period}`);
            const result = await response.json();
            
            if (result.code === 0 && result.data.dates?.length > 0) {
                this.renderChart(result.data);
            } else {
                this.renderEmptyChart(code);
            }
        } catch (error) {
            console.error('加载图表数据失败:', error);
            this.renderEmptyChart(code);
        }
    }

    // 渲染空图表
    renderEmptyChart(code, message = '暂无数据') {
        const option = {
            title: {
                text: `${code} ${message}`,
                left: 'center',
                top: 'center',
                textStyle: {
                    color: '#64748b'
                }
            },
            tooltip: { trigger: 'axis' },
            grid: {
                left: 50,
                right: 20,
                top: 40,
                bottom: 40
            },
            xAxis: { type: 'category', data: [] },
            yAxis: { type: 'value', scale: true },
            series: []
        };
        this.chart.setOption(option, true);
    }

    // 渲染图表
    renderChart(data) {
        const option = {
            title: {
                text: `${data.code} 价格走势`,
                left: 20,
                top: 10
            },
            tooltip: {
                trigger: 'axis',
                axisPointer: { type: 'cross' }
            },
            legend: {
                data: ['价格', '成交量'],
                bottom: 10
            },
            grid: {
                left: 50,
                right: 50,
                top: 60,
                bottom: 60
            },
            xAxis: {
                type: 'category',
                data: data.dates,
                axisLabel: {
                    formatter: (value) => {
                        const date = new Date(value);
                        return `${date.getMonth() + 1}/${date.getDate()}`;
                    }
                }
            },
            yAxis: [
                {
                    type: 'value',
                    scale: true,
                    axisLabel: {
                        formatter: '¥{value}'
                    }
                },
                {
                    type: 'value',
                    scale: true,
                    show: false
                }
            ],
            series: [
                {
                    name: '价格',
                    type: 'line',
                    data: data.prices,
                    smooth: true,
                    lineStyle: { width: 2 },
                    itemStyle: { color: '#2563eb' },
                    areaStyle: {
                        color: {
                            type: 'linear',
                            x: 0, y: 0, x2: 0, y2: 1,
                            colorStops: [
                                { offset: 0, color: 'rgba(37, 99, 235, 0.3)' },
                                { offset: 1, color: 'rgba(37, 99, 235, 0.05)' }
                            ]
                        }
                    }
                },
                {
                    name: '成交量',
                    type: 'bar',
                    yAxisIndex: 1,
                    data: data.volumes,
                    itemStyle: {
                        color: 'rgba(37, 99, 235, 0.3)'
                    }
                }
            ]
        };
        
        this.chart.setOption(option, true);
    }

    // 加载历史记录
    async loadHistory() {
        if (!this.selectedEtf) return;
        
        try {
            const response = await fetch(`/api/strategy/${this.selectedEtf}/history?days=30`);
            const result = await response.json();
            
            if (result.code === 0) {
                this.renderHistory(result.data);
            }
        } catch (error) {
            console.error('加载历史记录失败:', error);
        }
        
        // 加载绩效统计
        try {
            const perfResponse = await fetch(`/api/strategy/${this.selectedEtf}/performance?days=30`);
            const perfResult = await perfResponse.json();
            
            if (perfResult.code === 0) {
                this.renderPerformance(perfResult.data);
            }
        } catch (error) {
            console.error('加载绩效统计失败:', error);
        }
    }

    // 渲染绩效统计
    renderPerformance(data) {
        if (!data || data.total === 0) return;
        
        const container = document.getElementById('historyTableBody');
        
        // 在表格后添加统计行
        const statsHtml = `
            <tr style="background: #f8fafc; font-weight: 600;">
                <td colspan="2">统计 (近30天)</td>
                <td>已记录: ${data.followed} 次</td>
                <td>未执行: ${data.not_followed} 次</td>
                <td>-</td>
            </tr>
        `;
        
        // 如果表格为空，添加空状态
        if (container.innerHTML.includes('暂无历史记录')) {
            container.innerHTML = statsHtml;
        } else {
            container.insertAdjacentHTML('beforeend', statsHtml);
        }
    }

    // 渲染历史记录
    renderHistory(data) {
        const tbody = document.getElementById('historyTableBody');
        
        if (data.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" class="empty-state">暂无历史记录</td></tr>';
            return;
        }
        
        tbody.innerHTML = data.map(item => `
            <tr>
                <td>${item.date}</td>
                <td>${item.strategy}</td>
                <td>${item.action}</td>
                <td>${item.actual || '-'}</td>
                <td>${item.remark || '-'}</td>
            </tr>
        `).join('');
    }
}

// 初始化应用
document.addEventListener('DOMContentLoaded', () => {
    window.app = new ETFQuantApp();
});
