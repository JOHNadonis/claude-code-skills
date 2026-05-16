# 资料摘要和来源

本 skill 的策略库来自公开常见量化范式和平台工作流整理，不承诺任何策略未来收益。使用时以官方文档和真实回测为准。

## 平台资料

- 聚宽 JoinQuant：用于 Python 策略回测、模拟盘、定时函数、交易成本、订单接口。
  - [JoinQuant 官网](https://www.joinquant.com/)
  - [JoinQuant API PDF](https://cdn.joinquant.com/help/img/JoinQuantAPI.pdf)
  - [JoinQuant 股票数据文档](https://www.joinquant.com/help/data/stock?f=home&m=footer)

- 果仁：用于非编程筛选、排名、股票池、轮动模型和因子方向快速验证。
  - [果仁股票帮助](https://guorn.com/stock/help)
  - [果仁首页功能说明](https://guorn.com/?from=joinquant)

## 数据和扩展资料

- [AKShare 快速入门](https://akshare.akfamily.xyz/tutorial.html)：可作为本地行情/财务数据源之一。
- [Tushare 龙虎榜接口 top_list](https://tushare.pro/document/2?doc_id=106)：用于事件和龙虎榜策略研究。
- [上交所交易公开信息](https://www.sse.com.cn/disclosure/diclosure/public/seven_index.shtml)：用于公开交易数据和制度信息。
- [中证指数策略指数研究](https://www.csindex.com.cn/)：用于理解红利、低波、质量、动量等策略指数范式。

## 已整理成模板的主流策略

1. 小市值质量增强。
2. 红利低波质量。
3. ETF 趋势轮动。
4. 多因子指数增强。
5. 动量趋势。
6. 短期反转。
7. 财报/业绩预告事件。
8. 龙虎榜/资金情绪。

## 使用原则

- 来源只是启发，不能替代回测。
- 策略模板是研究起点，不是买卖建议。
- 平台 API 可能变化，生成代码要以官方当前文档校正。
- A 股制度变化、监管风格和交易成本会改变策略有效性。
