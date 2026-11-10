import os
import sys
import time
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import create_app
from core.rules import Game
from backend import dump_state, load_state


class ApiTest(unittest.TestCase):
    def setUp(self):
        # 接口层用 mock 引擎，保证测试快且与算法解耦。
        os.environ['TIGER_ENGINE'] = 'mock'
        self.app = create_app()
        self.client = self.app.test_client()

    def tearDown(self):
        self.app.extensions['ai_pool'].shutdown(wait=True)
        os.environ.pop('TIGER_ENGINE', None)

    def test_page(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'api.js', response.data)

    def test_move_and_roundtrip(self):
        state = self.client.get('/api/state').json['state']
        for _ in range(30):
            if state['over']:
                break
            move = state['legalMoves'][0]
            result = self.client.post('/api/move', json=dict(state=state, move=move))
            self.assertEqual(result.status_code, 200, result.json)
            state = result.json['state']
            self.assertEqual(load_state(state).moves, state['ply'])

    def test_invalid_payloads(self):
        state = dump_state(Game())
        for data in (None, [], {}, {'state': {}}, {'state': state, 'move': {'kind': 'place', 'to': 0}}):
            response = self.client.post('/api/move', json=data)
            self.assertIn(response.status_code, (400, 415))
        state['board'][0] = True
        self.assertEqual(self.client.post('/api/state', json={'state': state}).status_code, 400)

    def test_ai_job(self):
        state = dump_state(Game())
        result = self.client.post('/api/ai', json={'state': state})
        self.assertEqual(result.status_code, 202)
        key = result.json['taskId']
        for _ in range(100):
            result = self.client.get('/api/tasks/' + key)
            if result.json.get('status') != 'pending':
                break
            time.sleep(.01)
        self.assertEqual(result.json['status'], 'done')
        self.assertIn(result.json['move'], state['legalMoves'])
        self.assertEqual(result.json['engine'], 'mock')
        self.assertEqual(result.json['state']['ply'], 1)

    def test_terminal_and_isolation(self):
        g = Game()
        g.moves = 300
        state = dump_state(g)
        self.assertTrue(self.client.post('/api/state', json={'state': state}).json['state']['over'])
        self.assertEqual(self.client.get('/api/state').json['state']['ply'], 0)
        self.assertEqual(self.client.get('/api/tasks/missing').status_code, 404)


if __name__ == '__main__':
    unittest.main()
