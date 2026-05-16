---
name: research-paper
description: Human-in-the-loop 学术论文研究系统。6 阶段流水线：选题 → 数据工程 → 计量分析 → 论文写作 → 评审 → 修改。支持 CSV/Excel/Stata 数据集，生成完整学术论文。
user_invocable: true
triggers:
  - /research-paper
  - 写论文
  - 研究分析
  - 做一篇论文
  - research paper
  - 学术研究
---

# Research Paper Pipeline — 学术论文研究系统

## 核心定位

Human-in-the-loop 实证研究论文生成系统。6 阶段流水线，Codex 负责选题、写作、评审、改写（AI 推理），Python 脚本负责数据扫描、计量回归、机械审查（计算密集型）。人在关键节点把关，机器执行标准化流程。

## 使用方式

```
/research-paper                           # 启动交互式流程
写一篇关于教育回报率的论文，数据在 ~/data/chns.csv
研究分析：收入不平等，用 ~/datasets/cfps.dta
```

**用户需要提供**：
1. 研究方向（一句话描述感兴趣的领域/话题）
2. 数据集路径（CSV/Excel/Stata .dta 文件）

**可选**：
- 具体研究假设
- 偏好的计量方法
- 论文语言（默认英文）

## 架构总览

```
用户: 研究方向 + 数据集路径
       │
       ▼
┌──────────────────────┐
│  Phase 1: 选题        │  data_profiler.py → Codex 生成 4-5 选题
└──────┬───────────────┘
       ▼
  ★ Human Gate (必选)     用户选题
       │
       ▼
┌──────────────────────┐
│  Phase 2: 数据工程     │  Codex 设计变量 + 写 regression_spec.json
└──────┬───────────────┘
       ▼
┌──────────────────────┐
│  Phase 3: 计量分析     │  econometrics.py 执行回归
└──────┬───────────────┘
       ▼
┌──────────────────────┐
│  Phase 4: 论文写作     │  Codex 撰写完整论文
└──────┬───────────────┘
       ▼
┌──────────────────────┐
│  Phase 5: 评审        │  review_scorer.py + Codex 定性打分
└──────┬───────────────┘
       ▼
  < 7分 且 < 3轮 ──→ Phase 6: 改写 ──→ 回到 Phase 5
       │
  ≥ 7分 或 = 3轮
       ▼
  输出终稿 + 附件
```

## Phase 0: 初始化

1. 确认用户提供了研究方向和数据集路径
2. 如果缺少任一项，询问用户补充
3. 创建工作目录：

```bash
WORK_DIR="/tmp/research-work-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$WORK_DIR"
```

4. 确定脚本目录：`SKILL_DIR` 为本 skill 所在目录（`~/.Codex/skills/research-paper`）

## Phase 1: 选题 (Topic Generation)

### 1.1 数据扫描

运行 data_profiler.py 扫描用户数据集：

```bash
uv run "$SKILL_DIR/scripts/data_profiler.py" \
  --input "$DATA_PATH" \
  --output "$WORK_DIR/data_profile.json"
```

读取输出的 `data_profile.json`，理解数据集包含的变量、面板结构、数据质量。

**如果脚本报错**（文件不存在、格式无法解析、空数据集）：
- 向用户报告错误
- 建议修正（检查路径、文件格式、编码）
- 等用户提供修正后的路径，重试

### 1.2 生成选题

基于数据画像 + 用户描述的研究方向，生成 **4-5 个可行研究选题**。每个选题包含：
- 标题（中英双语）
- 一句话研究问题
- 拟用的因变量和核心自变量（从数据画像中选取）
- 预期贡献（为什么这个选题有价值）

**选题必须和数据匹配**。不要提出数据集无法支撑的选题。重点检查：
- 因变量和核心自变量在数据中是否存在
- 是否有足够的变异（不是常量列）
- 缺失值比例是否可接受

### 1.3 ★ Human Gate — 用户选题（必选）

以编号列表呈现选题，请用户选择：

```
请选择一个研究方向（输入编号）：

1. Marriage Dissolution and Gender Income Gap / 婚姻解体与性别收入差距
   - 研究问题：离婚对女性收入的因果效应
   - 核心变量：income (Y) ← marital_status (X), 控制 education, age
   - 价值：填补中国语境下的实证空白

2. ...

3. ...

4. ...

5. ...
```

等用户回复编号后继续。

## Phase 2: 数据工程 (Data Engineering)

### 2.1 变量设计

基于选定主题和数据画像，设计完整的变量体系：

- **因变量 (Y)**：明确定义，说明是否需要对数变换
- **核心自变量 (X)**：与研究假设直接相关的解释变量
- **控制变量 (Controls)**：文献中常用的混淆因素
- **工具变量 (IV)**：如果计划做 2SLS，说明工具变量及其合理性
- **固定效应**：个体/时间固定效应的选择

### 2.2 模型规划

设计 regression_spec.json 并写入 `$WORK_DIR/regression_spec.json`。包括：

- **基准模型** (baseline_ols)：最简单的 OLS 回归
- **面板模型** (panel_fe/panel_re)：如果数据有面板结构
- **工具变量模型** (iv_2sls)：如果内生性是核心关注
- **稳健性检验** (robustness)：子样本、替代因变量、替代度量
- **诊断检验** (diagnostics)：Hausman、VIF、BP 异方差
- **变量变换** (transformations)：对数化、平方项、虚拟变量

regression_spec.json 格式：

```json
{
  "models": [
    {
      "name": "baseline_ols",
      "type": "ols",
      "dependent": "log_income",
      "independent": ["education_years", "age", "age_sq", "female"],
      "controls": ["province_dummies"],
      "robust_se": true,
      "cluster_var": null
    },
    {
      "name": "panel_fe",
      "type": "panel_fe",
      "dependent": "log_income",
      "independent": ["education_years", "health_score"],
      "entity_var": "indid",
      "time_var": "wave",
      "cluster_var": "hhid"
    },
    {
      "name": "iv_2sls",
      "type": "iv_2sls",
      "dependent": "log_income",
      "endogenous": ["education_years"],
      "instruments": ["parent_education", "school_distance"],
      "exogenous": ["age", "female"],
      "entity_var": "indid",
      "time_var": "wave"
    }
  ],
  "robustness": [
    {
      "name": "subsample_urban",
      "base_model": "baseline_ols",
      "filter": "urban == 1"
    },
    {
      "name": "alternative_dep",
      "base_model": "baseline_ols",
      "dependent_override": "income_rank"
    }
  ],
  "diagnostics": ["hausman", "vif", "breusch_pagan", "durbin_wu_hausman"],
  "transformations": {
    "log_income": "np.log(income + 1)",
    "age_sq": "age ** 2",
    "province_dummies": "C(province)"
  }
}
```

### 2.3 ☆ Human Gate — 变量确认（可选）

向用户展示规划的变量和模型设计摘要。如果用户之前说过"直接做""你看着办"等，跳过此步。

## Phase 3: 计量分析 (Econometric Analysis)

### 3.1 执行回归

```bash
uv run "$SKILL_DIR/scripts/econometrics.py" \
  --data "$DATA_PATH" \
  --spec "$WORK_DIR/regression_spec.json" \
  --output "$WORK_DIR/regression_results.json"
```

### 3.2 解读结果

读取 `regression_results.json`，做以下分析：

1. **核心发现**：主要系数的方向、大小、显著性
2. **诊断解读**：Hausman 检验 → FE vs RE 选择；VIF → 多重共线性；BP 检验 → 异方差
3. **稳健性判断**：子样本/替代变量下结果是否稳定
4. **局限性识别**：哪些方面仍有不足

### 3.3 异常处理

**所有模型失败**：
- 展示错误信息
- 分析可能原因（完全多重共线性、方差为零、样本不足）
- 重新设计更简单的 regression_spec.json（先跑单变量 OLS）
- 最多重试 2 次。仍失败则中止，输出诊断报告

**部分模型失败**：
- 用成功的模型继续
- 在论文中注明尝试过但失败的模型

**结果全部不显著**（p > 0.10）：
- 这是有效的研究发现（null result）
- 论文框架调整为"无效应的证据"
- 询问用户："结果显示无显著效应。继续写 null-result 论文，还是调整选题？"

## Phase 4: 论文写作 (Paper Writing)

撰写完整学术论文，保存为 `$WORK_DIR/paper.md`。

### 论文结构（必选章节）

```markdown
# [论文标题]

## Abstract
[250 词摘要：研究问题、方法、数据、核心发现、贡献]

## 1. Introduction
[1000-1500 词：研究背景、研究问题、重要性、方法概述、核心发现预告、论文结构]

## 2. Literature Review
[800-1200 词：相关文献综述、研究空白、本文贡献定位]

## 3. Data and Methodology
### 3.1 Data
[数据来源、样本描述、变量定义与描述性统计]
### 3.2 Empirical Strategy
[计量模型设定、识别策略、内生性讨论]

## 4. Empirical Results
### 4.1 Baseline Results
[基准回归结果、系数解读]
### 4.2 [其他模型结果]
[面板/IV 结果]

## 5. Robustness Checks
[稳健性检验结果]

## 6. Conclusion
[400-600 词：核心发现总结、政策含义、局限性、未来研究方向]

## References
[参考文献列表]
```

### 写作规范

- **学术语气**：正式、客观、精确
- **嵌入回归表**：直接使用 regression_results.json 中的 ASCII 回归表
- **引用规范**：在正文中引用描述性统计数据和回归系数时，数值必须与 regression_results.json 一致
- **参考文献**：生成合理的参考文献（基于研究领域的经典和前沿文献）
- **总字数**：5000-8000 词

## Phase 5: 评审 (Review)

### 5.1 机械检查

```bash
uv run "$SKILL_DIR/scripts/review_scorer.py" \
  --paper "$WORK_DIR/paper.md" \
  --regression-results "$WORK_DIR/regression_results.json" \
  --output "$WORK_DIR/review_mechanical.json"
```

读取 `review_mechanical.json`，获取章节完整性、字数、系数一致性等机械检查结果。

### 5.2 定性评审

基于论文内容和回归结果，对 5 个维度逐一评分（1-10 分）：

#### 维度 1: Novelty / 新颖性
| 分数 | 标准 |
|------|------|
| 9-10 | 原创研究问题，前人未探索，真正的新洞察 |
| 7-8 | 有意义地扩展现有研究，新角度 |
| 5-6 | 标准问题但应用于新语境 |
| 3-4 | 大部分是复制，微小变化 |
| 1-2 | 纯复制，无新贡献 |

#### 维度 2: Causal Identification / 因果识别
| 分数 | 标准 |
|------|------|
| 9-10 | 干净的自然实验或 RCT；内生性令人信服地解决 |
| 7-8 | Panel FE + IV，合理的工具变量；内生性被讨论和部分解决 |
| 5-6 | Panel FE 无 IV；承认内生性但解决有限 |
| 3-4 | 仅 OLS + 控制变量；提及但未解决内生性 |
| 1-2 | 朴素 OLS；未讨论因果 vs 相关 |

#### 维度 3: Data Fitness / 数据适配性
| 分数 | 标准 |
|------|------|
| 9-10 | 数据集完美匹配研究问题；大样本、丰富变量、面板结构 |
| 7-8 | 良好匹配；足够观测值；大部分需要的变量可用 |
| 5-6 | 可接受但有明显缺口（缺少关键控制、有限时期） |
| 3-4 | 勉强匹配；大量缺失数据或需要代理变量 |
| 1-2 | 数据集不适合该研究问题 |

#### 维度 4: Writing Quality / 写作质量
| 分数 | 标准 |
|------|------|
| 9-10 | 可发表水平；逻辑清晰、语言精准、论证结构好 |
| 7-8 | 强初稿；小的语言/流程问题；各节连贯 |
| 5-6 | 可接受；部分节需要重组或更清晰的阐述 |
| 3-4 | 清晰度问题显著；节间缺乏逻辑连接 |
| 1-2 | 混乱；论证不清 |

#### 维度 5: Robustness / 稳健性
| 分数 | 标准 |
|------|------|
| 9-10 | 3+ 稳健性检验；结果在所有规格下稳定；包含安慰剂检验 |
| 7-8 | 2-3 个稳健性检验；主要结果成立；注意到微小敏感性 |
| 5-6 | 1-2 个稳健性检验；对规格有些敏感 |
| 3-4 | 最少的稳健性检验；结果脆弱 |
| 1-2 | 无稳健性检验 |

### 5.3 通过判定

```
综合评分 = mean(novelty, causal_id, data_fitness, writing, robustness)
```

判定规则：
- `综合评分 >= 7.0` 且所有单项 >= 4 → **通过** → 输出终稿
- `综合评分 < 7.0` 且 `当前轮次 < 3` → **不通过** → 进入 Phase 6
- `当前轮次 = 3` → **强制通过** → 输出终稿 + 标注"最大修改轮次已达"

输出评审报告格式：

```
📊 评审结果（第 N 轮）

| 维度 | 得分 | 评语 |
|------|------|------|
| Novelty | 7 | ... |
| Causal ID | 5 | ... |
| Data Fitness | 8 | ... |
| Writing | 6 | ... |
| Robustness | 7 | ... |

综合评分: 6.6 / 10
阈值: 7.0
判定: ❌ 未通过 → 进入修改（第 N+1 轮）
薄弱环节: Causal ID (5), Writing (6)
```

## Phase 6: 改写 (Rewrite)

### 6.1 针对性修改

识别得分最低的 2 个维度，针对性改写：

- **Causal ID 低**：加强识别策略讨论、增加内生性论证、考虑增加 IV 模型
- **Writing 低**：改善论证逻辑、加强节间过渡、提升语言质量
- **Robustness 低**：增加稳健性检验、补充子样本分析
- **Novelty 低**：加强贡献阐述、突出与现有文献的差异
- **Data Fitness 低**：更好地论证数据选择的合理性、补充描述性统计

更新 `$WORK_DIR/paper.md`。

### 6.2 循环控制

`round_number += 1`，回到 Phase 5 重新评审。

## 输出终稿

通过评审后（或达到 3 轮上限），执行以下操作：

1. 展示论文摘要和评审轨迹：

```
✅ 论文完成！

标题: Education Returns in Rural China: Evidence from CHNS
总字数: 6,500
评审轮次: 2
最终评分: 7.4 / 10
评分轨迹: 4.2 → 7.4

文件已保存:
  📄 论文: $WORK_DIR/paper.md
  📊 回归结果: $WORK_DIR/regression_results.json
  📋 数据画像: $WORK_DIR/data_profile.json
  📝 评审记录: $WORK_DIR/review_mechanical.json
```

2. 询问用户是否需要复制到指定目录（默认 `./output/`）

## 错误处理手册

| 场景 | 触发条件 | 处理 |
|------|----------|------|
| 数据文件无法读取 | data_profiler.py 报错 | 报告错误，建议修正，等用户重试 |
| 变量不足以支撑选题 | 选题后发现核心变量不存在 | 回到 Phase 1.3 换题 |
| 所有回归模型失败 | econometrics.py 零成功 | 简化模型重试（最多 2 次），仍失败则中止 |
| 部分模型失败 | 部分模型有错误 | 用成功模型继续，论文中注明 |
| 结果全部不显著 | 所有 p > 0.10 | 确认用户意愿：null result 论文 or 换题 |
| 评分卡在阈值下 | 3 轮后仍 < 7 分 | 输出 best-effort 版本，标注薄弱环节 |
| uv/Python 依赖安装失败 | 网络问题 | 报告错误，建议手动安装 |

## 使用示例

### 示例 1：教育回报率研究
```
用户: 写一篇关于教育回报率的论文，数据在 ~/data/chns_2018.csv
Codex: [运行 data_profiler.py] → [展示 5 个选题] → [用户选 2 号]
       → [设计变量 + 模型] → [运行回归] → [写论文] → [评审 4.2 分]
       → [改写] → [评审 7.8 分] → [输出终稿]
```

### 示例 2：性别工资差距研究
```
用户: 研究分析：性别工资差距，用 ~/datasets/cfps_panel.dta
      我想重点看婚姻状态的调节效应
Codex: [扫描数据] → [围绕婚姻调节效应生成选题]
       → [用户选题] → [设计交互项模型] → [执行] → [写作] → [评审循环]
```

### 示例 3：使用命令触发
```
用户: /research-paper
Codex: 请提供以下信息：
       1. 研究方向（一句话描述）
       2. 数据集文件路径
```
