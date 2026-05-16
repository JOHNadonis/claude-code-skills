# Opus Style Output Skill

一个让 Codex / GPT 模型输出更接近 Claude Opus 风格的全局 Skill。

它的目标不是“装成 Claude”，而是把日常开发中的回答、总结、评审、前端文案变得更清楚、更好读、更像一个成熟产品同事交付出来的内容。

## 它解决什么问题

| 使用前 | 使用后 |
|---|---|
| 最终总结像开发日志 | 变成清晰的交付总结 |
| 回答又长又散 | 先给结论，再分点说明 |
| 方案对比不直观 | 自动倾向使用 Markdown 表格 |
| 前端标题像技术说明 | 改成用户能理解的产品短语 |
| 文案暴露实现逻辑 | 只描述用户价值、状态和动作 |
| 总结缺少层次 | 使用 `✅ / 📁 / 🧪 / ⚠️ / 💡` 分区 |

## 核心能力

- **全局输出优化**：默认应用在 Codex 的大多数回答和最终总结中。
- **Opus 风格表达**：温和、清晰、有结构，少废话但不生硬。
- **表格优先**：做比较、规划、评审、架构取舍时，优先用表格提高可读性。
- **Emoji 分区**：用少量 emoji 让总结更容易扫读。
- **前端文案约束**：标题、按钮、导航、卡片名优先使用短名词结构或功能名。
- **用户视角 copy**：UI 文案面向最终用户，不写开发思路、实现逻辑、debug 细节。

## 安装方式

把本目录复制到 Codex 的 skills 目录：

```bash
cp -R opus-style-output ~/.codex/skills/
```

安装后的结构应该是：

```text
~/.codex/skills/opus-style-output/
├── SKILL.md
├── README.md
├── agents/
│   └── openai.yaml
└── references/
    └── USAGE.md
```

如果你把这个文件夹作为 GitHub 仓库发布，仓库根目录就是 `opus-style-output` 本身，不需要再额外套一层目录。

## 使用方式

### 自动触发

这个 Skill 的触发条件写成了全局触发：

```text
Always use this skill globally for Codex responses unless the user explicitly requests a different style.
```

也就是说，只要 Codex 识别到这个 Skill，大多数回答都会默认套用这套输出风格。

### 手动触发

如果你想明确要求使用它，可以在 prompt 里写：

```text
使用 $opus-style-output 总结这次改动
```

或者：

```text
用 $opus-style-output 帮我优化这些前端文案
```

## 前后对比

### 代码任务总结

使用前：

```text
Modified src/components/Header.tsx and updated the CTA logic. Also changed the empty state copy and adjusted validation messages. Tests were not run.
```

使用后：

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

### 前端标题和按钮

| 不推荐 | 推荐 |
|---|---|
| 查看助手正在做什么 | 助手工作状态 |
| 选择助手的回复方式 | 模型设置 |
| 查看生成结果 | 结果预览 |
| 管理你创建的所有任务 | 任务管理 |
| 让 AI 开始分析你的内容 | 开始分析 |

### 前端状态和提示

| 场景 | 不推荐 | 推荐 |
|---|---|---|
| 加载状态 | AI is analyzing your request | 结果准备中 |
| 设置页标题 | Configure model provider settings | 模型设置 |
| 工作台标题 | Agent task orchestration dashboard | 助手工作状态 |
| 表单校验 | Real-time validation pipeline failed | 内容校验失败 |

## 适合谁用

- 经常用 Codex 做开发的人。
- 希望 Codex 最终总结更像“交付说明”的人。
- 经常让 AI 写前端页面、按钮、空状态、toast、弹窗文案的人。
- 希望 GPT 模型回答更接近 Claude Opus 风格的人。
- 想把团队内部 AI 输出风格统一起来的人。

## 注意事项

- 这个 Skill 只是输出风格约束，不会改变模型本身能力。
- 如果你需要纯 JSON、纯日志、无 emoji、无表格，请在 prompt 中明确说明。
- 如果你的项目已有更严格的 AGENTS.md 或系统提示，优先级可能高于这个 Skill。
- “Opus 风格”指的是清晰、温和、结构化的表达习惯，不代表调用或依赖 Claude 模型。

## 文件说明

| 文件 | 说明 |
|---|---|
| `SKILL.md` | Skill 主文件，包含触发条件和核心规则 |
| `agents/openai.yaml` | Codex UI 展示信息 |
| `references/USAGE.md` | 更详细的中文使用教程和对比示例 |
| `README.md` | GitHub 分享首页说明 |

## 许可

你可以自由复制、修改、分享这个 Skill。
