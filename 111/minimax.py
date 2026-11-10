# minimax.py —— 旧 9 点原型的历史入口，现已转发到 37 点正式引擎
# =====================================================
# 原来的 9 点迷你棋盘实现（mini_graph / generate_moves / evaluate）已停止维护，
# 正式搜索见 engines/rule_based.py（Alpha-Beta + 迭代加深 + 限时）。
#
# 这里保留 A 文档里约定的 get_best_move 四参数签名，方便旧调用方无痛迁移：
#   get_best_move(board, player, phase, remaining_sheep, depth=3)
# 内部会构造 37 点 Game 并用正式引擎搜索。

from __future__ import annotations

from typing import List, Optional

from engines.rule_based import choose_move
from generate_moves import game_from_state


def get_best_move(board: List[int], player: int, phase: int,
                  remaining_sheep: int, depth: int = 3) -> Optional[tuple]:
    """兼容旧接口：给一个 37 长棋盘，返回当前方的合法走法（或 None）。"""
    g = game_from_state(board, phase, player, remaining_sheep)
    if g.is_over():
        return None

    return choose_move(g, max_depth=depth)
