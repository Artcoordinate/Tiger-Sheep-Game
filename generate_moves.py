# generate_moves.py —— 已废弃
# 原 9 点原型的走法生成与 make/undo，现已被 core/rules.py 的 Game 取代：
#   合法走法 = Game.legal_moves()
#   走一步   = Game.apply(move)
#   悔一步   = Game.undo()
# 原实现保留在 legacy/generate_moves.py，仅作历史参考。
