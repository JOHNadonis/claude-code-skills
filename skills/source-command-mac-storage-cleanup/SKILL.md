---
name: source-command-mac-storage-cleanup
description: "macOS 存储空间诊断、清理与迁移。扫描空间占用大户，清理缓存，迁移大数据到外置硬盘（symlink），查找已卸载 App 的孤儿数据。当用户说\"清理存储\"\"清理内存\"\"存储空间不够\"\"磁盘满了\"\"空间不足\"\"电脑卡了清理一下\"\"Mac清理\"\"存储空间快用完了\"等存储相关自然语言时触发。"
---

# source-command-mac-storage-cleanup

Use this skill when the user asks to run the migrated source command `mac-storage-cleanup`.

## Command Template

# Mac Storage Cleanup — macOS 存储空间清理与迁移

一站式诊断 Mac 存储空间问题，提供清理、迁移、孤儿数据扫描全流程。

## Usage

```
/mac-storage-cleanup
/mac-storage-cleanup /Volumes/MyDrive
```

---

## Workflow

### Phase 0: 环境检测

1. 检查磁盘状态：
   ```bash
   df -h /
   df -h /Volumes/*
   ```
2. 如果用户提供了外置硬盘路径，验证其可写性和剩余空间
3. 如果没提供，列出可用的外置硬盘让用户选择

### Phase 1: 空间诊断 — 找出空间被谁吃了

并行扫描以下目录，按大小降序排列：

```bash
# 1. 用户主目录大文件夹
du -sh ~/Library/Application\ Support ~/Library/Caches ~/Library/Containers ~/Library/Group\ Containers ~/Downloads ~/Desktop ~/Documents ~/Movies ~/Music ~/Pictures 2>/dev/null | sort -rh

# 2. Application Support 详细（>100MB）
find ~/Library/"Application Support" -maxdepth 1 -type d -exec du -sh {} + 2>/dev/null | sort -rh | head -20

# 3. Containers 详细（>100MB）
find ~/Library/Containers -maxdepth 1 -type d -exec du -sh {} + 2>/dev/null | sort -rh | head -20

# 4. Caches 详细
du -sh ~/Library/Caches/*/ 2>/dev/null | sort -rh | head -15

# 5. 应用程序本体
du -sh /Applications/*/ 2>/dev/null | sort -rh | head -15

# 6. 开发工具链
du -sh ~/.npm ~/.nvm ~/.bun ~/.cargo ~/.rustup ~/.local ~/.docker ~/.cache ~/.Codex 2>/dev/null | sort -rh

# 7. Apple 航拍壁纸（macOS Sonoma+ 的隐藏大户）
du -sh ~/Library/Application\ Support/com.apple.wallpaper/aerials/ 2>/dev/null
```

输出**空间占用排行榜**，标注每项的类型（缓存/应用数据/系统数据/开发工具）。

### Phase 2: 分类与方案制定

将所有大项（>200MB）分为四类，制定操作方案：

| 类型 | 操作 | 说明 |
|------|------|------|
| **缓存** | 直接清理 | Caches 目录、npm/pip 缓存等，应用会自动重建 |
| **应用数据** | symlink 迁移到外置硬盘 | 飞书、Chrome、音乐等大型 App 数据 |
| **孤儿数据** | 直接删除 | 已卸载 App 的残留数据 |
| **系统数据** | 建议/跳过 | Apple 壁纸等，告知用户选择 |

**输出清理方案表格**，包含每项的操作、预计释放空间，让用户确认后再执行。

### Phase 3: 孤儿数据扫描 — 找出已卸载 App 的残留

**关键安全步骤 — 必须扫描全部 App 安装路径：**

```bash
# macOS App 可以存在于以下所有位置，必须全部扫描！
# 1. /Applications/
# 2. /Library/Input Methods/         （输入法）
# 3. /Library/PreferencePanes/       （系统设置面板）
# 4. /Library/Audio/Plug-Ins/        （音频插件）
# 5. /Library/Screen Savers/         （屏幕保护）
# 6. /Library/QuickLook/             （Quick Look 插件）
# 7. ~/Applications/                 （用户级应用）
# 8. mdfind 全局兜底搜索
```

对每个 Application Support / Containers / Caches 中的大目录：

1. **全路径扫描**：在上述所有路径中搜索对应 App
2. **进程检查**：`ps aux | grep` 确认是否在运行
3. **双重确认**：只有「全路径都找不到 + 进程也不在」才标记为孤儿

```bash
# 判断 App 是否存在的完整检查函数逻辑
for app_name in <目标列表>; do
  # 搜索所有安装路径
  found=$(find /Applications /Library/Input\ Methods ~/Applications \
    /Library/PreferencePanes /Library/Screen\ Savers /Library/QuickLook \
    -maxdepth 2 -iname "*${app_name}*" 2>/dev/null | head -1)
  # mdfind 兜底
  [ -z "$found" ] && found=$(mdfind "kMDItemKind == 'Application'" 2>/dev/null | grep -i "$app_name" | head -1)
  # 进程检查
  running=$(ps aux | grep -i "$app_name" | grep -v grep)
  # 判定
  if [ -z "$found" ] && [ -z "$running" ]; then
    echo "ORPHAN: $app_name"
  fi
done
```

**输出孤儿清单**，让用户逐项确认后再删除。

### Phase 4: 执行清理

#### 4a. 缓存清理（安全，直接执行）

```bash
rm -rf ~/Library/Caches/<目标缓存目录>/*
npm cache clean --force  # 如果有 npm
```

#### 4b. Symlink 迁移（需要外置硬盘）

对每个要迁移的目录，严格按以下顺序执行：

1. **检查 App 是否在运行** — 运行中则提醒用户先退出
2. **创建目标目录**：`mkdir -p <外置硬盘>/mac-app-data/`
3. **rsync 复制**：`rsync -ah <源>/ <目标>/`
4. **验证完整性**：对比文件数和总大小
5. **替换为 symlink**：`rm -rf <源> && ln -s <目标> <源>`
6. **验证 symlink**：`ls -la <源>` 确认指向正确

#### 4c. 孤儿数据清理（需用户确认）

- 删除内置 SSD 上的孤儿目录
- 如果有已迁移到外置的孤儿数据，一并清理 + 删除无效 symlink

### Phase 5: 结果报告

输出最终报告：

```
| 指标 | 清理前 | 清理后 |
|------|--------|--------|
| 内置 SSD 剩余 | X GB | Y GB |
| 外置硬盘剩余 | X GB | Y GB |
| 总释放空间 | — | Z GB |

有效 symlink 清单：
- App名 → 外置硬盘路径

已清理孤儿数据：
- App名 (大小)
```

---

## Safety Rules — 安全红线

1. **绝不自动删除**：所有删除操作必须先列清单，等用户确认
2. **全路径扫描**：判断 App 是否存在时，必须扫描 `/Applications/`、`/Library/Input Methods/`、`/Library/PreferencePanes/`、`~/Applications/` 等全部路径 + `mdfind` 兜底 + 进程检查。**绝不能只搜 /Applications/**
3. **进程即存在**：如果 `ps aux` 发现相关进程在运行，无论在哪个目录都找不到 .app，也必须判定为「已安装」，不可删除
4. **迁移前验证**：rsync 后必须对比文件数和大小，不一致则中止
5. **宁漏勿误**：任何一步存疑，跳过该条目，不可冒险删除
6. **外置硬盘依赖提醒**：迁移完成后必须告知用户——外置硬盘拔掉后相关 App 会无法使用
