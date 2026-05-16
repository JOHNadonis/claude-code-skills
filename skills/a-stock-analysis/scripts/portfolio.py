#!/usr/bin/env python3
"""
持仓管理脚本：增删改查 A 股持仓记录，支持做T成本自动计算和交易历史。

用法：
  python3 portfolio.py show                             # 查看所有持仓
  python3 portfolio.py add 002463 沪电股份 1000 85.50   # 买入（已持仓则加权平均）
  python3 portfolio.py sell 002463 500 90.00            # 卖出（自动记录盈亏）
  python3 portfolio.py t0 002463 500 90.00 87.00        # 做T（卖出+回补，自动降成本）
  python3 portfolio.py update 002463 1200 84.00         # 手动修正：代码 新股数 新成本
  python3 portfolio.py remove 002463                    # 清仓
  python3 portfolio.py note 002463 "关注BOLL上轨压力"   # 添加备注
  python3 portfolio.py history                          # 查看交易记录
  python3 portfolio.py history 002463                   # 查看某只股票的交易记录
"""

import json
import sys
from datetime import datetime
from pathlib import Path

PORTFOLIO_FILE = Path(__file__).parent.parent / "data" / "portfolio.json"
TRADES_FILE = Path(__file__).parent.parent / "data" / "trades.json"


# ──────────────────────────────────────────────────────────────────────────────
# I/O helpers
# ──────────────────────────────────────────────────────────────────────────────

def _load() -> dict:
    PORTFOLIO_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not PORTFOLIO_FILE.exists():
        return {"holdings": [], "updated_at": ""}
    return json.loads(PORTFOLIO_FILE.read_text(encoding="utf-8"))


def _save(data: dict) -> None:
    data["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    PORTFOLIO_FILE.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def _load_trades() -> list[dict]:
    if not TRADES_FILE.exists():
        return []
    return json.loads(TRADES_FILE.read_text(encoding="utf-8"))


def _append_trade(record: dict) -> None:
    """追加一条交易记录到 trades.json。"""
    trades = _load_trades()
    record["time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    trades.append(record)
    TRADES_FILE.write_text(
        json.dumps(trades, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def _find(data: dict, code: str) -> int:
    for i, h in enumerate(data["holdings"]):
        if h["code"] == code.strip():
            return i
    return -1


# ──────────────────────────────────────────────────────────────────────────────
# Commands
# ──────────────────────────────────────────────────────────────────────────────

def cmd_show(data: dict) -> None:
    holdings = data.get("holdings", [])
    if not holdings:
        print("【持仓为空】使用 `add` 命令添加持仓。")
        return
    print(f"{'代码':<8} {'名称':<10} {'股数':>8} {'成本(元)':>10} {'买入日期':<12} {'备注'}")
    print("-" * 72)
    for h in holdings:
        print(
            f"{h['code']:<8} {h['name']:<10} {h['shares']:>8} "
            f"{h['cost']:>10.2f} {h.get('buy_date', ''):<12} {h.get('note', '')}"
        )
    print(f"\n共 {len(holdings)} 只持仓 | 更新于 {data.get('updated_at', '')}")


def cmd_add(data: dict, code: str, name: str, shares: int, cost: float) -> None:
    """买入：已持仓则加权平均计算新成本。"""
    idx = _find(data, code)
    if idx >= 0:
        old_shares = data["holdings"][idx]["shares"]
        old_cost = data["holdings"][idx]["cost"]
        total_shares = old_shares + shares
        new_cost = round((old_shares * old_cost + shares * cost) / total_shares, 4)
        data["holdings"][idx]["shares"] = total_shares
        data["holdings"][idx]["cost"] = new_cost
        _save(data)
        print(f"✅ 加仓：{name}({code})  +{shares}股 @ {cost:.2f}元")
        print(f"   新均价：{new_cost:.2f} 元（原 {old_cost:.2f}，共 {total_shares} 股）")
        _append_trade({"type": "buy", "code": code, "name": name,
                       "shares": shares, "price": cost, "note": "加仓"})
    else:
        entry = {
            "code": code.strip(),
            "name": name.strip(),
            "shares": shares,
            "cost": cost,
            "buy_date": datetime.now().strftime("%Y-%m-%d"),
            "note": "",
        }
        data["holdings"].append(entry)
        _save(data)
        print(f"✅ 新建持仓：{name}({code})  {shares}股 @ {cost:.2f}元")
        _append_trade({"type": "buy", "code": code, "name": name,
                       "shares": shares, "price": cost, "note": "新建"})


def cmd_sell(data: dict, code: str, shares: int, price: float) -> None:
    """卖出（含部分清仓），自动计算盈亏并记录。"""
    idx = _find(data, code)
    if idx < 0:
        print(f"❌ 未找到持仓：{code}")
        sys.exit(1)
    h = data["holdings"][idx]
    if shares > h["shares"]:
        print(f"❌ 卖出数量 {shares} 超过持仓 {h['shares']} 股")
        sys.exit(1)

    pnl = round((price - h["cost"]) * shares, 2)
    pnl_pct = round((price / h["cost"] - 1) * 100, 2)

    if shares == h["shares"]:
        data["holdings"].pop(idx)
        print(f"✅ 全部清仓：{h['name']}({code})  {shares}股 @ {price:.2f}元")
    else:
        data["holdings"][idx]["shares"] -= shares
        print(f"✅ 部分卖出：{h['name']}({code})  -{shares}股 @ {price:.2f}元")
        print(f"   剩余：{data['holdings'][idx]['shares']} 股 @ 成本 {h['cost']:.2f} 元")

    sign = "+" if pnl >= 0 else ""
    print(f"   本次盈亏：{sign}{pnl:.2f} 元（{sign}{pnl_pct:.2f}%）")
    _save(data)
    _append_trade({"type": "sell", "code": code, "name": h["name"],
                   "shares": shares, "price": price, "pnl": pnl})


def cmd_t0(data: dict, code: str, sell_shares: int, sell_price: float, rebuy_price: float) -> None:
    """
    做T：同日卖出 + 回补，自动计算新成本。
    前提：持仓 ≥ sell_shares × 2（卖出后有底仓，回补后恢复原股数）
    """
    idx = _find(data, code)
    if idx < 0:
        print(f"❌ 未找到持仓：{code}")
        sys.exit(1)

    # 先保存原始值，再修改（避免字典引用导致打印错误）
    name = data["holdings"][idx]["name"]
    old_cost = data["holdings"][idx]["cost"]
    total_shares = data["holdings"][idx]["shares"]

    # 卖出收入 - 回补花费 = 做T收益
    profit = round((sell_price - rebuy_price) * sell_shares, 2)
    # 新成本 = 原总持仓成本 - 做T收益，分摊到原始股数
    new_cost = round((old_cost * total_shares - profit) / total_shares, 4)

    data["holdings"][idx]["cost"] = new_cost
    _save(data)

    print(f"✅ 做T完成：{name}({code})")
    print(f"   卖出：{sell_shares}股 @ {sell_price:.2f}元")
    print(f"   回补：{sell_shares}股 @ {rebuy_price:.2f}元")
    print(f"   做T收益：+{profit:.2f} 元")
    print(f"   成本从 {old_cost:.2f} → {new_cost:.2f} 元（降低 {old_cost - new_cost:.4f} 元）")
    _append_trade({"type": "t0", "code": code, "name": h["name"],
                   "sell_shares": sell_shares, "sell_price": sell_price,
                   "rebuy_price": rebuy_price, "profit": profit,
                   "cost_before": h["cost"], "cost_after": new_cost})


def cmd_update(data: dict, code: str, shares: int, cost: float) -> None:
    """手动修正持仓数量和成本（用于账户对账或特殊操作后）。"""
    idx = _find(data, code)
    if idx < 0:
        print(f"❌ 未找到持仓：{code}")
        sys.exit(1)
    old_shares = data["holdings"][idx]["shares"]
    old_cost = data["holdings"][idx]["cost"]
    data["holdings"][idx]["shares"] = shares
    data["holdings"][idx]["cost"] = cost
    _save(data)
    name = data["holdings"][idx]["name"]
    print(f"✅ 已手动修正：{name}({code})")
    print(f"   股数：{old_shares} → {shares}  成本：{old_cost:.2f} → {cost:.2f}")


def cmd_remove(data: dict, code: str) -> None:
    idx = _find(data, code)
    if idx < 0:
        print(f"❌ 未找到持仓：{code}")
        sys.exit(1)
    name = data["holdings"][idx]["name"]
    data["holdings"].pop(idx)
    _save(data)
    print(f"✅ 已清仓：{name}({code})")
    _append_trade({"type": "remove", "code": code, "name": name, "note": "手动清仓"})


def cmd_note(data: dict, code: str, note: str) -> None:
    idx = _find(data, code)
    if idx < 0:
        print(f"❌ 未找到持仓：{code}")
        sys.exit(1)
    data["holdings"][idx]["note"] = note
    _save(data)
    print(f"✅ 已备注：{code} → {note}")


def cmd_history(filter_code: str = "") -> None:
    """显示交易历史，可按股票代码过滤。"""
    trades = _load_trades()
    if filter_code:
        trades = [t for t in trades if t.get("code") == filter_code]
    if not trades:
        print("【无交易记录】" + (f" 代码：{filter_code}" if filter_code else ""))
        return

    print(f"{'时间':<20} {'类型':<6} {'代码':<8} {'名称':<10} {'股数':>8} {'价格':>8} {'盈亏':>10}")
    print("-" * 78)
    total_pnl = 0.0
    for t in trades:
        pnl = t.get("pnl") or t.get("profit") or 0
        total_pnl += pnl
        price = t.get("price") or t.get("sell_price") or 0
        shares = t.get("shares") or t.get("sell_shares") or 0
        pnl_str = f"+{pnl:.2f}" if pnl > 0 else (f"{pnl:.2f}" if pnl < 0 else "—")
        print(
            f"{t.get('time', ''):<20} {t.get('type', ''):<6} "
            f"{t.get('code', ''):<8} {t.get('name', ''):<10} "
            f"{shares:>8} {price:>8.2f} {pnl_str:>10}"
        )
    sign = "+" if total_pnl >= 0 else ""
    print(f"\n共 {len(trades)} 条记录 | 累计已实现盈亏：{sign}{total_pnl:.2f} 元")


# ──────────────────────────────────────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────────────────────────────────────

def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    args = sys.argv[1:]
    data = _load()

    if not args or args[0] == "show":
        cmd_show(data)
    elif args[0] == "add" and len(args) >= 5:
        cmd_add(data, args[1], args[2], int(args[3]), float(args[4]))
    elif args[0] == "sell" and len(args) >= 4:
        cmd_sell(data, args[1], int(args[2]), float(args[3]))
    elif args[0] == "t0" and len(args) >= 5:
        cmd_t0(data, args[1], int(args[2]), float(args[3]), float(args[4]))
    elif args[0] == "update" and len(args) >= 4:
        cmd_update(data, args[1], int(args[2]), float(args[3]))
    elif args[0] == "remove" and len(args) >= 2:
        cmd_remove(data, args[1])
    elif args[0] == "note" and len(args) >= 3:
        cmd_note(data, args[1], " ".join(args[2:]))
    elif args[0] == "history":
        cmd_history(args[1] if len(args) >= 2 else "")
    else:
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
