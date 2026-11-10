# -*- coding: utf-8 -*-
"""D 的走法生成层：生成 + 启发式排序。

规则只有一份，就是 A 的 `core/rules.py` 里 `Game.legal_moves()`。这里**不重写规则**，
只做两件引擎真正需要的事：

1. 生成：向规则层要当前行棋方的全部合法走法——规则正确性由 A 保证，避免出现第三套规则；
2. 排序：按"这步好不好"打分后排好序再交给 Alpha-Beta。好步先搜，剪枝更狠，
   同深度实测快 3~4 倍。排序只影响搜索效率，不改变选步正确性。

对外接口：
    generate_moves(game)  -> List[tuple]  排好序的合法走法
    order_moves(game, moves) -> List[tuple]  只排序，不生成
    score_move(game, move) -> in  单步启发式分（对**行棋方**越好分越高）
    game_from_state(board, phase, player, remaining_sheep) -> Game  旧签名适配
"""
from __future__ import annotations

from typing import Iterable, List, Tuple

from core.rules import SHEEP, TIGER, Game

W_CENTER = 4           # 中心度权重：最多给到 4 * 4 = 16 分
EAT_BONUS = 10_000     # 吃子永远排最前
MOVE_BASE = 100        # 走子基础分，保证排在添子前面


def game_from_state(board: List[int], phase: int, player: int,
                    remaining_sheep: int) -> Game:
    """用旧的四参数（棋盘数组 + 阶段 + 行棋方 + 手牌）还原一个 Game。

    `Game.captured` 不由外部传入，按"24 只羊减去场上与手牌"倒推；
    `moves` 从 0 起算，只用于终局判定与"越快取胜越好"的步数偏好。
    """
    board = list(board)
    if len(board) != 37:
        raise ValueError("board 必须是 37 长数组（0 空 / 1 虎 / 2 羊）")

    game = Game()
    game.board = board
    game.phase = phase
    game.player = player
    game.sheep_in_hand = remaining_sheep
    game.captured = 24 - board.count(SHEEP) - remaining_sheep
    game.moves = 0
    game._check_end()
    return game


def _center_bonus(index: int, points) -> int:
    """0..16 的中心度加分；越靠中心越高。"""
    r, c = points[index]
    return W_CENTER * (4 - (abs(r - 4) + abs(c - 2)))


def score_move(game: Game, move: Tuple) -> int:
    """单步启发式打分（越大越先搜）。

    打分站在**行棋方**的立场：
    - 吃子对虎是直接收益，永远排最前；
    - 走子按"向中心靠"给分；
    - 添子只可能由羊执行。羊贴着虎等于把子送到虎嘴边（虎跳吃就是"虎—羊—空"），
      所以靠近虎要**减**分；靠近自己人（抱团堵路）和靠中心才是加分。
    """
    kind = move[0]
    if kind == "eat":
        return EAT_BONUS

    points = game.spec.points
    if kind == "move":
        frm, to = move[1], move[2]
        return MOVE_BASE + _center_bonus(to, points) - _center_bonus(frm, points)

    to = move[1]
    r, c = points[to]
    score = _center_bonus(to, points)
    for i, v in enumerate(game.board):
        dist = abs(points[i][0] - r) + abs(points[i][1] - c)
        if v == SHEEP:
            score += max(0, 12 - dist)         # 抱团
        elif v == TIGER:
            score -= 3 * max(0, 12 - dist)     # 离虎越近越危险
    return score


def order_moves(game: Game, moves: Iterable[Tuple]) -> List[Tuple]:
    """按启发式分从高到低排序，不改动传入的走法集合。"""
    return sorted(moves, key=lambda move: score_move(game, move), reverse=True)


def generate_moves(game: Game) -> List[Tuple]:
    """当前行棋方的合法走法，已按启发式排好序。"""
    return order_moves(game, game.legal_moves())
