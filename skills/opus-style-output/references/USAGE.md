# Opus-Style Output 使用教程

## 这个 skill 是什么

`opus-style-output` 是一个给 Codex / GPT 模型使用的全局输出风格 skill。它会让模型回答更像 Claude Opus：结构清楚、重点明确、语气自然、总结好读，并在合适的时候使用表格和 emoji。

## 适合解决什么问题

| 使用前常见问题 | 使用后效果 |
|---|---|
| 最终总结像开发日志 | 输出变成用户能看懂的交付总结 |
| 回答又长又散 | 先给结论，再分点说明 |
| 比较方案不直观 | 自动倾向使用 markdown 表格 |
| 前端文案像技术说明 | 改成面向用户的产品短语 |
| 总结缺少层次 | 使用 `✅ / 📁 / 🧪 / ⚠️ / 💡` 等清晰分区 |

## 安装方式

把下面目录放到 Codex skills 目录中：

```bash
~/.codex/skills/opus-style-output/
```

核心文件：

```bash
~/.codex/skills/opus-style-output/SKILL.md
~/.codex/skills/opus-style-output/agents/openai.yaml
```

## 全局触发方式

在 `SKILL.md` 的 `description` 中写明：

```text
Always use this skill globally for Codex responses unless the user explicitly requests a different style.
```

这样 Codex 在大多数回答、总结、计划、评审、前端文案任务里都会倾向自动使用这个 skill。

如果想手动强制使用，可以在 prompt 里写：

```text
使用 $opus-style-output 总结这次改动
```

## 使用前后对比

### 使用前

```text
Modified src/components/Header.tsx and updated the CTA logic. Also changed the empty state copy and adjusted validation messages. Tests were not run.
```

### 使用后

```text
✅ 已完成
- 优化首页按钮文案，让用户更容易理解下一步操作。
- 更新空状态提示，减少技术感表达。
- 调整表单校验提示，让错误说明更清楚。

📁 涉及文件
- src/components/Header.tsx
- src/components/EmptyState.tsx

🧪 验证
- 尚未运行自动化测试。

💡 后续建议
- 可以在浏览器里快速检查按钮、空状态和表单错误提示的展示效果。
```

## 前端文案对比

| 场景 | 使用前 | 使用后 |
|---|---|---|
| 加载状态 | AI is analyzing your request | 结果准备中 |
| 设置页标题 | Configure model provider settings | 模型设置 |
| 工作台标题 | Agent task orchestration dashboard | 助手工作状态 |
| 表单校验 | Real-time validation pipeline failed | 内容校验失败 |

## 标题和按钮命名规则

标题、导航、卡片名、按钮名优先使用短名词结构或功能名，不要写成完整句子。

| 不推荐 | 推荐 |
|---|---|
| 查看助手正在做什么 | 助手工作状态 |
| 选择助手的回复方式 | 模型设置 |
| 查看生成结果 | 结果预览 |
| 管理你创建的所有任务 | 任务管理 |
| 让 AI 开始分析你的内容 | 开始分析 |

## 推荐用法

- 用它统一 Codex 的最终总结风格。
- 用它改造前端标题、按钮、空状态、toast、dialog 文案。
- 用它做方案比较、架构取舍、优先级排序和 review 总结。
- 如果某次任务需要纯 JSON、纯日志、无 emoji、无表格，可以在 prompt 里明确说明。
