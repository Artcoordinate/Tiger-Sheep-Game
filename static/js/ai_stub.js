/* ai_stub.js —— 人机对弈的对手（B 负责接口，D 负责算法）
 *
 * 团队文档对 B 的作业1 要求是「Canvas/DOM 绘制虎羊棋不规则棋盘，实现人机
 * 点击交互」，所以界面里必须有一个能陪人下完的对手。这里先放一个最小可用
 * 策略，保证在 D 的 rule_based.py 到位之前，界面已经可以完整对弈。
 *
 * 接入约定（D 接手时只需要满足这个签名，game.js 不用改）：
 *   window.AI.chooseMove(state) -> { kind, from, over, to } | null
 *
 *   state 就是 game.js 维护的那份状态对象，字段：
 *     board    Array<number>  37 长，0 空 / 1 王 / 2 大臣
 *     turn     number         轮到谁，1 王 / 2 大臣
 *     phase    number         1 添子阶段 / 2 走子阶段
 *     inHand   number         大臣手里还剩几枚
 *     captured number         王已吃掉的大臣数
 *     ply      number         已经走了多少手
 *
 * D 的引擎做好后，两种接法任选其一：
 *   a) 纯前端：把 rule_based.py 的逻辑翻成 JS 覆盖本文件；
 *   b) 走后端：本文件改成 fetch('/api/move', {method:'POST', body: JSON.stringify(state)})，
 *      由 C 的 app.py 调 D 的引擎。
 */
(function () {
  'use strict';

  const R = window.RULES;
  const L = window.BOARD_LAYOUT;

  const CR = 4, CC = 2;   // 9 行 x 5 列棋盘的中心行列

  function centerDist(i) {
    const p = L.points[i];
    return Math.abs(p[0] - CR) + Math.abs(p[1] - CC);
  }

  function pickRandom(list) {
    return list[Math.floor(Math.random() * list.length)];
  }

  /* 临时策略（明确标为占位，不是 D 的 minimax）：
   *   1. 能跳吃就跳吃，优先吃靠近中心的
   *   2. 走子时向中心收拢；王反过来往边上躲
   *   3. 同分随机，避免每局一模一样
   */
  function chooseMove(state) {
    const moves = R.legalMoves(state);
    if (!moves.length) return null;

    const eats = moves.filter(function (m) { return m.kind === 'eat'; });
    if (eats.length) {
      const best = Math.min.apply(null, eats.map(function (m) { return centerDist(m.over); }));
      return pickRandom(eats.filter(function (m) { return centerDist(m.over) === best; }));
    }

    const ds = moves.map(function (m) { return centerDist(m.to); });
    const target = state.turn === R.KING ? Math.max.apply(null, ds) : Math.min.apply(null, ds);
    return pickRandom(moves.filter(function (m) { return centerDist(m.to) === target; }));
  }

  window.AI = {
    name: '启发式占位 AI（B 临时实现，等 D 的 minimax 替换）',
    chooseMove: chooseMove,
  };
})();
