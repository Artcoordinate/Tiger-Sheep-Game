/* board.js —— 37 点棋盘 Canvas 渲染层（B 负责）
 *
 * 只做三件事：把数据画成棋盘、把点击换算成节点编号、把状态高亮出来。
 * 不含任何规则判断，规则全部走 window.RULES。
 *
 * 数据来源：js/board_data.js（由 scripts/export_board.py 从 vendor/board.py 生成）
 * 布局：A 给的坐标已含 60px 边距，bbox 就是整张画布，等比缩放到屏幕。
 */
(function () {
  'use strict';

  const L = window.BOARD_LAYOUT;
  const PAD = 0;                                     // A 的坐标已含边距，不再另加
  const X0 = L.bbox[0], Y0 = L.bbox[1];
  const X1 = L.bbox[2], Y1 = L.bbox[3];
  const VW = (X1 - X0) + PAD * 2;
  const VH = (Y1 - Y0) + PAD * 2;

  const CELL = L.cell || 72;                         // 一格的像素数（A 的坐标基准）
  const PIECE_R = 0.24 * CELL;                       // 棋子半径 = 0.24 格
  const HIT_R = 0.55 * CELL;                         // 点击命中半径 = 0.55 格

  const C = {
    board: '#b07a46',
    line: '#141414',
    select: '#f0b429',
    target: 'rgba(74, 222, 128, 0.50)',
    targetEdge: 'rgba(148, 255, 190, 0.95)',
    capture: 'rgba(239, 83, 80, 0.55)',
    captureEdge: 'rgba(255, 138, 128, 0.95)',
    last: 'rgba(255, 238, 180, 0.9)',
  };

  class BoardView {
    constructor(canvas) {
      this.canvas = canvas;
      this.ctx = canvas.getContext('2d');
      this.state = null;
      this.pulse = null;
      this.dirty = true;
      this.scale = 1;
      this.w = 0;
      this.h = 0;

      this._resize();
      if (window.ResizeObserver) {
        new ResizeObserver(() => this._resize()).observe(canvas.parentElement);
      } else {
        window.addEventListener('resize', () => this._resize());
      }
      this._tick = this._loop.bind(this);
      requestAnimationFrame(this._tick);
    }

    /* ------------------------------ 尺寸 / 坐标 ------------------------------ */
    _resize() {
      const wrap = this.canvas.parentElement;
      let w = Math.max(280, wrap.clientWidth || 640);
      let h = Math.round(w * VH / VW);

      // 窗口不够高时改成按高度反算宽度，避免棋盘把页面顶出一屏
      const maxH = Math.max(320, window.innerHeight - 170);
      if (h > maxH) {
        h = Math.round(maxH);
        w = Math.round(h * VW / VH);
        this.canvas.style.width = w + 'px';
      } else {
        this.canvas.style.width = '100%';
      }

      const dpr = window.devicePixelRatio || 1;

      this.canvas.style.height = h + 'px';
      this.canvas.width = Math.round(w * dpr);
      this.canvas.height = Math.round(h * dpr);
      this.ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

      this.w = w;
      this.h = h;
      this.scale = w / VW;
      this.dirty = true;
    }

    px(x) { return (x - X0 + PAD) * this.scale; }
    py(y) { return (y - Y0 + PAD) * this.scale; }

    /* ------------------------------ 对外接口 ------------------------------ */
    setState(s) { this.state = s; this.dirty = true; }

    pulseAt(node) { this.pulse = { node: node, t0: performance.now() }; this.dirty = true; }

    hitTest(clientX, clientY) {
      const rect = this.canvas.getBoundingClientRect();
      const x = (clientX - rect.left) / this.scale + X0 - PAD;
      const y = (clientY - rect.top) / this.scale + Y0 - PAD;

      let best = -1;
      let bestD = Infinity;
      for (let i = 0; i < L.nodes.length; i++) {
        const dx = L.nodes[i][0] - x;
        const dy = L.nodes[i][1] - y;
        const d = dx * dx + dy * dy;
        if (d < bestD) { bestD = d; best = i; }
      }
      return bestD <= HIT_R * HIT_R ? best : -1;
    }

    /* ------------------------------ 主循环 ------------------------------ */
    _loop(ts) {
      if (this.pulse) {
        if (ts - this.pulse.t0 > 460) this.pulse = null;
        this.dirty = true;
      }
      if (this.dirty && this.state) {
        this.draw(ts);
        this.dirty = false;
      }
      requestAnimationFrame(this._tick);
    }

    /* ------------------------------ 绘制 ------------------------------ */
    draw(ts) {
      const ctx = this.ctx;
      const s = this.scale;
      const st = this.state;

      ctx.clearRect(0, 0, this.w, this.h);

      // 1. 木色底板
      ctx.fillStyle = C.board;
      ctx.fillRect(this.px(X0), this.py(Y0), (X1 - X0) * s, (Y1 - Y0) * s);

      // 2. 76 条连线
      ctx.beginPath();
      for (let i = 0; i < L.edges.length; i++) {
        const a = L.edges[i][0];
        const b = L.edges[i][1];
        ctx.moveTo(this.px(L.nodes[a][0]), this.py(L.nodes[a][1]));
        ctx.lineTo(this.px(L.nodes[b][0]), this.py(L.nodes[b][1]));
      }
      ctx.strokeStyle = C.line;
      ctx.lineWidth = Math.max(1.0, s * 0.026 * CELL);
      ctx.lineCap = 'round';
      ctx.stroke();

      const r = PIECE_R * s;

      // 3. 上一步的起点/落点（添子阶段没有起点，from 为 -1）
      if (st.lastMove) {
        if (st.lastMove.from >= 0) {
          this._ring(this.px(L.nodes[st.lastMove.from][0]), this.py(L.nodes[st.lastMove.from][1]),
                     r * 1.5, C.last, 1.5, [s * 0.03 * CELL, s * 0.05 * CELL]);
        }
        this._ring(this.px(L.nodes[st.lastMove.to][0]), this.py(L.nodes[st.lastMove.to][1]),
                   r * 1.5, C.last, 1.5, [s * 0.03 * CELL, s * 0.05 * CELL]);
      }

      // 4. 合法落点
      for (let i = 0; i < st.targets.length; i++) {
        const m = st.targets[i];
        const x = this.px(L.nodes[m.to][0]);
        const y = this.py(L.nodes[m.to][1]);
        const cap = m.kind === 'eat';              // 虎跳吃落点画红圈
        ctx.beginPath();
        ctx.arc(x, y, r * 0.66, 0, Math.PI * 2);
        ctx.fillStyle = cap ? C.capture : C.target;
        ctx.fill();
        ctx.lineWidth = Math.max(1.2, s * 0.022);
        ctx.strokeStyle = cap ? C.captureEdge : C.targetEdge;
        ctx.stroke();
      }

      // 5. 选中光环
      if (st.selected >= 0) {
        this._ring(this.px(L.nodes[st.selected][0]), this.py(L.nodes[st.selected][1]),
                   r * 1.42, C.select, 2.2, null);
      }

      // 6. 棋子
      for (let i = 0; i < L.nodeCount; i++) {
        const v = st.board[i];
        if (v === 0) continue;
        const x = this.px(L.nodes[i][0]);
        const y = this.py(L.nodes[i][1]);
        if (v === 1) this._king(ctx, x, y, r);
        else this._minister(ctx, x, y, r);
      }

      // 7. 落子脉冲
      if (this.pulse) {
        const t = (ts - this.pulse.t0) / 460;
        if (t < 1) {
          const x = this.px(L.nodes[this.pulse.node][0]);
          const y = this.py(L.nodes[this.pulse.node][1]);
          ctx.beginPath();
          ctx.arc(x, y, r * (1 + t * 1.7), 0, Math.PI * 2);
          ctx.strokeStyle = 'rgba(255, 244, 200, ' + (0.75 * (1 - t)).toFixed(3) + ')';
          ctx.lineWidth = Math.max(1.5, s * 0.04 * CELL * (1 - t));
          ctx.stroke();
        }
      }
    }

    _ring(x, y, radius, color, width, dash) {
      const ctx = this.ctx;
      ctx.save();
      ctx.beginPath();
      if (dash) ctx.setLineDash(dash);
      ctx.arc(x, y, radius, 0, Math.PI * 2);
      ctx.strokeStyle = color;
      ctx.lineWidth = width;
      ctx.stroke();
      ctx.restore();
    }

    _king(ctx, x, y, r) {
      ctx.save();
      ctx.beginPath();
      ctx.arc(x, y, r * 1.06, 0, Math.PI * 2);
      ctx.fillStyle = 'rgba(0, 0, 0, 0.28)';
      ctx.fill();

      const g = ctx.createRadialGradient(x - r * 0.36, y - r * 0.40, r * 0.10, x, y, r);
      g.addColorStop(0, '#7a7a7a');
      g.addColorStop(0.42, '#2a2a2a');
      g.addColorStop(1, '#040404');
      ctx.beginPath();
      ctx.arc(x, y, r, 0, Math.PI * 2);
      ctx.fillStyle = g;
      ctx.fill();
      ctx.strokeStyle = 'rgba(0, 0, 0, 0.9)';
      ctx.lineWidth = Math.max(0.8, r * 0.10);
      ctx.stroke();
      ctx.restore();
    }

    _minister(ctx, x, y, r) {
      ctx.save();
      ctx.beginPath();
      ctx.arc(x, y, r * 1.06, 0, Math.PI * 2);
      ctx.fillStyle = 'rgba(0, 0, 0, 0.28)';
      ctx.fill();

      const g = ctx.createRadialGradient(x - r * 0.36, y - r * 0.40, r * 0.10, x, y, r);
      g.addColorStop(0, '#ffffff');
      g.addColorStop(0.55, '#efe7d9');
      g.addColorStop(1, '#b8ad9a');
      ctx.beginPath();
      ctx.arc(x, y, r, 0, Math.PI * 2);
      ctx.fillStyle = g;
      ctx.fill();
      ctx.strokeStyle = '#1a1a1a';
      ctx.lineWidth = Math.max(0.9, r * 0.11);
      ctx.stroke();
      ctx.restore();
    }
  }

  window.BoardView = BoardView;
})();
