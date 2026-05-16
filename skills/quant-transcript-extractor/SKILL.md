---
name: quant-transcript-extractor
description: Extract actionable quant knowledge from raw Chinese/English transcripts (course verbatim text, forum discussions, recordings converted to text) and convert it into backtest-ready rules, risk controls, and hypothesis cards. Use when the user provides long unstructured text and asks to extract useful content for AI quant, strategy research, or trading system design; triggers include "逐字稿", "课程文稿", "论坛内容", "提取规则", "量化知识提炼", "extract rules from transcript".
---

# Quant Transcript Extractor

## Overview

Turn noisy transcript text into structured quant artifacts:
- Rule candidates (`entry`, `exit`, `risk`, `position`, `invalidation`)
- Backtest hypotheses with measurable fields
- Conflict list and uncertainty flags

Use deterministic preprocessing first, then do semantic extraction.

## Workflow

1. Normalize transcript text with `scripts/extract_quant_knowhow.py`.
2. Build an evidence table from extracted sentences.
3. Convert evidence into backtest-ready rule cards.
4. Flag conflicts and unknown parameters before coding any strategy.

## Step 1: Preprocess and Bootstrap Extraction

Run:

```bash
python3 scripts/extract_quant_knowhow.py \
  --input /path/to/transcript.txt \
  --output /path/to/extract.json
```

The script:
- removes common transcript noise (timestamps, filler words, speaker marks)
- splits long text into sentences
- tags sentence categories via quant-specific keyword heuristics
- extracts simple numeric parameters (percent, basis points, lookback days, multipliers)
- emits draft rule candidates with confidence labels

## Step 2: Build Evidence Table

For each candidate in `extract.json`, produce:
- `claim`: what the speaker recommends
- `evidence_text`: original sentence
- `category`: one of `entry/exit/risk/position/filter/invalidation/regime/cost/execution/metric`
- `params`: parsed numbers and units
- `confidence`: `high/medium/low` from script + context check

Reject vague statements that cannot be tested.

## Step 3: Convert to Backtest Rule Cards

Use the JSON schema in `references/output-schema.md`.

Each rule card must include:
- market and timeframe
- instrument universe
- entry condition in strict IF-THEN form
- exit condition
- risk controls (max loss, sizing, cooldown, forbidden conditions)
- invalidation criteria (when the rule should stop trading)

If a required field is missing, set it to `TBD` and append a clarification question.

## Step 4: Quality Gate Before Implementation

Before writing strategy code, check:
- no look-ahead wording ("next day known in advance")
- no ambiguous action verbs ("consider buying" without threshold)
- transaction-cost assumptions are explicit
- at least one failure mode is listed

If the gate fails, return a gap report instead of a fake-complete strategy.

## Output Contract

Return these sections in order:
1. `Structured Rules`
2. `Conflicts and Gaps`
3. `Backtest Experiment Queue` (priority ordered)
4. `Questions for User` (only unresolved blockers)
