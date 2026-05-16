---
name: research-dbs
description: dontbesilent 商业诊断工具箱。用于商业模式诊断、对标分析、内容创作诊断、短视频开头优化、小红书标题、AI 写作检测、慢就是快、执行力诊断、概念拆解、聊天室式多视角分析，以及 Agent 工作台迁移。
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [business, diagnosis, content, strategy, thinking-tools, chinese]
---

# dontbesilent 商业诊断工具箱

这是一个面向“问题消解 / 诊断 / 路由”的 skill。优先把用户问题归类，再调用最合适的分析框架。

## 触发场景

当用户提到以下任一类问题时，优先加载本 skill：

- 商业模式、产品定位、项目可做性、问题消解
- 对标、竞品、平台运营、增长路径
- 内容创作、文案、短视频开头、标题优化、小红书标题
- AI 味检测、改写前的诊断
- 执行力卡住、知道该做什么但做不动
- 概念模糊，需要拆解定义
- 想听多个角色视角、做聊天室式讨论
- Claude Code / Codex / AGENTS.md / CLAUDE.md / Agent 工作台迁移

## 工作原则

1. **先诊断，再回答**：不要直接跳到解决方案
2. **先消解歧义**：概念不清时先拆定义
3. **先找对标，再做内容**：路径不清时先 benchmark
4. **先验证，再扩展**：避免过度设计和无关改动

## 核心子工具映射

- `/dbs`：主入口，自动路由
- `/dbs-diagnosis`：商业模式诊断
- `/dbs-benchmark`：对标分析
- `/dbs-content`：内容创作诊断
- `/dbs-hook`：短视频开头优化
- `/dbs-xhs-title`：小红书标题公式
- `/dbs-ai-check`：AI 写作特征识别
- `/dbs-slowisfast`：慢就是快
- `/dbs-action`：执行力诊断
- `/dbs-deconstruct`：概念拆解
- `/dbs-chatroom`：定向聊天室
- `/dbs-chatroom-austrian`：奥派聊天室
- `/dbs-agent-migration`：Agent 工作台迁移

## 使用方式

当用户的问题更适合先诊断时，优先输出：

- 问题归类
- 关键歧义
- 可能的下一步
- 需要的最小额外信息

如果用户已经给了足够材料，就直接进入对应框架，不要多绕。
