"""仅用于 C/B 联调；不是 D 的 Minimax。"""
def choose_move(game):
    moves = game.legal_moves()
    return next((m for m in moves if m[0] == 'eat'), moves[0] if moves else None)
