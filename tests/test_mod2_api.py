import os
import sys
import time
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import create_app
from backend import dump_state, move_object
from core.rules import Game


class Mod2ApiTest(unittest.TestCase):
    def setUp(self):
        self.env = patch.dict(os.environ, {'TIGER_ENGINE': 'rule_based', 'TIGER_MCTS_TIME': '.01',
                                           'TIGER_MCTS_PLAYOUTS': '2', 'TIGER_MCTS_ROLLOUT': '2'})
        self.env.start()
        os.environ.pop('TIGER_ENGINE_API', None)
        self.app = create_app()
        self.client = self.app.test_client()

    def tearDown(self):
        self.app.extensions['ai_pool'].shutdown(wait=True)
        self.env.stop()

    def job(self, state, engine=None):
        payload = {'state': state}
        if engine is not None:
            payload['engine'] = engine
        response = self.client.post('/api/ai', json=payload)
        self.assertEqual(response.status_code, 202, response.json)
        for _ in range(500):
            result = self.client.get('/api/tasks/' + response.json['taskId'])
            if result.json.get('status') != 'pending':
                self.assertEqual(result.status_code, 200, result.json)
                return result.json
            time.sleep(.01)
        self.fail('AI task timeout')

    def test_explicit_mcts_both_sides(self):
        g = Game()
        for _ in range(2):
            state = dump_state(g)
            result = self.job(state, 'mcts')
            self.assertEqual(result['engine'], 'mcts')
            self.assertIn(result['move'], state['legalMoves'])
            from backend import load_state
            g = load_state(result['state'])

    def test_default_and_request_override(self):
        state = dump_state(Game())
        self.assertEqual(self.job(state)['engine'], 'rule_based')
        self.assertEqual(self.job(state, 'mock')['engine'], 'mock')
        self.assertEqual(os.environ['TIGER_ENGINE'], 'rule_based')

    def test_invalid_engine_before_submit(self):
        for name in ('bogus', '../mcts', [], 1):
            r = self.client.post('/api/ai', json={'state': dump_state(Game()), 'engine': name})
            self.assertEqual(r.status_code, 400)

    def record(self):
        return dict(version=1, engine='mcts', mode='ai', humanSide='king', result=None,
                    reason='', date='2026-11-23', blackName='玩家', whiteName='MCTS', moves=[])

    def test_record_replay_and_turn(self):
        r = self.record()
        move = move_object(Game().legal_moves()[0])
        r['moves'] = [dict(move, side='king')]
        response = self.client.post('/api/records/validate', json={'record': r})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['plies'], 1)
        r['moves'][0]['side'] = 'minister'
        self.assertEqual(self.client.post('/api/records/validate', json={'record': r}).status_code, 400)

    def test_record_false_result(self):
        r = self.record()
        r['result'] = 'draw'
        self.assertEqual(self.client.post('/api/records/validate', json={'record': r}).status_code, 400)

    def test_record_complete(self):
        g = Game()
        r = self.record()
        while not g.is_over():
            m = g.legal_moves()[0]
            r['moves'].append(dict(move_object(m), side='king' if g.player == 1 else 'minister'))
            g.apply(m)
        r['result'] = {0: 'draw', 1: 'king_win', 2: 'minister_win'}[g.winner]
        response = self.client.post('/api/records/validate', json={'record': r})
        self.assertEqual(response.status_code, 200, response.json)
        self.assertTrue(response.json['complete'])
