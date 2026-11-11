/* game.js —— 交互状态机（B 负责）
 *
 * 职责：
 *   1. 维护对局状态（棋盘、轮到谁、添子/走子阶段、手牌、选中项、历史）
 *   2. 把点击翻译成「选子 / 走子 / 放子 / 取消」
 *   3. 同步右侧信息面板与结束遮罩
 *   4. 人机模式下驱动 window.AI 应招
 *
 * 不含规则判断，合法性一律问 window.RULES（接口与 A 的 rules.py 对齐）；
 * 不含搜索算法，对手一律问 window.AI（接口与 D 的 rule_based.py 对齐）。
 */
(function () {
  'use strict';

  const L = window.BOARD_LAYOUT;
  const R = window.RULES;

  const canvas = document.getElementById('board');
  const view = new BoardView(canvas);

  const el = {
    turnCard: document.getElementById('turn-card'),
    turnDot: document.getElementById('turn-dot'),
    turnText: document.getElementById('turn-text'),
    minister: document.getElementById('stat-minister'),
    hand: document.getElementById('stat-hand'),
    ply: document.getElementById('stat-ply'),
    eaten: document.getElementById('stat-eaten'),
    hint: document.getElementById('hint'),
    btnRestart: document.getElementById('btn-restart'),
    btnUndo: document.getElementById('btn-undo'),
    modeSelect: document.getElementById('mode-select'),
    overlay: document.getElementById('overlay'),
    overIcon: document.getElementById('over-icon'),
    overTitle: document.getElementById('over-title'),
    overDesc: document.getElementById('over-desc'),
    overRestart: document.getElementById('over-restart'),
  };

  let state = null;
  let mode = 'ai';              // 'ai' 电脑执大臣 | 'ai-king' 电脑执王 | 'human' 真人双人
  let aiBusy = false;           // 电脑思考中，锁住鼠标
  let seq = 0;                  // 对局代数，用来作废旧的对局定时器

  let aiEnabled = false;        // 本局有没有电脑对手（false = 真人双人）
  let humanSide = R.KING;       // 人执哪一方
  let aiSide = R.MIN;           // 电脑执哪一方

  /* 按右上角下拉推导「谁执哪一方」。王先走，所以电脑执王时开局就轮到它。 */
  function applyMode() {
    mode = el.modeSelect ? el.modeSelect.value : 'ai';
    aiEnabled = (mode === 'ai' || mode === 'ai-king');
    aiSide = (mode === 'ai-king') ? R.KING : R.MIN;
    humanSide = (aiSide === R.KING) ? R.MIN : R.KING;
  }

  /* 演示 / 截图入口用：强制本地双人，不触发电脑 */
  function forceHuman() {
    mode = 'human';
    aiEnabled = false;
  }

  function sideName(side) {
    return side === R.KING ? '王' : '大臣';
  }

  /* ---------------------------------------------------------- 状态 */
  function newGame() {
    aiBusy = false;
    seq++;
    applyMode();

    state = {
      board: L.initBoard.slice(),
      turn: R.RULE.firstPlayer,     // A 的规则：王先走
      phase: 1,                     // 1 = 添子阶段
      inHand: L.sheepInHand,        // 大臣手里还有 16 枚
      captured: 0,                  // 已被王吃掉的大臣数
      ply: 0,
      selected: -1,
      targets: [],
      lastMove: null,
      history: [],
      over: false,
    };

    // 演示 / 截图入口：
    //   index.html#demo  → 选中王，展示跳吃红圈
    //   index.html#place → 添子阶段，展示所有可放点位
    if (location.hash === '#demo') {
      forceHuman();
      state.selected = L.tigerStart[0];
      state.targets = R.movesOf(state, state.selected);
    } else if (location.hash === '#place') {
      forceHuman();
      state.turn = R.MIN;
      state.targets = R.legalMoves(state);
    } else if (location.hash === '#aiplay') {
      // 演示：人机对局进行中的画面（王先吃一手，大臣补一手）
      forceHuman();
      applyToState({ kind: 'eat', from: 8, over: 12, to: 16 });
      applyToState({ kind: 'place', from: -1, over: -1, to: 18 });
    }

    hideOverlay();
    setHint(hintForTurn());
    render();
    maybeAI();
  }

  function applyToState(mv) {
    const nx = R.applyMove(state, mv);
    state.board = nx.board;
    state.phase = nx.phase;
    state.inHand = nx.inHand;
    state.captured = nx.captured;
    state.turn = nx.turn;
    state.ply = nx.ply;
    state.lastMove = nx.lastMove;
  }

  function snapshot() {
    return {
      board: state.board.slice(),
      turn: state.turn,
      phase: state.phase,
      inHand: state.inHand,
      captured: state.captured,
      ply: state.ply,
      lastMove: state.lastMove,
    };
  }

  function restore(prev) {
    state.board = prev.board;
    state.turn = prev.turn;
    state.phase = prev.phase;
    state.inHand = prev.inHand;
    state.captured = prev.captured;
    state.ply = prev.ply;
    state.lastMove = prev.lastMove;
    state.selected = -1;
    state.targets = [];
    state.over = false;
  }

  function hintForTurn() {
    if (aiEnabled && state.turn === aiSide) {
      return '轮到电脑（' + sideName(aiSide) + '）。';
    }
    if (state.phase === 1 && state.turn === R.MIN) {
      return '添子阶段：点任意空点放下大臣（手里还有 ' + state.inHand + ' 枚）。';
    }
    if (state.turn === R.KING) {
      return '轮到王：点黑子选中，绿圈是普通移动，红圈是跳吃。';
    }
    return '轮到大臣：点白子选中，再点绿圈移动。';
  }

  /* ---------------------------------------------------------- 渲染 */
  function render() {
    view.setState(state);

    el.minister.textContent = R.count(state.board, R.MIN);
    el.hand.textContent = state.inHand;
    el.ply.textContent = state.ply;
    el.eaten.textContent = state.captured;

    const isKing = state.turn === R.KING;
    const who = aiEnabled ? (state.turn === aiSide ? ' · 电脑' : ' · 你') : '';
    el.turnText.textContent = (isKing ? '黑方 · 王' : '白方 · 大臣') + who;
    el.turnDot.className = 'turn-dot' + (isKing ? ' king' : '');
    el.turnCard.className = 'turn-card' + (isKing ? ' active-king' : '');

    el.btnUndo.disabled = state.history.length === 0;
  }

  function setHint(text, warn) {
    el.hint.textContent = text;
    el.hint.className = 'hint' + (warn ? ' warn' : '');
  }

  function clearSel() {
    state.selected = -1;
    state.targets = [];
    render();
  }

  /* ---------------------------------------------------------- 走子 */
  async function doMove(move) {
    const generation = seq;
    aiBusy = true;
    let response;
    try {
      response = await API.request("/api/move", {state: snapshot(), move});
    } catch (error) {
      if (generation === seq) { aiBusy = false; setHint(error.message, true); }
      return;
    }
    if (generation !== seq) return;
    aiBusy = false;
    state.history.push(snapshot());

    const mover = state.turn;
    const next = response.state;

    state.board = next.board;
    state.phase = next.phase;
    state.inHand = next.inHand;
    state.captured = next.captured;
    state.turn = next.turn;
    state.ply = next.ply;
    state.lastMove = next.lastMove;
    state.selected = -1;
    state.targets = [];

    view.pulseAt(move.to);

    if (move.kind === 'place') {
      setHint('大臣放到 ' + move.to + ' 号点，手里还剩 ' + state.inHand + ' 枚。'
        + (state.phase === 2 ? '16 枚已放完，进入走子阶段。' : ''));
    } else if (move.kind === 'eat') {
      setHint('王跳过 ' + move.over + ' 号点的大臣落到 ' + move.to
        + ' 号点，累计吃掉 ' + state.captured + ' / ' + R.RULE.kingWinWhenCaptured + ' 枚。');
    } else {
      setHint((mover === R.KING ? '王' : '大臣') + '从 ' + move.from + ' 移到 ' + move.to + ' 号点。');
    }

    render();
    checkEnd();
    if (!state.over) maybeAI();
  }

  /* ---------------------------------------------------------- 电脑应招 */
  function maybeAI() {
    if (!aiEnabled || state.over) return;
    if (state.turn !== aiSide) return;
    if (!window.AI) return;

    aiBusy = true;
    setHint('电脑（' + sideName(aiSide) + '）正在思考…');

    const my = seq;
    // 加一点延迟，让“AI 思考”在白板上看得出来
    setTimeout(async function () {
      if (my !== seq) return;          // 期间点过重新开始 / 换模式，作废
      if (!state || state.over) { aiBusy = false; return; }
      try {
        const mv = await window.AI.chooseMove(snapshot());
        if (my !== seq) return;
        aiBusy = false;
        if (!mv) { checkEnd(); return; }
        await doMove(mv);
      } catch (error) {
        if (my !== seq) return;
        aiBusy = false;
        setHint(error.message + '；可悔棋或重新开始。', true);
      }
    }, 360);
  }

  function checkEnd() {
    const res = R.checkEnd(state);
    if (res) finish(res.winner, res.reason);
  }

  function finish(winner, desc) {
    state.over = true;
    state.selected = -1;
    state.targets = [];
    render();

    if (winner === R.KING) {
      el.overIcon.textContent = '♔';
      el.overTitle.textContent = '王 方 获 胜';
      setHint('王方获胜。');
    } else if (winner === R.MIN) {
      el.overIcon.textContent = '♙';
      el.overTitle.textContent = '大 臣 方 获 胜';
      setHint('大臣方获胜。');
    } else {
      el.overIcon.textContent = '½';
      el.overTitle.textContent = '和  棋';
      setHint('和棋。');
    }
    el.overDesc.textContent = desc;
    el.overlay.classList.remove('hidden');
  }

  function hideOverlay() {
    el.overlay.classList.add('hidden');
  }

  /* ---------------------------------------------------------- 点击 */
  canvas.addEventListener('click', function (e) {
    if (!state || state.over || aiBusy) return;

    const idx = view.hitTest(e.clientX, e.clientY);

    // 点到盘外或过远
    if (idx < 0) {
      clearSel();
      return;
    }

    // 1. 落到已高亮的点 → 走这一步
    for (let i = 0; i < state.targets.length; i++) {
      if (state.targets[i].to === idx) {
        doMove(state.targets[i]);
        return;
      }
    }

    // 2. 添子阶段：点空点直接放下大臣
    if (state.phase === 1 && state.turn === R.MIN) {
      if (state.board[idx] === R.EMPTY) {
        doMove({ kind: 'place', from: -1, over: -1, to: idx });
      } else {
        setHint('这个点上已经有棋子了，挑一个空点放。', true);
        clearSel();
      }
      return;
    }

    // 3. 选中自己的棋子
    if (state.board[idx] === state.turn) {
      const moves = R.movesOf(state, idx);
      state.selected = idx;
      state.targets = moves;
      if (moves.length === 0) {
        setHint(idx + ' 号点的这枚棋子当前无路可走，换一枚试试。', true);
      } else if (moves.some(function (m) { return m.kind === 'eat'; })) {
        setHint('已选中 ' + idx + ' 号点——红圈是跳吃落点，绿圈是普通移动。');
      } else {
        setHint('已选中 ' + idx + ' 号点，点击绿圈落子。');
      }
      render();
      return;
    }

    // 4. 点到对方棋子 / 别处 → 取消
    if (state.selected >= 0) {
      setHint('这里不能落子，已取消选择。', true);
    }
    clearSel();
  });

  /* ---------------------------------------------------------- 按钮 */
  el.btnRestart.addEventListener('click', newGame);
  el.overRestart.addEventListener('click', newGame);

  if (el.modeSelect) {
    el.modeSelect.addEventListener('change', function () {
      if (location.hash) history.replaceState(null, '', location.pathname);
      newGame();
    });
  }

  el.btnUndo.addEventListener('click', function () {
    if (aiBusy || !state.history.length) return;

    restore(state.history.pop());
    // 人机模式下退回人类回合：电脑一步 + 人类一步一起撤
    if (aiEnabled && state.turn !== humanSide && state.history.length) {
      restore(state.history.pop());
    }

    hideOverlay();
    setHint('已悔棋，回到第 ' + state.ply + ' 手。' + hintForTurn().replace(/^.*?：/, ''));
    render();
  });

  /* ---------------------------------------------------------- 启动 */
  newGame();
})();
