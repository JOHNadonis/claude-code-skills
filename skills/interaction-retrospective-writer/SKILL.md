---
name: interaction-retrospective-writer
description: Summarize a recent collaboration/interaction with Claude Code or other coding agents into reusable lessons and a publishable WeChat article draft. Use when the user asks to "总结交流过程", "沉淀经验", "复盘", "写一篇分享", or wants project/task conversation converted into methodology + content output.
---

# Interaction Retrospective Writer

## Overview
Turn raw interaction logs (task chats, project collaboration, troubleshooting dialogue) into two outputs:
1) a reusable experience summary card, and 2) a WeChat article draft for external sharing.

## Workflow
1. Confirm source scope: what interaction window to summarize (single task / one day / full project phase).
2. Extract facts only: goals, actions, decisions, errors, fixes, outcomes.
3. Build a reusable method layer: patterns, anti-patterns, checklists, prompts.
4. Generate two outputs in order:
   - `经验沉淀卡` (internal use)
   - `公众号文章草稿` (external sharing)
5. Add a short “可复用模板” section so the user can repeat the process quickly.

## Output 1: 经验沉淀卡
Use this fixed structure:
- 背景与目标（1-2句）
- 关键动作（按时间顺序 3-8 条）
- 关键决策与原因（2-5 条）
- 踩坑与修正（至少 2 条）
- 可复用方法（SOP / 检查清单 / 提示词）
- 下一步建议（1-3 条）

## Output 2: 公众号文章草稿
Use this structure:
- 标题（给 3 个备选）
- 开头钩子（痛点/反直觉结论）
- 背景：为什么做这件事
- 过程：怎么做（保留关键细节）
- 踩坑：错在哪里、怎么改
- 方法论：可复制的框架
- 结果与收益：具体变化
- 结尾：给读者一个立刻可执行动作

## Quality Rules
- Never fabricate facts not present in the interaction source.
- When data is uncertain, mark it as `待确认`.
- Keep operational details concrete; avoid empty motivational text.
- Prefer concise, direct Chinese with clear sections.
- For sharing draft, hide sensitive details by default (tokens, secrets, private identifiers).

## Reference
- For ready-to-use templates and quick fill-in format, read `references/templates.md`.
