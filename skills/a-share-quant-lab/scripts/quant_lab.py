#!/usr/bin/env python3
"""
A-share AI quant lab.

This script turns AI-generated research ideas into reproducible specs, exports
JoinQuant/Guorn scaffolds, runs a simple CSV-based prototype backtest, and
records validation results.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import sys
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from textwrap import dedent
from typing import Any


SKILL_DIR = Path(__file__).parent.parent
DATA_DIR = SKILL_DIR / "data"
WORKSPACE_DIR = SKILL_DIR / "workspace"
STRATEGY_DB = DATA_DIR / "strategy_specs.json"
SPEC_DIR = WORKSPACE_DIR / "specs"
STRATEGY_DIR = WORKSPACE_DIR / "strategies"
BACKTEST_DIR = WORKSPACE_DIR / "backtests"
REPORT_DIR = WORKSPACE_DIR / "reports"


STRATEGY_TEMPLATES: dict[str, dict[str, Any]] = {
    "smallcap_momentum_quality": {
        "label": "小市值质量增强",
        "hypothesis": "A 股小市值存在弹性和规模溢价，但需要用盈利、流动性和风险过滤排雷。",
        "suitable_for": ["小资金", "低频轮动", "进攻型组合"],
        "risk_notes": ["小票流动性和滑点会吞掉收益", "监管风格切换时可能失效", "财务雷要硬过滤"],
        "universe": {
            "base": "A_SHARE",
            "exclude_st": True,
            "exclude_suspended": True,
            "exclude_new_stock_days": 180,
            "exclude_limit_up_down": True,
            "min_amount": 100000000,
        },
        "signals": [
            {"name": "small_market_cap", "type": "market_cap", "direction": "negative", "weight": 0.30},
            {"name": "momentum_60d", "type": "price_momentum", "window": 60, "direction": "positive", "weight": 0.25},
            {"name": "momentum_20d", "type": "price_momentum", "window": 20, "direction": "positive", "weight": 0.15},
            {"name": "volatility_20d", "type": "realized_volatility", "window": 20, "direction": "negative", "weight": 0.15},
            {"name": "liquidity_20d", "type": "amount_mean", "window": 20, "direction": "positive", "weight": 0.15},
        ],
        "portfolio": {"top_n": 20, "max_position_weight": 0.05, "rebalance_frequency": "monthly", "cash_buffer": 0.02},
    },
    "dividend_lowvol_quality": {
        "label": "红利低波质量",
        "hypothesis": "高分红、低波动、现金流质量较好的公司在 A 股具备更强防守属性。",
        "suitable_for": ["防守型账户", "低频", "回撤敏感"],
        "risk_notes": ["高股息可能是周期利润高点", "价值陷阱需要现金流和负债率过滤"],
        "universe": {
            "base": "A_SHARE",
            "exclude_st": True,
            "exclude_suspended": True,
            "exclude_new_stock_days": 365,
            "exclude_limit_up_down": True,
            "min_amount": 80000000,
        },
        "signals": [
            {"name": "dividend_yield", "type": "column", "column": "dividend_yield", "direction": "positive", "weight": 0.30},
            {"name": "roe", "type": "column", "column": "roe", "direction": "positive", "weight": 0.20},
            {"name": "pb", "type": "column", "column": "pb", "direction": "negative", "weight": 0.20},
            {"name": "volatility_60d", "type": "realized_volatility", "window": 60, "direction": "negative", "weight": 0.20},
            {"name": "cashflow_quality", "type": "column", "column": "ocf_to_profit", "direction": "positive", "weight": 0.10},
        ],
        "portfolio": {"top_n": 30, "max_position_weight": 0.04, "rebalance_frequency": "monthly", "cash_buffer": 0.03},
    },
    "etf_trend_rotation": {
        "label": "ETF 趋势轮动",
        "hypothesis": "宽基和行业 ETF 的中期趋势存在延续，趋势过滤可降低个股踩雷风险。",
        "suitable_for": ["新手量化", "小资金", "低踩雷需求"],
        "risk_notes": ["震荡市来回打脸", "行业顶部动量最强，退出规则必须硬"],
        "universe": {
            "base": "ETF_POOL",
            "exclude_st": False,
            "exclude_suspended": True,
            "exclude_new_stock_days": 60,
            "exclude_limit_up_down": False,
            "min_amount": 50000000,
        },
        "signals": [
            {"name": "momentum_20d", "type": "price_momentum", "window": 20, "direction": "positive", "weight": 0.25},
            {"name": "momentum_60d", "type": "price_momentum", "window": 60, "direction": "positive", "weight": 0.45},
            {"name": "volatility_20d", "type": "realized_volatility", "window": 20, "direction": "negative", "weight": 0.20},
            {"name": "liquidity_20d", "type": "amount_mean", "window": 20, "direction": "positive", "weight": 0.10},
        ],
        "entry_rules": ["close > ma60"],
        "exit_rules": ["close < ma60", "rank drops below top 50%"],
        "portfolio": {"top_n": 3, "max_position_weight": 0.34, "rebalance_frequency": "weekly", "cash_buffer": 0.02},
    },
    "multi_factor_index_enhanced": {
        "label": "多因子指数增强",
        "hypothesis": "价值、质量、动量、低波和流动性多因子合成比单因子更稳。",
        "suitable_for": ["系统化研究", "指数增强", "中低频"],
        "risk_notes": ["因子越多越容易过拟合", "行业和市值偏离需要控制"],
        "universe": {
            "base": "CSI500",
            "exclude_st": True,
            "exclude_suspended": True,
            "exclude_new_stock_days": 180,
            "exclude_limit_up_down": True,
            "min_amount": 100000000,
        },
        "signals": [
            {"name": "value_pb", "type": "column", "column": "pb", "direction": "negative", "weight": 0.20},
            {"name": "quality_roe", "type": "column", "column": "roe", "direction": "positive", "weight": 0.20},
            {"name": "growth_np", "type": "column", "column": "net_profit_growth", "direction": "positive", "weight": 0.15},
            {"name": "momentum_60d", "type": "price_momentum", "window": 60, "direction": "positive", "weight": 0.20},
            {"name": "volatility_20d", "type": "realized_volatility", "window": 20, "direction": "negative", "weight": 0.15},
            {"name": "liquidity_20d", "type": "amount_mean", "window": 20, "direction": "positive", "weight": 0.10},
        ],
        "portfolio": {"top_n": 50, "max_position_weight": 0.03, "rebalance_frequency": "monthly", "cash_buffer": 0.02},
    },
    "momentum_trend": {
        "label": "动量趋势",
        "hypothesis": "强势股票/行业在资金抱团阶段存在趋势延续。",
        "suitable_for": ["趋势行情", "中短线研究"],
        "risk_notes": ["震荡市容易反复止损", "动量拥挤时回撤快"],
        "universe": {
            "base": "A_SHARE",
            "exclude_st": True,
            "exclude_suspended": True,
            "exclude_new_stock_days": 120,
            "exclude_limit_up_down": True,
            "min_amount": 150000000,
        },
        "signals": [
            {"name": "momentum_20d", "type": "price_momentum", "window": 20, "direction": "positive", "weight": 0.35},
            {"name": "momentum_60d", "type": "price_momentum", "window": 60, "direction": "positive", "weight": 0.35},
            {"name": "volume_breakout", "type": "amount_mean", "window": 5, "direction": "positive", "weight": 0.15},
            {"name": "volatility_20d", "type": "realized_volatility", "window": 20, "direction": "negative", "weight": 0.15},
        ],
        "entry_rules": ["close > ma20", "close > ma60"],
        "exit_rules": ["close < ma20", "drawdown from entry > 8%"],
        "portfolio": {"top_n": 10, "max_position_weight": 0.10, "rebalance_frequency": "weekly", "cash_buffer": 0.05},
    },
    "short_term_reversal": {
        "label": "短期反转",
        "hypothesis": "短期过度下跌且无基本面硬雷的股票可能出现均值回归。",
        "suitable_for": ["小仓试验", "严格止损", "低频反转"],
        "risk_notes": ["容易接飞刀", "问题股越跌越便宜", "必须排除利空和 ST"],
        "universe": {
            "base": "A_SHARE",
            "exclude_st": True,
            "exclude_suspended": True,
            "exclude_new_stock_days": 180,
            "exclude_limit_up_down": True,
            "min_amount": 120000000,
        },
        "signals": [
            {"name": "reversal_5d", "type": "price_momentum", "window": 5, "direction": "negative", "weight": 0.35},
            {"name": "reversal_20d", "type": "price_momentum", "window": 20, "direction": "negative", "weight": 0.25},
            {"name": "liquidity_20d", "type": "amount_mean", "window": 20, "direction": "positive", "weight": 0.20},
            {"name": "volatility_20d", "type": "realized_volatility", "window": 20, "direction": "negative", "weight": 0.20},
        ],
        "portfolio": {"top_n": 10, "max_position_weight": 0.08, "rebalance_frequency": "weekly", "cash_buffer": 0.10},
    },
    "earnings_event": {
        "label": "财报/业绩预告事件",
        "hypothesis": "业绩预告超预期、扣非改善和现金流改善会被市场逐步定价。",
        "suitable_for": ["公告驱动", "AI 新闻理解", "低频事件"],
        "risk_notes": ["公告日必须处理可得性", "事件样本少", "一字板买不进"],
        "universe": {
            "base": "A_SHARE",
            "exclude_st": True,
            "exclude_suspended": True,
            "exclude_new_stock_days": 365,
            "exclude_limit_up_down": True,
            "min_amount": 100000000,
        },
        "signals": [
            {"name": "profit_growth", "type": "column", "column": "net_profit_growth", "direction": "positive", "weight": 0.35},
            {"name": "deducted_profit_growth", "type": "column", "column": "deducted_profit_growth", "direction": "positive", "weight": 0.25},
            {"name": "cashflow_quality", "type": "column", "column": "ocf_to_profit", "direction": "positive", "weight": 0.20},
            {"name": "momentum_20d", "type": "price_momentum", "window": 20, "direction": "positive", "weight": 0.20},
        ],
        "portfolio": {"top_n": 15, "max_position_weight": 0.07, "rebalance_frequency": "monthly", "cash_buffer": 0.05},
    },
    "dragon_tiger_momentum": {
        "label": "龙虎榜/资金情绪",
        "hypothesis": "机构席位和强势资金异动在短期可能延续，但噪声和滑点很高。",
        "suitable_for": ["高风险小仓", "事件跟踪", "短线研究"],
        "risk_notes": ["追高风险大", "回测成交价不真实", "最好只做观察或小仓"],
        "universe": {
            "base": "A_SHARE",
            "exclude_st": True,
            "exclude_suspended": True,
            "exclude_new_stock_days": 120,
            "exclude_limit_up_down": True,
            "min_amount": 200000000,
        },
        "signals": [
            {"name": "net_big_money", "type": "column", "column": "net_big_money", "direction": "positive", "weight": 0.35},
            {"name": "institution_net_buy", "type": "column", "column": "institution_net_buy", "direction": "positive", "weight": 0.30},
            {"name": "momentum_5d", "type": "price_momentum", "window": 5, "direction": "positive", "weight": 0.20},
            {"name": "liquidity_5d", "type": "amount_mean", "window": 5, "direction": "positive", "weight": 0.15},
        ],
        "portfolio": {"top_n": 5, "max_position_weight": 0.08, "rebalance_frequency": "weekly", "cash_buffer": 0.20},
    },
}


RESEARCH_HINTS: dict[str, dict[str, list[str] | str]] = {
    "smallcap_momentum_quality": {
        "primary_skill": "MX_StockPick",
        "secondary_skills": ["MX_FinData", "MX_FinSearch"],
        "stockpick_query": "A股 市值较小 非ST 日均成交额充足 ROE为正 扣非净利为正",
        "findata_query": "股票 市值 ROE PB 资产负债率 流动比率 经营现金流 净利润",
        "finsearch_query": "公司 最新公告 业绩预告 回购 增持 机构调研",
        "validation_note": "先看排名分段是否单调，再看成本和流动性是否吃掉收益。",
    },
    "dividend_lowvol_quality": {
        "primary_skill": "MX_FinData",
        "secondary_skills": ["MX_StockPick", "MX_FinSearch"],
        "stockpick_query": "A股 高股息 连续分红 低波动 经营现金流为正",
        "findata_query": "股票 股息率 ROE PB 资产负债率 经营现金流 净利润",
        "finsearch_query": "分红 业绩说明会 回购 增持 现金流 公告",
        "validation_note": "分红策略要看除权后总回报，不要只看收盘价。",
    },
    "etf_trend_rotation": {
        "primary_skill": "MX_StockPick",
        "secondary_skills": ["MX_FinData", "MX_FinSearch"],
        "stockpick_query": "ETF 宽基 行业 动量强 成交额充足",
        "findata_query": "ETF 近20日收益 近60日收益 波动率 成交额",
        "finsearch_query": "板块政策 资金流 行业轮动 主题催化",
        "validation_note": "先检验趋势过滤能否减少回撤，再看收益是否还能保留。",
    },
    "multi_factor_index_enhanced": {
        "primary_skill": "MX_StockPick",
        "secondary_skills": ["MX_FinData", "MX_FinSearch"],
        "stockpick_query": "沪深300 中证500 中证1000 成分股 非ST 高流动性",
        "findata_query": "股票 PE PB ROE 净利润增速 经营现金流 市值 成交额",
        "finsearch_query": "指数调仓 监管变化 行业权重 政策窗口",
        "validation_note": "多因子先保证稳定，再考虑行业中性和风格中性。",
    },
    "momentum_trend": {
        "primary_skill": "MX_FinData",
        "secondary_skills": ["MX_StockPick", "MX_FinSearch"],
        "stockpick_query": "A股 强势股 放量突破 成交额充足 非ST",
        "findata_query": "股票 20日涨幅 60日涨幅 量比 BOLL RSI 成交额",
        "finsearch_query": "板块动量 机构调研 龙虎榜 题材催化",
        "validation_note": "动量策略必须严格控制震荡市和追高回撤。",
    },
    "short_term_reversal": {
        "primary_skill": "MX_FinData",
        "secondary_skills": ["MX_StockPick", "MX_FinSearch"],
        "stockpick_query": "A股 超跌反弹 低换手 非ST 流动性足",
        "findata_query": "股票 RSI 乖离率 近5日跌幅 近20日跌幅 量比",
        "finsearch_query": "利空公告 诉讼 业绩预警 监管问询",
        "validation_note": "反转策略要先做雷区过滤，再看反弹能否兑现。",
    },
    "earnings_event": {
        "primary_skill": "MX_FinSearch",
        "secondary_skills": ["MX_StockPick", "MX_FinData"],
        "stockpick_query": "业绩预增 现金流改善 回购 增持 高增长 A股",
        "findata_query": "股票 营收增速 净利润增速 扣非净利增速 经营现金流 毛利率",
        "finsearch_query": "最新公告 业绩预告 业绩快报 回购 增持 重大合同",
        "validation_note": "事件策略必须按公告可得时间回放，不能偷看未来。",
    },
    "dragon_tiger_momentum": {
        "primary_skill": "MX_FinSearch",
        "secondary_skills": ["MX_FinData", "MX_StockPick"],
        "stockpick_query": "龙虎榜活跃 强势题材 龙头股 低ST风险",
        "findata_query": "股票 龙虎榜 净流入 主力净流入 超大单净流入 量比",
        "finsearch_query": "龙虎榜 机构席位 游资净买入 题材催化",
        "validation_note": "资金情绪策略噪声大，只适合小仓高频复盘，不适合重仓幻想。",
    },
}


def now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def stamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def slug(text: str) -> str:
    chars = []
    for ch in text.strip().lower():
        if ch.isalnum():
            chars.append(ch)
        elif chars and chars[-1] != "_":
            chars.append("_")
    value = "".join(chars).strip("_")
    return value[:60] or "strategy"


def ensure_dirs() -> None:
    for path in [DATA_DIR, SPEC_DIR, STRATEGY_DIR, BACKTEST_DIR, REPORT_DIR]:
        path.mkdir(parents=True, exist_ok=True)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def file_hash(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return "sha256:" + h.hexdigest()


def canonical_json_hash(data: Any) -> str:
    raw = json.dumps(data, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def load_db() -> dict[str, Any]:
    if not STRATEGY_DB.exists():
        return {"strategies": []}
    return read_json(STRATEGY_DB)


def save_db(db: dict[str, Any]) -> None:
    write_json(STRATEGY_DB, db)


def spec_path(strategy_id: str) -> Path:
    return SPEC_DIR / f"{strategy_id}.json"


def find_spec(strategy: str) -> dict[str, Any]:
    path = Path(strategy)
    if path.exists():
        return read_json(path)
    direct = spec_path(strategy)
    if direct.exists():
        return read_json(direct)
    db = load_db()
    for item in db.get("strategies", []):
        if item.get("strategy_id") == strategy or item.get("name") == strategy:
            p = Path(item.get("path", ""))
            if p.exists():
                return read_json(p)
    raise SystemExit(f"未找到策略：{strategy}")


def upsert_spec(spec: dict[str, Any], path: Path) -> None:
    db = load_db()
    sid = spec["meta"]["strategy_id"]
    item = {
        "strategy_id": sid,
        "name": spec["meta"]["name"],
        "template": spec["meta"].get("template", ""),
        "path": str(path),
        "updated_at": now(),
    }
    strategies = [x for x in db.get("strategies", []) if x.get("strategy_id") != sid]
    strategies.append(item)
    db["strategies"] = sorted(strategies, key=lambda x: x["strategy_id"])
    save_db(db)


def default_dates() -> dict[str, str]:
    return {
        "start": "2018-01-01",
        "end": "2025-12-31",
        "train_start": "2018-01-01",
        "train_end": "2021-12-31",
        "validation_start": "2022-01-01",
        "validation_end": "2023-12-31",
        "test_start": "2024-01-01",
        "test_end": "2025-12-31",
    }


def build_spec(strategy_id: str, template_id: str, idea: str, name: str = "") -> dict[str, Any]:
    if template_id not in STRATEGY_TEMPLATES:
        raise SystemExit(f"未知模板：{template_id}")
    t = deepcopy(STRATEGY_TEMPLATES[template_id])
    sid = slug(strategy_id)
    return {
        "meta": {
            "strategy_id": sid,
            "name": name or t["label"],
            "template": template_id,
            "created_at": now(),
            "updated_at": now(),
            "market": "A_SHARE",
            "frequency": "daily",
            "description": idea or t["hypothesis"],
        },
        "hypothesis": idea or t["hypothesis"],
        "universe": t["universe"],
        "date_range": default_dates(),
        "signals": t["signals"],
        "entry_rules": t.get("entry_rules", []),
        "exit_rules": t.get("exit_rules", []),
        "portfolio": {
            "selection_method": "top_rank",
            "top_n": t["portfolio"]["top_n"],
            "max_position_weight": t["portfolio"]["max_position_weight"],
            "rebalance_frequency": t["portfolio"]["rebalance_frequency"],
            "cash_buffer": t["portfolio"].get("cash_buffer", 0.02),
        },
        "risk": {
            "max_drawdown_stop": 0.25,
            "single_stock_stop_loss": 0.12,
            "benchmark": "000300.XSHG",
            "constraints": ["T+1", "limit up/down", "suspension", "transaction cost", "slippage"],
        },
        "cost": {
            "commission_rate": 0.0003,
            "stamp_tax_rate": 0.001,
            "slippage_bps": 5,
        },
        "backtest": {
            "engine": "local_csv_simple",
            "initial_cash": 1000000,
            "execution_price": "next_open",
            "record_trades": True,
        },
        "research_controls": {
            "forbid_future_data": True,
            "walk_forward_required": True,
            "min_test_years": 2,
            "max_parameter_trials": 30,
            "random_seed": 42,
        },
        "notes": {
            "suitable_for": t.get("suitable_for", []),
            "risk_notes": t.get("risk_notes", []),
        },
        "results": [],
        "versions": [{"version": 1, "time": now(), "change": "Initial strategy spec frozen from template."}],
    }


def validate_spec(spec: dict[str, Any]) -> list[tuple[str, str, str]]:
    checks: list[tuple[str, str, str]] = []

    def add(status: str, label: str, message: str) -> None:
        checks.append((status, label, message))

    meta = spec.get("meta", {})
    add("PASS" if meta.get("strategy_id") else "FAIL", "strategy_id", "策略 ID 必须存在。")
    add("PASS" if spec.get("hypothesis") else "FAIL", "hypothesis", "策略假设必须存在。")
    add("PASS" if spec.get("signals") else "FAIL", "signals", "至少要有一个信号。")
    weights = [float(s.get("weight", 0)) for s in spec.get("signals", [])]
    total_weight = sum(weights)
    add("PASS" if 0.8 <= total_weight <= 1.2 else "WARN", "signal_weight_sum", f"信号权重合计 {total_weight:.2f}，建议接近 1。")

    universe = spec.get("universe", {})
    add("PASS" if universe.get("exclude_st", False) else "WARN", "exclude_st", "A 股个股策略建议排除 ST。")
    add("PASS" if universe.get("exclude_suspended", False) else "WARN", "exclude_suspended", "建议排除停牌股票。")
    add("PASS" if universe.get("min_amount", 0) else "WARN", "liquidity_filter", "建议设置成交额过滤。")

    portfolio = spec.get("portfolio", {})
    max_weight = float(portfolio.get("max_position_weight", 1))
    add("PASS" if max_weight <= 0.1 else "WARN", "max_position_weight", f"单票上限 {max_weight:.1%}，小票策略建议 <=10%。")
    add("PASS" if portfolio.get("rebalance_frequency") in {"daily", "weekly", "monthly", "quarterly"} else "FAIL", "rebalance_frequency", "调仓频率必须是 daily/weekly/monthly/quarterly。")

    controls = spec.get("research_controls", {})
    add("PASS" if controls.get("forbid_future_data") else "FAIL", "future_data_guard", "必须开启未来函数防护。")
    add("PASS" if controls.get("walk_forward_required") else "WARN", "walk_forward", "建议要求 walk-forward / 样本外验证。")
    return checks


def cmd_templates(_: argparse.Namespace) -> None:
    print("模板ID                         名称               适合")
    print("-" * 78)
    for key, item in STRATEGY_TEMPLATES.items():
        suitable = "、".join(item.get("suitable_for", [])[:3])
        print(f"{key:<30} {item['label']:<16} {suitable}")


def cmd_template(args: argparse.Namespace) -> None:
    item = STRATEGY_TEMPLATES.get(args.template)
    if not item:
        raise SystemExit(f"未知模板：{args.template}")
    print(json.dumps(item, ensure_ascii=False, indent=2))


def research_plan_for_template(template_id: str) -> dict[str, Any]:
    template = STRATEGY_TEMPLATES.get(template_id)
    if not template:
        raise SystemExit(f"未知模板：{template_id}")
    hints = RESEARCH_HINTS.get(template_id, {})
    return {
        "template": template_id,
        "label": template["label"],
        "hypothesis": template["hypothesis"],
        "primary_skill": hints.get("primary_skill", "MX_StockPick"),
        "secondary_skills": hints.get("secondary_skills", []),
        "queries": {
            "MX_StockPick": hints.get("stockpick_query", ""),
            "MX_FinData": hints.get("findata_query", ""),
            "MX_FinSearch": hints.get("finsearch_query", ""),
        },
        "strategy_rules": {
            "universe": template.get("universe", {}),
            "signals": template.get("signals", []),
            "entry_rules": template.get("entry_rules", []),
            "exit_rules": template.get("exit_rules", []),
            "portfolio": template.get("portfolio", {}),
        },
        "validation_steps": [
            "冻结 strategy spec，不边看结果边改参数。",
            "用果仁验证筛选和排名分段是否单调。",
            "用本地 CSV 做第一层方向验证。",
            "用聚宽回测处理交易成本、涨跌停、停牌、T+1。",
            "做分年、样本外、2x/3x 成本敏感性和参数扰动。",
        ],
        "risk_notes": template.get("risk_notes", []),
        "validation_note": hints.get("validation_note", ""),
    }


def cmd_plan(args: argparse.Namespace) -> None:
    plan = research_plan_for_template(args.template)
    if args.json:
        print(json.dumps(plan, ensure_ascii=False, indent=2))
        return
    print(f"研究计划：{plan['label']} ({plan['template']})")
    print(f"策略假设：{plan['hypothesis']}")
    print(f"主调用 skill：{plan['primary_skill']}")
    secondary = plan.get("secondary_skills", [])
    print(f"辅助 skill：{'、'.join(secondary) if secondary else '无'}")
    print("\n建议查询：")
    for skill, query in plan["queries"].items():
        if query:
            print(f"- {skill}: {query}")
    print("\n验证步骤：")
    for i, step in enumerate(plan["validation_steps"], start=1):
        print(f"{i}. {step}")
    print("\n主要风险：")
    for item in plan["risk_notes"]:
        print(f"- {item}")
    if plan.get("validation_note"):
        print(f"\n研究提醒：{plan['validation_note']}")


def cmd_new(args: argparse.Namespace) -> None:
    ensure_dirs()
    spec = build_spec(args.strategy_id, args.template, args.idea or "", args.name or "")
    path = spec_path(spec["meta"]["strategy_id"])
    if path.exists() and not args.force:
        raise SystemExit(f"策略已存在：{path}，如需覆盖加 --force")
    write_json(path, spec)
    upsert_spec(spec, path)
    print(f"已创建策略规格：{path}")
    print(f"模板：{args.template}")
    print("下一步：export-guorn 做筛选验证，export-jq 生成聚宽骨架，backtest-csv 做本地原型验证。")


def cmd_list(_: argparse.Namespace) -> None:
    db = load_db()
    items = db.get("strategies", [])
    if not items:
        print("暂无策略规格。")
        return
    print("策略ID                         模板                           更新时间")
    print("-" * 90)
    for item in items:
        print(f"{item['strategy_id']:<30} {item.get('template', ''):<30} {item.get('updated_at', '')}")


def cmd_show(args: argparse.Namespace) -> None:
    spec = find_spec(args.strategy)
    if args.json:
        print(json.dumps(spec, ensure_ascii=False, indent=2))
        return
    meta = spec["meta"]
    print(f"策略：{meta['name']} ({meta['strategy_id']})")
    print(f"模板：{meta.get('template', '')}")
    print(f"假设：{spec.get('hypothesis', '')}")
    print("\n信号：")
    for s in spec.get("signals", []):
        print(f"- {s.get('name')} | {s.get('type')} | {s.get('direction')} | weight={s.get('weight')}")
    print("\n组合：")
    for k, v in spec.get("portfolio", {}).items():
        print(f"- {k}: {v}")
    if spec.get("results"):
        print("\n最近结果：")
        for r in spec["results"][-3:]:
            m = r.get("metrics", {})
            print(f"- {r.get('created_at')} | {r.get('platform')} | annual={m.get('annual_return')} drawdown={m.get('max_drawdown')} sharpe={m.get('sharpe')}")


def cmd_validate(args: argparse.Namespace) -> None:
    spec = find_spec(args.strategy)
    checks = validate_spec(spec)
    for status, label, message in checks:
        print(f"[{status}] {label}: {message}")
    if any(status == "FAIL" for status, _, _ in checks):
        raise SystemExit(1)


def jq_scaffold(spec: dict[str, Any]) -> str:
    meta = spec["meta"]
    portfolio = spec["portfolio"]
    freq = portfolio.get("rebalance_frequency", "weekly")
    scheduler = {
        "daily": "run_daily(rebalance, time='09:45')",
        "weekly": "run_weekly(rebalance, weekday=1, time='09:45')",
        "monthly": "run_monthly(rebalance, monthday=1, time='09:45')",
        "quarterly": "run_monthly(rebalance, monthday=1, time='09:45')  # TODO: add quarterly gate",
    }.get(freq, "run_weekly(rebalance, weekday=1, time='09:45')")
    signals = json.dumps(spec.get("signals", []), ensure_ascii=False, indent=4)
    entry_rules = json.dumps(spec.get("entry_rules", []), ensure_ascii=False, indent=4)
    exit_rules = json.dumps(spec.get("exit_rules", []), ensure_ascii=False, indent=4)
    return dedent(f'''\
    # Generated by a-share-quant-lab.
    # Strategy: {meta["strategy_id"]} - {meta["name"]}
    # Hypothesis: {spec.get("hypothesis", "")}
    #
    # This is an execution scaffold. Map factor placeholders to JoinQuant fields
    # and run a real backtest before any live use.

    def initialize(context):
        set_benchmark('{spec.get("risk", {}).get("benchmark", "000300.XSHG")}')
        set_option('use_real_price', True)
        set_order_cost(OrderCost(
            open_tax=0,
            close_tax={spec.get("cost", {}).get("stamp_tax_rate", 0.001)},
            open_commission={spec.get("cost", {}).get("commission_rate", 0.0003)},
            close_commission={spec.get("cost", {}).get("commission_rate", 0.0003)},
            min_commission=5
        ), type='stock')
        set_slippage(FixedSlippage({spec.get("cost", {}).get("slippage_bps", 5) / 10000:.6f}))

        g.strategy_id = '{meta["strategy_id"]}'
        g.top_n = {int(portfolio.get("top_n", 20))}
        g.max_position_weight = {float(portfolio.get("max_position_weight", 0.05))}
        g.cash_buffer = {float(portfolio.get("cash_buffer", 0.02))}
        g.signals = {signals}
        g.entry_rules = {entry_rules}
        g.exit_rules = {exit_rules}

        {scheduler}


    def before_trading_start(context):
        g.candidates = get_candidate_universe(context)


    def rebalance(context):
        current_data = get_current_data()
        stocks = filter_universe(context, g.candidates, current_data)
        scores = compute_scores(context, stocks)
        target_stocks = select_top_stocks(scores, g.top_n)
        adjust_positions(context, target_stocks, current_data)


    def get_candidate_universe(context):
        base = '{spec.get("universe", {}).get("base", "A_SHARE")}'
        if base == 'CSI300':
            return get_index_stocks('000300.XSHG')
        if base == 'CSI500':
            return get_index_stocks('000905.XSHG')
        if base == 'CSI1000':
            return get_index_stocks('000852.XSHG')
        return get_index_stocks('000985.XSHG')  # 全A近似，必要时替换为自定义股票池


    def filter_universe(context, stocks, current_data):
        result = []
        for stock in stocks:
            data = current_data[stock]
            if data.paused:
                continue
            if data.is_st:
                continue
            if data.last_price >= data.high_limit or data.last_price <= data.low_limit:
                continue
            result.append(stock)
        return result


    def compute_scores(context, stocks):
        # TODO: Replace placeholder score logic with JoinQuant price/fundamental fields.
        # Important: do not use same-day close to trade same day.
        scores = {{}}
        for stock in stocks:
            scores[stock] = 0.0
        return scores


    def select_top_stocks(scores, top_n):
        return [
            stock for stock, score in
            sorted(scores.items(), key=lambda item: item[1], reverse=True)[:top_n]
        ]


    def adjust_positions(context, target_stocks, current_data):
        target_set = set(target_stocks)
        for stock in list(context.portfolio.positions.keys()):
            pos = context.portfolio.positions[stock]
            if stock not in target_set and pos.closeable_amount > 0:
                order_target_value(stock, 0)

        if not target_stocks:
            return
        target_value = context.portfolio.total_value * min(
            g.max_position_weight,
            (1.0 - g.cash_buffer) / max(len(target_stocks), 1)
        )
        for stock in target_stocks:
            data = current_data[stock]
            if data.paused or data.last_price >= data.high_limit:
                continue
            order_target_value(stock, target_value)


    def after_trading_end(context):
        log.info('strategy_id=%s total_value=%s cash=%s' % (
            g.strategy_id, context.portfolio.total_value, context.portfolio.cash
        ))
    ''')


def cmd_export_jq(args: argparse.Namespace) -> None:
    ensure_dirs()
    spec = find_spec(args.strategy)
    sid = spec["meta"]["strategy_id"]
    path = STRATEGY_DIR / f"{sid}_joinquant.py"
    path.write_text(jq_scaffold(spec), encoding="utf-8")
    print(f"已生成聚宽策略骨架：{path}")
    print("提醒：这是 scaffold，需要把因子占位逻辑映射到聚宽真实字段后再跑正式回测。")


def guorn_markdown(spec: dict[str, Any]) -> str:
    meta = spec["meta"]
    universe = spec.get("universe", {})
    signals = spec.get("signals", [])
    portfolio = spec.get("portfolio", {})
    lines = [
        f"# 果仁筛选说明：{meta['strategy_id']}",
        "",
        f"策略假设：{spec.get('hypothesis', '')}",
        "",
        "## 1. 股票池",
        f"- 基础池：{universe.get('base', 'A_SHARE')}",
        f"- 排除 ST：{universe.get('exclude_st')}",
        f"- 排除停牌：{universe.get('exclude_suspended')}",
        f"- 上市天数：>{universe.get('exclude_new_stock_days', 0)}",
        f"- 最低成交额：>{universe.get('min_amount', 0)}",
        "",
        "## 2. 筛选条件",
        "- 先用流动性和风险过滤，再做排名。",
        "- 小盘/高换手策略必须提高成交额门槛。",
        "",
        "## 3. 排名因子",
    ]
    for s in signals:
        direction = "越高越好" if s.get("direction") == "positive" else "越低越好"
        lines.append(f"- {s.get('name')}：{direction}，权重 {s.get('weight')}")
    lines += [
        "",
        "## 4. 调仓",
        f"- 调仓频率：{portfolio.get('rebalance_frequency')}",
        f"- 持仓数量：前 {portfolio.get('top_n')} 只",
        f"- 单票上限：{portfolio.get('max_position_weight')}",
        "",
        "## 5. 验收重点",
        "- 排名分组是否单调。",
        "- 扣交易成本后是否仍有效。",
        "- 最大回撤是否能接受。",
        "- 换手是否过高。",
        "- 样本外是否明显衰减。",
    ]
    return "\n".join(lines) + "\n"


def cmd_export_guorn(args: argparse.Namespace) -> None:
    ensure_dirs()
    spec = find_spec(args.strategy)
    sid = spec["meta"]["strategy_id"]
    path = STRATEGY_DIR / f"{sid}_guorn.md"
    path.write_text(guorn_markdown(spec), encoding="utf-8")
    print(f"已生成果仁筛选说明：{path}")


def cmd_schema(args: argparse.Namespace) -> None:
    path = Path(args.out)
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = [
        ["date", "code", "open", "high", "low", "close", "pre_close", "volume", "amount", "paused", "is_st", "is_limit_up", "is_limit_down", "industry", "market_cap", "turnover_rate"],
        ["2024-01-02", "000001.XSHE", "9.80", "10.05", "9.72", "9.96", "9.78", "120000000", "1180000000", "0", "0", "0", "0", "Bank", "210000000000", "0.58"],
        ["2024-01-02", "600000.XSHG", "7.10", "7.22", "7.05", "7.18", "7.11", "85000000", "610000000", "0", "0", "0", "0", "Bank", "180000000000", "0.31"],
    ]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(rows)
    print(f"已生成 CSV schema 示例：{path}")


def require_pandas():
    try:
        import pandas as pd  # type: ignore
        import numpy as np  # type: ignore
        return pd, np
    except ImportError as exc:
        raise SystemExit("本地回测需要 pandas 和 numpy。请先安装后再跑 backtest-csv。") from exc


def load_market_csv(path: Path):
    pd, _ = require_pandas()
    df = pd.read_csv(path)
    required = {"date", "code", "open", "close", "volume", "amount", "paused", "is_st"}
    missing = required - set(df.columns)
    if missing:
        raise SystemExit(f"CSV 缺少字段：{', '.join(sorted(missing))}")
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values(["code", "date"]).reset_index(drop=True)
    for col in ["open", "close", "volume", "amount"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    for col in ["paused", "is_st", "is_limit_up", "is_limit_down"]:
        if col not in df.columns:
            df[col] = 0
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
    return df


def add_signal_columns(df, spec: dict[str, Any]):
    pd, np = require_pandas()
    out = df.copy()
    g = out.groupby("code", group_keys=False)
    out["ret_1d"] = g["close"].pct_change()
    for sig in spec.get("signals", []):
        name = sig["name"]
        typ = sig.get("type")
        window = int(sig.get("window", 20))
        if typ == "price_momentum":
            out[name] = g["close"].pct_change(window)
        elif typ == "realized_volatility":
            out[name] = g["close"].pct_change().rolling(window).std().reset_index(level=0, drop=True)
        elif typ == "amount_mean":
            out[name] = g["amount"].rolling(window).mean().reset_index(level=0, drop=True)
        elif typ == "market_cap":
            col = sig.get("column", "market_cap")
            out[name] = pd.to_numeric(out[col], errors="coerce") if col in out.columns else np.nan
        elif typ == "liquidity":
            col = sig.get("column", "amount")
            out[name] = pd.to_numeric(out[col], errors="coerce") if col in out.columns else np.nan
        elif typ == "column":
            col = sig.get("column", name)
            out[name] = pd.to_numeric(out[col], errors="coerce") if col in out.columns else np.nan
        else:
            out[name] = np.nan
    if any(rule == "close > ma20" for rule in spec.get("entry_rules", [])):
        out["ma20"] = g["close"].rolling(20).mean().reset_index(level=0, drop=True)
    if any(rule == "close > ma60" or rule == "close < ma60" for rule in spec.get("entry_rules", []) + spec.get("exit_rules", [])):
        out["ma60"] = g["close"].rolling(60).mean().reset_index(level=0, drop=True)
    return out


def score_frame(df, spec: dict[str, Any]):
    pd, np = require_pandas()
    scored = df.copy()
    scored["score"] = 0.0
    for sig in spec.get("signals", []):
        name = sig["name"]
        direction = sig.get("direction", "positive")
        weight = float(sig.get("weight", 0))
        if name not in scored.columns:
            continue
        def zscore(s):
            s = pd.to_numeric(s, errors="coerce")
            std = s.std(ddof=0)
            if not std or math.isnan(std):
                return s * np.nan
            return (s - s.mean()) / std
        z = scored.groupby("date")[name].transform(zscore)
        if direction == "negative":
            z = -z
        scored["score"] = scored["score"] + z.fillna(0) * weight
    return scored


def apply_universe_filters(df, spec: dict[str, Any]):
    universe = spec.get("universe", {})
    mask = df["paused"].fillna(0).astype(int) == 0
    if universe.get("exclude_st", True):
        mask &= df["is_st"].fillna(0).astype(int) == 0
    if universe.get("exclude_limit_up_down", True):
        mask &= df["is_limit_up"].fillna(0).astype(int) == 0
        mask &= df["is_limit_down"].fillna(0).astype(int) == 0
    min_amount = float(universe.get("min_amount", 0) or 0)
    if min_amount:
        mask &= df["amount"].fillna(0) >= min_amount
    for rule in spec.get("entry_rules", []):
        if rule == "close > ma20" and "ma20" in df.columns:
            mask &= df["close"] > df["ma20"]
        if rule == "close > ma60" and "ma60" in df.columns:
            mask &= df["close"] > df["ma60"]
    return df[mask].copy()


def rebalance_dates(dates, frequency: str):
    pd, _ = require_pandas()
    unique = pd.Series(sorted(pd.to_datetime(dates).unique()))
    if frequency == "daily":
        return list(unique)
    if frequency == "weekly":
        return list(unique.groupby(unique.dt.to_period("W")).first())
    if frequency == "monthly":
        return list(unique.groupby(unique.dt.to_period("M")).first())
    if frequency == "quarterly":
        return list(unique.groupby(unique.dt.to_period("Q")).first())
    return list(unique.groupby(unique.dt.to_period("W")).first())


def max_drawdown(values: list[float]) -> float:
    peak = values[0] if values else 1.0
    mdd = 0.0
    for v in values:
        peak = max(peak, v)
        if peak:
            mdd = min(mdd, v / peak - 1)
    return mdd


def compute_metrics(equity_rows: list[dict[str, Any]]) -> dict[str, Any]:
    if len(equity_rows) < 2:
        return {}
    values = [float(r["equity"]) for r in equity_rows]
    returns = [values[i] / values[i - 1] - 1 for i in range(1, len(values)) if values[i - 1]]
    total_return = values[-1] / values[0] - 1
    years = max(len(returns) / 252, 1 / 252)
    annual_return = (1 + total_return) ** (1 / years) - 1
    mean_ret = sum(returns) / len(returns) if returns else 0.0
    variance = sum((r - mean_ret) ** 2 for r in returns) / len(returns) if returns else 0.0
    annual_vol = math.sqrt(variance) * math.sqrt(252)
    sharpe = (mean_ret * 252 / annual_vol) if annual_vol else 0.0
    win_rate = sum(1 for r in returns if r > 0) / len(returns) if returns else 0.0
    return {
        "total_return": round(total_return, 6),
        "annual_return": round(annual_return, 6),
        "annual_volatility": round(annual_vol, 6),
        "sharpe": round(sharpe, 6),
        "max_drawdown": round(max_drawdown(values), 6),
        "win_rate": round(win_rate, 6),
    }


def run_backtest(df, spec: dict[str, Any]) -> dict[str, Any]:
    pd, _ = require_pandas()
    df = add_signal_columns(df, spec)
    df = score_frame(df, spec)
    eligible = apply_universe_filters(df, spec)
    dates = sorted(df["date"].unique())
    date_set = set(rebalance_dates(dates, spec.get("portfolio", {}).get("rebalance_frequency", "weekly")))

    initial_cash = float(spec.get("backtest", {}).get("initial_cash", 1000000))
    equity = initial_cash
    holdings: list[str] = []
    prev_prices: dict[str, float] = {}
    equity_rows: list[dict[str, Any]] = []
    position_rows: list[dict[str, Any]] = []
    trade_rows: list[dict[str, Any]] = []
    turnover_sum = 0.0
    cost_rate = float(spec.get("cost", {}).get("commission_rate", 0.0003)) * 2
    cost_rate += float(spec.get("cost", {}).get("stamp_tax_rate", 0.001))
    cost_rate += float(spec.get("cost", {}).get("slippage_bps", 5)) / 10000 * 2

    top_n = int(spec.get("portfolio", {}).get("top_n", 20))
    cash_buffer = float(spec.get("portfolio", {}).get("cash_buffer", 0.02))

    by_date = {d: group.copy() for d, group in df.groupby("date")}
    eligible_by_date = {d: group.copy() for d, group in eligible.groupby("date")}

    for date in dates:
        day = by_date[date]
        price_map = dict(zip(day["code"], day["close"]))
        if holdings and prev_prices:
            returns = []
            for code in holdings:
                p0 = prev_prices.get(code)
                p1 = price_map.get(code)
                if p0 and p1:
                    returns.append(p1 / p0 - 1)
            if returns:
                equity *= 1 + (sum(returns) / len(returns)) * (1 - cash_buffer)

        if date in date_set:
            cand = eligible_by_date.get(date)
            if cand is not None and not cand.empty:
                cand = cand.dropna(subset=["score"]).sort_values("score", ascending=False)
                target = list(cand.head(top_n)["code"])
                old_set = set(holdings)
                new_set = set(target)
                if old_set or new_set:
                    turnover = len(old_set.symmetric_difference(new_set)) / max(len(old_set.union(new_set)), 1)
                    turnover_sum += turnover
                    equity *= max(0.0, 1 - turnover * cost_rate)
                for code in sorted(old_set - new_set):
                    trade_rows.append({"date": str(pd.to_datetime(date).date()), "code": code, "side": "sell", "reason": "rebalance_out"})
                for code in sorted(new_set - old_set):
                    trade_rows.append({"date": str(pd.to_datetime(date).date()), "code": code, "side": "buy", "reason": "rebalance_in"})
                holdings = target

        for code in holdings:
            position_rows.append({"date": str(pd.to_datetime(date).date()), "code": code, "weight": round((1 - cash_buffer) / max(len(holdings), 1), 6)})
        equity_rows.append({"date": str(pd.to_datetime(date).date()), "equity": round(equity, 4), "holdings": len(holdings)})
        prev_prices = price_map

    metrics = compute_metrics(equity_rows)
    metrics["turnover"] = round(turnover_sum, 6)
    metrics["rebalance_count"] = len([d for d in dates if d in date_set])
    metrics["average_holdings"] = round(sum(r["holdings"] for r in equity_rows) / len(equity_rows), 4) if equity_rows else 0
    return {"metrics": metrics, "equity": equity_rows, "positions": position_rows, "trades": trade_rows}


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def append_result_to_spec(spec: dict[str, Any], result_record: dict[str, Any]) -> None:
    sid = spec["meta"]["strategy_id"]
    path = spec_path(sid)
    if path.exists():
        latest = read_json(path)
        latest.setdefault("results", []).append(result_record)
        latest["meta"]["updated_at"] = now()
        write_json(path, latest)
        upsert_spec(latest, path)


def cmd_backtest_csv(args: argparse.Namespace) -> None:
    ensure_dirs()
    spec = find_spec(args.strategy)
    data_path = Path(args.prices)
    df = load_market_csv(data_path)
    result = run_backtest(df, spec)
    sid = spec["meta"]["strategy_id"]
    run_id = f"{sid}_{stamp()}"
    out_dir = BACKTEST_DIR / run_id
    out_dir.mkdir(parents=True, exist_ok=True)
    write_csv(out_dir / "equity_curve.csv", result["equity"])
    write_csv(out_dir / "positions.csv", result["positions"])
    write_csv(out_dir / "trades.csv", result["trades"])
    record = {
        "result_id": run_id,
        "strategy_id": sid,
        "platform": "local_csv",
        "engine": "local_csv_simple",
        "created_at": now(),
        "spec_hash": canonical_json_hash(spec),
        "data_hash": file_hash(data_path),
        "metrics": result["metrics"],
        "artifacts": {
            "equity_curve_csv": str(out_dir / "equity_curve.csv"),
            "positions_csv": str(out_dir / "positions.csv"),
            "trades_csv": str(out_dir / "trades.csv"),
        },
        "warnings": local_warnings(spec, result["metrics"]),
    }
    write_json(out_dir / "backtest_result.json", record)
    append_result_to_spec(spec, record)
    print(f"本地简化回测完成：{out_dir / 'backtest_result.json'}")
    for k, v in record["metrics"].items():
        print(f"- {k}: {v}")
    if record["warnings"]:
        print("警告：")
        for w in record["warnings"]:
            print(f"- {w}")


def run_and_store_backtest(spec: dict[str, Any], data_path: Path, label: str = "") -> dict[str, Any]:
    df = load_market_csv(data_path)
    result = run_backtest(df, spec)
    sid = spec["meta"]["strategy_id"]
    run_id = f"{sid}_{label + '_' if label else ''}{stamp()}"
    out_dir = BACKTEST_DIR / run_id
    out_dir.mkdir(parents=True, exist_ok=True)
    write_csv(out_dir / "equity_curve.csv", result["equity"])
    write_csv(out_dir / "positions.csv", result["positions"])
    write_csv(out_dir / "trades.csv", result["trades"])
    record = {
        "result_id": run_id,
        "strategy_id": sid,
        "platform": "local_csv",
        "engine": "local_csv_simple",
        "created_at": now(),
        "spec_hash": canonical_json_hash(spec),
        "data_hash": file_hash(data_path),
        "metrics": result["metrics"],
        "artifacts": {
            "equity_curve_csv": str(out_dir / "equity_curve.csv"),
            "positions_csv": str(out_dir / "positions.csv"),
            "trades_csv": str(out_dir / "trades.csv"),
        },
        "warnings": local_warnings(spec, result["metrics"]),
    }
    write_json(out_dir / "backtest_result.json", record)
    append_result_to_spec(spec, record)
    return record


def cmd_batch_backtest(args: argparse.Namespace) -> None:
    ensure_dirs()
    data_path = Path(args.prices)
    specs: list[dict[str, Any]] = []
    if args.all_templates:
        for template_id in STRATEGY_TEMPLATES:
            sid = f"batch_{template_id}"
            spec = build_spec(sid, template_id, STRATEGY_TEMPLATES[template_id]["hypothesis"])
            path = spec_path(spec["meta"]["strategy_id"])
            write_json(path, spec)
            upsert_spec(spec, path)
            specs.append(spec)
    else:
        for strategy in args.strategies:
            specs.append(find_spec(strategy))
    if not specs:
        raise SystemExit("请提供策略 ID，或使用 --all-templates。")

    rows: list[dict[str, Any]] = []
    for spec in specs:
        record = run_and_store_backtest(spec, data_path, label="batch")
        metrics = record.get("metrics", {})
        rows.append({
            "strategy_id": record["strategy_id"],
            "annual_return": metrics.get("annual_return"),
            "max_drawdown": metrics.get("max_drawdown"),
            "sharpe": metrics.get("sharpe"),
            "win_rate": metrics.get("win_rate"),
            "turnover": metrics.get("turnover"),
            "warnings": "; ".join(record.get("warnings", [])),
            "result_id": record["result_id"],
        })

    out = BACKTEST_DIR / f"batch_summary_{stamp()}.csv"
    write_csv(out, rows)
    print(f"批量回测完成：{out}")
    print("strategy_id                  annual_return  max_drawdown  sharpe     warnings")
    print("-" * 100)
    for row in rows:
        print(f"{row['strategy_id']:<28} {row['annual_return']!s:<14} {row['max_drawdown']!s:<13} {row['sharpe']!s:<10} {row['warnings']}")


def local_warnings(spec: dict[str, Any], metrics: dict[str, Any]) -> list[str]:
    warnings: list[str] = []
    if metrics.get("max_drawdown", 0) < -float(spec.get("risk", {}).get("max_drawdown_stop", 0.25)):
        warnings.append("最大回撤超过策略阈值。")
    if metrics.get("turnover", 0) > 20:
        warnings.append("换手偏高，必须做 2x/3x 成本敏感性。")
    if metrics.get("sharpe", 0) < 0.5:
        warnings.append("Sharpe 偏低，收益稳定性不足。")
    if metrics.get("sharpe", 0) > 5:
        warnings.append("Sharpe 异常高，优先检查样本、未来函数、合成数据或成交假设。")
    if metrics.get("annual_return", 0) > 1:
        warnings.append("年化收益异常高，不能作为实盘依据，必须用真实数据和样本外复核。")
    if spec.get("universe", {}).get("base") in {"A_SHARE", "CSI1000", "ETF_POOL"} and spec.get("universe", {}).get("min_amount", 0) < 50000000:
        warnings.append("流动性过滤偏低，小票策略可能回测虚高。")
    return warnings


def cmd_record_result(args: argparse.Namespace) -> None:
    ensure_dirs()
    spec = find_spec(args.strategy)
    sid = spec["meta"]["strategy_id"]
    result = {
        "result_id": f"{sid}_{args.platform}_{stamp()}",
        "strategy_id": sid,
        "platform": args.platform,
        "engine": args.platform,
        "created_at": now(),
        "period": args.period,
        "metrics": {
            "annual_return": args.annual_return,
            "max_drawdown": args.max_drawdown,
            "sharpe": args.sharpe,
            "win_rate": args.win_rate,
            "turnover": args.turnover,
        },
        "summary": args.summary,
        "warnings": [],
    }
    append_result_to_spec(spec, result)
    path = BACKTEST_DIR / f"{result['result_id']}.json"
    write_json(path, result)
    print(f"已记录结果：{path}")


def checklist(spec: dict[str, Any], result: dict[str, Any] | None = None) -> dict[str, Any]:
    checks: list[dict[str, str]] = []

    def add(cid: str, status: str, msg: str) -> None:
        checks.append({"id": cid, "status": status, "message": msg})

    controls = spec.get("research_controls", {})
    add("spec_frozen", "PASS" if spec.get("versions") else "WARN", "策略规格应在回测前冻结。")
    add("future_guard", "PASS" if controls.get("forbid_future_data") else "FAIL", "必须开启未来函数防护。")
    add("walk_forward", "PASS" if controls.get("walk_forward_required") else "WARN", "建议做训练/验证/样本外切分。")
    add("st_filter", "PASS" if spec.get("universe", {}).get("exclude_st") else "WARN", "A 股个股策略建议排除 ST。")
    add("liquidity_filter", "PASS" if spec.get("universe", {}).get("min_amount", 0) else "WARN", "建议设置成交额过滤。")
    add("cost_model", "PASS" if spec.get("cost") else "FAIL", "必须设置交易成本。")
    add("position_cap", "PASS" if float(spec.get("portfolio", {}).get("max_position_weight", 1)) <= 0.1 else "WARN", "单票仓位建议 <=10%。")
    add("signal_count", "PASS" if len(spec.get("signals", [])) <= 8 else "WARN", "信号过多可能过拟合。")

    if result:
        metrics = result.get("metrics", {})
        sharpe = metrics.get("sharpe")
        mdd = metrics.get("max_drawdown")
        turnover = metrics.get("turnover")
        add("result_exists", "PASS", "已读取回测结果。")
        if sharpe is not None:
            if sharpe > 5:
                add("sharpe_suspicious", "WARN", f"Sharpe={sharpe}，异常高，优先排查未来函数/样本过短/合成数据。")
            else:
                add("sharpe_floor", "PASS" if sharpe >= 0.8 else "WARN", f"Sharpe={sharpe}。")
        annual_return = metrics.get("annual_return")
        if annual_return is not None and annual_return > 1:
            add("annual_return_suspicious", "WARN", f"annual_return={annual_return}，异常高，不能直接外推到实盘。")
        if mdd is not None:
            add("drawdown_control", "PASS" if mdd >= -0.25 else "WARN", f"max_drawdown={mdd}。")
        if turnover is not None:
            add("turnover_reasonable", "PASS" if turnover <= 20 else "WARN", f"turnover={turnover}。")
    else:
        add("result_exists", "WARN", "未提供回测结果，只能检查规格。")

    status = "PASS"
    if any(c["status"] == "FAIL" for c in checks):
        status = "FAIL"
    elif any(c["status"] == "WARN" for c in checks):
        status = "WARN"
    return {
        "strategy_id": spec["meta"]["strategy_id"],
        "status": status,
        "checks": checks,
        "recommendations": [
            "先跑果仁分组/排名验证，再跑聚宽正式回测。",
            "至少做分年、样本外、2x/3x 成本敏感性。",
            "对比等权基准和简单动量/红利基准。",
            "回测通过后先模拟盘或小仓，不从曲线直接重仓。",
        ],
    }


def cmd_checklist(args: argparse.Namespace) -> None:
    spec = find_spec(args.strategy)
    result = read_json(Path(args.result)) if args.result else None
    report = checklist(spec, result)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return
    print(f"策略检查：{report['strategy_id']} | 状态：{report['status']}")
    for c in report["checks"]:
        print(f"[{c['status']}] {c['id']}: {c['message']}")
    print("建议：")
    for r in report["recommendations"]:
        print(f"- {r}")


def cmd_result_list(args: argparse.Namespace) -> None:
    base = Path(args.dir) if args.dir else BACKTEST_DIR
    if not base.exists():
        print("暂无回测结果。")
        return
    paths = sorted(base.rglob("backtest_result.json")) + sorted(p for p in base.glob("*.json") if p.name != "strategy_specs.json")
    if not paths:
        print("暂无回测结果。")
        return
    print("结果文件")
    print("-" * 100)
    for path in paths:
        print(path)


def result_records(base: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    if not base.exists():
        return records
    paths = sorted(base.rglob("backtest_result.json")) + sorted(p for p in base.glob("*.json") if p.name != "strategy_specs.json")
    seen: set[str] = set()
    for path in paths:
        if str(path) in seen:
            continue
        seen.add(str(path))
        try:
            record = read_json(path)
            record["_path"] = str(path)
            records.append(record)
        except Exception:
            continue
    return records


def cmd_compare(args: argparse.Namespace) -> None:
    base = Path(args.dir) if args.dir else BACKTEST_DIR
    records = result_records(base)
    if args.strategy:
        wanted = set(args.strategy)
        records = [r for r in records if r.get("strategy_id") in wanted]
    if not records:
        print("暂无可比较结果。")
        return

    latest_by_strategy: dict[str, dict[str, Any]] = {}
    for record in records:
        sid = record.get("strategy_id", "")
        if not sid:
            continue
        if sid not in latest_by_strategy or record.get("created_at", "") > latest_by_strategy[sid].get("created_at", ""):
            latest_by_strategy[sid] = record

    rows = []
    for record in latest_by_strategy.values():
        metrics = record.get("metrics", {})
        rows.append({
            "strategy_id": record.get("strategy_id", ""),
            "annual_return": metrics.get("annual_return"),
            "max_drawdown": metrics.get("max_drawdown"),
            "sharpe": metrics.get("sharpe"),
            "win_rate": metrics.get("win_rate"),
            "turnover": metrics.get("turnover"),
            "warning_count": len(record.get("warnings", [])),
            "created_at": record.get("created_at", ""),
        })

    rows.sort(key=lambda r: (r["sharpe"] if isinstance(r["sharpe"], (int, float)) else -999), reverse=True)
    print("strategy_id                  annual_return  max_drawdown  sharpe     win_rate   turnover   warn")
    print("-" * 104)
    for row in rows:
        print(
            f"{row['strategy_id']:<28} "
            f"{str(row['annual_return']):<14} "
            f"{str(row['max_drawdown']):<13} "
            f"{str(row['sharpe']):<10} "
            f"{str(row['win_rate']):<10} "
            f"{str(row['turnover']):<10} "
            f"{row['warning_count']}"
        )
    if args.out:
        write_csv(Path(args.out), rows)
        print(f"\n已导出比较表：{args.out}")


def render_report(spec: dict[str, Any], result: dict[str, Any] | None) -> str:
    metrics = result.get("metrics", {}) if result else {}
    check = checklist(spec, result)
    lines = [
        f"# 策略研究报告：{spec['meta']['strategy_id']}",
        "",
        f"策略名称：{spec['meta']['name']}",
        f"策略假设：{spec.get('hypothesis', '')}",
        "",
        "## 规则",
        "",
        f"- 股票池：{spec.get('universe', {}).get('base')}",
        f"- 调仓：{spec.get('portfolio', {}).get('rebalance_frequency')}",
        f"- 持仓数量：{spec.get('portfolio', {}).get('top_n')}",
        f"- 单票上限：{spec.get('portfolio', {}).get('max_position_weight')}",
        "",
        "## 信号",
    ]
    for s in spec.get("signals", []):
        lines.append(f"- {s.get('name')}：{s.get('type')}，方向 {s.get('direction')}，权重 {s.get('weight')}")
    lines += ["", "## 回测指标"]
    if metrics:
        for k, v in metrics.items():
            lines.append(f"- {k}: {v}")
    else:
        lines.append("- 暂无回测结果。")
    lines += ["", "## 防过拟合检查", f"- 总体状态：{check['status']}"]
    for c in check["checks"]:
        lines.append(f"- [{c['status']}] {c['id']}：{c['message']}")
    lines += ["", "## 下一步"]
    for r in check["recommendations"]:
        lines.append(f"- {r}")
    return "\n".join(lines) + "\n"


def cmd_report(args: argparse.Namespace) -> None:
    ensure_dirs()
    spec = find_spec(args.strategy)
    result = read_json(Path(args.result)) if args.result else None
    out = Path(args.out) if args.out else REPORT_DIR / f"{spec['meta']['strategy_id']}_{stamp()}.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render_report(spec, result), encoding="utf-8")
    print(f"已生成研究报告：{out}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A-share AI quant lab")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("templates", help="List built-in strategy templates")
    p.set_defaults(func=cmd_templates)

    p = sub.add_parser("template", help="Show a strategy template")
    p.add_argument("template")
    p.set_defaults(func=cmd_template)

    p = sub.add_parser("plan", help="Show research plan and skill calls for a template")
    p.add_argument("template")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_plan)

    p = sub.add_parser("new", help="Create a strategy spec from template")
    p.add_argument("strategy_id")
    p.add_argument("--template", default="smallcap_momentum_quality")
    p.add_argument("--idea", default="")
    p.add_argument("--name", default="")
    p.add_argument("--force", action="store_true")
    p.set_defaults(func=cmd_new)

    p = sub.add_parser("list", help="List strategy specs")
    p.set_defaults(func=cmd_list)

    p = sub.add_parser("show", help="Show strategy spec")
    p.add_argument("strategy")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_show)

    p = sub.add_parser("validate", help="Validate strategy spec")
    p.add_argument("strategy")
    p.set_defaults(func=cmd_validate)

    p = sub.add_parser("export-jq", help="Export JoinQuant scaffold")
    p.add_argument("strategy")
    p.set_defaults(func=cmd_export_jq)

    p = sub.add_parser("export-guorn", help="Export Guorn screening guide")
    p.add_argument("strategy")
    p.set_defaults(func=cmd_export_guorn)

    p = sub.add_parser("schema", help="Write market CSV schema sample")
    p.add_argument("--out", default=str(DATA_DIR / "market_data.schema.csv"))
    p.set_defaults(func=cmd_schema)

    p = sub.add_parser("backtest-csv", help="Run simple local CSV backtest")
    p.add_argument("strategy")
    p.add_argument("--prices", required=True)
    p.set_defaults(func=cmd_backtest_csv)

    p = sub.add_parser("batch-backtest", help="Run simple CSV backtest for multiple strategies")
    p.add_argument("strategies", nargs="*")
    p.add_argument("--prices", required=True)
    p.add_argument("--all-templates", action="store_true")
    p.set_defaults(func=cmd_batch_backtest)

    p = sub.add_parser("record-result", help="Record external backtest metrics")
    p.add_argument("strategy")
    p.add_argument("--platform", default="joinquant")
    p.add_argument("--period", default="")
    p.add_argument("--annual-return", type=float, default=None)
    p.add_argument("--max-drawdown", type=float, default=None)
    p.add_argument("--sharpe", type=float, default=None)
    p.add_argument("--win-rate", type=float, default=None)
    p.add_argument("--turnover", type=float, default=None)
    p.add_argument("--summary", default="")
    p.set_defaults(func=cmd_record_result)

    p = sub.add_parser("checklist", help="Run anti-overfitting checklist")
    p.add_argument("strategy")
    p.add_argument("--result", default="")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_checklist)

    p = sub.add_parser("result-list", help="List stored results")
    p.add_argument("--dir", default="")
    p.set_defaults(func=cmd_result_list)

    p = sub.add_parser("compare", help="Compare latest stored results")
    p.add_argument("strategy", nargs="*")
    p.add_argument("--dir", default="")
    p.add_argument("--out", default="")
    p.set_defaults(func=cmd_compare)

    p = sub.add_parser("report", help="Render strategy research report")
    p.add_argument("strategy")
    p.add_argument("--result", default="")
    p.add_argument("--out", default="")
    p.set_defaults(func=cmd_report)

    return parser


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
