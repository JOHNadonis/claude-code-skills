# 金融圆桌 — MCP 数据前置步骤（Phase 3 启用）

> 当 financial-datasets MCP 连接可用时，在 Step 1（开场）之前执行此步骤。
> 如果 MCP 不可用，跳过此步骤，直接从 Step 1 开始。

## Step 0：数据准备

在圆桌开场前，主动拉取议题标的的关键数据。

### 个股分析

```
依次调用：
1. getStockPriceSnapshot(ticker)       → 当前股价、日涨跌
2. getFinancialMetricsSnapshot(ticker) → PE/PB/市值/股息率
3. getIncomeStatement(ticker, period='ttm') → 营收/净利润/自由现金流
4. getAnalystEstimates(ticker)         → 分析师目标价/EPS预测
5. getNews(ticker, limit=3)            → 最新3条重要新闻
```

### 输出格式：数据速览卡片

```
■ 实时数据速览 — {TICKER}（{今日日期}）
├─ 股价：${price} | 今日 {change}%
├─ 市值：{marketCap} | PE(TTM)：{pe}x | PB：{pb}x
├─ TTM 营收：{revenue} | 净利润：{netIncome} | FCF：{fcf}
├─ 分析师共识：目标价 ${targetPrice}（{upside}%上行空间，{numAnalysts}位）
└─ 近期新闻：
   • {news1.title}（{news1.date}）
   • {news2.title}（{news2.date}）
```

### 行业/宏观分析

```
依次调用：
1. screenStocks(filters=[{sector}])    → 行业代表性公司
2. getNews(limit=5)                    → 行业/宏观新闻
3. 对2-3家代表公司调用 getFinancialMetricsSnapshot
```

### 数据失败降级

如果任何 MCP 调用失败：
- 打印简短提示：「暂无实时数据，将基于公开信息进行分析」
- 继续执行圆桌，不阻断流程
- 在投研摘要末尾标注：「⚠ 本次分析未使用实时数据，数字仅供参考」

## 数据如何驱动发言

获取数据后，在主持人开场时简要汇报，并引导嘉宾基于真实数字发言：

- **巴菲特**：关注 FCF 收益率（FCF/市值）和 ROE
- **查诺斯**：关注营收增长 vs 应收账款增长是否背离
- **达利欧**：关注宏观新闻中的利率/汇率信号
- **西蒙斯**：关注价格动量（近30/60/90天收益率）
- **马克斯**：关注 PE 处于历史百分位
- **凯西·伍德**：关注分析师目标价上行空间是否体现创新溢价
- **段永平**：关注 FCF 是否能支撑长期分红/回购

