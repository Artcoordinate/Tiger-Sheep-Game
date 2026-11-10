# -*- coding: utf-8 -*-
"""D 的引擎与兼容层测试：不依赖 Flask，只验证搜索/评估/接口约定。"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.rules import EMPTY, SHEEP, TIGER, Game          # noqa: E402
from engines.adapter import choose                        # noqa: E402
from engines.rule_based import choose_move, evaluate      # noqa: E402
from minimax import get_best_move                         # noqa: E402


class EngineTest(unittest.TestCase):
    def test_opening_returns_legal_move(self):
        g = Game()
        move = choose_move(g, max_depth=2, time_limit=2.0)
        self.assertIn(move, g.legal_moves())

    def test_does_not_mutate_input_game(self):
        g = Game()
        before = (list(g.board), g.player, g.moves, g.sheep_in_hand)
        choose_move(g, max_depth=2, time_limit=2.0)
        self.assertEqual((g.board, g.player, g.moves, g.sheep_in_hand), before)

    def test_prefers_capture_when_available(self):
        # 开局虎在 (2,2)，正下方三只羊都可跳吃；深度 1 应直接吃。
        g = Game()
        eats = [m for m in g.legal_moves() if m[0] == "eat"]
        self.assertTrue(eats, "开局应当存在跳吃走法")
        move = choose_move(g, max_depth=1, time_limit=1.0)
        self.assertEqual(move[0], "eat")

    def test_sheep_places_during_placement_phase(self):
        g = Game()
        g.player = SHEEP
        move = choose_move(g, max_depth=2, time_limit=1.0)
        self.assertEqual(move[0], "place")
        self.assertIn(move, g.legal_moves())
        self.assertEqual(g.board[move[1]], EMPTY)

    def test_capture_improves_score(self):
        g = Game()
        base = evaluate(g)
        eat = next(m for m in g.legal_moves() if m[0] == "eat")
        g.apply(eat)
        self.assertGreater(evaluate(g), base)

    def test_terminal_returns_none(self):
        g = Game()
        g.winner = TIGER
        self.assertIsNone(choose_move(g))

    def test_adapter_reports_engine_and_legal_move(self):
        g = Game()
        move, name = choose(g)
        self.assertEqual(name, "rule_based")
        self.assertIn(move, g.legal_moves())

    def test_legacy_entry_point(self):
        g = Game()
        move = get_best_move(g.board[:], g.player, g.phase, g.sheep_in_hand, depth=2)
        self.assertIn(move, g.legal_moves())


if __name__ == "__main__":
    unittest.main()
