---
name: xiaohongshu-hot
description: 自动抓取小红书热榜话题，获取实时热点内容。适用于查询小红书热榜、热搜与热点话题。
---

# 小红书热榜查询 Skill

自动抓取小红书热榜话题，获取实时热点内容。

## 触发条件

当用户提到以下关键词时激活：
- 小红书热榜
- 小红书热搜
- 小红书热点
- 查看小红书
- xiaohongshu hot
- 红书热榜

## 功能

使用 Playwright 自动化浏览器访问小红书热榜页面，提取热门话题和热度数据。

## 使用方法

直接运行脚本：

```bash
python3 ~/.agents/skills/xiaohongshu-hot/xiaohongshu_hot.py
```

## 输出格式

- 热榜排名
- 话题标题
- 热度数值
- 相关笔记数量

## 依赖

- Python 3
- Playwright (`pip3 install playwright --break-system-packages`)
- Chromium 浏览器 (`playwright install chromium`)

## 注意事项

- 小红书有反爬虫机制，使用非无头模式模拟真实用户
- 页面加载需要5秒左右
- 会生成截图保存到 `/tmp/xiaohongshu_hot.png`
