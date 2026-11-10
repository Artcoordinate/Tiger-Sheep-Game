"""本地课程演示服务。运行 python app.py，访问 http://127.0.0.1:5000。"""
from concurrent.futures import ThreadPoolExecutor
from threading import Lock, BoundedSemaphore
from time import monotonic
from uuid import uuid4

from flask import Flask, jsonify, render_template, request
from werkzeug.exceptions import HTTPException
from backend import load_state, dump_state, move_tuple, move_object
from core.rules import Game
from engines.adapter import choose


def create_app():
    app = Flask(__name__)
    app.config['MAX_CONTENT_LENGTH'] = 16384
    pool = ThreadPoolExecutor(max_workers=2, thread_name_prefix='ai')
    slots = BoundedSemaphore(4)
    jobs, lock = {}, Lock()

    def body():
        data = request.get_json()
        if not isinstance(data, dict):
            raise ValueError('JSON 请求体必须是对象')
        return data

    @app.errorhandler(ValueError)
    def invalid(e):
        return jsonify(error=str(e)), 400

    @app.errorhandler(HTTPException)
    def http_error(e):
        return jsonify(error=e.description), e.code

    @app.get('/')
    def index():
        return render_template('index.html')

    @app.get('/api/state')
    def initial():
        return jsonify(state=dump_state(Game()))

    @app.post('/api/state')
    def state():
        return jsonify(state=dump_state(load_state(body().get('state'))))

    @app.post('/api/move')
    def move():
        data = body()
        g = load_state(data.get('state'))
        g.apply(move_tuple(data.get('move')))
        return jsonify(state=dump_state(g))

    def compute(g):
        try:
            move, engine = choose(g)
            if move is not None:
                g.apply(move)
            return dict(move=move_object(move), state=dump_state(g), engine=engine)
        finally:
            slots.release()

    @app.post('/api/ai')
    def ai():
        g = load_state(body().get('state'))
        with lock:
            now = monotonic()
            for key, (created, future) in list(jobs.items()):
                if future.done() and now - created > 300:
                    del jobs[key]
            if len(jobs) >= 256 or not slots.acquire(blocking=False):
                return jsonify(error='AI 队列已满，请稍后重试'), 429
            key = uuid4().hex
            try:
                jobs[key] = (now, pool.submit(compute, g))
            except Exception:
                slots.release()
                raise
        return jsonify(taskId=key, status='pending'), 202

    @app.get('/api/tasks/<key>')
    def task(key):
        with lock:
            entry = jobs.get(key)
        if entry is None:
            return jsonify(error='任务不存在或已过期'), 404
        future = entry[1]
        if not future.done():
            return jsonify(status='pending')
        try:
            return jsonify(status='done', **future.result())
        except Exception:
            app.logger.exception('AI task failed')
            return jsonify(status='failed', error='算法计算失败，请查看后端日志'), 500

    app.extensions['ai_pool'] = pool
    return app


app = create_app()
if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, threaded=True, debug=False)
