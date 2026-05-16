#!/usr/bin/env python3
"""
盘中实盘辅助分析脚本：读取持仓，并行拉取行情+技术面+资金面+量化信号，生成操作决策报告。

用法：
  python3 intraday.py              # 分析所有持仓
  python3 intraday.py 002463       # 只分析指定代码
  python3 intraday.py --market     # 只输出大盘概况，不分析个股
"""

import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

# ──────────────────────────────────────────────────────────────────────────────
# 路径配置
# ──────────────────────────────────────────────────────────────────────────────
SKILL_DIR = Path(__file__).parent.parent
PORTFOLIO_FILE = SKILL_DIR / "data" / "portfolio.json"
MX_SCRIPT = Path.home() / ".claude/skills/MX_FinData/scripts/get_data.py"


def _run_mx(query: str) -> dict:
    """调用 MX_FinData 查询，返回 Excel 路径信息。"""
    try:
        result = subprocess.run(
            [sys.executable, str(MX_SCRIPT), "--query", query],
            capture_output=True, text=True, encoding="utf-8",
            timeout=60
        )
        out = result.stdout.strip()
        lines = {l.split(":")[0].strip(): l.split(":", 1)[1].strip()
                 for l in out.splitlines() if ":" in l}
        if result.returncode != 0:
            return {"error": result.stderr.strip()[:300]}
        return {"file": lines.get("文件", ""), "rows": lines.get("行数", "0")}
    except subprocess.TimeoutExpired:
        return {"error": "查询超时（60s）"}
    except Exception as e:
        return {"error": str(e)}


def _load_portfolio() -> list[dict]:
    if not PORTFOLIO_FILE.exists():
        return []
    data = json.loads(PORTFOLIO_FILE.read_text(encoding="utf-8"))
    return data.get("holdings", [])


def _read_excel_as_text(path: str) -> str:
    """把 Excel 所有 sheet 转成文本，供 Claude 阅读。"""
    try:
        import pandas as pd
        xl = pd.ExcelFile(path)
        parts = []
        for sheet in xl.sheet_names:
            df = pd.read_excel(xl, sheet_name=sheet)
            parts.append(f"【{sheet}】\n{df.to_string(index=False)}")
        return "\n\n".join(parts)
    except Exception as e:
        return f"(读取失败: {e})"


def run_queries(holdings: list[dict], market_only: bool = False, filter_code: str = "") -> dict:
    """并行执行所有 MX 查询，返回原始数据字典。"""
    codes_str = " ".join(f"{h['name']}{h['code']}" for h in holdings[:5])
    results = {}

    target = holdings
    if filter_code:
        target = [h for h in holdings if h["code"] == filter_code]
        if not target:
            print(f"❌ 未找到持仓代码：{filter_code}")
            return results

    # ── 定义所有查询任务 ────────────────────────────────────────────────────────
    queries: dict[str, str] = {
        "market_index": "上证指数 深证成指 创业板指 最新点位 涨跌幅 成交量 成交额",
        "northbound": "北向资金 今日净流入 沪股通 深股通",
    }

    if not market_only and holdings:
        queries.update({
            # 竞价：量化必读信号，9:15-9:25窗口
            "auction": f"{codes_str} 集合竞价 竞价量比 开盘溢价率 竞价成交量",
            # 行情+BOLL+量比（量比是量化时代最重要的信号过滤器）
            "price_boll": f"{codes_str} 最新价 涨跌幅 成交量 换手率 量比 BOLL布林线",
            # 均线+RSI+5日均量（用于计算量比背景）
            "ma_rsi": f"{codes_str} RSI 5日均线 10日均线 20日均线 近期收盘价 5日平均量",
            # 资金流向
            "capital_flow": f"{codes_str} 主力净流入 超大单净流入 大单净流入 小单净流入 资金流向",
            # 龙虎榜：游资/机构席位，A股特有的机构行为预判
            "dragon_tiger": f"{codes_str} 龙虎榜 机构席位 游资净买入 上榜原因",
            # 风险标记：解禁和质押是最容易踩雷的两个坑
            "risk_flags": f"{codes_str} 解禁日期 限售股解禁 大股东质押比例 融资余额变化",
            # 公告
            "announcements": f"{codes_str} 最新公告 重大事项 业绩预告",
        })

    total = len(queries)
    print(f"📡 并行执行 {total} 个查询（最大并发 4）...", flush=True)

    # ── 并行执行 ────────────────────────────────────────────────────────────────
    with ThreadPoolExecutor(max_workers=min(total, 4)) as pool:
        future_map = {pool.submit(_run_mx, q): key for key, q in queries.items()}
        for future in as_completed(future_map):
            key = future_map[future]
            try:
                r = future.result()
                results[key] = r
                if r.get("file"):
                    results[f"{key}_data"] = _read_excel_as_text(r["file"])
                status = f"✅ {key}" if not r.get("error") else f"❌ {key}: {r['error'][:60]}"
            except Exception as e:
                results[key] = {"error": str(e)}
                status = f"❌ {key}: {e}"
            print(f"  {status}", flush=True)

    # ── 板块资讯（串行，依赖 target 信息）──────────────────────────────────────
    if not market_only and holdings:
        sector_hints = " ".join(
            h.get("note", "").split("关注")[0]
            for h in target if h.get("note")
        ).strip()
        sector_query = sector_hints or " ".join(h["name"] for h in target[:3])
        print("📡 查询板块资讯...", flush=True)
        r = _run_mx(f"{sector_query} 板块资金流向 行业动态 今日涨跌")
        results["sector_news"] = r
        if r.get("file"):
            results["sector_news_data"] = _read_excel_as_text(r["file"])

    results["macro_news_required"] = True
    return results


def build_prompt(holdings: list[dict], data: dict) -> str:
    """构建给 Claude 的分析 prompt。"""
    today = datetime.now().strftime("%Y-%m-%d %H:%M")
    holding_str = "\n".join(
        f"  - {h['name']}({h['code']})：持有 {h['shares']} 股，成本 {h['cost']:.2f} 元，"
        f"买入日期 {h.get('buy_date', '')}，备注：{h.get('note', '无')}"
        for h in holdings
    )

    sections = [
        f"# 实盘辅助分析请求 — {today}",
        "",
        "## 当前持仓",
        holding_str or "（无持仓）",
        "",
        "## 原始数据（来自东方财富妙想 MX_FinData）",
        "",
    ]

    label_map = {
        "market_index_data":  "### 大盘指数",
        "northbound_data":    "### 北向资金",
        "auction_data":       "### 集合竞价（量化必读信号）",
        "price_boll_data":    "### 个股行情 + BOLL + 量比",
        "ma_rsi_data":        "### 个股均线 + RSI + 5日均量",
        "capital_flow_data":  "### 个股资金流向",
        "dragon_tiger_data":  "### 龙虎榜（游资 / 机构席位）",
        "risk_flags_data":    "### 风险标记（解禁 / 质押 / 融资）",
        "announcements_data": "### 个股最新公告 & 重大事项",
        "sector_news_data":   "### 板块资讯 & 行业动态",
    }

    for key, label in label_map.items():
        if key in data:
            sections += [label, "```", data[key], "```", ""]

    sections += [
        "---",
        "## ⚠️ Claude 分析前必须执行的步骤（强制，不可跳过）",
        "",
        f"1. WebSearch: \"A股 今日重要消息 {today[:10]}\"",
        f"2. WebSearch: \"美股 期货 今日行情 {today[:10]}\"",
        "3. 若持仓有特定板块（PCB/液冷/半导体等），追加搜索该板块今日动态",
        "",
        "---",
        "## 请按 references/report-template.md 格式输出分析报告",
        "",
        "## 量化时代新增必须分析的信号",
        "",
        "**竞价信号解读（先于所有技术面）：**",
        "| 竞价形态 | 含义 | 操作意义 |",
        "|---------|------|---------|",
        "| 高开 + 量比>2 | 真启动，量化确认 | 可积极参与 |",
        "| 高开 + 量比<0.8 | 假高开/洗盘 | 等待回落再介入 |",
        "| 低开 + 放量 | 恐慌盘，量化可能抄底 | 观察企稳，不急于止损 |",
        "| 平开 + 缩量 | 方向未定 | 等 9:45 后信号明确再操作 |",
        "",
        "**量比过滤器（所有技术信号必须通过此过滤）：**",
        "| 量比 | 信号可靠性 | 建议 |",
        "|------|-----------|------|",
        "| > 2.0 | 高，量化确认有效 | 技术信号可信度高 |",
        "| 1.0～2.0 | 中，正常活跃 | 技术信号正常参考 |",
        "| < 0.8 | 低，缩量横盘 | 技术信号可靠性下降，不建议做T |",
        "",
        "**解禁/质押风险调整止损：**",
        "- 距解禁日 < 30 天：止损收紧至 max(MA20, 成本×0.97)",
        "- 质押比例 > 40%：持有评级降一星，不建议加仓",
        "",
        "**龙虎榜解读：**",
        "- 机构席位净买入 > 游资净买入：最强信号，跟随",
        "- 游资连续2日净买入：短线机会，但注意出货风险",
        "- 机构卖出 + 游资买入：接力游戏，谨慎",
    ]

    return "\n".join(sections)


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    args = sys.argv[1:]

    market_only = "--market" in args
    filter_code = next((a for a in args if a.isdigit() and len(a) >= 6), "")

    holdings = _load_portfolio()
    if not holdings and not market_only:
        print("【提示】持仓为空，仅输出大盘分析。")
        print("使用 `python3 scripts/portfolio.py add 代码 名称 股数 成本` 添加持仓。")
        market_only = True

    print(f"\n{'='*60}")
    print(f"  A股实盘辅助 — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  持仓数量：{len(holdings)} 只")
    print(f"{'='*60}\n")

    data = run_queries(holdings, market_only=market_only, filter_code=filter_code)

    print("\n" + "=" * 60)
    print("  以下为结构化数据，请 Claude 据此生成分析报告")
    print("=" * 60 + "\n")
    print(build_prompt(holdings, data))


if __name__ == "__main__":
    main()
