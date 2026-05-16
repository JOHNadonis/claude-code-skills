# PPT + 音频 → 视频生成器

自动将 PPT 和播客音频合成为带字幕的视频。

## 功能

- ✅ PPT 自动转图片
- ✅ 音频转文字（带时间戳）
- ✅ AI 智能匹配 PPT 页面与音频时间点
- ✅ 自动生成视频
- ✅ 可选字幕烧录

## 安装

已经装好了，包括：
- ✅ LibreOffice（PPT 转 PDF）
- ✅ poppler（PDF 处理）
- ✅ Python 依赖（Whisper、python-pptx、pdf2image 等）

如果在其他机器上使用，需要安装：

```bash
# macOS
brew install --cask libreoffice
brew install poppler

# 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate

# 安装 Python 依赖
pip install openai-whisper python-pptx pillow openai pyyaml pdf2image
```

## 使用

### 1. 配置 API

编辑 `config.yaml`，填入你的中转 API 信息：

```yaml
api:
  base_url: "https://your-proxy.com/v1"
  api_key: "sk-your-key-here"
  model: "claude-sonnet-4-20250514"
```

### 2. 运行

```bash
# 激活虚拟环境
source .venv/bin/activate

# 基础用法
python ppt_video.py --pptx 演示文稿.pptx --audio 播客.mp3

# 带字幕
python ppt_video.py --pptx 演示文稿.pptx --audio 播客.mp3 --subs

# 指定输出路径
python ppt_video.py --pptx 演示文稿.pptx --audio 播客.mp3 --output 我的视频.mp4
```

### 3. 流程

```
1. PPT 转图片 → slides/ 目录
2. 提取 PPT 文字
3. Whisper 转录音频（需要几分钟）
4. AI 匹配生成 timeline.json
5. 【人工检查】查看 timeline.json，确认时间点
6. 生成视频
7. （可选）烧录字幕
```

## 时间线调整

如果 AI 匹配的时间点不准，可以手动编辑 `timeline.json`：

```json
[
  {"slide": 1, "start": 0.0, "end": 35.2},
  {"slide": 2, "start": 35.2, "end": 72.8},
  {"slide": 3, "start": 72.8, "end": 115.0}
]
```

修改后重新运行，会跳过前面的步骤直接生成视频。

## 输出文件

- `slides/` - PPT 图片
- `timeline.json` - 时间线
- `播客.srt` - 字幕文件
- `output.mp4` - 最终视频
- `output_with_subs.mp4` - 带字幕的视频（如果用了 --subs）

## 常见问题

### Whisper 太慢？

换小模型：

```yaml
whisper:
  model: "small"  # 或 "base"
```

### 时间线不准？

1. 检查 PPT 每页是否有足够的文字内容
2. 手动调整 `timeline.json`
3. 或者在播客文稿里加更明显的分段标记

### 视频分辨率？

修改 `config.yaml`：

```yaml
video:
  resolution: "1280x720"  # 或其他分辨率
```

## 技术栈

- LibreOffice - PPT 转图片
- python-pptx - 提取 PPT 文字
- OpenAI Whisper - 语音转文字
- Claude API - 智能匹配
- FFmpeg - 视频合成
