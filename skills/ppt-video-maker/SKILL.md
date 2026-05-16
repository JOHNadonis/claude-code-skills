---
name: ppt-video-maker
description: 将 PPT 和播客音频自动合成为视频。当用户提到"PPT 视频"、"音频配 PPT"、"播客配图"、"生成视频"、"PPT 转视频"，或提供 .pptx 和 .mp3/.wav 文件时使用。
---

# PPT + 音频 → 视频生成器

自动将 PPT 演示文稿和播客音频合成为带字幕的视频。

## 核心功能

1. PPT 自动转图片（有缓存则跳过）
2. 音频转录（豆包大模型 ASR，云端，速度快；备用：faster-whisper 本地）
3. 转录结果缓存为 SRT（重跑时直接读缓存）
4. AI 智能匹配 PPT 页面与音频时间点（有 timeline.json 则跳过）
5. FFmpeg 合成视频
6. 可选字幕烧录

## 工作流程

```
用户提供：PPT 文件 + 音频文件
  ↓
Step 1: 检查工具目录是否存在
  ↓
Step 2: 检查依赖是否安装
  ↓
Step 3: 运行生成脚本（各步骤均有缓存，重跑极快）
  ↓
Step 4: 展示 timeline.json，让用户确认后继续
  ↓
Step 5: 合成并展示结果
```

## 实现步骤

### Step 1: 检查工具目录

```bash
if [ -d "/Volumes/OS/ppt-video-maker" ]; then
  cd /Volumes/OS/ppt-video-maker
else
  echo "工具目录不存在"
  exit 1
fi
```

### Step 2: 检查依赖

必需：
- LibreOffice (`soffice`)
- poppler (`pdfinfo`)
- Python 虚拟环境 (`.venv/`)
- Python 包：`python-pptx pdf2image openai pyyaml websocket-client faster-whisper`

```bash
which soffice || brew install --cask libreoffice
which pdfinfo || brew install poppler
[ -d .venv ] || python3 -m venv .venv
source .venv/bin/activate
pip install python-pptx pdf2image openai pyyaml websocket-client faster-whisper
```

### Step 3: 运行生成脚本

```bash
source .venv/bin/activate

# 基础用法（脚本会在 timeline.json 生成后暂停等用户确认）
python ppt_video.py --pptx <PPT路径> --audio <音频路径>

# 跳过确认自动生成（二次运行或用户说"直接生成"时用）
python ppt_video.py --pptx <PPT路径> --audio <音频路径> --yes

# 带字幕
python ppt_video.py --pptx <PPT路径> --audio <音频路径> --yes --subs
```

**转录耗时参考（豆包 ASR）**：
- 10 分钟音频 ≈ 4 分钟转录（云端，准确率高）
- 转录结果缓存为 `<音频名>.srt`，下次重跑直接跳过

**各步骤缓存规则**：
| 步骤 | 跳过条件 |
|------|---------|
| PPT → 图片 | `slides_<pptx名>/slide_*.png` 已存在 |
| 音频转录 | `<音频名>.srt` 已存在 |
| AI 匹配 | `timeline_<pptx名>.json` 存在且条目数 = PPT 页数 |

> 缓存按 PPT 文件名隔离，切换不同 PPT 无需手动清缓存。

### Step 4: 时间线确认

脚本生成 `timeline.json` 后会暂停（除非用了 `--yes`）：

```
✅ 时间线已保存: timeline.json
💡 请检查 timeline.json，如需调整可手动修改后重新运行
是否继续生成视频？(y/n):
```

此时：
1. 读取并展示 `timeline.json` 给用户
2. 询问是否满意
3. 满意则输入 `y` 继续；不满意则修改 timeline.json 后重新运行（会跳过转录）

### Step 5: 展示结果

```
- 视频文件：output.mp4（或用户指定路径）
- 字幕文件：<音频名>.srt
- 时间线：timeline.json（可手动调整后重跑）
```

## 配置文件（config.yaml）

```yaml
api:
  base_url: "https://..."   # OpenAI 兼容 API（用于 AI 匹配）
  api_key: "sk-..."
  model: "Codex-sonnet-4-6"

transcription:
  backend: "doubao"          # "doubao"（推荐）或 "whisper"（本地备用）
  doubao_app_id: "..."
  doubao_access_token: "..."
  doubao_resource_id: "volc.seedasr.sauc.duration"  # 小时版模型2.0

video:
  resolution: "1920x1080"
  fps: 30
```

豆包 ASR 凭证从**火山引擎控制台 → 豆包语音 → 服务接口认证信息**获取。

## 错误处理

### 文件名含中文导致 LibreOffice 失败
先把文件复制到工具目录并重命名：
```bash
cd /Volumes/OS/ppt-video-maker
cp /path/to/原文件.pptx input.pptx
cp /path/to/原文件.mp3 input.mp3
python ppt_video.py --pptx input.pptx --audio input.mp3
```

### 豆包 ASR 失败
config.yaml 中改 `backend: "whisper"` 使用本地 faster-whisper（4x 原版速度）。

### AI 只匹配了前几张 PPT
已修复：脚本发送全部转录内容。若仍不完整，手动编辑 `timeline.json` 后用 `--yes` 重跑。

### FFmpeg pad filter 报错
已修复（resolution 格式自动转换）。

## 示例对话

**用户**：帮我把 slides.pptx 和 podcast.mp3 合成视频

**Codex**：
1. 把文件复制到工具目录（避免中文路径问题）
2. 运行脚本，告知"正在用豆包转录音频，约 4 分钟"
3. 展示 timeline.json 让用户确认
4. 用户确认后输入 y 或重跑加 --yes 生成视频

**用户**：时间线不对，第 3 页应该从 45 秒开始

**Codex**：
1. 编辑 `timeline.json`，调整第 3 页 `start: 45.0`，同步修改第 2 页 `end`
2. 重新运行（加 `--yes`，跳过转录直接生成）

## 注意事项

1. **中文路径**：LibreOffice 不支持带特殊字符的路径，务必先 cp 到工具目录
2. **重跑极快**：有缓存时只跑 FFmpeg 合成，约 1-2 分钟
3. **时间线检查**：AI 匹配不保证完美，建议人工过一遍
4. **豆包账单**：小时版按实际转录时长计费，10 分钟音频约消耗 10 分钟额度
