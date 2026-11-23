/* sgf.js —— 棋谱的序列化与解析（B 负责）
 *
 * 内部格式（前端 ↔ 后端 / localStorage 存档）：
 *   {
 *     version: 1,
 *     engine: 'rule_based' | 'mcts',
 *     mode: 'ai' | 'ai-king' | 'human',
 *     humanSide: 'king' | 'minister' | null,
 *     result: 'king_win' | 'minister_win' | 'draw',
 *     reason: '王吃掉 10 名大臣',
 *     date: '2026-11-23',
 *     moves: [{ side: 'king'|'minister', kind: 'place'|'move'|'eat',
 *               from: 8, over: 13, to: 18 }]
 *   }
 *
 * SGF 文本借用围棋的骨架（GM/FF/CA/SZ/RE + ;B[] / ;W[]），
 * 但走法值不用围棋的 aa/bb 坐标——棋盘是 37 个不规则点，
 * 硬映射到 19×19 反而没法读。改成带类型前缀的点号：
 *   P18        大臣放子到 18 号点
 *   M16-21     走子 16 → 21
 *   E8-13-18   跳吃 8 越过 13 落到 18
 * 别的组用冒号加 J/S：P:20 / S:08:04 / J:08:18:13，解析时一并认下。
 *
 * 一个文件可以放多局（SGF 本身就是游戏集合格式），
 * 实验二要求的 10 局棋谱导成一个 .sgf 就行。
 */
(function () {
  'use strict';

  const APP = 'TigerSheep:2.0';
  const SIZE = 37;

  /* ------------------------------------------------------------ 走法 */

  function moveToToken(move) {
    if (!move) return '';
    if (move.kind === 'place') return 'P' + move.to;
    if (move.kind === 'eat') return 'E' + move.from + '-' + move.over + '-' + move.to;
    return 'M' + move.from + '-' + move.to;
  }

  function tokenToMove(token) {
    const text = String(token == null ? '' : token).trim().toUpperCase();
    if (!text) return null;

    // 走法值两种写法都认：
    //   我们：P18 / M16-21 / E8-13-18       E 依次是 起点-被吃-落点
    //   别组：P:20 / S:08:04 / J:08:18:13   J 依次是 起点-落点-被吃
    // 冒号和 '-' 都当分隔符，J/S 换成正统的 E/M。
    let head = text.charAt(0);
    const swap = head === 'J';
    if (head === 'J') head = 'E';
    else if (head === 'S') head = 'M';

    const parts = text.slice(1).split(/[-:]/).filter(function (s) { return s !== ''; });
    const nums = [];
    for (let i = 0; i < parts.length; i++) {
      const n = parseInt(parts[i], 10);
      if (!Number.isFinite(n) || n < 0 || n > SIZE - 1) return null;
      nums.push(n);
    }

    if (head === 'P' && nums.length === 1) {
      return { kind: 'place', from: -1, over: -1, to: nums[0] };
    }
    if (head === 'M' && nums.length === 2) {
      return { kind: 'move', from: nums[0], over: -1, to: nums[1] };
    }
    if (head === 'E' && nums.length === 3) {
      if (swap) return { kind: 'eat', from: nums[0], over: nums[2], to: nums[1] };
      return { kind: 'eat', from: nums[0], over: nums[1], to: nums[2] };
    }
    return null;
  }

  /* ------------------------------------------------------------ 文本 */

  function escapeText(value) {
    return String(value == null ? '' : value)
      .replace(/\\/g, '\\\\')
      .replace(/\]/g, '\\]')
      .replace(/[\r\n]+/g, ' ');
  }

  function unescapeText(value) {
    return String(value == null ? '' : value).replace(/\\([\s\S])/g, '$1');
  }

  function sideTag(side) {
    return side === 'king' ? 'B' : 'W';
  }

  function sideFromTag(tag) {
    return tag === 'B' ? 'king' : 'minister';
  }

  function resultTag(result) {
    if (result === 'king_win') return 'B+';
    if (result === 'minister_win') return 'W+';
    return '0';
  }

  function resultFromTag(tag) {
    const text = String(tag || '').trim().toUpperCase();
    if (text === 'B+') return 'king_win';
    if (text === 'W+') return 'minister_win';
    return 'draw';
  }

  /* ------------------------------------------------------------ 导出 */

  function gameToSGF(game) {
    const g = game || {};
    const head = [
      'GM[1]', 'FF[4]', 'CA[UTF-8]', 'AP[' + APP + ']', 'SZ[' + SIZE + ']',
      'GN[' + escapeText(g.title || '国王与大臣棋') + ']',
      'DT[' + escapeText(g.date || '') + ']',
      'PB[' + escapeText(g.blackName || '王方') + ']',
      'PW[' + escapeText(g.whiteName || '大臣方') + ']',
      'RE[' + resultTag(g.result) + ']',
    ];
    if (g.engine) head.push('AN[' + escapeText(g.engine) + ']');
    if (g.mode) head.push('RU[' + escapeText(g.mode) + ']');
    if (g.reason) head.push('C[' + escapeText(g.reason) + ']');

    const body = (g.moves || []).map(function (move) {
      return ';' + sideTag(move.side) + '[' + moveToToken(move) + ']';
    });

    return '(\n' + head.join('') + '\n' + body.join('') + ')\n';
  }

  function archiveToSGF(list) {
    return (list || []).map(gameToSGF).join('');
  }

  /* ------------------------------------------------------------ 解析 */

  /* 按括号切出每局的正文；跳过属性值里的括号与转义字符 */
  function splitTrees(src) {
    const trees = [];
    const text = String(src || '');
    let depth = 0;
    let start = -1;
    let inBracket = false;
    let escaped = false;

    for (let i = 0; i < text.length; i++) {
      const ch = text.charAt(i);
      if (escaped) { escaped = false; continue; }
      if (ch === '\\') { escaped = true; continue; }
      if (inBracket) {
        if (ch === ']') inBracket = false;
        continue;
      }
      if (ch === '[') { inBracket = true; continue; }
      if (ch === '(') {
        if (depth === 0) start = i + 1;
        depth++;
      } else if (ch === ')') {
        depth--;
        if (depth === 0 && start >= 0) {
          trees.push(text.slice(start, i));
          start = -1;
        }
        if (depth < 0) depth = 0;
      }
    }
    return trees;
  }

  function readProp(head, key) {
    const re = new RegExp('(?:^|[^A-Z])' + key + '\\[((?:\\\\.|[^\\]])*)\\]');
    const hit = re.exec(head);
    return hit ? unescapeText(hit[1]) : '';
  }

  function parseTree(inner) {
    const text = String(inner || '');
    const firstSemicolon = text.indexOf(';');
    // 别的工具导出的 SGF 内层常以 ';' 开头（"(;GM[1]...)"），此时头部属性在第二个分号之前。
    const head = firstSemicolon > 0
      ? text.slice(0, firstSemicolon)
      : text.slice(0, text.indexOf(';', 1) >= 0 ? text.indexOf(';', 1) : text.length);

    const moves = [];
    const re = /;\s*([BW])\s*\[([^\]]*)\]/g;
    let hit;
    while ((hit = re.exec(text)) !== null) {
      const move = tokenToMove(hit[2]);
      if (!move) continue;
      move.side = sideFromTag(hit[1]);
      moves.push(move);
    }

    return {
      version: 1,
      size: parseInt(readProp(head, 'SZ') || String(SIZE), 10),
      date: readProp(head, 'DT'),
      engine: readProp(head, 'AN'),
      mode: readProp(head, 'RU'),
      reason: readProp(head, 'C'),
      result: resultFromTag(readProp(head, 'RE')),
      blackName: readProp(head, 'PB'),
      whiteName: readProp(head, 'PW'),
      moves: moves,
    };
  }

  function parseSGF(text) {
    return splitTrees(text).map(parseTree).filter(function (g) {
      return g.moves.length > 0;
    });
  }

  /* ------------------------------------------------------------ 对外 */

  window.SGF = {
    SIZE: SIZE,
    moveToToken: moveToToken,
    tokenToMove: tokenToMove,
    gameToSGF: gameToSGF,
    archiveToSGF: archiveToSGF,
    parseSGF: parseSGF,
  };
})();
