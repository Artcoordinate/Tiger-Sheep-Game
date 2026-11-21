"""engines.mcts: 向后兼容的转发壳。

C 的 adapter.py 按 `engines.<TIGER_ENGINE>` 动态导入，白名单里已经有 `mcts`。
算法本体在 `mod2/`，这里只做转发，不含任何逻辑。
"""

from mod2.mcts import choose_move, evaluate  # noqa: F401
