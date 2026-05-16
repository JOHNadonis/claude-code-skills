# L2-L6 量化模块详细文档

> 本文档是 a-stock-analysis skill 的扩展参考，包含 18 个量化模块的完整框架。
> 主文件：SKILL.md | 数据目录：~/.claude/projects/-Volumes-OS/memory/

---

## 📚 18 模块索引

### Level 2：时间维度 + 宏观背景
- [宏观流动性面板](../../../.claude/projects/-Volumes-OS/memory/stock_analysis_framework.md#第四章宏观流动性面板模块-2a-已上线) — 每日必扫，先看宏观再看个股
- [板块轮动雷达](../../../.claude/projects/-Volumes-OS/memory/stock_analysis_framework.md#第二章板块轮动雷达系统) — 资金梯队 + 五阶段生命周期
- [板块协整矩阵](../../../.claude/projects/-Volumes-OS/memory/stock_analysis_framework.md#第六章板块协整矩阵模块-2c-上线) — 同涨同跌簇 + 对冲对 + 领先滞后链

### Level 3：产业链 + 机构细分
- [产业链传导图谱](../../../.claude/projects/-Volumes-OS/memory/industry_chain_maps.md) — 10 大主流产业链上中下游
- [机构行为细分](../../../.claude/projects/-Volumes-OS/memory/institutional_behavior.md) — 北向/融资/公募/险资/大宗 五类机构
- [产业中观指标](../../../.claude/projects/-Volumes-OS/memory/industry_middle_tier.md) — 开工率/库存/订单可见度

### Level 4：情绪周期 + 衍生品
- [情绪周期四象限](../../../.claude/projects/-Volumes-OS/memory/emotion_cycle_quadrants.md) — 恐慌/修复/亢奋/崩塌识别
- [衍生品领先信号](../../../.claude/projects/-Volumes-OS/memory/derivatives_signals.md) — 期货基差/期权IV/两融结构
- [筹码结构深度](../../../.claude/projects/-Volumes-OS/memory/chip_structure.md) — 股东户数/解禁日历/产业资本

### Level 5：量化因子 + 动态仓位
- [四因子评分系统](../../../.claude/projects/-Volumes-OS/memory/four_factor_scoring.md) — Value/Growth/Momentum/Quality
- [行情特征识别](../../../.claude/projects/-Volumes-OS/memory/market_style_identifier.md) — 价值/成长、大/小盘、指数/个股市
- [动态仓位管理](../../../.claude/projects/-Volumes-OS/memory/dynamic_position_mgmt.md) — 凯利公式 + 波动率目标

### Level 6：自适应 + 回测闭环
- [市场状态识别器](../../../.claude/projects/-Volumes-OS/memory/market_state_identifier.md) — 牛/熊/震荡/切换期
- [自动回测闭环](../../../.claude/projects/-Volumes-OS/memory/auto_backtest_loop.md) — 信号胜率/因子IC/策略表现
- [组合层面管理](../../../.claude/projects/-Volumes-OS/memory/portfolio_management.md) — 行业敞口/风格敞口/相关性

---

## 🔗 模块间联动关系

```
宏观面板 → 情绪象限 → 市场状态识别 → 因子权重调整
    ↓
板块轮动 → 产业链传导 → 个股筛选
    ↓
机构共识度 + 衍生品信号 → 买卖时机
    ↓
四因子评分 → 动态仓位 → 组合管理
    ↓
自动回测 → 权重优化 → 闭环迭代
```

---

## 📍 快速触发关键词

| 关键词 | 触发模块 |
|--------|---------|
| "今日宏观" / "盘前扫描" | 宏观流动性面板 |
| "板块轮动" / "资金流向" | 板块轮动雷达 |
| "更新矩阵" / "板块关系" | 板块协整矩阵 |
| "产业链" / "谁会受益" | 产业链传导图谱 |
| "机构共识度" / "北向买什么" | 机构行为细分 |
| "开工率" / "库存周期" | 产业中观指标 |
| "当前象限" / "情绪如何" | 情绪周期四象限 |
| "期货升贴水" / "期权IV" | 衍生品领先信号 |
| "筹码集中" / "解禁" | 筹码结构深度 |
| "因子评分" / "给XX打分" | 四因子评分系统 |
| "风格识别" / "价值成长切换" | 行情特征识别 |
| "买多少" / "仓位" | 动态仓位管理 |
| "市场状态" / "牛熊判断" | 市场状态识别器 |
| "回测" / "胜率统计" | 自动回测闭环 |
| "组合管理" / "行业敞口" | 组合层面管理 |

---

## 🚫 全局禁止行为（跨模块）

1. **凭记忆回答金融数据** — 必须调用 mx skills 获取实时数据
2. **先有结论再找理由** — 必须先走一票否决 + 四因子评分
3. **把叙事当主角** — 叙事权重只占 15%，核心是基本面 + 估值 + 资金面
4. **用不同维度评估不同股票** — 所有候选股必须走完相同的评分表
5. **被质疑时立刻翻盘** — 先分类事实性/判断性质疑，重走框架后才改结论
6. **推荐时不看矩阵** — 每次推荐检查簇归属，同簇不超过 2 只
7. **忽视资金方向** — 北向买防御 = 避险，买成长 = 进攻，方向比金额重要 10 倍
8. **推荐前不报象限** — 每次推荐开头必须写当前情绪象限
9. **推荐后不入库** — 每次推荐必写入 trading_logs/recommendations/

---

## 📂 数据管道架构

```
/Users/whc/.claude/projects/-Volumes-OS/memory/trading_logs/
├── daily_panel/          每日宏观面板快照
├── signal_triggers/      每个信号的触发日志（JSONL 追加）
├── recommendations/      每次推荐的完整快照
└── outcomes/             推荐后 5/10/20 日实际回报
```

**三个核心数据流**：
1. **每日扫描** → 写入 `daily_panel/YYYY-MM-DD.json`
2. **每次推荐** → 写入 `recommendations/YYYY-MM-DD_rec.json` + 追加 `signal_triggers/*.jsonl`
3. **每周复盘** → 写入 `outcomes/YYYY-MM-DD_eval.json`

---

## 🗓️ 数据积累阶段里程碑

| 时点 | 数据量 | 能做什么 |
|---|---|---|
| Day 0 (2026-04-22) | 1 天 | 建库 |
| Day 30 | ~20 交易日 | 初步趋势观察 |
| Day 60 | ~40 交易日 | 第一次真实回测 |
| Day 90 | ~60 交易日 | 信号胜率数字化 |
| Day 180 | 半年 | 框架权重自优化 |
| Day 365 | 一年 | 真正量化研究助手 |

---

## 💡 核心方法论压缩

**"先看资金，后看价格；先看龙头，后看跟风；先看海外，后看 A 股；先看 ETF，后看个股。"**

**"先过否决项，再做加分。叙事是加分，不是主项。被质疑先分类，不自动翻盘。"**

**"量化不是'听起来像量化'。量化 = 每个数字背后都有可追溯的实验。"**
