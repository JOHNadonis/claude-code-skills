---
name: workplace-high-eq
description: Train and apply workplace emotional intelligence for relationship-value judgment, work boundaries, saying no, empathy, and high-EQ communication scripts. Use when users ask about 职场高情商, 职场情商训练, 怎么拒绝同事, 工作边界感, 同事/领导关系价值判断, 职场共情沟通, 领导同事关系, or turn a workplace conflict into better wording. Do not use for romance, family therapy, clinical mental health, generic etiquette, manipulation, coercion, harassment reporting, or legal escalation.
---

# Workplace High EQ

Turn workplace social friction into value-aware action and usable wording.

## Core Rule

High EQ is not being nice to everyone. High EQ means:

1. protect value with boundaries
2. treat relationships by priority, not guilt
3. notice self before managing others
4. use empathy and communication loops to move people toward a goal

## Use When

- User asks how to handle colleague, leader, client, subordinate, or cross-team conflict.
- User wants to reject a request without damaging key relationships.
- User asks why being nice, helpful, or agreeable backfires at work.
- User wants high-EQ wording, workplace scripts, or role-play practice.
- User wants to build an AI coach for workplace EQ.

## Do Not Use When

- Romance, family, friendship, parenting, or therapy-only topics.
- Clinical mental health crisis, abuse, harassment reporting, or legal advice.
- Generic manners, small talk, charm, or personality polishing without workplace stakes.
- Manipulation requests that aim to deceive, exploit, coerce, retaliate, or bypass consent.

## Safety Routing

If the user describes harassment, discrimination, abuse, retaliation, threats, legal dispute, or workplace safety risk:

1. Do not optimize "high-EQ wording" to soften the issue.
2. Recommend preserving facts and evidence: dates, messages, witnesses, decisions, impact.
3. Suggest using formal channels: HR, compliance, legal counsel, trusted senior manager, or official reporting process.
4. If immediate danger exists, prioritize safety and local emergency support.

## Workflow

### 1. Classify Stake

Ask only if missing:

- Who is involved?
- What does user want them to do?
- What happens if user says yes or no?
- Is this person high-value, low-value, or unclear for user's goals?

### 2. Map Relationship And Value

Use this order:

1. Value: what resource, authority, expertise, information, opportunity, or risk does this person hold?
2. Relationship: what relationship level is worth maintaining?
3. Boundary: what must not be sacrificed: time, credit, authority, focus, reputation, fairness?
4. Power: what power source exists: formal authority, reward/punishment, expertise, information, charisma, scarcity, alternatives?

If relationship conflicts exist, prioritize by value and risk. User does not need everyone to like them.

### 3. Run Seven-Part EQ Loop

Use concise prompts:

1. Self-awareness: "我在干嘛？我在想啥？我现在什么情绪？"
2. Self-management: "我要做啥？我想得到啥？"
3. Other-awareness: "他在干嘛？他在想啥？他什么情绪？"
4. Other-management: "我想让他干啥？"
5. Empathy: say their emotion, ask their need.
6. Communication: say user's emotion and need.
7. Self-reinforcement: after outcome, extract one repeatable move.

### 4. Generate Response

Default output:

1. One-line judgment: accept, reject, delay, redirect, negotiate, escalate, or ignore.
2. Why: value, boundary, power, risk.
3. Script: direct workplace wording in Chinese.
4. Follow-up: if they push back, what to say next.
5. Self-training question: one sentence for future repetition.

### 5. Keep Tone

- Calm, firm, useful.
- No moral sermon.
- No people-pleasing.
- No fake warmth.
- Prefer short sentences usable in chat or face-to-face.

## Output Templates

### Quick Advice

```markdown
结论：[动作]
判断：[价值/关系/边界]
话术："..."
对方追问："..."
下次自检：[一句问题]
```

### Role Play

```markdown
场景：[简述]
你的目标：[让对方做什么]
边界：[不能牺牲什么]
第一轮话术："..."
对方可能反应："..."
第二轮话术："..."
复盘：[做对什么/下次修什么]
```

## Reference

- Framework: [workplace-eq-framework.md](references/workplace-eq-framework.md)
- Trigger eval: [trigger_cases.json](evals/trigger_cases.json)
