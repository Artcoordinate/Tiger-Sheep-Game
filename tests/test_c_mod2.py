import os
import sys
import time
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import create_app
from backend import dump_state, load_state
from core.rules import Game


class CMod2Test(unittest.TestCase):
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

    def job(self, g, engine=None):
        payload = {'state': dump_state(g)}
        if engine is not None:
            payload['engine'] = engine
        response = self.client.post('/api/ai', json=payload)
        self.assertEqual(response.status_code, 202, response.json)
        for _ in range(500):
            result = self.client.get('/api/tasks/' + response.json['taskId'])
            if result.json.get('status') != 'pending':
                self.assertEqual(result.status_code, 200, result.json)
                self.assertEqual(response.json['engine'], result.json['engine'])
                return result.json
            time.sleep(.01)
        self.fail('AI timeout')

    def test_mcts_both_sides(self):
        g = Game()
        for _ in range(2):
            result = self.job(g, 'mcts')
            self.assertEqual(result['engine'], 'mcts')
            from backend import move_object
            self.assertIn(result['move'], [move_object(m) for m in g.legal_moves()])
            g = load_state(result['state'])

    def test_default(self):
        self.assertEqual(self.job(Game())['engine'], 'rule_based')

    def test_override_without_global_change(self):
        self.assertEqual(self.job(Game(), 'mcts')['engine'], 'mcts')
        self.assertEqual(os.environ['TIGER_ENGINE'], 'rule_based')

    def test_invalid_engine_before_enqueue(self):
        with patch('app.ThreadPoolExecutor.submit') as submit:
            for name in ('', 'bogus', 'adapter', '__init__', '../mcts', 'cnn', [], 1):
                response = self.client.post('/api/ai', json={'state': dump_state(Game()), 'engine': name})
                self.assertEqual(response.status_code, 400, name)
            submit.assert_not_called()

    def test_invalid_environment_default(self):
        os.environ['TIGER_ENGINE'] = 'bogus'
        self.assertEqual(self.client.post('/api/ai', json={'state': dump_state(Game())}).status_code, 400)
        self.assertEqual(self.job(Game(), 'mcts')['engine'], 'mcts')

    def test_legacy_rejected(self):
        os.environ['TIGER_ENGINE_API'] = 'legacy'
        self.assertEqual(self.client.post('/api/ai', json={'state': dump_state(Game()), 'engine': 'mcts'}).status_code, 400)
