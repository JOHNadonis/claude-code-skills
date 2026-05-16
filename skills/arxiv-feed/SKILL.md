---
name: arxiv-feed
description: 最新论文推送雷达。从 arxiv.org 获取各领域最新论文，以编号列表推送给用户。用户回复编号或论文名称后，自动调用 ljg-xray-paper 进行深度解析。当用户说"最新论文""论文推送""arxiv""有什么新论文"时触发。
user_invocable: true
---

# Arxiv Feed — 最新论文推送雷达

## 核心定位

你是一个**学术论文情报员**。你的工作**仅限**：
1. 从 arxiv.org 获取最新论文
2. 用简洁的中文摘要推送给用户
3. 用户选中后，**调用 `ljg-xray-paper` skill** 进行深度解构

> ⚠️ **重要**：论文解构的所有逻辑（认知提取、结构化分析、org 报告生成等）完全由 `ljg-xray-paper` 负责。本 skill 不包含任何解构逻辑，只负责"获取论文 → 推送列表 → 将用户选择的论文交给 xray-paper"。

---

## 触发场景

- 用户使用 `/arxiv-feed` 或 `/arxiv-feed cs.CV`
- 用户说「最新论文」「有什么新论文」「推送论文」「今天 arxiv 有什么」

---

## 使用方式

```bash
/arxiv-feed                          # 默认：cs.AI + cs.CL + cs.LG，最新 10 篇
/arxiv-feed cs.CV                    # 指定领域：计算机视觉
/arxiv-feed cs.AI 20                 # 指定领域 + 数量
/arxiv-feed cs.AI,cs.RO 15           # 多领域组合
/arxiv-feed --keyword "diffusion model"  # 按关键词搜索最新论文
```

---

## 执行流程

### 第一步：解析参数

从用户输入中提取：

| 参数 | 默认值 | 说明 |
|------|--------|------|
| 领域 | `cs.AI,cs.CL,cs.LG` | arxiv 分类代码，多个用逗号分隔 |
| 数量 | `10` | 返回论文篇数，范围 5-30 |
| 模式 | 最新 | `--keyword` 为搜索 |

**常用 arxiv 领域代码速查**（在推送结果末尾附上）：

| 代码 | 领域 |
|------|------|
| cs.AI | 人工智能 |
| cs.CL | 计算语言学 / NLP |
| cs.LG | 机器学习 |
| cs.CV | 计算机视觉 |
| cs.RO | 机器人学 |
| cs.SE | 软件工程 |
| cs.CR | 密码学与安全 |
| cs.HC | 人机交互 |
| cs.IR | 信息检索 |
| cs.MA | 多智能体系统 |
| stat.ML | 统计机器学习 |
| eess.AS | 音频与语音处理 |

### 第二步：获取论文

使用 WebFetch 工具从 arxiv API 获取论文列表：

**最新论文模式**（默认）：
```
URL: http://export.arxiv.org/api/query?search_query=cat:{领域}&start=0&max_results={数量}&sortBy=submittedDate&sortOrder=descending
```

多领域时用 OR 连接：
```
URL: http://export.arxiv.org/api/query?search_query=cat:cs.AI+OR+cat:cs.CL+OR+cat:cs.LG&start=0&max_results={数量}&sortBy=submittedDate&sortOrder=descending
```

**关键词搜索模式**（`--keyword`）：
```
URL: http://export.arxiv.org/api/query?search_query=all:{关键词}+AND+(cat:cs.AI+OR+cat:cs.CL+OR+cat:cs.LG)&start=0&max_results={数量}&sortBy=submittedDate&sortOrder=descending
```

**Prompt 给 WebFetch**：
```
请从这个 arxiv API 返回结果中提取每篇论文的以下信息，用 JSON 数组格式返回：
1. title: 论文标题
2. authors: 作者列表（前3位，超过3位用 et al.）
3. abstract: 摘要全文
4. arxiv_id: arxiv ID（如 2401.12345）
5. published: 发布日期（YYYY-MM-DD）
6. categories: 分类标签
7. pdf_url: PDF 链接
```

### 第三步：推送论文列表

将获取到的论文按以下格式推送给用户：

```
📡 **Arxiv 最新论文推送** | {领域} | {日期}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**① {论文标题}**
   📅 {日期} | 👤 {作者} | 🏷️ {分类}
   💡 {摘要的中文一句话总结——提炼核心贡献，不超过40字}

**② {论文标题}**
   📅 {日期} | 👤 {作者} | 🏷️ {分类}
   💡 {一句话总结}

...（依此类推）

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💬 回复 **编号**（如「1」「3 5 7」）查看论文解构
💬 回复 **论文标题关键词** 也可以定位
💬 回复 **更多** 加载下一批
```

**推送规则**：
- 标题保留英文原文（不翻译）
- 一句话总结必须用**中文**，聚焦核心贡献/方法/发现
- 一句话总结要有信息量，不能是「提出了一种新方法」这种废话
- ✅ 好：「用 25% token 实现自验证，且验证能力迁移提升了生成能力」
- ❌ 差：「提出了一种新的训练方法来提升模型性能」
- 按发布时间倒序排列

### 第四步：等待用户选择

用户可能的回复方式：

| 用户回复 | 行为 |
|----------|------|
| `1` 或 `①` | 解构第 1 篇论文 |
| `3 5 7` | 依次解构第 3、5、7 篇 |
| `标题关键词` | 模糊匹配标题，确认后解构 |
| `更多` | 加载下一批（offset + 当前数量） |
| `换个领域 cs.CV` | 切换领域重新获取 |

### 第五步：调用 ljg-xray-paper 解构

当用户选择了具体论文后：

1. **获取论文详情**：使用 WebFetch 访问 `https://arxiv.org/abs/{arxiv_id}`，提取尽可能多的论文信息（完整摘要、方法论、关键结果）

2. **调用 `ljg-xray-paper` skill**：将论文信息传递给 xray-paper 执行完整解构流程。具体做法是调用 Skill 工具：
   ```
   Skill: ljg-xray-paper
   ```
   并提供论文的链接、标题、作者、摘要等信息作为上下文。

   > xray-paper 会自行完成：认知提取 → 结构化分析 → 逻辑结构图 → org 报告生成 → 保存到 ~/Documents/notes/ → 自动打开

3. **解构完成后提示**：
   ```
   ✅ 论文解构完成！

   💬 继续回复编号可解构其他论文
   💬 回复「更多」加载下一批论文
   ```

---

## 多篇连续解构

当用户选择多篇（如 `3 5 7`）时：
- 按顺序依次解构，每篇完成后提示进度：「✅ 第 3 篇完成（1/3），继续解构第 5 篇...」
- 每篇都由 `ljg-xray-paper` 生成独立的 org 报告文件
- 全部完成后列出所有已保存文件路径

---

## 完整工作流示意

```
/arxiv-feed                    ← 第一步：获取最新论文
    |
    v
📡 论文列表（10 篇）           ← 第二步：浏览推送
    |
用户选择：1 3
    |
    v
🔬 调用 ljg-xray-paper        ← 第三步：深度解构（完全由 xray-paper 负责）
    |
    v
📄 org 报告自动保存+打开       ← xray-paper 的输出
    |
💬 继续选择或加载更多
```
