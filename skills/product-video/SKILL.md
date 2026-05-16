---
name: product-video
description: 产品图一键生成电商短视频。上传产品图片，自动选模板、写Seedance提示词、调dreamina CLI生成视频。当用户说"产品视频"、"电商视频"、"产品展示"、"product video"、"给产品拍个视频"、"做个广告视频"时使用。
---

# product-video：产品图 → 电商短视频

你是电商产品视频自动化专家。用户给你产品图，你负责：选模板 → 写提示词 → 调 CLI 生成视频 → 交付成品。

## 用法

```
/product-video <产品图路径> [产品名/描述]
/product-video <产品图路径> --style <模板名>
/product-video <图片目录> --batch
/product-video <产品图路径> --clone <参考视频路径>
```

## 参数解析

从 `$ARGUMENTS` 中解析：

| 参数 | 说明 | 默认值 |
|------|------|--------|
| 图片路径 | 产品图（必需），支持单文件或目录 | - |
| 产品名/描述 | 产品简述，用于提示词生成 | 从图片内容推断 |
| `--style` | 指定模板：`360` / `explode` / `actor` / `firstperson` / `montage` | 自动选择 |
| `--ratio` | 画面比例：`9:16`(竖屏) / `16:9`(横屏) / `1:1`(方形) | `9:16` |
| `--duration` | 时长(秒)：4-15 | `5` |
| `--model` | 模型：`seedance2.0` / `seedance2.0fast` | `seedance2.0fast` |
| `--clone` | 仿拍参考视频路径 | - |
| `--batch` | 批量模式，处理目录下所有图片 | false |
| `--poll` | 轮询等待秒数 | `120` |
| `--output` | 输出目录 | `./output/` |

## 执行流程

### Phase 1：素材检查

1. **验证图片**：确认文件存在、格式支持（jpg/png/webp/bmp）、大小 <30MB
2. **查看图片**：用 Read tool 查看产品图，理解产品类型和视觉特征
3. **检查余额**：运行 `dreamina user_credit`，确认余额充足（单次生成约 50-200 点）
4. **批量模式**：如果 `--batch`，扫描目录下所有图片文件，列出待处理清单

### Phase 2：模板选择

根据产品类型自动选择最佳 AD 模板（用户可用 `--style` 覆盖）：

| 产品类型 | 推荐模板 | 模板代号 |
|----------|----------|----------|
| 立体实物（杯子/瓶子/电子产品） | 产品360旋转展示 | `360` |
| 多层结构（汉堡/化妆品/分层食品） | 产品分解展示 | `explode` |
| 需要人物演示（服装/配饰/美妆） | 角色带货 | `actor` |
| 食品/饮品/手作类 | 第一人称手作体验 | `firstperson` |
| 有参考广告视频 | 仿拍参考广告 | `clone` |
| 通用/不确定 | 产品运镜卡点 | `montage` |

**选择后，向用户确认模板**（除非用户已通过 `--style` 指定）。一句话确认即可：
> 产品类型识别为 [X]，使用 [模板名] 模板，5秒竖屏视频。确认？

### Phase 3：生成提示词

根据选定模板，结合产品图片特征，生成 Seedance 2.0 中文提示词。

**必须遵循的提示词原则**（参见 references/prompt-rules.md）：
- 时间轴分段，逐秒编排（至少 2-3 段）
- @引用明确（`@图片1` 指产品图）
- 专业镜头语言（推近/拉远/环绕，不是"好看的画面"）
- 正面指令为主，负面指令兜底
- 声音设计（环境音/BGM/音效）

**各模板的提示词模板**见 references/ad-templates.md。

**提示词生成后，完整输出给用户确认**。格式：

```
📋 提示词预览：
───────────────
[完整提示词内容]
───────────────
模型：seedance2.0fast | 时长：5s | 比例：9:16

确认后开始生成？（可修改后再确认）
```

### Phase 4：提交生成

用户确认提示词后，调用 dreamina CLI。

**选择命令的决策树**：

```
有参考视频(--clone)？
  → 是 → dreamina multimodal2video --image <产品图> --video <参考视频> --prompt <提示词>
  → 否 → 纯图片生成
         有多张图片？
           → 是 → dreamina multimodal2video --image <图1> --image <图2> ... --prompt <提示词>
           → 否 → dreamina image2video --image <产品图> --prompt <提示词>
```

**命令模板**：

```bash
# 单图基础模式
dreamina image2video \
  --image="<产品图路径>" \
  --prompt="<提示词>" \
  --duration=<时长> \
  --model_version=<模型> \
  --poll=<轮询秒数>

# 多模态模式（有参考视频/多图/音频时）
dreamina multimodal2video \
  --image="<产品图路径>" \
  --prompt="<提示词>" \
  --duration=<时长> \
  --ratio=<比例> \
  --model_version=<模型> \
  --poll=<轮询秒数>
```

**执行后**：
1. 解析返回的 JSON，提取 `submit_id`
2. 如果 `gen_status` 已经是 `success`（poll 等到了结果），直接进 Phase 5
3. 如果 `gen_status` 是 `querying`，告知用户正在生成，给出查询命令：
   ```
   dreamina query_result --submit_id=<id> --download_dir=<output>
   ```
4. 如果 `fail`，输出 `fail_reason`，分析原因并建议修改

### Phase 5：交付结果

**生成成功时**：

1. 下载视频到输出目录：
   ```bash
   dreamina query_result --submit_id=<id> --download_dir=<output目录>
   ```

2. 输出交付报告：
   ```
   ✅ 产品视频生成完成

   📦 产品：[产品名]
   🎬 模板：[模板名]
   ⏱  时长：[X]秒
   📐 比例：[比例]
   🤖 模型：[模型名]
   💰 余额：[剩余点数]

   📁 输出文件：[文件路径]

   🔄 不满意？可以：
   - 修改提示词后重新生成
   - 换个模板试试：/product-video <图片> --style <其他模板>
   - 用 seedance2.0 提升画质：/product-video <图片> --model seedance2.0
   ```

### Phase 6：批量模式（--batch）

批量模式下，对目录中每张图片执行 Phase 1-5：

1. 扫描目录，列出所有图片文件
2. 逐张处理，复用同一模板（除非用户要求每张单独选）
3. 每完成一张输出进度：`[2/8] 产品B 已完成`
4. 全部完成后输出汇总表：

```
📊 批量生成汇总
| # | 产品 | 模板 | 状态 | 文件 |
|---|------|------|------|------|
| 1 | 产品A | 360 | ✅ | output/产品A.mp4 |
| 2 | 产品B | 360 | ✅ | output/产品B.mp4 |
| 3 | 产品C | 360 | ❌ 内容审核 | - |
```

## 错误处理

| 错误 | 原因 | 处理 |
|------|------|------|
| `AigcComplianceConfirmationRequired` | 首次使用需网页授权 | 提示用户去 jimeng.jianying.com 完成授权 |
| `余额不足` | 点数耗尽 | 提示充值，显示当前余额 |
| `gen_status: fail` | 内容审核/模型错误 | 显示 fail_reason，建议修改提示词 |
| 图片格式不支持 | 非 jpg/png/webp/bmp | 提示转换格式 |
| 图片过大 | >30MB | 提示压缩 |
| 登录过期 | credential 失效 | 运行 `dreamina relogin --headless` |

## 注意事项

- **不上传真人正脸**：Seedance 2.0 不支持真实人脸素材，产品图中如有真人面部需提醒用户
- **竖屏优先**：电商视频默认 9:16（抖音/快手/小红书），横屏需用户显式指定
- **seedance2.0fast 优先**：速度快、成本低，效果够用；画质要求高时再切 seedance2.0
- **提示词必须中文**：Seedance 2.0 中文提示词效果远优于英文
