---
name: create-skill
description: 创建新的 Codex Skill 的交互式向导。引导用户完成从需求定义到测试验证的完整流程。当用户想要创建自定义 Skill 时使用。
---

# Create Skill 向导

本 Skill 是一个「元 Skill」——用于指导创建新的 Codex Skills。它确保每个新 Skill 都有完整的结构和文档。

---

## 触发条件

**关键词触发：**
- 用户说「创建一个新 Skill」「新建 Skill」「make a skill」
- 用户使用 `/create-skill` 命令
- 用户描述想要自动化的工作流

---

## 阶段一：需求收集

### 1.1 询问基本信息

**必须收集的信息：**

1. **Skill 名称**（kebab-case 格式）
   - 例：`code-review`、`api-generator`、`data-validator`

2. **一句话描述**
   - 用于 SKILL.md 的 description 字段
   - 应清晰说明用途和触发场景

3. **主要用途**
   - 这个 Skill 要解决什么问题？
   - 用户什么时候会需要它？

4. **输入和输出**
   - 需要什么输入？（文件、参数、用户确认）
   - 产出什么结果？（文件、报告、代码）

5. **是否自动激活**
   - `autoActivate: true` - 无需触发词，符合条件自动运行
   - `autoActivate: false`（默认）- 需要用户明确触发

### 1.2 确认理解

在收集完信息后，用表格形式确认：

```
| 项目 | 值 |
|------|-----|
| 名称 | [skill-name] |
| 描述 | [description] |
| 触发方式 | [手动/自动] |
| 输入 | [inputs] |
| 输出 | [outputs] |
```

等待用户确认后再继续。

---

## 阶段二：创建目录结构

### 2.1 标准结构

```
.Codex/skills/[skill-name]/
├── SKILL.md          # 核心指令文件（必需）
├── examples/         # 示例文件（可选）
│   └── example.md
└── templates/        # 模板文件（可选）
    └── template.md
```

### 2.2 执行创建

```bash
# 创建目录
mkdir -p .Codex/skills/[skill-name]

# 验证创建
ls -la .Codex/skills/[skill-name]
```

**重要**：根据 MEMORY.md 最佳实践，创建前后都要验证目录结构。

---

## 阶段三：编写 SKILL.md

### 3.1 必需章节

每个 SKILL.md 必须包含：

```markdown
---
name: [skill-name]
description: [一句话描述，用于 Skill 列表显示]
autoActivate: false  # 或 true
---

# [Skill 标题]

[简要介绍 Skill 的用途]

---

## 触发条件

**关键词触发：**
- [触发词1]
- [触发词2]
- `/[skill-name]` 命令

---

## 阶段一：[第一个阶段名]

### 1.1 [步骤名]
[具体指令]

### 1.2 [步骤名]
[具体指令]

---

## 阶段二：[第二个阶段名]

[继续...]

---

## 使用示例

### 示例 1：[场景名]

**用户**：[用户输入]

**Codex**：[期望的 Codex 回复]

---

## 配置选项（可选）

[如果 Skill 支持配置]

---

## 常见问题（可选）

**Q: [问题]**
A: [回答]
```

### 3.2 编写指南

- **指令要明确**：告诉 Codex「做什么」而不是「可以做什么」
- **分阶段执行**：复杂任务拆分为多个阶段
- **包含检查点**：每个阶段结束后确认再继续
- **提供示例**：至少一个完整的使用示例

---

## 阶段四：测试验证

### 4.1 语法验证

确保 SKILL.md：
- frontmatter 格式正确（`---` 包裹的 YAML）
- Markdown 语法正确
- 没有未闭合的代码块

### 4.2 功能测试

引导用户进行测试调用：

```
现在让我们测试一下新创建的 Skill。

请输入以下命令触发它：
/[skill-name]

或者说：
「[触发词示例]」
```

### 4.3 验证清单

- [ ] Skill 出现在 `/help` 的 Skill 列表中
- [ ] 触发词能正确激活 Skill
- [ ] 每个阶段按预期执行
- [ ] 输出符合预期

---

## 快捷命令

| 命令 | 说明 |
|------|------|
| `/create-skill` | 启动创建向导 |
| `/create-skill [name]` | 直接指定名称开始创建 |
| `/create-skill --from [file]` | 基于现有文件创建 Skill |

---

## 使用示例

### 示例 1：创建代码审查 Skill

**用户**：/create-skill

**Codex**：
好的，让我们创建一个新的 Skill！

请回答以下问题：

1. **Skill 名称**（kebab-case）：
2. **一句话描述**：
3. **主要用途**：这个 Skill 要解决什么问题？
4. **输入/输出**：需要什么，产出什么？
5. **触发方式**：手动触发还是自动激活？

**用户**：
1. code-review
2. 对代码变更进行系统性审查，检查安全性、性能和最佳实践
3. 在提交代码前进行全面的代码审查
4. 输入：git diff 或文件路径；输出：审查报告
5. 手动触发

**Codex**：
确认信息：

| 项目 | 值 |
|------|-----|
| 名称 | code-review |
| 描述 | 对代码变更进行系统性审查... |
| 触发方式 | 手动 |
| 输入 | git diff 或文件路径 |
| 输出 | 审查报告 |

确认无误？我将开始创建目录和 SKILL.md。

**用户**：确认

**Codex**：
[创建目录]
[编写 SKILL.md]
[显示创建结果]

Skill 创建完成！现在来测试一下：

请输入 `/code-review` 或说「帮我审查代码」

---

### 示例 2：从描述快速创建

**用户**：创建一个 Skill，用于将 Markdown 文件转换为微信公众号格式

**Codex**：
我来帮你创建这个 Skill。

基于你的描述，我理解的需求是：

| 项目 | 值 |
|------|-----|
| 名称 | md-to-wechat |
| 描述 | 将 Markdown 文件转换为微信公众号兼容的 HTML 格式 |
| 输入 | Markdown 文件路径 |
| 输出 | 微信公众号格式的 HTML |

需要调整吗？

---

## Skill 设计最佳实践

1. **单一职责**：一个 Skill 只做一件事，做好
2. **明确边界**：清楚说明什么情况用、什么情况不用
3. **优雅降级**：当输入不完整时，引导用户补充而非失败
4. **可组合**：设计时考虑与其他 Skill 联动的可能
5. **文档完整**：好的文档让 Skill 自解释

---

## 常见问题

**Q: Skill 放在哪个目录？**
A: 全局 Skill 放 `~/.Codex/skills/`，项目级 Skill 放 `.Codex/skills/`（项目根目录）

**Q: 如何让 Skill 自动激活？**
A: 在 frontmatter 中设置 `autoActivate: true`，并在触发条件中说明自动激活的场景

**Q: 可以用其他语言写 Skill 吗？**
A: SKILL.md 必须是 Markdown，但可以在其中调用任何语言的脚本

**Q: 如何分享 Skill？**
A: 将整个 skill 目录复制给他人，或使用 `install-skill` 的流程
