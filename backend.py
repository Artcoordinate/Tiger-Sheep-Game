"""B 的状态/动作对象与 A 的 Game 之间的边界。状态由浏览器持有。"""
from core.rules import Game


def integer(value, low, high):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f'需要 {low}..{high} 的整数')
    return value


def load_state(data):
    if not isinstance(data, dict):
        raise ValueError('state 必须是对象')
    g = Game()
    board = data.get('board')
    if not isinstance(board, list) or len(board) != 37:
        raise ValueError('board 必须为 37 长数组')
    g.board = [integer(v, 0, 2) for v in board]
    g.player = integer(data.get('turn'), 1, 2)
    g.phase = integer(data.get('phase'), 1, 2)
    g.sheep_in_hand = integer(data.get('inHand'), 0, 16)
    g.captured = integer(data.get('captured'), 0, 24)
    g.moves = integer(data.get('ply'), 0, 300)
    if board.count(1) != 2 or board.count(2) + g.sheep_in_hand + g.captured != 24:
        raise ValueError('棋子数量不守恒：2 王、24 大臣（含手牌和被吃）')
    if g.phase != (1 if g.sheep_in_hand else 2):
        raise ValueError('phase 与 inHand 不一致')
    g._check_end()
    return g


def move_object(m):
    if m is None:
        return None
    return dict(kind=m[0], to=m[-1], **{'from': -1 if m[0] == 'place' else m[1]},
                over=m[2] if m[0] == 'eat' else -1)


def move_tuple(m):
    if not isinstance(m, dict) or m.get('kind') not in ('place', 'move', 'eat'):
        raise ValueError('动作必须包含 kind: place/move/eat')
    to = integer(m.get('to'), 0, 36)
    if m['kind'] == 'place':
        return ('place', to)
    frm = integer(m.get('from'), 0, 36)
    if m['kind'] == 'eat':
        return ('eat', frm, integer(m.get('over'), 0, 36), to)
    return ('move', frm, to)


def dump_state(g):
    return dict(board=g.board[:], turn=g.player, phase=g.phase,
                inHand=g.sheep_in_hand, captured=g.captured, ply=g.moves,
                lastMove=move_object(g.last_move), over=g.is_over(),
                winner=g.winner, reason=g.end_reason,
                legalMoves=[move_object(m) for m in g.legal_moves()])
