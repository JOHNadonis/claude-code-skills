---
name: zhuopai-yijian-chengpian
description: 抖音桌拍带货一键成片。配合 zhuopai-daihuo（文案）+ 抖音短视频素材快剪工厂 MCP（渲染），把写好的 n 篇桌拍文案批量灌入 AI 桌拍自动混剪生成成片。用户提到"桌拍成片"、"一键成片"、"桌拍混剪"、"跑成片"、"把文案做成视频"、"素材渲染"时触发。输入：商品名 + 分镜素材目录 + 文案文件（或调 zhuopai-daihuo 现写），输出：n 个成片视频。
---

# 桌拍带货一键成片

把 zhuopai-daihuo 写好的 n 篇文案，批量交给「抖音短视频素材快剪工厂」的 AI 桌拍渲染成成片视频。

## 前置条件

- 桌面 app「抖音短视频素材快剪工厂」已打开并登录（MCP 依赖它运行）
- MCP 工具可用：`enqueue_auto_mix` / `wait_auto_mix_task` / `list_auto_mix_tasks` / `retry_auto_mix_task` / `scan_product_materials` / `open_studio_output`
- 分镜素材目录是绝对路径，按「子文件夹 = 分镜场景」组织（如 `1.扔进画面/ 6.二合一/ 15.挤在手掌/`）
- bdpan CLI 已安装并登录（`bdpan whoami` 返回已登录），成片渲染完上传到百度网盘用

## 工作流程

### 1. 确认输入

收集三样，缺了先问：

| 输入 | 说明 |
|------|------|
| 商品名 | 成片命名和文案上下文用 |
| 分镜素材目录 | 绝对路径，含分镜场景子文件夹 |
| 文案 | 已有 txt 路径，或让 skill 现调 `zhuopai-daihuo` 生成 |
| 商品链接（可选） | 填进任务，进文案上下文，不依赖"关联商品" |

### 2. 校验素材目录

用 `scan_product_materials` 扫描素材目录，确认分镜场景结构存在、有可用的视频素材。返回为空或结构异常时，停下来问老大，不要硬提交。

### 3. 准备文案

- 已有 txt：确认是 zhuopai-daihuo 格式（多篇用 `---` 分隔）。**imported 模式整段文案 = 一个成片**，所以必须拆：运行 `scripts/split_copy.py <txt> <输出目录>` 按 `---` 拆成逐篇文件 `01.txt 02.txt ...`。每篇就是一条成片。
- 现写：调 `zhuopai-daihuo`，拿到 n 篇后按同样方式拆分。

### 4. 提交任务（每篇一个）

对每一篇文案，调用 `enqueue_auto_mix`：

```
productRoot          = 分镜素材目录（绝对路径）
productName          = 商品名
scriptProvider       = "imported"
startImmediately     = false            # 全部排队，最后统一启动
options.manualScript = 单篇文案全文（读 txt 文件内容填进来）
options.manualScriptFile = 单篇 txt 路径（只用于判断扩展名，不读文件内容）
options.productUrl   = 商品链接（如有）
```

> **重要（实际跑坑）**：imported 模式**必须把文案全文放进 `manualScript`**。`manualScriptFile` 只用来判断扩展名（SRT/JSONL 等），**不会读取文件内容**。只传路径会报「导入口播为空」。桌面 UI 是选文件后把内容填进文本域再提交的，等价做法 = 读文件内容 → manualScript。

**关于详情页图**（MCP 已支持，2026-08-16 上线）：先调 `fetch_auto_mix_product_details(productRoot, productUrl)` 自动抓图 → 图落本地 `~/Pictures/<商品名>（商品ID）/`，返回的 enqueueOptions 自带 `productEvidenceDirectory` + `productDetailSelectedFiles` + `productFacts`。提交时 options 里传 `productEvidenceDirectory` + `productDetailMixEnabled: true` + `productDetailSelectedFiles`（相对 evidence 目录的路径）。渲染日志出现 `[detail-image] 已加载 N 张商品详情图，由豆包按口播语义插入中段画面` 即插入成功。**没有确认本地有图时，不要擅自开 productDetailMixEnabled。**

### 5. 启动队列并等待

- 全部入队后调 `start_auto_mix_queue` 统一开跑
- 每个任务用返回的 `task.id` 轮询 `wait_auto_mix_task`（timeoutSeconds 20-30），直到终态（completed / failed / stopped）
- 等待期间不要重复 enqueue 同一个任务

### 6. 上传成片到百度网盘

渲染完成后，把**成功**的成片上传到百度网盘，方便老大直接在网盘里使用。bdpan 权限被隔离在「我的应用数据/bdpan/」内（API 路径 `/apps/bdpan/`），只传成功任务。

- **上传前确认**：`bdpan whoami` 已登录；未登录先跑 `bash .claude/skills/baidu-drive/scripts/login.sh` 引导老大授权（拿授权链接发给老大，收到 32 位授权码后喂 stdin 完成登录）
- **远端目录**：`桌拍成片/<商品名>成片/`（`/apps/bdpan/` 下，命令用相对路径，别用中文"我的应用数据"）
- **步骤**：
  1. 建文件夹：`bdpan mkdir "桌拍成片/<商品名>成片"`（已存在无妨，跳过即可）
  2. 上传：
     - 成片都在一个输出目录时，整目录传：`bdpan upload "<成片输出目录>/" "桌拍成片/<商品名>成片"`（本地目录以 `/` 结尾）
     - 分散或需逐个控制文件名时，单文件传：`bdpan upload "<成片路径>" "桌拍成片/<商品名>成片/<文件名>"`（单文件远端路径**必须是文件名**，禁止 `/` 结尾）
  3. 核对：`bdpan ls "桌拍成片/<商品名>成片"`，确认上传数量 = 成功成片数
- 上传文件名保留成片原名；本地同名可先 `ls` 远端判断是否已存在再传（已存在需问老大覆盖与否）
- 给老大汇报网盘路径 + 在线查看链接（`bdpan ls` 输出里有链接，或拼 `https://pan.baidu.com/disk/main#/index?category=all&path=%2Fapps%2Fbdpan%2F...`）

> bdpan 公共追踪参数（可选，Agent 行为规范）：命令附 `--agentname "myagents" --session-input '<本轮用户原始输入>' --session-id '<会话ID>'`，仅服务质量追踪，省略不报错。

### 7. 收尾汇报

- 完成的任务：用 `open_studio_output` 打开输出目录，汇报成片路径
- 失败的任务：读任务日志，属外部输入问题（素材缺失、文案格式错）就修好再 `retry_auto_mix_task`（原 task.id），不要新建任务
- 给老大一张小结：成功 n 条 / 失败 m 条 + 输出路径 + 失败原因
- 上传结果：网盘目录 `桌拍成片/<商品名>成片/` 已上传 n 个成片 + 在线查看链接

## 红线

- 素材目录必须绝对路径，不解析别名/相对路径
- 同一任务用 task.id 等待，不重复 enqueue
- 未确认本地详情图时，禁止 `productDetailMixEnabled: true`
- 桌面 app 没运行时 MCP 全挂：先 `studio_status` 确认，挂了就提示老大打开 app
- **app 重启 = 任务全灭，积分照扣（2026-08-16 实测）**：app 重启（PID 变更即重启信号）会清空任务列表、终止所有排队/渲染任务，已渲染成片不落盘、不可追回。每个启动任务扣 5 积分，失败/被中断同样扣分且不退款。**提交前 + 等待中定期 `studio_status` 看 PID**，PID 变了立即停止等待（成片已丢，只能重跑，先跟老大确认积分成本）
- **队列是共享的，别误启别人的任务**：app 队列被多个 agent/老大共用（2026-08-16 重启后老大把逐本 10 篇重新入队）。`start_auto_mix_queue` 会启动队列里所有 queued 任务，`start` 前先 `list_auto_mix_tasks`，确认没有非本批次的任务再启动
- 百度网盘上传：bdpan 未登录不传；远端路径只能在 `/apps/bdpan/` 范围内；只传成功任务；不读/不输出 `~/.config/bdpan/config.json` 里的 Token；远端已存在同名文件时不擅自覆盖，先问老大

## 兜底：MCP 工具不可用时用 CLI

如果当前会话没有 MCP 工具，可用桌面 app 自带 CLI（效果等同）。**实测命令是 `--cli enqueue`（不是 auto-mix enqueue，后者 Unknown CLI command，2026-08-18 验证）**：

```
APP="/Applications/抖音短视频素材快剪工厂.app/Contents/MacOS/抖音短视频素材快剪工厂"
"$APP" --cli enqueue "/素材/绝对路径" \
  --product-name "商品名" --script-provider imported \
  --options-json /tmp/opts.json --no-start
```

`/tmp/opts.json` 里放 `{"manualScript": "文案全文（读文件内容）", "manualScriptFile": "/.../01.txt", "productUrl": "https://..."}`。
`--no-start` 入队不启动；全入队后 `"$APP" --cli start-queue`。
等待：`"$APP" --cli tasks` 看列表、`"$APP" --cli task <task-id>` 看日志（日志含原始控制字符，解析 JSON 用 `strict=False`）。
渲染输出：**每任务独立输出目录** `素材目录名-桌拍-YYYYMMDD-HHMMSS[-N]`，每个目录 1 个 mp4（任务编号后缀）。

## 详情图能力（MCP 已上线，2026-08-16）

- `fetch_auto_mix_product_details` 已可用：自动抓详情图 + 生成 productFacts，无需再提示 UI 手动操作
- 详情图插入：`options.productEvidenceDirectory` + `productDetailMixEnabled` + `productDetailSelectedFiles`（fetch 返回的 enqueueOptions 直接带）
- 能力边界同步见 `references/mcp-capability-map.md`
- 待探索：productFacts / includeDetail 作为 enqueue 明面参数直接传的效果
