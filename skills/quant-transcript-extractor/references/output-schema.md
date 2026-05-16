# Output Schema

Use this schema after preprocessing transcript text.

## 1) Structured Rules

Each rule card should follow:

```json
{
  "rule_id": "QTR-001",
  "source_ids": ["R0003", "R0012"],
  "market": "A-share",
  "timeframe": "daily",
  "universe": "CSI300 components",
  "entry_if": "IF close breaks 20-day high and turnover > 1.5x median THEN open long next bar",
  "exit_if": "IF close falls below 10-day low OR stoploss hit THEN exit",
  "position_sizing": "risk parity with max single-position 10%",
  "risk_controls": [
    "portfolio max drawdown stop at 12%",
    "single trade stoploss 2%"
  ],
  "transaction_cost": "0.08% round-trip + slippage 5 bps",
  "invalidation": "disable when 20-day realized volatility > 2x rolling 1y median",
  "confidence": "medium",
  "missing_fields": []
}
```

## 2) Conflicts and Gaps

Represent conflicts explicitly:

```json
{
  "conflict_id": "C-01",
  "topic": "stop-loss threshold",
  "statements": [
    {"source_id": "R0044", "claim": "1.5% stoploss"},
    {"source_id": "R0079", "claim": "3% stoploss"}
  ],
  "resolution_status": "unresolved",
  "needed_test": "parameter sweep 1% to 4%, step 0.5%"
}
```

## 3) Backtest Experiment Queue

Create experiments with strict pass criteria:

```json
{
  "exp_id": "E-01",
  "rule_id": "QTR-001",
  "priority": 1,
  "dataset_range": "2018-01-01..2025-12-31",
  "split": "walk-forward",
  "metrics": ["CAGR", "MaxDD", "Sharpe", "Calmar", "Turnover"],
  "pass_gate": {
    "maxdd_lte": 0.18,
    "sharpe_gte": 1.0,
    "oos_cagr_gte": 0.10
  }
}
```

## 4) Review Checklist

- Ensure every rule has explicit `entry_if` and `exit_if`.
- Reject claims without measurable thresholds.
- Ensure cost/slippage assumptions are present.
- Mark `TBD` for missing parameters instead of guessing.
- Keep source traceability via `source_ids`.
