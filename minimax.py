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

from core.rules import Game, SHEEP
from engines.rule_based import choose_move


def get_best_move(board: List[int], player: int, phase: int,
                  remaining_sheep: int, depth: int = 3) -> Optional[tuple]:
    """兼容旧接口：给一个 37 长棋盘，返回当前方的合法走法（或 None）。"""
    if len(board) != 37:
        raise ValueError("board 必须是 37 长数组（0 空 / 1 虎 / 2 羊）")

    g = Game()
    g.board = list(board)
    g.player = player
    g.phase = phase
    g.sheep_in_hand = remaining_sheep
    g.captured = 24 - board.count(SHEEP) - remaining_sheep
    g.moves = 0
    g._check_end()
    if g.is_over():
        return None

    return choose_move(g, max_depth=depth)
