# 国王与大臣棋（37 点）

> 实践作业一：基于下棋规则进行决策的国王与大臣棋程序
> 规则参考：《深度学习与围棋》实验指导书第二章、第三章；棋盘拓扑依据 **图 2-1 国王与大臣棋初始布局**。

---

## 一、棋盘

**37 个交叉点、76 条连边、9 行 × 5 列竖版**，和课本图 2-1 同方向。

| 区域 | 节点编号 | 结构 |
|---|---|---|
| 上王宫（三角形） | 0 – 2 底边，3 – 5 腰线 | 尖顶即正方形上边中点 **8** |
| 中央正方形 | 6 – 30 | 5×5 交点；4×4 个小格**每格一条斜线**，按 `(行+列)` 奇偶交替 |
| 下王宫（三角形） | 31 – 33 腰线，34 – 36 底边 | 尖顶即正方形下边中点 **28** |

初始布局（**8 枚在场 + 16 枚待放 = 24 枚大臣**）：

- **王**（黑，编码 `1`）：**8**、**28**
- **大臣**（白，编码 `2`）：**12, 13, 14, 17, 19, 22, 23, 24**，其余 16 枚在手里

![节点编号](docs/screenshots/board_numbered.png)

## 二、规则

| 项目 | 规则 |
|---|---|
| 先手 | **王**先走 |
| 大臣添子 | 前 16 手只能 `place` 到空点，放完自动进入走子阶段 |
| 王移动 | 沿连线走一步 |
| 王跳吃 | **王 – 大臣 – 空** 三点共线、大臣在正中间、两段都是相邻格 |
| 王胜 | 累计吃掉 **10** 枚大臣 |
| 大臣胜 | 王被完全围死，没有任何合法走法 |
| 和棋 | 总步数达到 **300** |

![初始布局](docs/screenshots/board_layout.png)

---

## 三、运行

**前端零依赖，双击即可：**

```
templates/index.html    对局界面（默认人机对弈，可切真人双人）
templates/test.html     棋盘数据与规则自测（16 项）
```

演示 / 截图用的三个入口：

```
templates/index.html#place    添子阶段，高亮全部可放点位
templates/index.html#demo     选中王，展示跳吃红圈
templates/index.html#aiplay   人机对局进行中的样子
```

`templates/` + `static/` 就是 Flask 的默认约定，C 的 `app.py` 写好后直接
`render_template('index.html')` 即可，静态资源不用搬。也可以先起静态服务：

```bash
python -m http.server 8000
# 打开 http://localhost:8000/templates/index.html
```

> HTML 里引用的是 `../static/...`：`file://` 双击时解析到项目根的 `static/`；
> 走 Flask 时浏览器把 `/../static/...` 规范化成 `/static/...`，两种方式都能跑。
> 布局被编译进 `static/js/board_data.js` 而不是 `fetch` 读 JSON，是为了规避 `file://` 的 CORS。

---

## 四、数据流

```
core/board.py          A 出品：37 点、76 条边、坐标、开局数组
core/rules.py          A 出品：合法走法、胜负、和棋
        │
        │  python scripts/export_board.py
        ▼
static/js/board_data.js     自动生成，勿手改
        │
        ├── static/js/board.js         只负责画（渲染 / 命中检测 / 高亮）
        ├── static/js/rules_stub.js    只负责规则（逐条复刻 rules.py）
        ├── static/js/ai_stub.js       只负责对手（临时启发式，等 D 替换）
        └── static/js/game.js          只负责交互（选子 / 落子 / 悔棋 / 终局 / 驱动 AI）
```

**A 改了棋盘，只要重跑一次导出，前端一行代码都不用动：**

```bash
python scripts/export_board.py      # 重新生成 board_data.js
python scripts/draw_board.py        # 重新生成两张棋盘图
```

`export_board.py` 自带体检：点数、边数、重边、孤立点、开局子数、坐标越界，任何一条不过就拒绝导出。

---

## 五、目录

```
.
├── app.py                       # C：Flask 入口（待补）
│
├── core/                        # A 的原始实现，只读，不要改
│   ├── board.py                 # 37 点拓扑 + 坐标 + 初始布局
│   └── rules.py                 # Game 类：走法 / 胜负 / 悔棋
│
├── engines/                     # D / E：算法引擎层（待补）
│
├── templates/                   # B：页面
│   ├── index.html               # 对局界面
│   └── test.html                # 16 项自测
│
├── static/                      # B：静态资源
│   ├── css/style.css
│   └── js/
│       ├── board_data.js        # 自动生成，勿手改
│       ├── board.js             # Canvas 渲染：等比缩放 / 高 DPI / 命中检测
│       ├── rules_stub.js        # 规则层，待 C 的接口接管
│       ├── ai_stub.js           # 对手层，待 D 的 minimax 接管
│       └── game.js              # 点击状态机 / 回合 / 悔棋 / 终局 / 人机驱动
│
├── scripts/
│   ├── export_board.py          # board.py → board_data.js
│   └── draw_board.py            # board.py → 两张棋盘图
│
└── docs/
    ├── screenshots/             # 报告用截图
    └── A给组员的说明.md
```

---

## 六、界面已实现

团队文档对 B 的作业一要求是：**「Canvas/DOM 绘制虎羊棋不规则棋盘，实现人机点击交互」**。逐条对应：

| 文档要求 | 实现 |
|---|---|
| Canvas/DOM 绘制不规则棋盘 | Canvas 绘制 37 点 / 76 条连线，按 `bbox` 等比缩放，支持高 DPI 与窗口自适应 |
| **人机点击交互** | 右上角「对手」可选 **电脑（大臣）** / **真人双人**；人机模式下你执王先走，电脑自动应招 |

交互细节：

- **两个阶段自动切换**：大臣添子（点空位放子）↔ 双方走子
- 点击选子 → 高亮合法落点 → 点击落子，全流程无刷新
- **王跳吃可视化**：绿圈为普通移动，**红圈为跳吃落点**
- 上一步的起点与落点虚线标记，落子脉冲动画
- 侧栏实时显示：当前回合、大臣在场 / 手中、回合步数、累计被吃
- 悔棋（人机模式下一次退两步，直接回到你的回合）、重新开始、终局遮罩
- 非法点击（空点 / 对方棋子 / 盘外）不崩溃，给出提示
- 电脑思考期间锁住鼠标；思考中点「重新开始」不会把旧的那一步落到新对局上

> 电脑对手是 `ai_stub.js` 里的**临时启发式**（能跳吃就吃，否则往中心收），
> 200 局冒烟零异常、王恒为 2 枚。D 的 `rule_based.py` 好了以后，
> 按文件头的接口约定替换本文件即可，`game.js` 不用改。

![对局界面](docs/screenshots/01_main.png)
![添子阶段](docs/screenshots/02_place.png)
![王跳吃](docs/screenshots/03_king_jump.png)
![人机对局](docs/screenshots/05_ai_play.png)

---

## 七、自测

`templates/test.html` 共 16 项，全部通过：

![自测](docs/screenshots/04_selftest.png)

覆盖：节点数 / 76 边无重边无自连无孤立点 / 邻接表双向一致 / 开局子力与位置 /
先手与手牌数 / 添子阶段走法 / 王开局跳吃 / 落点被占不可吃 / 中间无子不可跳 /
放满 16 枚自动进入走子阶段 / 走子阶段大臣只能移动 / `applyMove` 不改入参 /
吃满 10 枚判王胜 / 300 步判和 / 无路可走判负 / 坐标不越界。

---

## 八、分工

| 成员 | 角色 | 作业一职责 |
|---|---|---|
| A | 规则引擎 / 测试统筹 / 文档 PPT | `core/board.py`、`core/rules.py`（合法走法、胜负、和棋）、16 项自动化测试、报告与答辩 |
| B | 前端 UI / 可视化 | `templates/` + `static/` 全部：Canvas 渲染、人机交互、对手占位、界面文档 |
| C | 后端架构 / 接口 | `app.py`、`/api/state`、`/api/move`、算法挂载 |
| D | 传统搜索算法 | `engines/rule_based.py`：Minimax + Alpha-Beta、启发式评估；同时用真实引擎替换 `static/js/ai_stub.js` |
| E | 深度学习 / 强化学习 | 评估函数调参、后续 CNN 与 AlphaZero |

> 姓名 / 学号 / 班级待填写。

---

## 九、待确认与接口约定

以下三处请 A 对照教材正文再确认一次（改完重跑导出脚本即可同步到前端）：

1. **76 条边**：中央 4×4 个小格每格一条斜线，比"两条贯穿主对角线"多出 8 条辐射短斜线。
2. **24 枚大臣**：8 枚在场 + 16 枚待放。教材图 2-1 只画出在场 8 枚。
3. **王先走**：开局王在 8 号点，可跳吃 12 / 13 / 14 三枚大臣落到 16 / 18 / 20——
   等于开局白吃三子。若不是有意为之，先手应改成大臣。

后端（C）直接返回 A 的 `Game.state_dict()` 即可，字段：

```json
{
  "board": [0, 0, ...], "phase": 1, "player": 1,
  "sheep_in_hand": 16, "captured": 0, "moves": 0,
  "winner": null, "end_reason": "",
  "status": "轮到 虎 走 | 添子阶段 | ...",
  "legal_moves": [["place", 0], ["move", 8, 9]]
}
```

接入时只替换 `static/js/rules_stub.js` 里的 `legalMoves` / `applyMove` / `checkEnd`，
`board.js` 与 `game.js` 不用改动。

人机对手（D）只需要实现一个函数，`game.js` 通过 `window.AI.chooseMove(state)` 调用：

```js
// 整个 ai_stub.js 换掉，签名保持不变
window.AI = {
  chooseMove: function (state) {
    // state: { board, turn, phase, inHand, captured, ply }
    // 返回:  { kind:'move'|'eat'|'place', from, over, to }  或  null（无棋可走）
  }
};
```

也可以走后端：把 `ai_stub.js` 改成 `fetch('/api/move', ...)`，由 C 的 `app.py` 转发给 D 的引擎。

---

## 十、版本路线

| 分支 | 内容 |
|---|---|
| `hw1-rule` | 规则引擎 + 界面（本作业） |
| `hw2-mcts` | MCTS + UCT，搜索树可视化 |
| `hw3-cnn` | 卷积网络策略 / 价值预测，胜率与落子概率展示 |
| `hw4-alphazero` | 自对弈 + PUCT + 模型训练，实时评估可视化 |
