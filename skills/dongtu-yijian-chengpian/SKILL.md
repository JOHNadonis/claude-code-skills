---
name: dongtu-yijian-chengpian
description: 抖音 AI 动图一键成片。配合 dongtu-wenan（动图文案）+ 抖音短视频素材快剪工厂 MCP（渲染），把写好的 n 篇动图文案批量灌入「AI 动图批量」渲染成片。用户提到"动图成片"、"AI 动图批量"、"动图一键成片"、"把动图文案做成视频"、"动图渲染"时触发。注意与桌拍一键成片（zhuopai-yijian-chengpian）区分：素材是平铺 IMG_*.MOV 场景段，走 app 的动图AI（qianchuan）面板，不是桌拍分镜混剪。输入：商品素材目录 + 动图文案 txt（[] 分隔），输出：n 个成片 mp4 + 百度网盘上传。
---

# 动图一键成片

把 dongtu-wenan 写好的 n 篇动图文案，批量交给「抖音短视频素材快剪工厂」的 **AI 动图批量**（qianchuan 动图AI 面板）渲染成成片视频。

## 与桌拍一键成片（zhuopai-yijian-chengpian）的区别

| 维度 | 动图一键成片（本 skill） | 桌拍一键成片 |
|------|------------------------|--------------|
| 素材结构 | **平铺 IMG_*.MOV** 场景段（横屏 1920x1440），按 IMG 编号前缀分组 | 子文件夹 = 分镜场景 |
| 文案格式 | 独立 `[]` 行分隔（dongtu-wenan 输出格式），N 篇 = N 个 caption job | `---` 分隔，逐篇拆成独立文件 |
| 成片形态 | scene-combine 两段拼接 + 字幕烧录，2×2s 竖屏段 | 豆包 AI 混剪 + 口播配音 |
| 渲染面板 | 动图AI（qianchuan） | AI 桌拍（auto-mix） |
| 渲染参数 | **读已保存的 qianchuan-settings.json，不重新设置** | 提交时传入 options |

## 前置条件

- 桌面 app「抖音短视频素材快剪工厂」已打开并登录（MCP/CLI 依赖它运行）
- **已保存渲染参数存在**：`~/Library/Application Support/douyin-material-studio/qianchuan-settings.json`（位置/字体/批计划/素材段时长/creative overlay 等全在里）
- bdpan CLI 已安装并登录（`bdpan whoami` 返回已登录），成片渲染完上传到百度网盘用
- CLI 兜底可用：`APP="/Applications/抖音短视频素材快剪工厂.app/Contents/MacOS/抖音短视频素材快剪工厂"`

## 工作流程

### 1. 确认输入

| 输入 | 说明 |
|------|------|
| 商品名 | 成片标识（product 字段） |
| 素材目录 | 绝对路径，**平铺 IMG_*.MOV 场景段**（可能跨多个 IMG 编号段） |
| 动图文案 txt | dongtu-wenan 输出的合集 txt，独立 `[]` 行分隔 |

### 2. 清理素材目录（关键！）

**素材目录里绝不能有输出子文件夹**——动图AI 的 scan 会把素材目录内的任何子文件夹当 scene group，导致误判。每次 enqueue 前：

1. 检查素材目录内是否残留输出目录（命名规律：`<目录名>-output-YYYYMMDD-HHMMSS`、`<商品>-动图-YYYYMMDD*`）
2. 全部 `mv` 到工作区备份（`workspace/dongtu-wenan-output/<批次>/_素材目录清理/`），**不要 rm**
3. 确认后素材目录只剩平铺 `IMG_*.MOV`（忽略 `._` 开头 macOS 元数据）

### 3. 预览分组（必须 ≥2 组）

平铺素材用 **image-prefix** 分组。**auto 模式在平铺目录会把所有文件归成 1 组 → 报「分镜组合至少需要 2 个可用分镜组；当前只识别到 1 个」**。必须显式指定：

```
"$APP" --cli qianchuan-scan "<素材目录>" --source-type image-prefix --prefix-mode first-three-digits
```

- 分组数 ≥2 才可继续（scene-combine 需要两段拼接）
- 分组数以 IMG 编号前 3 位划分（如 IMG_522x / IMG_523x / ...）
- 分组数记录备查：8.14 批次实测 = 伊风 7、素说美丽 7、碌柚叶 7、凸凸兔 14、Haa 11、烙色 12

### 4. 提交任务（每商品一个）

用 `qianchuan-enqueue`。**渲染参数全部走已保存设置，不重新设置**（buildAgentQianchuanOptions 会自动 merge `qianchuan-settings.json`），只覆盖三个必传：

- `--product "<商品名>"`（覆盖已保存的旧商品名）
- `--copy-source file --copy-file "<文案txt绝对路径>"`（覆盖文案来源）
- `--options-json` 里只有 `sceneSourceType: "image-prefix"` + `imagePrefixMode: "first-three-digits"`（平铺素材分组必需，其余不碰）

```
cat > /tmp/qianchuan-opts.json << 'EOF'
{"sceneSourceType": "image-prefix", "imagePrefixMode": "first-three-digits"}
EOF
"$APP" --cli qianchuan-enqueue "<素材目录绝对路径>" \
  --product "<商品名>" \
  --copy-source file --copy-file "<文案txt>" \
  --scene-combine \
  --options-json /tmp/qianchuan-opts.json \
  --no-start
```

N 个商品各 enqueue 一次（`--no-start` 全部排队），确认 summary.queued = N 再统一启动。

### 5. 启动队列并等待

- 全入队后 `"$APP" --cli qianchuan-start-queue`
- `"$APP" --cli qianchuan-tasks` 看汇总，`"$APP" --cli qianchuan-task <完整id>` 看单任务日志
- 任务日志推进顺序：`[scene-render] 00xx`（拼接 N 个场景组合）→ `[jobs] N caption render job(s)` → `[render] ..._captioned.mp4`（逐条烧录字幕）→ `[points] 动图素材 N 条，扣除 N 积分` → `[done] 输出目录`
- **进度校验点**：`[jobs] N` 必须 = 文案篇数（50 篇 = 50 个 caption job）；每个 scene-render 是 `IMG_529x:IMG_5297.MOV + IMG_530x:IMG_5300.MOV` 两段拼接
- **批计划验证**：日志里 scene_combo 0001-0010 落第1批、0011-0020 落第2批……与已保存 `outputFolderPlan` 一致

### 6. 校验成片数量与字幕

```
# 成片 = *_captioned.mp4，剔除 ._ 开头的 macOS AppleDouble 元数据
find "<输出目录>" -name '*_captioned.mp4' ! -name '._*' | wc -l   # 必须 = 文案篇数
for d in "<输出目录>"/*/; do echo "$(basename "$d"): $(ls "$d"/*_captioned.mp4 2>/dev/null | wc -l)"; done
```

- 输出目录在素材目录内：`<素材目录名>-output-YYYYMMDD-HHMMSS/`，按已保存 `outputFolderPlan` 分成第1批~第5批
- 每批数量 = 批计划数量（如 10×5 批 = 50）
- 抽查 1-2 个成片：ffprobe 看时长（2×sceneSegmentDuration 秒）、截帧看字幕是否烧录

### 7. 上传成片到百度网盘

渲染完成后把成功成片上传百度网盘。bdpan 权限隔离在「我的应用数据/bdpan/」（API 路径 `/apps/bdpan/`），只传成功任务。

- **上传前确认**：`bdpan whoami` 已登录；未登录先跑 `bash .claude/skills/baidu-drive/scripts/login.sh` 引导老大授权
- **远端目录**：`动图成片/<商品名>成片/`（`/apps/bdpan/` 下，命令用相对路径，别用中文"我的应用数据"）
- **步骤**：
  1. 建文件夹：`bdpan mkdir "动图成片/<商品名>成片"`（已存在无妨）
  2. 整目录上传：`bdpan upload "<成片输出目录>/" "动图成片/<商品名>成片"`（本地目录以 `/` 结尾）——注意素材目录里还混着 `-output-*` 输出目录，上传时只传输出目录本身
  3. 核对：`bdpan ls "动图成片/<商品名>成片"`，确认上传数 = 成功成片数
- 给老大汇报网盘路径 + 在线查看链接（`bdpan ls` 输出里有，或拼 `https://pan.baidu.com/disk/main#/index?category=all&path=%2Fapps%2Fbdpan%2F...`）

### 8. 收尾汇报

- 完成任务 / 失败任务 + 输出路径 + 失败原因
- 积分消耗（每成片 5 分，余额变动）
- 上传结果：网盘目录 + 在线链接
- 渲染完清理素材目录内生成的 `-output-*` 输出目录（移走备份，保持素材目录干净，下次复用）

## 红线

- **参数读已保存设置，不重新设置**：渲染参数（位置/字体/字号/行宽/批计划/素材段时长/visual 范围/creative overlay）必须来自 `qianchuan-settings.json`。enqueue 只覆盖 product / copy-file / sceneSourceType，不碰其他
- 素材目录必须先清理输出子文件夹，否则 scan 误判分组（报"只识别到 1 组"）
- 平铺 IMG 素材必须 `sceneSourceType: image-prefix` + `imagePrefixMode: first-three-digits`，auto 在平铺目录归 1 组必失败
- 文案必须用独立 `[]` 行分隔（dongtu-wenan 输出格式），同 `copyDelimiter` 一致；分隔符拼在一行会被当 1 条 caption
- 素材目录必须绝对路径，不解析别名/相对路径
- `qianchuan-clear` 会清掉整个动图AI 队列：先 `qianchuan-tasks` 确认没有别人的任务再清
- **app 重启 = 任务全灭，积分照扣**（2026-08-16 实测，与桌拍同坑）：app 重启（PID 变更）清空任务列表，已渲染成片不落盘。提交前 + 等待中定期 `studio_status` 看 PID，PID 变了立即停止等待，重跑前先跟老大确认积分成本
- 积分：每成片 5 分（50 篇 = 250 分）；失败/中断不退款
- 百度网盘上传：bdpan 未登录不传；远端路径只能在 `/apps/bdpan/` 范围内；只传成功任务；不读/不输出 `~/.config/bdpan/config.json` 里的 Token

## 兜底：MCP 工具可用时的等价调用

当前会话若加载了 app MCP（methods 含 `qianchuan.enqueue` 等），可用 MCP 等价工具：

| CLI | MCP |
|-----|-----|
| `qianchuan-scan` | `qianchuan.scenes.scan` |
| `qianchuan-enqueue` | `qianchuan.enqueue` |
| `qianchuan-start-queue` | `qianchuan.queue.start` |
| `qianchuan-tasks` / `qianchuan-task` | `qianchuan.tasks.list` / `qianchuan.task.wait` |
| `qianchuan-clear` | `qianchuan.queue.clear` |
| `qianchuan-concurrency` | `qianchuan.queue.concurrency` |

参数语义一致：enqueue 传 `options` 对象（`sceneSourceType`/`imagePrefixMode`），渲染参数仍走已保存设置。

## 参考

- 动图文案生成：`dongtu-wenan` skill（写文案 + 卡审）
- 百度网盘上传：`baidu-drive` skill（bdpan 官方 CLI）
- 实测批次：2026-08-14 六商品 × 50 篇 = 300 成片（2026-08-16 跑通）
  - 分组数（image-prefix first-three-digits）：伊风 7、素说美丽 7、碌柚叶 7、凸凸兔 14、Haa 11、烙色 12
  - 成片：竖屏 1440x1920、单段 ~1.85s（sceneSegmentDuration=2 含 trim）、字幕右上角 top-right
  - 输出：`<素材目录名>-output-YYYYMMDD-HHMMSS/`，按已保存批计划分 第1批~第5批（10×5）
  - 积分：每成片 5 分，300 成片扣 300 分；余额变动参考 app `studio_status`
  - 网盘：`动图成片/<商品名>成片/` 6 目录，300 成片全部上传核对通过
  - **经验**：5 商品并行 enqueue 渲染时 caption 阶段明显变慢（单任务 50 个 ~2 分钟，5 并行 caption 约 4 倍慢）；批量提交前先把素材目录输出清干净，否则多任务并发时第一个任务 auto scan 会误吞别的任务输出目录
