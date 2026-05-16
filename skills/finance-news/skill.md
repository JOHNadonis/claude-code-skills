---
name: finance-news
description: 手动触发金融晨报采集与分析，生成包含 A 股、美股、加密货币、Polymarket、财经新闻的中文简报。
---

# Finance News

手动触发 morning-briefing 流水线：数据采集 → Codex 分析 → 生成晨报。

## When to use (trigger phrases)

- "跑一下晨报"
- "finance news"
- "金融简报"
- "市场数据"
- "跑 briefing"
- "今天行情怎么样"（当需要完整简报时）

## How it works

执行 `~/.myagents/projects/myagent/scripts/morning-briefing/run.sh`，流程：

1. `gather.py` 从东方财富（A股指数+个股）、Yahoo Finance（美股/外汇/商品）、CoinGecko（加密货币）、Polymarket（预测市场）、RSS（财经新闻）采集数据
2. 原始数据喂给 Codex Sonnet 生成结构化中文晨报
3. macOS 弹通知

## Instructions

当用户触发此 skill 时，按以下步骤执行：

### Step 1: 运行采集脚本

```bash
bash ~/.myagents/projects/myagent/scripts/morning-briefing/run.sh
```

### Step 2: 读取晨报

```bash
cat ~/.myagents/projects/myagent/workspace/briefings/briefing_$(date +%Y-%m-%d).md
```

### Step 3: 推送给用户

将晨报内容完整输出给用户。如果晨报为空或脚本失败，检查日志：

```bash
cat ~/.myagents/projects/myagent/workspace/briefings/run_$(date +%Y-%m-%d).log
```

### Step 4: 追加分析（可选）

基于晨报数据，追加：
- 「A股盘前参考」：利好/利空/中性判断 + 重点关注板块
- 跟踪池异动提示（燃气轮机：600875,601727,603308,000738,002595,300034,600893,601369）

## 产出文件

路径：`~/.myagents/projects/myagent/workspace/briefings/`
- `raw_YYYY-MM-DD.md` — 原始数据
- `briefing_YYYY-MM-DD.md` — 分析晨报
- `run_YYYY-MM-DD.log` — 运行日志

## 查看最新晨报

```bash
cat ~/.myagents/projects/myagent/workspace/briefings/briefing_$(date +%Y-%m-%d).md
```

## 定时任务

已配置 launchd 每天自动执行 4 次（北京时间）：
- 06:00 — 盘前
- 11:00 — 午盘
- 15:00 — 收盘
- 19:00 — 晚间

plist: `~/Library/LaunchAgents/com.whc.morning-briefing.plist`

## 数据源

| 源 | 内容 | API |
|----|------|-----|
| 东方财富 | A股指数(7个) + 跟踪池个股(8只) | push2.eastmoney.com |
| Yahoo Finance | 美股指数、外汇、大宗商品 | query1.finance.yahoo.com |
| CoinGecko | 10个主流加密货币 | api.coingecko.com |
| Alternative.me | 加密恐惧贪婪指数 | api.alternative.me |
| Polymarket | 热门预测市场 top 20 | gamma-api.polymarket.com |
| RSS | CNBC、BBC、CoinDesk、MarketWatch | feedparser |
