# -*- coding: utf-8 -*-
"""从 core/board.py 画两张棋盘图，供实验报告"设计"章节使用
================================================================

    python scripts/draw_board.py

输出
----
docs/screenshots/board_layout.png     初始布局（画子，不标号）
docs/screenshots/board_numbered.png   节点编号（不画子，标号）

和 export_board.py 一样，图的唯一来源是 A 的 board.py。
"""

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "core"))

import board as B  # noqa: E402

SPEC = B.BOARD_37
WOOD = "#b07a46"
INK = "#141414"


def _canvas():
    fig, ax = plt.subplots(figsize=(5.2, 8.0), dpi=200)
    fig.patch.set_facecolor(WOOD)
    ax.set_facecolor(WOOD)

    for i, j in SPEC.edges:
        x1, y1 = SPEC.coords[i]
        x2, y2 = SPEC.coords[j]
        ax.plot([x1, x2], [y1, y2], color=INK, linewidth=1.3, zorder=1, solid_capstyle="round")

    ax.set_xlim(20, 388)
    ax.set_ylim(628, 20)          # y 轴翻转，和棋盘坐标一致
    ax.set_aspect("equal")
    ax.axis("off")
    fig.subplots_adjust(left=0.02, right=0.98, top=0.98, bottom=0.02)
    return fig, ax


def draw_layout(out: Path) -> None:
    fig, ax = _canvas()

    for i, v in enumerate(SPEC.initial):
        if v == B.EMPTY:
            continue
        x, y = SPEC.coords[i]
        if v == B.TIGER:
            ax.scatter([x], [y], s=540, c="#111111", edgecolors="#000000",
                       linewidths=1.2, zorder=3)
        else:
            ax.scatter([x], [y], s=540, c="#f5efe3", edgecolors="#1a1a1a",
                       linewidths=1.5, zorder=3)

    fig.savefig(out, facecolor=WOOD)
    plt.close(fig)


def draw_numbered(out: Path) -> None:
    fig, ax = _canvas()

    for i, (x, y) in enumerate(SPEC.coords):
        ax.scatter([x], [y], s=26, c="#1a1a1a", zorder=3)
        # 编号往右上角错开，避开线条
        ax.text(x + 11, y - 9, str(i), fontsize=8.5, color="#1b3fa0",
                fontweight="bold", zorder=4, ha="left", va="bottom")

    fig.savefig(out, facecolor=WOOD)
    plt.close(fig)


def main() -> int:
    out_dir = ROOT / "docs" / "screenshots"
    out_dir.mkdir(parents=True, exist_ok=True)

    lay = out_dir / "board_layout.png"
    num = out_dir / "board_numbered.png"
    draw_layout(lay)
    draw_numbered(num)

    print(f"  {lay.relative_to(ROOT)}   {(lay.stat().st_size / 1024):.0f} KB")
    print(f"  {num.relative_to(ROOT)}  {(num.stat().st_size / 1024):.0f} KB")
    print(f"  节点 {len(SPEC.points)}  连线 {len(SPEC.edges)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
