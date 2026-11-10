# generate_moves.py
from mini_graph import mini_adj


def generate_moves(board, player, phase, remaining_sheep):
    moves = []

    # 1. 添子阶段：羊只能放
    if phase == 1 and player == 2:
        for i in range(9):
            if board[i] == 0:
                moves.append(('place', i))
        return moves

    # 2. 走子阶段
    for i in range(9):
        if board[i] == player:
            # 普通移动
            for neighbor in mini_adj[i]:
                if board[neighbor] == 0:
                    moves.append(('move', i, neighbor))

            # 老虎专属：跳吃
            if player == 1:
                for neighbor in mini_adj[i]:
                    if board[neighbor] == 2:  # 邻居是羊
                        for next_pos in mini_adj[neighbor]:  # 羊的邻居
                            # 不能往回跳，且落点必须是空
                            if next_pos != i and board[next_pos] == 0:
                                moves.append(('eat', i, next_pos))
    return moves


def make_move(board, move, player):
    """执行走棋，返回被吃掉的羊的位置（如果有），用于悔棋"""
    eaten_pos = -1
    if move[0] == 'place':
        board[move[1]] = player
    elif move[0] == 'move':
        board[move[1]] = 0
        board[move[2]] = player
    elif move[0] == 'eat':
        board[move[1]] = 0
        board[move[2]] = player
        # 记录被吃羊的位置（简单找一下，实际37格需要严格计算方向）
        for neighbor in mini_adj[move[1]]:
            if board[neighbor] == 2:
                eaten_pos = neighbor
                board[eaten_pos] = 0
                break
    return eaten_pos


def undo_move(board, move, player, eaten_pos):
    """撤销走棋，恢复被吃的羊"""
    if move[0] == 'place':
        board[move[1]] = 0
    elif move[0] == 'move':
        board[move[2]] = 0
        board[move[1]] = player
    elif move[0] == 'eat':
        board[move[2]] = 0
        board[move[1]] = player
        if eaten_pos != -1:
            board[eaten_pos] = 2  # 把羊放回去