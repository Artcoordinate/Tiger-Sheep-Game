/* rules_stub.js —— 规则层（B 的临时实现，逐条复刻 A 的 vendor/rules.py）
 *
 * 为什么叫 stub：
 *   C 的 Flask 起来后，把 legalMoves / applyMove / checkEnd 换成
 *   fetch('/api/state') 和 fetch('/api/move')，board.js 与 game.js 一行都不用改。
 *
 * 和 A 的 rules.py 完全一致：
 *   1. 王(虎) 先走
 *   2. 大臣(羊) 前 16 手只能添子 place，第 16 枚放完自动进入走子阶段
 *   3. 王走一步；跳吃必须"王 - 大臣 - 空"三点共线、大臣落在正中间、且都是相邻格
 *   4. 王累计吃掉 10 枚大臣 → 王胜
 *   5. 总步数达到 300 → 和棋
 *   6. 轮到某方却没有合法走法 → 对方胜
 *
 * 走法对象统一为：
 *   { kind: 'place' | 'move' | 'eat', from, over, to }
 *   place 时 from / over 都是 -1
 */
(function () {
  'use strict';

  const L = window.BOARD_LAYOUT;
  const N = L.nodeCount;

  const KING = 1;          // A 的 TIGER
  const MIN = 2;           // A 的 SHEEP
  const EMPTY = 0;

  const RULE = {
    kingWinWhenCaptured: 10,          // 王累计吃掉 10 枚大臣 → 王胜
    drawAtPly: 300,                   // 总步数 300 → 和棋
    firstPlayer: L.firstPlayer || KING,
  };

  // (row,col) -> 下标。A 用棋盘格坐标推中点，这里也照做，保证和 rules.py 同一算法。
  const IDX = new Map();
  for (let i = 0; i < N; i++) IDX.set(L.points[i][0] * 5 + L.points[i][1], i);
  const ADJ = L.adj;

  const STEP = 1;                    // A 要求跳吃两段都必须是"一格"

  function idxOf(r, c) {
    const k = IDX.get(r * 5 + c);
    return k === undefined ? -1 : k;
  }

  /* ---------------------------- 合法走法 ---------------------------- */

  function legalMoves(st) {
    return st.turn === KING ? kingMoves(st.board) : ministerMoves(st);
  }

  function kingMoves(board) {
    const out = [];
    for (let i = 0; i < N; i++) {
      if (board[i] !== KING) continue;
      const p = L.points[i];
      for (let a = 0; a < ADJ[i].length; a++) {
        const j = ADJ[i][a];

        if (board[j] === EMPTY) {
          out.push({ kind: 'move', from: i, over: -1, to: j });
          continue;
        }
        if (board[j] !== MIN) continue;

        // 跳吃：i -> j(大臣) -> k(空)
        const q = L.points[j];
        const k = idxOf(2 * q[0] - p[0], 2 * q[1] - p[1]);
        if (k < 0) continue;                    // 落点不在盘上
        if (board[k] !== EMPTY) continue;       // 落点被占
        // 两段都必须是相邻格，排除"跨空洞的长线"
        if (Math.max(Math.abs(q[0] - p[0]), Math.abs(q[1] - p[1])) !== STEP) continue;
        if (Math.max(Math.abs(L.points[k][0] - q[0]), Math.abs(L.points[k][1] - q[1])) !== STEP) continue;
        if (ADJ[j].indexOf(k) < 0) continue;    // 大臣与落点之间必须有线
        if (ADJ[i].indexOf(j) < 0) continue;    // 王与大臣之间必须有线

        out.push({ kind: 'eat', from: i, over: j, to: k });
      }
    }
    return out;
  }

  function ministerMoves(st) {
    const board = st.board;
    const out = [];

    if (st.phase === 1) {
      // 添子阶段：只能往空点放
      for (let i = 0; i < N; i++) {
        if (board[i] === EMPTY) out.push({ kind: 'place', from: -1, over: -1, to: i });
      }
      return out;
    }

    // 走子阶段：沿连线走一步
    for (let i = 0; i < N; i++) {
      if (board[i] !== MIN) continue;
      for (let a = 0; a < ADJ[i].length; a++) {
        const j = ADJ[i][a];
        if (board[j] === EMPTY) out.push({ kind: 'move', from: i, over: -1, to: j });
      }
    }
    return out;
  }

  /* 选中某枚棋子后，它能走哪几步（添子阶段没有选子概念，返回空） */
  function movesOf(st, from) {
    if (st.phase === 1 && st.turn === MIN) return [];
    const all = legalMoves(st);
    const out = [];
    for (let i = 0; i < all.length; i++) {
      if (all[i].from === from) out.push(all[i]);
    }
    return out;
  }

  /* ---------------------------- 走一步 ---------------------------- */

  /* 返回"变化的字段"，由 game.js 合并；不改入参 */
  function applyMove(st, move) {
    const board = st.board.slice();
    let phase = st.phase;
    let inHand = st.inHand;
    let captured = st.captured;

    if (move.kind === 'place') {
      board[move.to] = MIN;
      inHand -= 1;
      if (inHand <= 0) { inHand = 0; phase = 2; }
    } else if (move.kind === 'move') {
      board[move.to] = board[move.from];
      board[move.from] = EMPTY;
    } else if (move.kind === 'eat') {
      board[move.to] = KING;
      board[move.from] = EMPTY;
      board[move.over] = EMPTY;
      captured += 1;
    } else {
      throw new Error('未知走法：' + move.kind);
    }

    return {
      board: board,
      phase: phase,
      inHand: inHand,
      captured: captured,
      turn: st.turn === KING ? MIN : KING,
      ply: st.ply + 1,
      lastMove: { kind: move.kind, from: move.from, to: move.to, over: move.over },
    };
  }

  /* ---------------------------- 胜负判断 ---------------------------- */

  function checkEnd(st) {
    if (st.captured >= RULE.kingWinWhenCaptured) {
      return { winner: KING, reason: '王累计吃掉 ' + st.captured + ' 枚大臣，王方获胜。' };
    }
    if (st.ply >= RULE.drawAtPly) {
      return { winner: 0, reason: '双方共走 ' + st.ply + ' 步，达到 ' + RULE.drawAtPly + ' 步上限，判和棋。' };
    }
    if (legalMoves(st).length === 0) {
      return st.turn === KING
        ? { winner: MIN, reason: '王被完全困死，没有任何合法走法，大臣方获胜。' }
        : { winner: KING, reason: '大臣无路可走，王方获胜。' };
    }
    return null;
  }

  function count(board, v) {
    let n = 0;
    for (let i = 0; i < board.length; i++) if (board[i] === v) n++;
    return n;
  }

  window.RULES = {
    RULE: RULE,
    KING: KING,
    MIN: MIN,
    EMPTY: EMPTY,
    legalMoves: legalMoves,
    movesOf: movesOf,
    applyMove: applyMove,
    checkEnd: checkEnd,
    count: count,
  };
})();
