#!/usr/bin/env python3
"""把 zhuopai-daihuo 产出的 txt（多篇用 --- 分隔）拆成逐篇文件。

用法:
    python3 split_copy.py <输入.txt> [输出目录]

输出目录默认 = 输入文件同目录下的 <文件名>.split/
产物: 01.txt 02.txt ... 每篇一条成片脚本。输出 .txt 清单到控制台。
"""
import os
import re
import sys


def split_copy(text: str) -> list[str]:
    """按 --- 分隔符拆文案，去掉多余空行，保留每篇完整正文。"""
    # 兼容 ---、---\n、纯 --- 行；拒绝出现在文案内部的短横线串误伤（只认行首孤立分隔线）
    parts = re.split(r"(?m)^\s*---\s*$", text)
    cleaned = []
    for part in parts:
        lines = [ln.rstrip() for ln in part.split("\n")]
        # 去掉开头的 zhuopai-daihuo 可能的序号/分隔噪音
        while lines and not lines[0].strip():
            lines.pop(0)
        while lines and not lines[-1].strip():
            lines.pop()
        body = "\n".join(lines).strip()
        if body:
            cleaned.append(body)
    return cleaned


def main() -> None:
    if len(sys.argv) < 2:
        print("用法: python3 split_copy.py <输入.txt> [输出目录]", file=sys.stderr)
        sys.exit(1)
    src = os.path.abspath(sys.argv[1])
    if not os.path.isfile(src):
        print(f"输入文件不存在: {src}", file=sys.stderr)
        sys.exit(1)
    with open(src, encoding="utf-8") as f:
        text = f.read()

    pieces = split_copy(text)
    if not pieces:
        print(f"未拆出任何文案（确认文件里有 --- 分隔的多篇，或直接单篇）: {src}", file=sys.stderr)
        sys.exit(1)

    out_dir = os.path.abspath(sys.argv[2]) if len(sys.argv) >= 3 else src + ".split"
    os.makedirs(out_dir, exist_ok=True)
    written = []
    for i, piece in enumerate(pieces, 1):
        out_path = os.path.join(out_dir, f"{i:02d}.txt")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(piece + "\n")
        written.append(out_path)
        print(f"{i:02d}.txt  {len(piece)}字  {out_path}")
    print(f"\n共 {len(pieces)} 篇 → {out_dir}")


if __name__ == "__main__":
    main()
