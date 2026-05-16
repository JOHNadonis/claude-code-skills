#!/usr/bin/env python3
"""
持仓主动预警脚本：定时检测资金流向异动、公告、止损临近、大盘风险，输出分级告警。

用法：
  python3 scripts/monitor.py              # 检查所有持仓
  python3 scripts/monitor.py 002463       # 只检查指定股票
  python3 scripts/monitor.py --market     # 只检查大盘
  python3 scripts/monitor.py --config     # 查看/修改告警阈值

定时运行（PM2 示例）：
  pm2 start "cd ~/.claude/skills/a-stock-analysis && python3 scripts/monitor.py" \
      --name a-stock-monitor --cron "0 9,10,11,13,14 * * 1-5" --no-autorestart

输出格式：
  🔴 CRITICAL  — 需要立即处理（止损触发/重大利空/大盘崩盘）
  🟡 WARNING   — 需要关注（接近止损/资金流向反转/异常量比）
  🔵 INFO      — 参考信息（异动机会/利好消息/大单流入）
"""

import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, time as dtime
from pathlib import Path

# ──────────────────────────────────────────────────────────────────────────────
# 路径配置
# ──────────────────────────────────────────────────────────────────────────────
SKILL_DIR     = Path(__file__).parent.parent
PORTFOLIO_FILE = SKILL_DIR / "data" / "portfolio.json"
ALERT_CONFIG  = SKILL_DIR / "data" / "alert_config.json"
MX_SCRIPT     = Path.home() / ".claude/skills/MX_FinData/scripts/get_data.py"

# ──────────────────────────────────────────────────────────────────────────────
# 默认告警阈值（可在 alert_config.json 中覆盖）
# ──────────────────────────────────────────────────────────────────────────────
DEFAULT_CONFIG = {
    # 止损相关
    "stop_loss_pct": 0.95,          # 成本×0.95 为止损位
    "stop_loss_warn_pct": 0.97,     # 距止损位<3% 触发WARNING
    # 量比相关
    "volume_ratio_low": 0.5,        # 量比<0.5 触发WARNING（地量）
    "volume_ratio_spike": 3.0,      # 量比>3.0 触发INFO（异动）
    # 资金流向相关（单位：万元）
    "capital_outflow_warn": -3000,  # 超大单净流出 > 3000万 → WARNING
    "capital_inflow_info": 3000,    # 超大单净流入 > 3000万 → INFO
    # 大盘相关
    "market_drop_warn": -1.0,       # 大盘跌 > 1% → WARNING
    "market_drop_critical": -2.0,   # 大盘跌 > 2% → CRITICAL
    "market_rise_info": 2.0,        # 大盘涨 > 2% → INFO（追高风险）
    # 解禁相关（天数）
    "unlock_warn_days": 30,         # 距解禁 < 30天 → WARNING
    "unlock_critical_days": 7,      # 距解禁 < 7天 → CRITICAL
    # 质押相关
    "pledge_warn_pct": 40,          # 质押比 > 40% → WARNING
}

# ──────────────────────────────────────────────────────────────────────────────
# 告警记录（避免同一条件重复推送）
# ──────────────────────────────────────────────────────────────────────────────
ALERT_LEVELS = {"CRITICAL": "🔴", "WARNING": "🟡", "INFO": "🔵"}


class Alert:
    def __init__(self, level: str, code: str, name: str, trigger: str, message: str, action: str = ""):
        self.level   = level    # CRITICAL / WARNING / INFO
        self.code    = code
        self.name    = name
        self.trigger = trigger  # 触发条件简述
        self.message = message  # 详细说明
        self.action  = action   # 建议操作
        self.time    = datetime.now().strftime("%H:%M:%S")

    def __str__(self):
        icon = ALERT_LEVELS.get(self.level, "⚪")
        lines = [
            f"{icon} [{self.level}] {self.name}({self.code}) — {self.trigger}",
            f"   {self.message}",
        ]
        if self.action:
            lines.append(f"   → 建议：{self.action}")
        return "\n".join(lines)


# ──────────────────────────────────────────────────────────────────────────────
# 工具函数
# ──────────────────────────────────────────────────────────────────────────────

def _load_config() -> dict:
    if ALERT_CONFIG.exists():
        try:
            user = json.loads(ALERT_CONFIG.read_text(encoding="utf-8"))
            return {**DEFAULT_CONFIG, **user}
        except Exception:
            pass
    return DEFAULT_CONFIG.copy()


def _load_portfolio() -> list[dict]:
    if not PORTFOLIO_FILE.exists():
        return []
    data = json.loads(PORTFOLIO_FILE.read_text(encoding="utf-8"))
    return data.get("holdings", [])


def _run_mx(query: str) -> str:
    """调用 MX_FinData，返回 Excel 内容文本；失败返回错误描述。"""
    try:
        result = subprocess.run(
            [sys.executable, str(MX_SCRIPT), "--query", query],
            capture_output=True, text=True, encoding="utf-8", timeout=60
        )
        if result.returncode != 0:
            return f"[ERROR] {result.stderr.strip()[:200]}"
        # 找到 Excel 路径
        for line in result.stdout.splitlines():
            if "文件:" in line or "文件：" in line:
                path = line.split(":", 1)[-1].strip().strip("：")
                return _read_excel(path)
        return result.stdout.strip()[:2000]
    except subprocess.TimeoutExpired:
        return "[ERROR] 查询超时"
    except Exception as e:
        return f"[ERROR] {e}"


def _read_excel(path: str) -> str:
    try:
        import pandas as pd
        xl = pd.ExcelFile(path)
        parts = []
        for sheet in xl.sheet_names:
            df = pd.read_excel(xl, sheet_name=sheet)
            parts.append(f"[{sheet}]\n{df.to_string(index=False)}")
        return "\n\n".join(parts)
    except Exception as e:
        return f"[读取失败: {e}]"


def _is_trading_hours() -> bool:
    """判断当前是否在交易时段。"""
    now = datetime.now().time()
    morning = dtime(9, 25) <= now <= dtime(11, 30)
    afternoon = dtime(13, 0) <= now <= dtime(15, 0)
    return morning or afternoon


def _parse_float(text: str, keyword: str) -> float | None:
    """从文本中提取关键字附近的数字。"""
    import re
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if keyword in line:
            # 在当前行和下一行找数字
            context = line + (" " + lines[i+1] if i+1 < len(lines) else "")
            nums = re.findall(r"-?\d+\.?\d*", context)
            if nums:
                try:
                    return float(nums[0])
                except ValueError:
                    pass
    return None


# ──────────────────────────────────────────────────────────────────────────────
# 告警检测函数
# ──────────────────────────────────────────────────────────────────────────────

def check_market(data: str, cfg: dict) -> list[Alert]:
    """检测大盘风险。"""
    alerts = []
    drop = _parse_float(data, "涨跌幅")
    if drop is not None:
        if drop <= cfg["market_drop_critical"]:
            alerts.append(Alert(
                "CRITICAL", "000001", "大盘",
                trigger=f"沪指跌幅 {drop:.1f}%",
                message="系统性下跌风险，个股可能连带下跌。",
                action="暂停所有加仓操作，止损单提前挂单，等待企稳信号。"
            ))
        elif drop <= cfg["market_drop_warn"]:
            alerts.append(Alert(
                "WARNING", "000001", "大盘",
                trigger=f"沪指跌幅 {drop:.1f}%",
                message="大盘走弱，个股加仓建议暂缓，做T适宜度降一档。",
                action="收缩操作，持仓观望，做T只做轻仓。"
            ))
        elif drop >= cfg["market_rise_info"]:
            alerts.append(Alert(
                "INFO", "000001", "大盘",
                trigger=f"沪指涨幅 {drop:.1f}%",
                message="强势市场，追高风险提升，高位个股注意止盈。",
                action="注意设置移动止盈，不要在高位追入。"
            ))
    return alerts


def check_capital_flow(code: str, name: str, data: str, cfg: dict) -> list[Alert]:
    """检测资金流向异动。"""
    alerts = []
    # 超大单净流入（万元）
    super_large = _parse_float(data, "超大单净流入")
    main_flow   = _parse_float(data, "主力净流入")

    if super_large is not None:
        if super_large <= cfg["capital_outflow_warn"]:
            alerts.append(Alert(
                "WARNING", code, name,
                trigger=f"超大单净流出 {abs(super_large):.0f}万",
                message=f"机构/大资金持续出逃，主力净流入：{main_flow:.0f}万 元。"
                        f"若连续出现，主力离场信号增强。",
                action="不加仓，关注是否连续3日净流出，若是则考虑减仓。"
            ))
        elif super_large >= cfg["capital_inflow_info"]:
            alerts.append(Alert(
                "INFO", code, name,
                trigger=f"超大单净流入 {super_large:.0f}万",
                message=f"大资金持续买入，主力净流入：{main_flow:.0f}万元，机构建仓信号。",
                action="关注技术面确认，量比 > 1.0 时可考虑跟进。"
            ))

    # 超大单 vs 主力冲突
    if super_large is not None and main_flow is not None:
        if (super_large > 0 and main_flow < 0) or (super_large < 0 and main_flow > 0):
            alerts.append(Alert(
                "INFO", code, name,
                trigger="超大单 vs 主力信号冲突",
                message=f"超大单净流入 {super_large:.0f}万，主力净流入 {main_flow:.0f}万，方向相反。"
                        "主力数据含做市商，以超大单为准。",
                action="以超大单方向判断，主力数据仅参考。"
            ))
    return alerts


def check_price_stoploss(code: str, name: str, cost: float, data: str, cfg: dict) -> list[Alert]:
    """检测价格是否接近或触及止损位。"""
    alerts = []
    current_price = _parse_float(data, "最新价")
    ma20          = _parse_float(data, "20日均线")

    if current_price is None:
        return alerts

    # 止损位计算
    stop_by_cost = cost * cfg["stop_loss_pct"]
    stop_loss    = max(stop_by_cost, ma20) if ma20 else stop_by_cost
    warn_line    = cost * cfg["stop_loss_warn_pct"]

    pct_vs_cost  = (current_price - cost) / cost * 100

    if current_price <= stop_loss:
        alerts.append(Alert(
            "CRITICAL", code, name,
            trigger=f"当前价 {current_price:.2f} ≤ 止损位 {stop_loss:.2f}",
            message=f"成本 {cost:.2f}，已亏损 {abs(pct_vs_cost):.1f}%，触及止损线。",
            action=f"执行止损：python3 scripts/portfolio.py sell {code} [股数] {current_price:.2f}"
        ))
    elif current_price <= warn_line:
        gap_pct = (current_price - stop_loss) / stop_loss * 100
        alerts.append(Alert(
            "WARNING", code, name,
            trigger=f"当前价 {current_price:.2f} 距止损位 {stop_loss:.2f} 仅 {gap_pct:.1f}%",
            message=f"成本 {cost:.2f}，浮亏 {abs(pct_vs_cost):.1f}%，止损位压力增大。",
            action="提前挂单或设置心理止损线，准备应对进一步下跌。"
        ))
    return alerts


def check_volume(code: str, name: str, data: str, cfg: dict) -> list[Alert]:
    """检测量比异动。"""
    alerts = []
    vol_ratio = _parse_float(data, "量比")
    if vol_ratio is None:
        return alerts

    if vol_ratio < cfg["volume_ratio_low"]:
        alerts.append(Alert(
            "WARNING", code, name,
            trigger=f"量比 {vol_ratio:.2f}（地量）",
            message="缩量至极端低位，方向未明，技术信号降级。",
            action="今日不操作，等放量确认方向后再参与。"
        ))
    elif vol_ratio > cfg["volume_ratio_spike"]:
        alerts.append(Alert(
            "INFO", code, name,
            trigger=f"量比 {vol_ratio:.2f}（异动）",
            message="成交量急剧放大，量化系统可能介入，注意方向确认。",
            action="量价配合方向：放量上涨 → 可参与；放量下跌 → 警惕出逃。"
        ))
    return alerts


def check_announcement(code: str, name: str, data: str) -> list[Alert]:
    """检测重大公告关键词。"""
    alerts = []
    # 利空关键词
    bearish_kw = ["处罚", "立案", "亏损", "业绩下修", "停产", "解除合同", "诉讼"]
    # 利好关键词
    bullish_kw = ["中标", "合同", "回购", "增持", "业绩超预期", "分红", "新品"]

    for kw in bearish_kw:
        if kw in data:
            alerts.append(Alert(
                "WARNING", code, name,
                trigger=f"公告含关键词：{kw}",
                message=f"检测到可能利空公告，请人工确认公告内容。",
                action="等公告消化后再操作，当日不进行加仓/做T。"
            ))
            break  # 只报一次

    for kw in bullish_kw:
        if kw in data:
            alerts.append(Alert(
                "INFO", code, name,
                trigger=f"公告含关键词：{kw}",
                message=f"检测到可能利好公告，请人工确认公告内容。",
                action="结合技术面判断，量比>1.0时可考虑参与。"
            ))
            break

    return alerts


# ──────────────────────────────────────────────────────────────────────────────
# 主流程
# ──────────────────────────────────────────────────────────────────────────────

def run_monitor(holdings: list[dict], market_only: bool, filter_code: str, cfg: dict) -> list[Alert]:
    all_alerts: list[Alert] = []
    codes_str = " ".join(f"{h['name']}{h['code']}" for h in holdings[:5])

    target = holdings
    if filter_code:
        target = [h for h in holdings if h["code"] == filter_code]

    # ── 并行查询 ──────────────────────────────────────────────────────────────
    queries: dict[str, str] = {
        "market": "上证指数 深证成指 最新点位 涨跌幅 成交量",
    }
    if not market_only and target:
        queries.update({
            "price":    f"{codes_str} 最新价 量比 涨跌幅 换手率",
            "capital":  f"{codes_str} 超大单净流入 主力净流入 大单净流入 小单净流出",
            "announce": f"{codes_str} 最新公告 重大事项",
        })

    print(f"🔍 执行 {len(queries)} 个监控查询...", flush=True)
    results: dict[str, str] = {}

    with ThreadPoolExecutor(max_workers=4) as pool:
        future_map = {pool.submit(_run_mx, q): k for k, q in queries.items()}
        for future in as_completed(future_map):
            key = future_map[future]
            try:
                results[key] = future.result()
                print(f"  ✅ {key}", flush=True)
            except Exception as e:
                results[key] = f"[ERROR] {e}"
                print(f"  ❌ {key}: {e}", flush=True)

    # ── 大盘检测 ──────────────────────────────────────────────────────────────
    if "market" in results:
        all_alerts += check_market(results["market"], cfg)

    # ── 个股检测 ──────────────────────────────────────────────────────────────
    if not market_only:
        for holding in target:
            code = holding["code"]
            name = holding["name"]
            cost = holding["cost"]
            price_data   = results.get("price", "")
            capital_data = results.get("capital", "")
            ann_data     = results.get("announce", "")

            all_alerts += check_price_stoploss(code, name, cost, price_data, cfg)
            all_alerts += check_volume(code, name, price_data, cfg)
            all_alerts += check_capital_flow(code, name, capital_data, cfg)
            all_alerts += check_announcement(code, name, ann_data)

    return all_alerts


def print_report(alerts: list[Alert]) -> None:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n{'='*62}")
    print(f"  📊 A股主动预警报告 — {now}")
    print(f"{'='*62}\n")

    if not alerts:
        print("✅ 无异常告警，持仓状态正常。")
        return

    # 按级别分组
    for level in ["CRITICAL", "WARNING", "INFO"]:
        group = [a for a in alerts if a.level == level]
        if not group:
            continue
        icon = ALERT_LEVELS[level]
        print(f"\n{icon} {level} ({len(group)} 条)\n" + "─" * 50)
        for alert in group:
            print(str(alert))
            print()

    # 统计
    critical_n = sum(1 for a in alerts if a.level == "CRITICAL")
    warning_n  = sum(1 for a in alerts if a.level == "WARNING")
    info_n     = sum(1 for a in alerts if a.level == "INFO")

    print("─" * 62)
    print(f"汇总：🔴 CRITICAL×{critical_n}  🟡 WARNING×{warning_n}  🔵 INFO×{info_n}")

    if critical_n > 0:
        print("\n⚠️  存在 CRITICAL 告警，请立即处理后再继续其他操作。")

    # 生成给 Claude 的分析 prompt
    print("\n" + "─" * 62)
    print("【Claude 分析指令】以下内容请 Claude 据此给出下一步操作建议：\n")
    print(f"当前时间：{now}")
    print("预警汇总：")
    for a in alerts:
        icon = ALERT_LEVELS[a.level]
        print(f"  {icon} {a.name}({a.code})：{a.trigger} — {a.message}")
    print("\n请根据以上预警，结合实盘铁律，给出每只股票的具体操作建议（含执行命令）。")


def show_config(cfg: dict) -> None:
    print("\n当前告警阈值配置：")
    for k, v in cfg.items():
        print(f"  {k}: {v}")
    print(f"\n修改方式：编辑 {ALERT_CONFIG}")
    print("示例：")
    print('  {"stop_loss_pct": 0.95, "capital_outflow_warn": -5000}')


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    args = sys.argv[1:]

    if "--config" in args:
        show_config(_load_config())
        return

    market_only = "--market" in args
    filter_code = next((a for a in args if a.isdigit() and len(a) >= 6), "")

    cfg      = _load_config()
    holdings = _load_portfolio()

    if not holdings and not market_only:
        print("【提示】持仓为空，仅检测大盘风险。")
        market_only = True

    if not _is_trading_hours():
        now_str = datetime.now().strftime("%H:%M")
        print(f"⚠️  当前时间 {now_str} 非交易时段，部分实时数据可能不准确，仅供参考。")

    alerts = run_monitor(holdings, market_only, filter_code, cfg)
    print_report(alerts)


if __name__ == "__main__":
    main()
