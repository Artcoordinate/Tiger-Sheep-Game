"""B version=1 棋谱 JSON：从初始局面逐步验证，不持久化。"""
from datetime import date
from backend import move_tuple, dump_state
from core.rules import Game


def validate_record(record):
    if not isinstance(record, dict) or type(record.get('version')) is not int or record['version'] != 1:
        raise ValueError('棋谱必须为 version=1 的对象')
    if record.get('engine') not in ('rule_based', 'mcts'):
        raise ValueError('棋谱 engine 必须为 rule_based/mcts')
    expected = {'ai': 'king', 'ai-king': 'minister', 'human': None}
    mode = record.get('mode')
    if not isinstance(mode, str) or mode not in expected or record.get('humanSide') != expected[mode]:
        raise ValueError('mode/humanSide 不一致')
    for key in ('date', 'blackName', 'whiteName', 'reason'):
        if not isinstance(record.get(key), str) or len(record[key]) > 1000:
            raise ValueError(f'{key} 必须为不超过1000字符的文本')
    try:
        if date.fromisoformat(record['date']).isoformat() != record['date']:
            raise ValueError()
    except ValueError:
        raise ValueError('date 必须为有效 YYYY-MM-DD 日期') from None
    moves = record.get('moves')
    if not isinstance(moves, list) or len(moves) > 300:
        raise ValueError('moves 必须为最多300步的数组')
    g = Game()
    for i, move in enumerate(moves, 1):
        try:
            if not isinstance(move, dict) or move.get('side') != ('king' if g.player == 1 else 'minister'):
                raise ValueError('行棋方与当前回合不符')
            action = move_tuple(move)
            if move.get('kind') == 'place' and (move.get('from') != -1 or move.get('over') != -1):
                raise ValueError('添子 from/over 应为 -1')
            if move.get('kind') == 'move' and move.get('over') != -1:
                raise ValueError('普通移动 over 应为 -1')
            g.apply(action)
        except ValueError as e:
            raise ValueError(f'棋谱第{i}步非法：{e}') from None
    result = {1: 'king_win', 2: 'minister_win', 0: 'draw', None: None}[g.winner]
    if record.get('result') != result:
        raise ValueError(f'棋谱 result 与重放结果不一致，应为 {result}')
    return dict(valid=True, plies=g.moves, complete=g.is_over(), result=result, state=dump_state(g))
