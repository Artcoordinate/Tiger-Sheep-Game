"""engines.rule_based: 向后兼容的转发壳。

C 的 adapter.py 按 `engines.<TIGER_ENGINE>` 动态导入，默认名字是 `rule_based`。
算法本体已经搬进 `mod1/`（版本目录约定），这里只做转发，不含任何逻辑。
"""

from mod1.rule_based import choose_move, evaluate  # noqa: F401
