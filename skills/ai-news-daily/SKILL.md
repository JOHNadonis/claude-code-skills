---
name: ai-news-daily
description: AI新闻日报v1.0.2 - 自动抓取全球AI行业最新动态，每日推送10条精选新闻。支持外部配置(config.yaml)、失败重试、完整内容保存确保AI生成200-250字摘要、英文自动翻译。安装后自动创建OpenClaw定时任务，每天早上9:00自动推送。用于定时抓取AI新闻、RSS聚合、智能去重。
---

# AI 新闻日报 v1.0.2

自动抓取全球 AI 行业最新动态，每日推送 10 条精选新闻。

## ✨ 功能特性

1. **自动推送** - 安装后自动创建 OpenClaw 定时任务，每天早上 9:00 推送
2. **AI生成摘要** - 200-250 字中文摘要，英文内容自动翻译
3. **外部配置** - 所有参数移到 `config/config.yaml`
4. **完整内容保存** - 保存 3000 字原始内容供生成摘要
5. **失败重试** - 自动重试失败的请求，指数退避
6. **智能去重** - URL归一化 + 标题相似度检测

## 🚀 快速开始

### 安装

```bash
# 解压 skill
unzip ai-news-daily-v1-0-2.skill -d ai-news-daily
cd ai-news-daily

# 安装依赖
pip install -r requirements.txt

# 运行设置（自动创建定时任务）
python3 src/setup.py
```

安装完成后，**每天早上 9:00 会自动推送新闻到当前对话**。

### 手动运行

```bash
# 立即抓取并推送
./run.sh
```

## ⚙️ 配置

编辑 `config/config.yaml`：

```yaml
# 抓取配置
fetch:
  max_workers: 4
  request_timeout: 15
  max_retries: 3

# 摘要配置  
summary:
  target_min: 200
  target_max: 250

# 输出配置
output:
  top_n: 10           # 每天推送几条
  
# 推送配置
push:
  openclaw:
    enabled: true
    output_file: data/openclaw_message.txt
```

## 📅 定时任务管理

```bash
# 查看所有定时任务
openclaw cron list

# 手动立即运行一次
openclaw cron run <job-id>

# 暂停任务
openclaw cron update <job-id> --enabled false

# 删除任务
openclaw cron remove <job-id>
```

## 📁 文件结构

```
ai-news-daily/
├── SKILL.md              # 本文件
├── config/
│   └── config.yaml       # 配置文件
├── src/
│   ├── daily_fetch.py    # 主程序（抓取新闻）
│   ├── generate_summaries.py  # 生成摘要
│   ├── push.py           # 推送脚本
│   └── setup.py          # 安装设置（创建定时任务）
├── data/
│   ├── news.db           # SQLite数据库
│   └── openclaw_message.txt  # 生成的消息
├── requirements.txt      # 依赖列表
└── run.sh                # 运行脚本
```

## 📰 新闻源

| 权重 | 来源 |
|------|------|
| 1.3 | 量子位、机器之心、36氪、新智元、智东西、InfoQ |
| 1.2 | TechCrunch AI、The Verge AI、MIT Tech Review |
| 1.1 | 雷锋网、钛媒体、极客公园 |
| 1.0 | 虎嗅 |

## 📤 输出格式

```
📰 AI 每日新闻 - 2026年03月02日

共 10 条精选
──────────────────────────────

1. [来源] 新闻标题

200-250字的中文摘要，英文内容已翻译...

🔗 [阅读原文](url)
...

🤖 AI News Aggregator | 每日更新
```

## 🛠️ 故障排除

### 定时任务未创建
```bash
# 手动创建
python3 src/setup.py
```

### 依赖安装失败
```bash
pip install --break-system-packages -r requirements.txt
```

### 新闻抓取失败
```bash
# 查看日志
tail -f data/fetch.log
```

## 🔧 工作原理

1. **抓取阶段** (`daily_fetch.py`)
   - 并发抓取 14 个 RSS 源
   - 保存完整原始内容到数据库
   - 智能去重，避免重复

2. **摘要阶段** (`generate_summaries.py`)
   - 从数据库读取原始内容
   - 生成 200-250 字中文摘要
   - 英文内容自动翻译

3. **推送阶段** (OpenClaw 定时任务)
   - 每天 9:00 自动触发
   - 生成摘要并推送到指定频道

## 📄 License

MIT
