# 快速开始

## 测试运行（演示模式）

```bash
cd /Volumes/OS/ppt-video-maker
source .venv/bin/activate
python test_demo.py
```

这会展示核心功能：
- ✅ PPT 文字提取
- ✅ PPT 转图片（每页独立）
- ✅ 模拟转录和时间线生成

## 实际使用

### 1. 配置 API

编辑 `config.yaml`：

```yaml
api:
  base_url: "https://your-proxy.com/v1"  # 你的中转地址
  api_key: "sk-xxx"                       # 你的 key
  model: "claude-sonnet-4-20250514"       # 模型名
```

### 2. 准备文件

- PPT 文件（.pptx）
- 音频文件（.mp3 或 .wav）

### 3. 运行

```bash
source .venv/bin/activate

# 基础用法
python ppt_video.py --pptx 你的PPT.pptx --audio 你的音频.mp3

# 带字幕
python ppt_video.py --pptx 你的PPT.pptx --audio 你的音频.mp3 --subs
```

### 4. 流程

```
1. PPT 转图片 (10秒)
   ↓
2. 提取 PPT 文字 (1秒)
   ↓
3. Whisper 转录音频 (3-5分钟，取决于音频长度)
   ↓
4. AI 匹配生成 timeline.json (30秒)
   ↓
5. 【人工检查】查看 timeline.json
   ↓
6. 确认后生成视频 (1-2分钟)
   ↓
7. （可选）烧录字幕 (1分钟)
```

### 5. 输出文件

- `slides/` - PPT 图片
- `timeline.json` - 时间线（可手动调整）
- `你的音频.srt` - 字幕文件
- `output.mp4` - 最终视频

## 时间线调整

如果 AI 匹配的时间点不准，编辑 `timeline.json`：

```json
[
  {"slide": 1, "start": 0.0, "end": 35.2},
  {"slide": 2, "start": 35.2, "end": 72.8},
  {"slide": 3, "start": 72.8, "end": 115.0}
]
```

修改后重新运行，会跳过前面的步骤直接生成视频。

## 性能优化

### Whisper 太慢？

换小模型（`config.yaml`）：

```yaml
whisper:
  model: "small"  # 或 "base"，速度快但准确度略低
```

### 视频太大？

降低分辨率（`config.yaml`）：

```yaml
video:
  resolution: "1280x720"  # 或 "1920x1080"
```

## 常见问题

### 1. LibreOffice 命令找不到

```bash
# 检查是否安装
which soffice

# 如果没有，重新安装
brew install --cask libreoffice
```

### 2. Whisper 报错

```bash
# 重新安装
pip install --upgrade openai-whisper
```

### 3. FFmpeg 找不到

```bash
# 安装 FFmpeg
brew install ffmpeg
```

### 4. 时间线完全不对

可能原因：
- PPT 页面文字太少，AI 无法匹配
- 播客内容与 PPT 顺序不一致

解决方法：
- 手动编辑 `timeline.json`
- 或在 PPT 每页加更多文字内容
