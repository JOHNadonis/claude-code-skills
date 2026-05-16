---
name: source-command-md2docx
description: "将 Markdown 文件转换为 Word (.docx) 文档。当用户说\"转成 Word\"\"转成文档\"\"导出 docx\"\"生成 Word\"\"转成 doc\"，或在保存/生成 Markdown 文件后要求转换时触发。也可直接传入文件路径进行转换。"
---

# source-command-md2docx

Use this skill when the user asks to run the migrated source command `md2docx`.

## Command Template

# Markdown to DOCX — Markdown 转 Word 文档

将 Markdown 文件转换为格式良好的 Word (.docx) 文档。

## Usage

```
/md2docx                              # 转换最近生成的 .md 文件
/md2docx ~/notes/my-article.md        # 转换指定文件
/md2docx ~/notes/*.md                 # 批量转换
```

---

## Workflow

### Step 1: 确认转换工具

```bash
which pandoc || echo "需要安装 pandoc：brew install pandoc"
```

如果 pandoc 未安装，执行 `brew install pandoc` 安装。

### Step 2: 确定要转换的文件

- **如果用户提供了文件路径**：直接使用该路径
- **如果没有提供路径**：查找当前对话中最近生成/保存的 .md 文件
- **如果都没有**：扫描当前目录和 ~/notes/ 下最近修改的 .md 文件，让用户选择

### Step 3: 执行转换

```bash
# 单文件转换
pandoc <input.md> -o <input.docx>

# 带目录的长文档
pandoc <input.md> --toc -o <input.docx>

# 带自定义样式（如果用户有 reference.docx）
pandoc <input.md> --reference-doc=<reference.docx> -o <input.docx>
```

转换规则：
- 输出文件名 = 输入文件名，扩展名改为 `.docx`
- 输出路径 = 与输入文件相同目录
- 如果 .md 文件超过 2000 字，自动加 `--toc` 生成目录

### Step 4: 验证并报告

```bash
ls -lh <output.docx>
```

输出转换结果：
```
✓ 已转换：<input.md> → <output.docx> (文件大小)
```

---

## 自动触发规则

当本 Skill 被 Codex 识别到以下场景时，应主动建议或自动执行转换：

1. **用户明确要求**：「转成 Word」「导出 docx」「转成文档」
2. **用户传入文件路径**：「把 xxx.md 转成 docx」
3. **批量转换**：「把 notes 目录下所有 md 都转成 docx」

---

## Notes

- 依赖 `pandoc`（通过 Homebrew 安装：`brew install pandoc`）
- 支持 Markdown 中的表格、代码块、图片引用、脚注等格式
- 如果用户有自定义 Word 模板（reference.docx），可以通过 `--reference-doc` 参数应用样式
