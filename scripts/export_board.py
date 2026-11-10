# -*- coding: utf-8 -*-
"""从 core/board.py（A 出品）导出前端数据 static/js/board_data.js
================================================================

A 的 board.py 是棋盘拓扑的**唯一真相源**。
A 改了棋盘（点数、连线、坐标），只需要重跑本脚本，前端一行代码都不用动：

    python scripts/export_board.py

导出内容
--------
window.BOARD_LAYOUT = {
  nodeCount    37                    节点数
  cell         72                    一格多少像素（A 坐标系的基准）
  bbox         [0, 0, 408, 648]      画布范围，A 的 coords 已经含边距
  nodes        [[x, y], ...]         37 个像素坐标
  points       [[row, col], ...]     37 个棋盘格坐标（9 行 × 5 列）
  edges        [[i, j], ...]         76 条单位连线
  adj          [[...], ...]          邻接表
  initBoard    [0, 0, ...]           开局数组，1=王(虎) 2=大臣(羊)
  sheepInHand  16                    开局大臣手里还有几只没放
  firstPlayer  1                     先手：1=王(虎) 2=大臣(羊)
  tigerStart   [8, 28]               王的开局点位（下标）
  sheepStart   [...]                 大臣的开局点位（下标）
}
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "core"))

import board as B  # noqa: E402


def build() -> dict:
    spec = B.BOARD_37

    return {
        "nodeCount": len(spec.points),
        "edgeCount": len(spec.edges),
        "cell": int(B.STEP),
        "bbox": [0, 0, int(B.WIDTH), int(B.HEIGHT)],
        "nodes": [[int(x), int(y)] for x, y in spec.coords],
        "points": [[int(r), int(c)] for r, c in spec.points],
        "edges": [[int(i), int(j)] for i, j in spec.edges],
        "adj": [list(int(n) for n in ns) for ns in spec.adj],
        "initBoard": [int(v) for v in spec.initial],
        "sheepInHand": int(B.SHEEP_IN_HAND),
        "firstPlayer": int(B.TIGER),          # A 的 rules.py: Game.player 初始为 TIGER
        "tigerStart": [int(spec.index[p]) for p in B.TIGER_START],
        "sheepStart": [int(spec.index[p]) for p in B.SHEEP_START],
    }


def check(data: dict) -> list:
    """导出前的体检。任何一条不过，前端画出来就是错的。"""
    errs = []

    if data["nodeCount"] != 37:
        errs.append(f"节点数 {data['nodeCount']}，应为 37")
    if data["edgeCount"] != len(data["edges"]):
        errs.append("edgeCount 与实际边数不符")

    used = set()
    for i, j in data["edges"]:
        if i == j:
            errs.append(f"自连边 ({i}, {j})")
        if (i, j) in used or (j, i) in used:
            errs.append(f"重复边 ({i}, {j})")
        used.add((min(i, j), max(i, j)))
        if 0 <= i < data["nodeCount"] and 0 <= j < data["nodeCount"]:
            continue
        errs.append(f"边下标越界 ({i}, {j})")

    for i, ns in enumerate(data["adj"]):
        if not ns:
            errs.append(f"孤立点 {i}")

    if len(data["initBoard"]) != data["nodeCount"]:
        errs.append("开局数组长度不对")
    if data["initBoard"].count(1) != 2:
        errs.append(f"开局王 {data['initBoard'].count(1)} 枚，应为 2")
    total_sheep = data["initBoard"].count(2) + data["sheepInHand"]
    if data["initBoard"].count(2) != 8:
        errs.append(f"开局在场大臣 {data['initBoard'].count(2)} 枚，应为 8")

    for name, k in (("x", 0), ("y", 1)):
        lo = min(p[k] for p in data["nodes"])
        hi = max(p[k] for p in data["nodes"])
        if lo < data["bbox"][k] or hi > data["bbox"][k + 2]:
            errs.append(f"{name} 坐标 {lo}..{hi} 超出 bbox")

    print(f"  节点 {data['nodeCount']}  连线 {data['edgeCount']}  "
          f"在场大臣 {data['initBoard'].count(2)} + 手里 {data['sheepInHand']} = {total_sheep}")
    return errs


def main() -> int:
    data = build()

    print("=== 从 core/board.py 导出 ===")
    errs = check(data)
    if errs:
        print("体检不通过：")
        for e in errs:
            print("  -", e)
        return 1

    out = ROOT / "static" / "js" / "board_data.js"
    body = json.dumps(data, ensure_ascii=False, indent=2)
    out.write_text(
        "/* 自动生成，请勿手改。\n"
        " * 数据来源：core/board.py（A 出品）\n"
        " * 重新生成：python scripts/export_board.py\n"
        " */\n"
        "window.BOARD_LAYOUT = " + body + ";\n",
        encoding="utf-8",
    )
    print(f"  已写入 {out.relative_to(ROOT)}  ({len(body)} 字节)")
    print("体检：全部通过")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
