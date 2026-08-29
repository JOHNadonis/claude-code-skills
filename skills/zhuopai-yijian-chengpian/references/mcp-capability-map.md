# 抖音短视频素材快剪工厂 MCP 能力地图（v1.3.2）

记录当前 MCP 能力边界，供 skill 维护对照。MCP 更新时同步改这里。

## 软件能力 vs MCP 暴露

| 桌面 UI 动作 | MCP/CLI | 说明 |
|--------------|---------|------|
| 填商品链接 | ✅ options.productUrl | 进文案上下文；等同关联，不依赖绑定 |
| 关联商品（绑定文件） | 不需要 | 只是写 auto-mix-product-link.json，渲染不读 |
| 获取商品详情图 | ✅ auto_mix.product_details.fetch | 下载主图+详情图到 ~/Pictures，AI 生成商品卖点.md/json（2026-08-16 上线） |
| 生成商品策略 | ✅ auto_mix.product_details.fetch 附带 | 返回 productFacts（AI 识图提取核心卖点/适用人群/钩子），productFacts 字段可进 enqueue options |
| 勾选插入详情页图 | ✅ options.productDetailMixEnabled + productDetailSelectedFiles | 需 productEvidenceDirectory + 相对路径；日志 `[detail-image] 已加载 N 张` |
| 选分镜素材文件夹 | ✅ scan_product_materials / productRoot | |
| AI 读分镜素材 | ✅ analyze_product_vision | 预分析可选，任务内也会自动 |
| 匹配成片 | ✅ enqueue_auto_mix + wait | |
| 打开输出目录 | ✅ open_studio_output | |

## Agent 通道完整 method 清单（app.status 实测，v1.3.2，2026-08-16）

- app.status
- qianchuan.*：settings.get / scenes.scan / tasks.list / enqueue / queue.start / queue.clear / queue.concurrency / task.wait / task.stop / task.retry
- auto_mix.*：scan / vision.analyze / settings.get / sound_effects.list / tasks.list / enqueue / queue.start / queue.clear / task.wait / task.stop / task.retry
- auto_mix.product_link.bind（写绑定文件，等同关联）
- auto_mix.product_details.fetch（2026-08-16 上线：下载详情图+生成卖点）
- auto_mix.product_detail_images.list / select（查看/勾选详情图）
- system.open_path

## 关键实现事实（源码验证 2026-08-15 / 实测 2026-08-16）

- enqueue_auto_mix 的 options 是 z.record(string, unknown) 全透传 → 桌面 UI 的全部表单字段都能塞进 options 生效
- 渲染消费：productDetailMixEnabled / productDetailSelectedFiles / productEvidenceDirectory / productFacts / productUrl / manualScriptFile（imported 模式）
- normalizeImportedNarration：imported 整段 = 一个成片，**不自动按 --- 拆** → skill 必须拆 txt
- 关联绑定文件 auto-mix-product-link.json 渲染流程不读，纯 UI 状态

## 详情图功能（2026-08-16 已上线）

- `fetch_auto_mix_product_details(productRoot, productUrl)`：绑定商品 → 下载主图+详情图到 `~/Pictures/<商品名>（商品ID）/`，AI 生成 `商品卖点.md/json`，返回 enqueueOptions（含 productEvidenceDirectory + productDetailSelectedFiles + productFacts）
- 插入详情图：enqueue options 传 `productEvidenceDirectory` + `productDetailMixEnabled:true` + `productDetailSelectedFiles`（相对 evidence 目录路径）
- 验证：渲染日志 `[detail-image] 已加载 N 张商品详情图，由豆包按口播语义插入中段画面`
- 待探索：productFacts / includeDetail 是否可作为 enqueue 明面参数直接传（当前 fetch 返回的 enqueueOptions 已含 productFacts 字段）
