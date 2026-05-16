---
name: scrapling
description: 使用 Scrapling 执行网页抓取、选择器提取与爬虫任务。适用于用户提到 Scrapling、网页抓取、CSS/XPath 提取、动态页面抓取、反爬绕过、Cloudflare、批量爬取、并发爬虫、爬虫暂停恢复等场景。
---

# Scrapling

## Overview

用 Scrapling 处理从单页提取到并发爬虫的抓取任务。优先使用本技能内脚本完成稳定、可复用的提取流程，再按需升级到 Scrapling 的 fetchers/spiders 能力。

## Workflow

1. 先确认任务类型：
   - 单页/少量页面结构化提取：直接用 `scripts/scrapling_extract.py`
   - 动态页面或反爬场景：使用 Scrapling fetchers（`StealthyFetcher`/`DynamicFetcher`）
   - 多页并发抓取：使用 Scrapling spiders
2. 若环境未安装 Scrapling，先运行 `scripts/install_scrapling.sh`
3. 执行抓取并输出结构化结果（JSON 优先）
4. 如用户要求“可复用”，沉淀为脚本并保留命令示例

## Setup

先检查是否已安装：

```bash
python3 -c "import scrapling; print(scrapling.__version__)"
```

未安装时执行：

```bash
bash /Users/whc/.agents/skills/scrapling/scripts/install_scrapling.sh all
```

安装模式：
- `base`：仅解析能力
- `fetchers`：含 fetchers（HTTP/动态/隐身抓取）
- `shell`：含 CLI shell 能力
- `ai`：含 AI/MCP 扩展
- `all`：全部能力

## Quick Extraction (Static/Lightweight)

使用脚本：

```bash
python3 /Users/whc/.agents/skills/scrapling/scripts/scrapling_extract.py \
  "https://example.com" --css "h1::text" --first
```

更多示例：

```bash
python3 /Users/whc/.agents/skills/scrapling/scripts/scrapling_extract.py \
  "https://example.com" --css "a::attr(href)" --json --output links.json

python3 /Users/whc/.agents/skills/scrapling/scripts/scrapling_extract.py \
  "https://example.com" --xpath "//title/text()" --first
```

## Dynamic / Anti-Bot / Spider Recipes

按需读取：`references/recipes.md`

触发条件：
- 用户明确说页面是 JS 渲染、被 Cloudflare/反爬拦截
- 需要并发抓取、断点续跑、流式产出
- 需要会话、代理轮换或多会话路由

执行前给出风险提醒：遵守目标站点条款和当地法律。
