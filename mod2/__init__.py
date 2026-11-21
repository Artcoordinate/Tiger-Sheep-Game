# -*- coding: utf-8 -*-
"""算法版本 2：MCTS（UCT）智能体。

对外接口与 mod1 完全一致，`engines/adapter.py` 不用改：

    NAME                                                 版本名
    choose_move(game, max_depth=None, time_limit=None)   -> tuple | None
    evaluate(game)                                       -> int（虎视角）

`max_depth` 在 MCTS 这边复用为"模拟封顶手数"，签名保持兼容。
环境变量：TIGER_MCTS_TIME（默认 1.5s）、TIGER_MCTS_PLAYOUTS、TIGER_MCTS_C、
TIGER_MCTS_ROLLOUT、TIGER_MCTS_SEED。
"""
from .mcts import choose_move, evaluate

NAME = "mod2"

__all__ = ["NAME", "choose_move", "evaluate"]
