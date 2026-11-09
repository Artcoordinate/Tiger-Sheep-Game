# evaluate.py

def evaluate(board, phase):
    if phase == 1:
        # 添子阶段，随便返回个值
        return 0

    tigers = board.count(1)
    sheep = board.count(2)
    # 老虎剩得多分高，羊剩得多分低（对老虎不利）
    return tigers * 100 - sheep * 10


def check_game_over(board):
    if board.count(2) < 2: return True
    if board.count(1) == 0: return True
    return False