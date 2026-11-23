import importlib
import os


AVAILABLE_ENGINES = ('rule_based', 'mcts', 'mock')


def resolve_engine(name=None):
    name = os.environ.get('TIGER_ENGINE', 'rule_based') if name is None else name
    if not isinstance(name, str) or name not in AVAILABLE_ENGINES:
        raise ValueError('没有这个引擎；可选 rule_based / mcts / mock')
    if os.environ.get('TIGER_ENGINE_API') == 'legacy' and name != 'mock':
        raise ValueError('正式引擎使用 choose_move(game)，请清除 TIGER_ENGINE_API=legacy')
    return name


def choose(game, engine=None):
    # D 可提供 choose_move(game)，或旧版四参数 choose_move。
    # 默认使用正式引擎 rule_based；联调/对照可用 TIGER_ENGINE=mock。
    name = resolve_engine(engine)
    module = importlib.import_module('engines.' + name)
    if os.environ.get('TIGER_ENGINE_API') == 'legacy':
        move = module.choose_move(game.board[:], game.phase, game.player, game.sheep_in_hand)
    else:
        move = module.choose_move(game.copy())
    if isinstance(move, dict):
        from backend import move_tuple
        move = move_tuple(move)
    if move is not None:
        move = tuple(move)
        # 兼容旧的三元组 eat：通过合法动作补齐 over。
        if len(move) == 3 and move[0] == 'eat':
            move = next((m for m in game.legal_moves() if m[0] == 'eat'
                         and m[1] == move[1] and m[-1] == move[-1]), move)
    if move not in game.legal_moves():
        if move is None and game.is_over():
            return None, name
        raise RuntimeError('算法返回了非法动作，请检查 D/E 引擎')
    return move, name
