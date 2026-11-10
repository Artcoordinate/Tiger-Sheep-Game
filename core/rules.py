# -*- coding: utf-8 -*-
"""
国王与大臣棋（虎羊棋）—— 规则引擎
==================================

这个文件只做“规则”，不做搜索算法。
D 的 Minimax、E 的评估函数、C 的后端、B 的界面，都应该调用这里的接口，
这样大家用的规则才是同一套。

核心约定
--------
board: 长度 37 的一维数组
    0 = 空，1 = 虎，2 = 羊
phase:
    1 = 添子阶段（羊还有棋子没放完）
    2 = 走子阶段（16 只羊已经放完）
player:
    1 = 轮到虎，2 = 轮到羊
move 有三种写法：
    ("place", to)            羊添子：把羊放到 to
    ("move", frm, to)        走一步：从 frm 走到 to
    ("eat", frm, over, to)   虎跳吃：从 frm 跳过 over，落到 to

用法
----
    from rules import Game

    g = Game()                   # 37 格
    print(g.legal_moves())       # 当前玩家的所有合法走法
    g.apply(("place", 18))       # 走一步（会检查合法性）
    print(g.board_text())
    print(g.status_text())

给 D 的 Minimax 用：
    g = Game()
    moves = g.legal_moves()
    g.apply(move)
    ...
    g.undo()
"""

from __future__ import annotations

import copy
import random
from typing import Dict, List, Optional, Tuple

from . import board as board_def
from .board import EMPTY, SHEEP, TIGER, BoardSpec

Move = Tuple


class Game:
    def __init__(self):
        self.spec: BoardSpec = board_def.get_board()
        self.board: List[int] = list(self.spec.initial)
        self.phase: int = 1
        self.player: int = TIGER          # 虎先走
        self.sheep_in_hand: int = board_def.SHEEP_IN_HAND
        self.captured: int = 0            # 已被吃掉的羊
        self.moves: int = 0               # 已经走了多少步（双方各算一步）
        self.winner: Optional[int] = None # None=未结束；1=虎胜；2=羊胜；0=和棋
        self.end_reason: str = ""
        self.last_move: Optional[Move] = None
        self.history: List[dict] = []

    # ------------------------------------------------------------------
    # 基本查询
    # ------------------------------------------------------------------
    @property
    def remaining_sheep(self) -> int:
        return self.sheep_in_hand

    def point(self, i: int) -> Tuple[int, int]:
        return self.spec.points[i]

    def index(self, point: Tuple[int, int]) -> int:
        return self.spec.index[point]

    def is_over(self) -> bool:
        return self.winner is not None

    def other(self, player: int) -> int:
        return SHEEP if player == TIGER else TIGER

    # ------------------------------------------------------------------
    # 合法走法
    # ------------------------------------------------------------------
    def legal_moves(self, player: Optional[int] = None) -> List[Move]:
        if self.winner is not None:
            return []
        if player is None:
            player = self.player
        if player == TIGER:
            return self._tiger_moves()
        return self._sheep_moves()

    def _tiger_moves(self) -> List[Move]:
        moves: List[Move] = []
        spec = self.spec
        for i, value in enumerate(self.board):
            if value != TIGER:
                continue
            ri, ci = spec.points[i]
            for j in spec.adj[i]:
                if self.board[j] == EMPTY:
                    # 普通走一步
                    moves.append(("move", i, j))
                elif self.board[j] == SHEEP:
                    # 跳吃：i -> j(羊) -> k(空)，三点必须在一条直线上，且 j 是 i、k 的中点
                    rj, cj = spec.points[j]
                    rk, ck = 2 * rj - ri, 2 * cj - ci
                    k = spec.index.get((rk, ck))
                    if k is None:
                        continue
                    if self.board[k] != EMPTY:
                        continue
                    # 只允许“一步”的跳：排除跨越空洞的长线
                    if max(abs(rj - ri), abs(cj - ci)) != 1:
                        continue
                    if max(abs(rk - rj), abs(ck - cj)) != 1:
                        continue
                    if k not in spec.adj[j] or j not in spec.adj[i]:
                        continue
                    moves.append(("eat", i, j, k))
        return moves

    def _sheep_moves(self) -> List[Move]:
        moves: List[Move] = []
        spec = self.spec
        if self.phase == 1:
            # 添子阶段：羊只能往空点放
            for i, value in enumerate(self.board):
                if value == EMPTY:
                    moves.append(("place", i))
            return moves

        # 走子阶段：羊只能沿连线走一步
        for i, value in enumerate(self.board):
            if value != SHEEP:
                continue
            for j in spec.adj[i]:
                if self.board[j] == EMPTY:
                    moves.append(("move", i, j))
        return moves

    # ------------------------------------------------------------------
    # 走一步 / 悔一步
    # ------------------------------------------------------------------
    def _snapshot(self) -> dict:
        return {
            "board": tuple(self.board),
            "phase": self.phase,
            "player": self.player,
            "sheep_in_hand": self.sheep_in_hand,
            "captured": self.captured,
            "moves": self.moves,
            "winner": self.winner,
            "end_reason": self.end_reason,
            "last_move": self.last_move,
        }

    def _restore(self, snap: dict) -> None:
        self.board = list(snap["board"])
        self.phase = snap["phase"]
        self.player = snap["player"]
        self.sheep_in_hand = snap["sheep_in_hand"]
        self.captured = snap["captured"]
        self.moves = snap["moves"]
        self.winner = snap["winner"]
        self.end_reason = snap["end_reason"]
        self.last_move = snap["last_move"]

    def apply(self, move: Move) -> "Game":
        """走一步。走法不合法会直接报错，方便测试。"""
        if self.winner is not None:
            raise ValueError("棋局已经结束")
        legal = self.legal_moves()
        if move not in legal:
            raise ValueError(f"不合法的走法：{move}\n当前合法走法：{legal[:20]} ...")

        self.history.append(self._snapshot())
        kind = move[0]

        if kind == "place":
            to = move[1]
            self.board[to] = SHEEP
            self.sheep_in_hand -= 1
            if self.sheep_in_hand == 0:
                self.phase = 2

        elif kind == "move":
            frm, to = move[1], move[2]
            self.board[frm] = EMPTY
            self.board[to] = self.player

        elif kind == "eat":
            frm, over, to = move[1], move[2], move[3]
            self.board[frm] = EMPTY
            self.board[over] = EMPTY
            self.board[to] = TIGER
            self.captured += 1

        else:
            raise ValueError(f"未知走法类型：{kind}")

        self.last_move = move
        self.moves += 1
        self.player = self.other(self.player)
        self._check_end()
        return self

    def undo(self) -> None:
        """撤销上一步（D 的搜索里会用到）。"""
        if not self.history:
            raise ValueError("没有可以撤销的走法")
        self._restore(self.history.pop())

    def copy(self) -> "Game":
        return copy.deepcopy(self)

    # ------------------------------------------------------------------
    # 胜负判断
    # ------------------------------------------------------------------
    def _check_end(self) -> None:
        if self.winner is not None:
            return

        # 1) 虎吃满 10 只羊
        if self.captured >= 10:
            self.winner = TIGER
            self.end_reason = "虎累计吃掉 10 只羊，虎胜"
            return

        # 2) 300 步和棋（双方各走一步算 1 步）
        if self.moves >= 300:
            self.winner = 0
            self.end_reason = "总步数达到 300，和棋"
            return

        # 3) 轮到谁，谁没有合法走法
        if not self.legal_moves(self.player):
            if self.player == TIGER:
                self.winner = SHEEP
                self.end_reason = "虎被围死，无路可走，羊胜"
            else:
                self.winner = TIGER
                self.end_reason = "羊无路可走，虎胜"
            return

    # ------------------------------------------------------------------
    # 给界面 / 后端用的文字和字典
    # ------------------------------------------------------------------
    def board_text(self) -> str:
        return board_def.text_board(self.board)

    def status_text(self) -> str:
        if self.winner is not None:
            name = {TIGER: "虎胜", SHEEP: "羊胜", 0: "和棋"}[self.winner]
            return f"{name}：{self.end_reason}（共 {self.moves} 步）"
        turn = "虎" if self.player == TIGER else "羊"
        phase = "添子阶段" if self.phase == 1 else "走子阶段"
        return (
            f"轮到 {turn} 走 | {phase} | 羊手里还有 {self.sheep_in_hand} 只 | "
            f"虎已吃 {self.captured} 只 | 已走 {self.moves} 步"
        )

    def state_dict(self) -> Dict:
        """给 C 的 Flask 接口直接返回这个字典即可。"""
        return {
            "board": list(self.board),
            "phase": self.phase,
            "player": self.player,
            "sheep_in_hand": self.sheep_in_hand,
            "captured": self.captured,
            "moves": self.moves,
            "winner": self.winner,
            "end_reason": self.end_reason,
            "status": self.status_text(),
            "legal_moves": self.legal_moves(),
        }

    @staticmethod
    def move_text(move: Move) -> str:
        if move[0] == "place":
            return f"羊放到 {move[1]}"
        if move[0] == "move":
            return f"{move[1]} → {move[2]}"
        if move[0] == "eat":
            return f"虎 {move[1]} 跳过 {move[2]} 到 {move[3]}，吃掉一只羊"
        return str(move)


# ----------------------------------------------------------------------
# 命令行小演示：随机双方自动下一局
# ----------------------------------------------------------------------
def _random_game(seed: Optional[int] = None) -> Game:
    rng = random.Random(seed)
    g = Game()
    while not g.is_over():
        moves = g.legal_moves()
        if not moves:
            break
        g.apply(rng.choice(moves))
    return g


if __name__ == "__main__":
    g = Game()
    print("=== 开局 ===")
    print(g.board_text())
    print(g.status_text())
    print("\n虎的合法走法（前 10 个）：")
    for m in g.legal_moves()[:10]:
        print("  ", m, "—", g.move_text(m))

    print("\n=== 随机自动下一局（37 格） ===")
    g2 = _random_game(seed=2026)
    print(g2.board_text())
    print(g2.status_text())
    if g2.winner is not None:
        print("结果：", {TIGER: "虎胜", SHEEP: "羊胜", 0: "和棋"}[g2.winner])
