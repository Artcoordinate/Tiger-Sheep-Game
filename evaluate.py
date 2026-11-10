# -*- coding: utf-8 -*-
"""
E 评估函数模块（已适配 A 的 core/rules.py 里的 Game）
‑ evaluate_tiger：AI操控老虎，老虎为MAX玩家，虎胜 +1000，羊胜 ‑1000
‑ evaluate_sheep：AI操控羊，羊为MAX玩家，羊胜 +1000，虎胜 ‑1000
入参均为 Game 实例对象，返回 int 整数
依赖属性：game.board（37 项，0 空 / 1 虎 / 2 羊）、game.spec.adj、game.phase
依赖方法：game.is_over()、game.winner（None 未结束 / 1 虎胜 / 2 羊胜 / 0 和棋）
"""
from core.rules import SHEEP, TIGER


def _positions(board):
    """把 37 长的 board 拆成虎、羊两个位置集合。"""
    tigers, sheep = set(), set()
    for i, value in enumerate(board):
        if value == TIGER:
            tigers.add(i)
        elif value == SHEEP:
            sheep.add(i)
    return tigers, sheep


def evaluate_tiger(game):
    """AI控制老虎：分数越高对老虎越有利"""
    if game.is_over():
        winner = game.winner
        if winner == TIGER:
            return 1000
        elif winner == SHEEP:
            return -1000

    score = 0
    tigers, sheep = _positions(game.board)
    adj = game.spec.adj

    # 棋子价值
    score += len(tigers) * 120
    score -= len(sheep) * 40

    # 老虎自由度与被围困威胁
    for pos in tigers:
        free_neighbor = 0
        sheep_around = 0
        for nxt in adj[pos]:
            if nxt in tigers:
                continue
            if nxt in sheep:
                sheep_around += 1
            else:
                free_neighbor += 1
        score += free_neighbor * 12
        score -= sheep_around * 18

    # 羊群抱团，对老虎不利
    for sheep_pos in sheep:
        sheep_neighbor = 0
        for nxt in adj[sheep_pos]:
            if nxt in sheep:
                sheep_neighbor += 1
        score -= sheep_neighbor * 6

    return score


def evaluate_sheep(game):
    """AI控制羊：分数越高对羊越有利"""
    if game.is_over():
        winner = game.winner
        if winner == SHEEP:
            return 1000
        elif winner == TIGER:
            return -1000

    score = 0
    tigers, sheep = _positions(game.board)
    adj = game.spec.adj

    # 棋子价值
    score += len(sheep) * 40
    score -= len(tigers) * 120

    # 老虎自由度：空位越少对羊越好；周边羊越多围困越好
    for pos in tigers:
        free_neighbor = 0
        sheep_around = 0
        for nxt in adj[pos]:
            if nxt in tigers:
                continue
            if nxt in sheep:
                sheep_around += 1
            else:
                free_neighbor += 1
        score -= free_neighbor * 12
        score += sheep_around * 18

    # 羊抱团加分，利于围堵
    for sheep_pos in sheep:
        sheep_neighbor = 0
        for nxt in adj[sheep_pos]:
            if nxt in sheep:
                sheep_neighbor += 1
        score += sheep_neighbor * 6

    return score
