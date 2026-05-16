# 聚宽 / 果仁 / 本地脚本工作流

## 平台分工

| 平台 | 最适合做什么 | 不适合做什么 |
|---|---|---|
| 果仁 | 非编程因子筛选、排名分段、动态股票池、轮动模型快速验证 | 复杂事件逻辑、复杂 Python 执行细节 |
| 聚宽 JoinQuant | Python 策略回测、模拟盘、交易成本、定时函数、订单逻辑 | 解释策略有效性、替代研究记录 |
| 本地脚本 | 保存策略规格、生成代码骨架、CSV 原型回测、结果记录、防过拟合检查 | 真实撮合、完整交易所规则 |
| MX_FinData / MX_StockPick / MX_FinSearch | 数据、股票池、新闻公告补充 | 直接判断策略有效 |

## 聚宽策略骨架

生成聚宽代码时，必须包含：

```python
def initialize(context):
    set_benchmark('000300.XSHG')
    set_option('use_real_price', True)
    set_order_cost(OrderCost(
        open_tax=0,
        close_tax=0.001,
        open_commission=0.0003,
        close_commission=0.0003,
        min_commission=5
    ), type='stock')
    set_slippage(FixedSlippage(0.002))
    run_weekly(rebalance, weekday=1, time='09:45')

def before_trading_start(context):
    pass

def rebalance(context):
    pass

def after_trading_end(context):
    pass
```

常用模块：

- 环境：`set_benchmark`、`set_option`、`set_order_cost`、`set_slippage`
- 调度：`run_daily`、`run_weekly`、`run_monthly`
- 行情：`get_price`、`history`、`attribute_history`、`get_current_data`
- 财务：`get_fundamentals(query(...))`
- 交易：`order_target_value`、`order_target_percent`、`order_value`
- 风控：停牌、ST、涨跌停、`closeable_amount`

## 果仁验证流程

果仁优先用来回答：“这个因子方向有没有基础价值？”

1. 股票池：全 A / 指数成分 / 行业 / 自定义池。
2. 筛选：非 ST、非停牌、上市天数、成交额、市值、财务硬雷。
3. 排名：动量、反转、价值、质量、成长、低波、流动性。
4. 调仓：周/月/季，先低频减少噪音。
5. 结果：看分段单调性、最大回撤、换手、扣成本后收益。

不要只看总收益。若排名高分组没有稳定优于低分组，因子方向不够硬。

## 本地 CSV 回测定位

本地回测只做“第一层方向验证”：

- 可验证：简单动量、低波、市值、成交额、等权轮动。
- 不保证：真实撮合、分钟滑点、财报公告日、完整复权细节。
- 必须迁移：通过本地验证后，再去聚宽/果仁复测。

CSV 最低字段：

```csv
date,code,open,close,volume,amount,paused,is_st
```

推荐字段：

```csv
date,code,open,high,low,close,pre_close,volume,amount,paused,is_st,is_limit_up,is_limit_down,industry,market_cap,turnover_rate
```

## 常见坑

| 坑 | 处理 |
|---|---|
| 未来函数 | 不用当日收盘后才知道的数据下当日单；财报用公告日/可得日 |
| 幸存者偏差 | 股票池按历史日期重建，不能只用今天仍上市股票 |
| 涨跌停 | 涨停买不进，跌停卖不出，回测必须过滤或降级 |
| 停牌 | 停牌不能交易，持仓估值要谨慎 |
| T+1 | 当天买入不能当天卖出，聚宽看 `closeable_amount` |
| 交易成本 | 佣金、印花税、最低佣金、滑点必须计入 |
| 小票容量 | 限制成交额和成交量占比，避免回测虚高 |
| 参数过拟合 | 训练/验证/样本外切分，做参数扰动和分年复测 |

## 平台迁移顺序

```text
AI idea
  -> 本地 strategy spec
  -> 本地 CSV 快速验证
  -> 果仁筛选/排名验证
  -> 聚宽代码回测
  -> 聚宽模拟盘
  -> 小仓实盘
```
