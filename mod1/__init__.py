# -*- coding: utf-8 -*-
"""算法版本 1：Alpha-Beta + 迭代加深 + 限时 + 启发式排序。

每个算法版本目录（mod1、mod2…）对外只暴露同一套接口，`engines/adapter.py` 只认这套：

    NAME                                            版本名，前端下拉框和日志用
    choose_move(game, max_depth=None, time_limit=None) -> tuple | None
    evaluate(game) -> int

以后加 MCTS 版（mod2）只要照抄这几个名字，adapter 不用改一行。
"""
from .rule_based import choose_move, evaluate

NAME = "mod1"

__all__ = ["NAME", "choose_move", "evaluate"]
