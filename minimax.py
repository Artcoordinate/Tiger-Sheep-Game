# minimax.py
from mini_graph import mini_init_board
from generate_moves import generate_moves, make_move, undo_move
from evaluate import evaluate, check_game_over


def minimax(board, depth, alpha, beta, is_maximizing, phase, remaining_sheep):
    # 1. 终点判定
    if depth == 0 or check_game_over(board):
        return evaluate(board, phase)

    if is_maximizing:
        max_eval = -99999
        moves = generate_moves(board, player=1, phase=phase, remaining_sheep=remaining_sheep)
        for move in moves:
            eaten_pos = make_move(board, move, player=1)
            eval = minimax(board, depth - 1, alpha, beta, False, phase, remaining_sheep)
            undo_move(board, move, player=1, eaten_pos=eaten_pos)

            max_eval = max(max_eval, eval)
            alpha = max(alpha, eval)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = 99999
        moves = generate_moves(board, player=2, phase=phase, remaining_sheep=remaining_sheep)
        for move in moves:
            eaten_pos = make_move(board, move, player=2)
            eval = minimax(board, depth - 1, alpha, beta, True, phase, remaining_sheep)
            undo_move(board, move, player=2, eaten_pos=eaten_pos)

            min_eval = min(min_eval, eval)
            beta = min(beta, eval)
            if beta <= alpha:
                break
        return min_eval


def get_best_move(board, player, phase, remaining_sheep, depth=3):
    """
    这是提供给后端(C)和前端(B)调用的唯一接口。
    输入:
        board: 长度为37的一维数组 (等你换了37格数据后就是37)
        player: 1 代表老虎, 2 代表羊
        phase: 1 代表添子阶段, 2 代表走子阶段
        remaining_sheep: 剩余需要放下的羊数量
        depth: 搜索深度，默认3，如果太慢可以改成2
    输出:
        一个元组，例如 ('eat', 0, 2) 或 ('place', 5) 或 ('move', 3, 4)
        如果无路可走，返回 None
    """
    best_score = -99999 if player == 1 else 99999
    best_move = None

    moves = generate_moves(board, player, phase, remaining_sheep)
    if not moves:
        return None

    for move in moves:
        eaten_pos = make_move(board, move, player)
        # 注意：这里的 is_maximizing 是 False（因为如果当前是老虎走，下一步该羊走极小化）
        eval = minimax(board, depth - 1, -99999, 99999, player == 2, phase, remaining_sheep)
        undo_move(board, move, player, eaten_pos=eaten_pos)

        if player == 1:  # 老虎要最大分
            if eval > best_score:
                best_score = eval
                best_move = move
        else:  # 羊要最小分
            if eval < best_score:
                best_score = eval
                best_move = move

    return best_move


if __name__ == '__main__':
    # 造一个老虎可以吃羊的局：
    # 0: 虎, 1: 羊, 2: 空
    # 老虎在 0 号位置，羊在 1 号位置，2 号位置是空的（根据 mini_adj，0连着1，1连着2）
    test_board = [
        1, 2, 0,
        0, 0, 0,
        0, 0, 0
    ]
    print("测试棋盘:", test_board)

    # 我们手动写一个提取最佳走法的逻辑（这部分以后要封装给 C）
    print("老虎正在思考怎么吃羊...")

    best_score = -99999
    best_move = None
    alpha = -99999
    beta = 99999

    # 获取老虎所有合法走法
    moves = generate_moves(test_board, player=1, phase=2, remaining_sheep=16)

    for move in moves:
        eaten_pos = make_move(test_board, move, player=1)
        # 刚走完，轮到羊（极小化），深度设小一点，比如 2
        eval = minimax(test_board, depth=2, alpha=alpha, beta=beta, is_maximizing=False, phase=2, remaining_sheep=16)
        undo_move(test_board, move, player=1, eaten_pos=eaten_pos)

        if eval > best_score:
            best_score = eval
            best_move = move

    print(f"AI 找到的最佳走法: {best_move} (得分: {best_score})")