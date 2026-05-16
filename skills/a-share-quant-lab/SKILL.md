---
name: a-share-quant-lab
description: A股 AI 量化研究台。用于把截图、新闻、公告、板块逻辑、主观看盘和交易直觉转成可回测策略，包括策略假设、因子库、股票池、果仁式筛选、聚宽 JoinQuant 策略骨架、本地 CSV 简化回测、回测结果记录、防过拟合检查和实盘前风控审计。当用户说“我的最终目标是量化”“帮我做量化策略”“把这个想法量化”“写聚宽代码”“做果仁筛选”“回测这个策略”“找高胜率策略模板”“做A股量化工具”时触发。
---

# A 股 AI 量化研究台

## 核心定位

老大，这个 skill 的定位是“一整个迷你量化团队”：AI 做研究员，Python 做审计员，聚宽/果仁做验证平台，原来的实盘 skill 做交易语境解释。目标不是追求神奇胜率，而是把每个想法沉淀成可复盘、可回测、可迭代的规则。

不要承诺收益；不要把网上策略照搬成“稳赢”；所有策略必须经过样本外、交易成本、流动性、涨跌停、停牌、T+1、参数稳定性检查。

## 子 skill 调用链

| 场景 | 优先调用 |
|---|---|
| 拉取个股/指数/财务/资金流结构化数据 | `MX_FinData` |
| 初筛股票池、行业、概念、指数成分 | `MX_StockPick` |
| 新闻、公告、研报、政策催化 | `MX_FinSearch` |
| 截图看盘、持仓建议、实盘话术 | `a-stock-analysis` |
| 策略规格、模板库、聚宽骨架、本地回测 | 本 skill 的 `scripts/quant_lab.py` |

## 工作流

```
想法/截图/新闻/持仓
  -> AI 提炼策略假设
  -> 从策略库选择模板或组合模板
  -> 冻结 strategy spec
  -> 果仁做因子方向和排名分段验证
  -> 聚宽做 Python 回测/模拟盘
  -> 本地记录结果和防过拟合检查
  -> 小仓实盘观察，持续复盘
```

## 常用命令

```bash
cd /Users/whc/.codex/skills/a-share-quant-lab

# 查看内置策略模板
python3 scripts/quant_lab.py templates
python3 scripts/quant_lab.py template smallcap_momentum_quality
python3 scripts/quant_lab.py plan smallcap_momentum_quality

# 从模板创建策略规格
python3 scripts/quant_lab.py new my_smallcap_v1 --template smallcap_momentum_quality \
  --idea "小市值+动量+质量过滤，寻找资金抱团的小盘弹性"

# 导出聚宽策略骨架和果仁筛选说明
python3 scripts/quant_lab.py export-jq my_smallcap_v1
python3 scripts/quant_lab.py export-guorn my_smallcap_v1

# 本地 CSV 简化回测
python3 scripts/quant_lab.py backtest-csv my_smallcap_v1 --prices data/sample_prices.csv
python3 scripts/quant_lab.py batch-backtest --all-templates --prices data/sample_prices.csv

# 记录聚宽/果仁回测结果
python3 scripts/quant_lab.py record-result my_smallcap_v1 \
  --platform joinquant --period "2021-2025" \
  --annual-return 0.18 --max-drawdown 0.23 --sharpe 1.05 \
  --win-rate 0.54 --turnover 8.2 --summary "样本内可用，震荡市回撤偏大"

# 防过拟合和实盘前审计
python3 scripts/quant_lab.py checklist my_smallcap_v1
python3 scripts/quant_lab.py show my_smallcap_v1
python3 scripts/quant_lab.py compare
```

## 输出协议

当用户要求量化某个想法时，必须输出：

1. 一句话策略假设。
2. 可程序化规则：股票池、入场、排名、出场、调仓、仓位、风控。
3. 适合的平台：果仁先测什么，聚宽再测什么，本地脚本能测什么。
4. 最大风险：未来函数、过拟合、流动性、涨跌停、交易成本、样本外失效。
5. 下一步命令：`quant_lab.py new/export/backtest/checklist`。

如果用户还没有明确策略模板，先执行或参考：

```bash
python3 scripts/quant_lab.py templates
python3 scripts/quant_lab.py plan [模板ID]
```

## 何时读取 references

- 主流策略类型：读取 `references/strategy-library.md`
- 聚宽/果仁工作流：读取 `references/platform-workflows.md`
- 来源和资料摘要：读取 `references/source-digest.md`
- 回测验收、防过拟合：读取 `references/validation-playbook.md`

## 铁律

| 触发 | 强制动作 |
|---|---|
| 用户追求“高胜率” | 改成“胜率、赔率、回撤、容量、稳定性一起看” |
| 策略只有回测收益漂亮 | 必须要求样本外、交易成本、参数稳定性 |
| 小盘/题材/高换手策略 | 必须提示滑点、涨跌停、冲击成本和容量 |
| AI 从新闻/截图生成策略 | 必须先冻结规则，再回测，不能边看结果边改 |
| 准备实盘 | 先模拟盘或小仓，不能从回测直接重仓 |
