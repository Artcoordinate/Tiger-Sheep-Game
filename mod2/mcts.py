# -*- coding: utf-8 -*-
"""mod2：MCTS（UCT）智能体。

和 mod1 的 Alpha-Beta 完全独立，只共用 A 的规则（`core.rules.Game`）：

    选择(UCB1) → 扩展 → 随机模拟 → 回传

设计取舍
--------
- 每次模拟都从 `node.game.copy()` 复制局面，全程不改调用方的棋局。
- 节点的 `value` 记的是"**轮到该节点行棋的一方**"的累计得分，
  所以父节点选子节点时要把子节点的均值取负（零和、negamax 视角）。
- 模拟封顶 `TIGER_MCTS_ROLLOUT` 手（默认 80），到点用"吃子进度"估个分，
  避免一局拖到 300 手和棋规则，也避免模拟空转。
- 时间预算独立于 mod1：`TIGER_MCTS_TIME`（默认 1.5s）。
"""
import math
import os
import random
import time
from typing import List, Optional

from core.rules import SHEEP, TIGER, Game

Move = tuple

# 终局分：比任何启发式分都大，但远小于浮点溢出
WIN = 10_000


def _env_float(name: str, default: float) -> float:
    try:
        return float(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default


def _heuristic(game: Game) -> float:
    """非终局估分，虎视角，范围约 [-1, 1]。

    虎的目标是吃满 10 只羊，所以按吃子进度给分；羊方由调用方取负。
    """
    return 2.0 * game.captured / 10.0 - 1.0


class _Node:
    """一个搜索节点：持有走完这一步之后的局面。"""

    __slots__ = ("game", "parent", "move", "children", "untried", "visits", "value")

    def __init__(self, game: Game, parent: Optional["_Node"] = None, move: Optional[Move] = None):
        self.game = game
        self.parent = parent
        self.move = move
        self.children: List["_Node"] = []
        self.untried = list(game.legal_moves())
        self.visits = 0
        self.value = 0.0

    def untried_ready(self) -> bool:
        return bool(self.untried)


def _uct(node: _Node, child: _Node, c: float) -> float:
    # child.value 是"子节点行棋方"的均值，对父节点要取负
    exploit = -child.value / child.visits
    explore = c * math.sqrt(math.log(node.visits) / child.visits)
    return exploit + explore


def _select(node: _Node, c: float) -> _Node:
    while not node.untried and node.children and not node.game.is_over():
        node = max(node.children, key=lambda ch: _uct(node, ch, c))
    return node


def _expand(node: _Node, rng: random.Random) -> _Node:
    move = node.untried.pop(rng.randrange(len(node.untried)))
    child_game = node.game.copy()
    child_game.apply(move)
    child = _Node(child_game, parent=node, move=move)
    node.children.append(child)
    return child


def _backprop(node: Optional[_Node], tiger_score: float) -> None:
    while node is not None:
        node.visits += 1
        node.value += tiger_score if node.game.player == TIGER else -tiger_score
        node = node.parent


def choose_move(game: Game, max_depth: Optional[int] = None, time_limit: Optional[float] = None,
                playouts: Optional[int] = None) -> Optional[Move]:
    """MCTS 选步。`max_depth` 复用为模拟封顶手数（兼容 mod1 的签名）。"""
    if game.is_over():
        return None
    root_moves = game.legal_moves()
    if not root_moves:
        return None
    if len(root_moves) == 1:
        return root_moves[0]

    budget = time_limit if time_limit is not None else _env_float("TIGER_MCTS_TIME", 1.5)
    cap = playouts if playouts is not None else int(_env_float("TIGER_MCTS_PLAYOUTS", 0))
    explore_c = _env_float("TIGER_MCTS_C", 1.414)
    rollout_cap = int(max_depth or _env_float("TIGER_MCTS_ROLLOUT", 80))
    seed = os.environ.get("TIGER_MCTS_SEED")
    rng = random.Random(int(seed)) if seed else random.Random()

    root = _Node(game.copy())
    deadline = time.perf_counter() + max(0.0, budget)
    count = 0
    while True:
        node = _select(root, explore_c)
        if node.game.is_over():
            sim = node.game.copy()
        elif node.untried_ready():
            node = _expand(node, rng)
            sim = node.game.copy()
        else:
            sim = node.game.copy()

        plies = 0
        while not sim.is_over() and plies < rollout_cap:
            moves = sim.legal_moves()
            if not moves:
                break
            pick = rng.choice(moves)
            if sim.player == TIGER:
                # 轻量启发：虎的模拟里优先吃子，否则随机模拟几乎看不到吃满 10 子
                eats = [mv for mv in moves if mv[0] == "eat"]
                if eats and rng.random() < 0.7:
                    pick = rng.choice(eats)
            sim.apply(pick)
            plies += 1

        _backprop(node, _terminal_score(sim))

        count += 1
        if (count & 7) == 0 and time.perf_counter() >= deadline:
            break
        if cap and count >= cap:
            break

    if not root.children:
        return root_moves[0]
    # 选访问次数最多的子节点；平手时按"根行棋方视角"的均值再挑
    best = max(root.children, key=lambda ch: (ch.visits, -ch.value / ch.visits))
    return best.move


def _terminal_score(game: Game) -> float:
    """回传用的虎视角得分；未结束时退回启发式。"""
    if game.winner == TIGER:
        return 1.0
    if game.winner == SHEEP:
        return -1.0
    if game.winner == 0:
        return 0.0
    return _heuristic(game)


def evaluate(game: Game) -> int:
    """统一接口用：虎视角的整型估值（终局给大分，越快取胜越高）。"""
    if game.is_over():
        if game.winner == TIGER:
            return WIN - game.moves
        if game.winner == SHEEP:
            return -WIN + game.moves
        return 0
    return int(round(_heuristic(game) * 1000))
