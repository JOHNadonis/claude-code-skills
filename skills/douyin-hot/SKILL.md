---
name: douyin-hot
description: 自动抓取抖音热榜话题，获取实时热点内容。适用于查询抖音热榜、热搜与热点视频话题。
---

# 抖音热榜查询 Skill

自动抓取抖音热榜话题，获取实时热点内容。

## 触发条件

当用户提到以下关键词时激活：
- 抖音热榜
- 抖音热搜
- 抖音热点
- 查看抖音
- douyin hot

## 功能

使用 Playwright 自动化浏览器访问抖音热榜页面，提取热门话题和热度数据。

## 使用方法

直接运行脚本：

```bash
python3 ~/.agents/skills/douyin-hot/douyin_hot.py
```

## 输出格式

- 热榜排名
- 话题标题
- 热度数值
- 相关热点视频

## 依赖

- Python 3
- Playwright (`pip3 install playwright --break-system-packages`)
- Chromium 浏览器 (`playwright install chromium`)

## 注意事项

- 抖音有反爬虫机制，使用非无头模式模拟真实用户
- 页面加载需要5秒左右
- 会生成截图保存到 `/tmp/douyin_hot.png`
