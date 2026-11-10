# -*- coding: utf-8 -*-
"""D 的正式搜索引擎：Alpha-Beta 剪枝 + 迭代加深 + 限时 + 走法排序。

规则一律走 A 的 Game 引擎（core/rules.py），这里只负责“选哪一步”。
所有评估都以**虎（王）的视角**：虎要最大化，羊（大臣）要最小化。

对外接口（与 engines/adapter.py 约定）：
    choose_move(game) -> tuple | None

可调环境变量：
    TIGER_DEPTH        迭代加深的最大深度，默认 4
    TIGER_TIME_LIMIT   单步思考的秒数上限，默认 1.0
"""
from __future__ import annotations

import os
import time
from typing import List, Optional, Tuple

from core.rules import SHEEP, TIGER, Game
from evaluate import evaluate_tiger as _tiger_score   # E 的评估函数

INF = 10 ** 9
WIN_SCORE = 1_000_000

W_TIGER_CENTER = 4     # 走法排序用的中心度权重


class _Timeout(Exception):
    """搜索超时，用于中断当前深度的搜索。"""


def _center_bonus(index: int, points) -> int:
    """0..4 的中心度加分；越靠中心越高。"""
    r, c = points[index]
    return W_TIGER_CENTER * (4 - (abs(r - 4) + abs(c - 2)))


def evaluate(game: Game) -> int:
    """静态评估：正分对虎有利，负分对羊有利。

    终局分留在搜索层给（带“越快赢越好”的步数偏好），
    非终局的启发式分一律来自 E 的 evaluate.py，不在引擎里另立一套。
    """
    if game.winner == TIGER:
        return WIN_SCORE - game.moves      # 越快赢越好
    if game.winner == SHEEP:
        return -WIN_SCORE + game.moves
    if game.winner == 0:
        return 0
    return _tiger_score(game)


def _score_move(game: Game, move: Tuple) -> int:
    """走法排序：吃子 > 向中心靠 > 其他。好的走法先搜，剪枝更狠。

    place 只可能由羊执行。羊贴着虎等于把子送到虎嘴边（虎跳吃就是“虎−羊−空”），
    所以靠近虎要**减**分；靠近自己人（抱团堵路）和靠中心才是加分。
    """
    kind = move[0]
    if kind == "eat":
        return 10_000
    points = game.spec.points
    if kind == "move":
        frm, to = move[1], move[2]
        return 100 + _center_bonus(to, points) - _center_bonus(frm, points)

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


def _ordered_moves(game: Game, moves: List[Tuple]) -> List[Tuple]:
    return sorted(moves, key=lambda m: _score_move(game, m), reverse=True)


def alphabeta(game: Game, depth: int, alpha: int, beta: int,
              deadline: float) -> int:
    """标准 Alpha-Beta。虎为极大方，羊为极小方。"""
    if time.monotonic() > deadline:
        raise _Timeout

    if depth == 0 or game.is_over():
        return evaluate(game)

    moves = game.legal_moves()
    if not moves:                       # 理论上 is_over 已覆盖，兜底
        return evaluate(game)

    if game.player == TIGER:
        best = -INF
        for move in _ordered_moves(game, moves):
            game.apply(move)
            try:
                value = alphabeta(game, depth - 1, alpha, beta, deadline)
            finally:
                game.undo()
            if value > best:
                best = value
            if best > alpha:
                alpha = best
            if alpha >= beta:
                break
        return best

    best = INF
    for move in _ordered_moves(game, moves):
        game.apply(move)
        try:
            value = alphabeta(game, depth - 1, alpha, beta, deadline)
        finally:
            game.undo()
        if value < best:
            best = value
        if best < beta:
            beta = best
        if alpha >= beta:
            break
    return best


def _root_search(game: Game, depth: int, deadline: float,
                 first: Optional[Tuple]) -> Tuple[Tuple, int]:
    """根节点搜索：返回 (最佳走法, 分数)。first 用于把上轮最佳排在最前面。"""
    moves = _ordered_moves(game, game.legal_moves())
    if first is not None and first in moves:
        moves.remove(first)
        moves.insert(0, first)

    maximizing = game.player == TIGER
    best_move = moves[0]
    best_score = -INF if maximizing else INF
    alpha, beta = -INF, INF

    for move in moves:
        game.apply(move)
        try:
            value = alphabeta(game, depth - 1, alpha, beta, deadline)
        finally:
            game.undo()

        if maximizing:
            if value > best_score:
                best_score, best_move = value, move
            alpha = max(alpha, best_score)
        else:
            if value < best_score:
                best_score, best_move = value, move
            beta = min(beta, best_score)
        if alpha >= beta:               # 根节点也允许剪枝
            break
    return best_move, best_score


def choose_move(game: Game,
                max_depth: Optional[int] = None,
                time_limit: Optional[float] = None) -> Optional[Tuple]:
    """给当前局面选一步。终局或没有合法走法时返回 None。"""
    if game.is_over():
        return None
    moves = game.legal_moves()
    if not moves:
        return None
    if len(moves) == 1:
        return moves[0]

    depth_cap = max_depth or int(os.environ.get("TIGER_DEPTH", "4"))
    budget = time_limit if time_limit is not None else float(
        os.environ.get("TIGER_TIME_LIMIT", "1.0"))
    deadline = time.monotonic() + max(0.05, budget)

    best = moves[0]
    for depth in range(1, depth_cap + 1):
        try:
            move, _ = _root_search(game, depth, deadline, best)
        except _Timeout:
            break                        # 丢弃没搜完的这一层
        best = move
        if time.monotonic() > deadline:
            break
    return best
