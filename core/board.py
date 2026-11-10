# -*- coding: utf-8 -*-
"""
国王与大臣棋（虎羊棋）—— 37 格棋盘定义（按课本图 2-1）
========================================================

坐标约定
--------
(row, col):
    row = 0..8  从上到下（9 行）
    col = 0..4  从左到右（5 列）
    棋盘是竖着看的，和课本图 2-1 方向一致：
    上下各一个“王宫”（三角形），中间是 5×5 的“米”字方格，
    每个小格都有两条斜线，形成很多小 X。

37 格：
    9×5 = 45 个网格交点，去掉 8 个“不成点”：
    (0,1) (0,3) (1,0) (1,4) (7,0) (7,4) (8,1) (8,3)
    剩下 37 个可落子点、76 条单位连线。

棋子编号：
    0 = 空，1 = 虎，2 = 羊
"""

from dataclasses import dataclass
from typing import Dict, List, Tuple

EMPTY, TIGER, SHEEP = 0, 1, 2

# ---------------------------------------------------------------------------
# 1. 37 个点（按行、列排序，顺序就是数组下标 0..36）
# ---------------------------------------------------------------------------
POINTS_37: Tuple[Tuple[int, int], ...] = (
    # row 0
    (0, 0), (0, 2), (0, 4),
    # row 1
    (1, 1), (1, 2), (1, 3),
    # row 2
    (2, 0), (2, 1), (2, 2), (2, 3), (2, 4),
    # row 3
    (3, 0), (3, 1), (3, 2), (3, 3), (3, 4),
    # row 4
    (4, 0), (4, 1), (4, 2), (4, 3), (4, 4),
    # row 5
    (5, 0), (5, 1), (5, 2), (5, 3), (5, 4),
    # row 6
    (6, 0), (6, 1), (6, 2), (6, 3), (6, 4),
    # row 7
    (7, 1), (7, 2), (7, 3),
    # row 8
    (8, 0), (8, 2), (8, 4),
)

# 8 个“不成点”
NON_POINTS = (
    (0, 1), (0, 3),
    (1, 0), (1, 4),
    (7, 0), (7, 4),
    (8, 1), (8, 3),
)

# 开局固定位置（按课本图：虎在上下王宫的尖上，羊在中心周围）
TIGER_START = ((2, 2), (6, 2))
SHEEP_START = (
    (3, 1), (3, 2), (3, 3),
    (4, 1),         (4, 3),
    (5, 1), (5, 2), (5, 3),
)
SHEEP_IN_HAND = 16   # 羊手里还没放下的 16 只

# ---------------------------------------------------------------------------
# 2. 76 条单位连线
#    横线 + 竖线 + 中间 5×5 每个小格的两条斜线 + 上下王宫的斜边。
# ---------------------------------------------------------------------------
EDGES_37: Tuple[Tuple[Tuple[int, int], Tuple[int, int]], ...] = (
    # ---- 横线 ----
    # row 0：两条长线，中间跨过 (0,1)/(0,3)
    ((0, 0), (0, 2)), ((0, 2), (0, 4)),
    # row 1
    ((1, 1), (1, 2)), ((1, 2), (1, 3)),
    # row 2
    ((2, 0), (2, 1)), ((2, 1), (2, 2)), ((2, 2), (2, 3)), ((2, 3), (2, 4)),
    # row 3
    ((3, 0), (3, 1)), ((3, 1), (3, 2)), ((3, 2), (3, 3)), ((3, 3), (3, 4)),
    # row 4
    ((4, 0), (4, 1)), ((4, 1), (4, 2)), ((4, 2), (4, 3)), ((4, 3), (4, 4)),
    # row 5
    ((5, 0), (5, 1)), ((5, 1), (5, 2)), ((5, 2), (5, 3)), ((5, 3), (5, 4)),
    # row 6
    ((6, 0), (6, 1)), ((6, 1), (6, 2)), ((6, 2), (6, 3)), ((6, 3), (6, 4)),
    # row 7
    ((7, 1), (7, 2)), ((7, 2), (7, 3)),
    # row 8：两条长线
    ((8, 0), (8, 2)), ((8, 2), (8, 4)),

    # ---- 竖线 ----
    # col 0
    ((2, 0), (3, 0)), ((3, 0), (4, 0)), ((4, 0), (5, 0)), ((5, 0), (6, 0)),
    # col 1
    ((2, 1), (3, 1)), ((3, 1), (4, 1)),
    ((4, 1), (5, 1)), ((5, 1), (6, 1)),
    # col 2
    ((0, 2), (1, 2)), ((1, 2), (2, 2)), ((2, 2), (3, 2)), ((3, 2), (4, 2)),
    ((4, 2), (5, 2)), ((5, 2), (6, 2)), ((6, 2), (7, 2)), ((7, 2), (8, 2)),
    # col 3
    ((2, 3), (3, 3)), ((3, 3), (4, 3)),
    ((4, 3), (5, 3)), ((5, 3), (6, 3)),
    # col 4
    ((2, 4), (3, 4)), ((3, 4), (4, 4)), ((4, 4), (5, 4)), ((5, 4), (6, 4)),

    # ---- 中间 5×5：每个小格保留一条斜线（4×4 个格子，共 16 条） ----
    # 按课本图：格子 (c+r) 为偶数时保留“左上-右下”，为奇数时保留“右上-左下”
    ((2, 0), (3, 1)), ((2, 2), (3, 1)), ((2, 2), (3, 3)), ((2, 4), (3, 3)),
    ((3, 1), (4, 0)), ((3, 1), (4, 2)), ((3, 3), (4, 2)), ((3, 3), (4, 4)),
    ((4, 0), (5, 1)), ((4, 2), (5, 1)), ((4, 2), (5, 3)), ((4, 4), (5, 3)),
    ((5, 1), (6, 0)), ((5, 1), (6, 2)), ((5, 3), (6, 2)), ((5, 3), (6, 4)),

    # ---- 上王宫的斜边：上 V + 下 V ----
    ((0, 0), (1, 1)), ((1, 1), (2, 2)),
    ((0, 4), (1, 3)), ((1, 3), (2, 2)),
    # ---- 下王宫的斜边：上 V + 下 V ----
    ((8, 0), (7, 1)), ((7, 1), (6, 2)),
    ((8, 4), (7, 3)), ((7, 3), (6, 2)),
)

# 画图用的像素坐标：x 向右，y 向下；中间一格 72 像素。
# 王宫（上下三角形）的高度按课本图 2-1 约为 1.67 格。
X0, Y0, STEP = 60, 60, 72
PALACE_H = 120         # 王宫总高：120 ≈ 1.67 × 72
PALACE_MID = 60        # 王宫中线到顶/底的距离

SQUARE_TOP = Y0 + PALACE_H
ROW_Y = {
    0: Y0,
    1: Y0 + PALACE_MID,
    2: SQUARE_TOP,
    3: SQUARE_TOP + STEP,
    4: SQUARE_TOP + 2 * STEP,
    5: SQUARE_TOP + 3 * STEP,
    6: SQUARE_TOP + 4 * STEP,
    7: SQUARE_TOP + 4 * STEP + PALACE_MID,
    8: SQUARE_TOP + 4 * STEP + PALACE_H,
}
WIDTH = 2 * X0 + 4 * STEP
HEIGHT = ROW_Y[8] + Y0


def _pixel(point: Tuple[int, int]) -> Tuple[int, int]:
    r, c = point
    return X0 + c * STEP, ROW_Y[r]


@dataclass(frozen=True)
class BoardSpec:
    """37 格棋盘的只读数据。"""

    points: Tuple[Tuple[int, int], ...]
    index: Dict[Tuple[int, int], int]
    coords: Tuple[Tuple[int, int], ...]
    edges: Tuple[Tuple[int, int], ...]          # 下标对 (i, j)
    adj: Tuple[Tuple[int, ...], ...]            # 邻接表
    initial: Tuple[int, ...]                    # 开局数组

    def __len__(self) -> int:
        return len(self.points)

    def idx(self, point: Tuple[int, int]) -> int:
        """(row, col) → 数组下标；不在棋盘上会报 KeyError。"""
        return self.index[point]

    def point(self, i: int) -> Tuple[int, int]:
        return self.points[i]

    def neighbors(self, i: int) -> Tuple[int, ...]:
        return self.adj[i]

    def degree(self, i: int) -> int:
        return len(self.adj[i])

    def is_legal(self, point: Tuple[int, int]) -> bool:
        return point in self.index


def _make_spec() -> BoardSpec:
    index = {p: i for i, p in enumerate(POINTS_37)}
    edges = tuple((index[a], index[b]) for a, b in EDGES_37)

    adj: List[List[int]] = [[] for _ in POINTS_37]
    for i, j in edges:
        adj[i].append(j)
        adj[j].append(i)
    adj_t = tuple(tuple(sorted(ns)) for ns in adj)

    initial = [EMPTY] * len(POINTS_37)
    for p in TIGER_START:
        initial[index[p]] = TIGER
    for p in SHEEP_START:
        initial[index[p]] = SHEEP

    coords = tuple(_pixel(p) for p in POINTS_37)
    return BoardSpec(
        points=POINTS_37,
        index=index,
        coords=coords,
        edges=edges,
        adj=adj_t,
        initial=tuple(initial),
    )


BOARD_37 = _make_spec()


def get_board() -> BoardSpec:
    return BOARD_37


# ---------------------------------------------------------------------------
# 3. 小工具：把数组画成文字棋盘 / 统计信息
# ---------------------------------------------------------------------------
CHAR = {EMPTY: "·", TIGER: "虎", SHEEP: "羊"}


def text_board(board: List[int]) -> str:
    """把一维数组画成 9 行 5 列的文字棋盘。"""
    spec = BOARD_37
    grid = [[" " for _ in range(5)] for _ in range(9)]
    for i, value in enumerate(board):
        r, c = spec.points[i]
        grid[r][c] = CHAR[value]
    lines = ["    " + " ".join(str(c) for c in range(5))]
    for r in range(9):
        lines.append(f"{r}   " + " ".join(grid[r]))
    return "\n".join(lines)


def _canon_edges(edges) -> set:
    return {tuple(sorted(e)) for e in edges}


def self_check() -> Dict[str, object]:
    """返回一份自检报告，测试脚本和文档都可以直接用它。"""
    spec = BOARD_37
    errors: List[str] = []

    if len(spec.points) != 37:
        errors.append(f"点数不对：{len(spec.points)}，应为 37")
    if len(spec.edges) != 76:
        errors.append(f"连线数不对：{len(spec.edges)}，应为 76")
    if len(set(spec.points)) != len(spec.points):
        errors.append("有重复的点")

    for i, j in spec.edges:
        if i == j:
            errors.append(f"自己连自己：{i}")
        if not (0 <= i < len(spec.points) and 0 <= j < len(spec.points)):
            errors.append(f"边下标越界：{(i, j)}")

    edge_set = _canon_edges(spec.edges)
    for i, ns in enumerate(spec.adj):
        for j in ns:
            if tuple(sorted((i, j))) not in edge_set:
                errors.append(f"邻接表多了一条边：{(i, j)}")
    for i, j in edge_set:
        if i not in spec.adj[j] or j not in spec.adj[i]:
            errors.append(f"邻接表少了一条边：{(i, j)}")

    isolated = [spec.points[i] for i, ns in enumerate(spec.adj) if not ns]
    if isolated:
        errors.append(f"有孤立点：{isolated}")

    # 左右镜像、上下镜像
    for p in spec.points:
        if (p[0], 4 - p[1]) not in spec.index:
            errors.append(f"左右不对称：{p}")
        if (8 - p[0], p[1]) not in spec.index:
            errors.append(f"上下不对称：{p}")
    for i, j in edge_set:
        a, b = spec.points[i], spec.points[j]
        for mirror in (lambda q: (q[0], 4 - q[1]), lambda q: (8 - q[0], q[1])):
            if tuple(sorted((spec.index[mirror(a)], spec.index[mirror(b)]))) not in edge_set:
                errors.append(f"连线不对称：{(a, b)}")

    if list(spec.initial).count(TIGER) != 2:
        errors.append("开局虎不是 2 只")
    if list(spec.initial).count(SHEEP) != 8:
        errors.append("开局羊不是 8 只")
    if spec.initial[spec.idx((4, 2))] != EMPTY:
        errors.append("中心点 (4,2) 应该是空的")

    return {
        "points": len(spec.points),
        "edges": len(spec.edges),
        "degrees": [len(ns) for ns in spec.adj],
        "errors": errors,
    }


if __name__ == "__main__":
    report = self_check()
    print("=== 37 格（按课本图 2-1） ===")
    print(f"点数：{report['points']}  连线：{report['edges']}")
    print(f"每个点的度数：{report['degrees']}")
    print("自检：", "全部通过 ✅" if not report["errors"] else report["errors"])
    print()
    print("37 格开局：")
    print(text_board(list(BOARD_37.initial)))
