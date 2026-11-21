# 给组员的说明：合并后的改动、归属与接口约定

> 撰写：D（曾雯薏） · 2026-11-10 · 2026-11-21 增补 mod2（MCTS）
> 仓库：`D:\python\111\chess`（合并后的唯一仓库，A/B/C/E 的原始材料都不必再单独跑）

## 一句话结论

A 的棋盘规则、B 的前端、C 的 Flask 后端、E 的评估函数、D 的两版引擎（`mod1/` Alpha-Beta、`mod2/` MCTS）已经合进同一个仓库，
`app.py` 起来就是一个能玩的完整对局：浏览器操作棋盘 → `/api/move` 落子 → 电脑走 `/api/ai` → `mod1/` 或 `mod2/` 搜索。
两版引擎对外接口完全相同，切换只靠环境变量，C 的 `engines/adapter.py` 一字节没改。

```powershell
cd D:\python\111\chess
.\.venv\Scripts\python.exe app.py                              # http://127.0.0.1:5000
.\.venv\Scripts\python.exe -m unittest discover -s tests       # 24 项，约 1.5 秒（含 MCTS 用例）
```

引擎相关环境变量（都有默认值，通常不用设）：

| 变量 | 默认 | 作用 |
|---|---|---|
| `TIGER_ENGINE` | `rule_based` | 选引擎：adapter 会导入 `engines.<名字>`。`rule_based` = `mod1`（Alpha-Beta），`mcts` = `mod2`（MCTS），`mock` 是固定的假引擎，接口联调/对照时用 |
| `TIGER_DEPTH` | `4` | 迭代加深的深度上限 |
| `TIGER_TIME_LIMIT` | `1.0` | mod1 单步思考的秒数上限（到点丢掉没搜完的那层） |
| `TIGER_MCTS_TIME` | `1.5` | mod2 单步思考秒数 |
| `TIGER_MCTS_PLAYOUTS` | `0` | mod2 模拟次数上限，0 = 只看时间 |
| `TIGER_MCTS_ROLLOUT` | `80` | mod2 单次模拟封顶手数 |
| `TIGER_MCTS_SEED` | 不设 | 固定随机种子，复现用 |

## 文件归属表

| 归属 | 文件 | 说明 |
|---|---|---|
| A | `core/board.py`、`core/rules.py` | 37 点棋盘 + `Game` 规则，逐字节沿用 A 的交付物，只把 import 改成包内相对导入 |
| B | `templates/`、`static/`（含 `static/js/board.js`、`game.js`、`api.js`、`board_data.js`） | 前端 UI 与绘制，`board_data.js` 由 `scripts/export_board.py` 从 `core/board.py` 生成 |
| C | `app.py`、`backend.py`、`engines/adapter.py`、`engines/mock.py`、`scripts/`、`tests/test_api.py`、`requirements.txt` | 接口层、状态编解码、引擎分发 |
| D | `mod1/`（`rule_based.py`、`generate_moves.py`、`minimax.py`、`__init__.py`）、`mod2/`（`mcts.py`、`__init__.py`）、`tests/test_engine.py`、`engines/rule_based.py`、`engines/mcts.py`（两个一行转发壳） | 走法生成 + 排序、Alpha-Beta 搜索、MCTS 智能体、旧签名兼容层；转发壳只为满足 C 的 adapter 按 `engines.<名字>` 导入的写法 |
| E | `mod1/evaluate.py` | 评估函数，被 `mod1/rule_based.py` 直接调用 |
| 归档 | `legacy/`、`docs/*给组员的说明*.md` | 旧 9 点原型、各组原始说明，不参与运行 |

`core/rules.py` 是唯一的规则实现：前端点击合法性、后端状态校验、引擎搜索全部走它，没有第二份拷贝。

D 的代码按版本目录组织：`mod1/`、`mod2/` 对外接口完全一致，adapter 只认这三个名字——`NAME`、`choose_move(game)`、`evaluate(game)`。

### mod1（Alpha-Beta，已完成）

内部按"生成 → 排序 → 搜索"分工，不重复规则：

| 文件 | 职责 | 对外接口 |
|---|---|---|
| `mod1/generate_moves.py` | 向 `Game.legal_moves()` 要合法走法，按行棋方口味打分排序（吃子 > 走子靠中心 > 添子：抱团加分、贴虎扣分） | `generate_moves(game)`、`order_moves(game, moves)`、`score_move(game, move)`、`game_from_state(...)` |
| `mod1/rule_based.py` | Alpha-Beta + 迭代加深 + 限时；每层都用 `generate_moves(game)` 拿排好序的走法 | `choose_move(game, max_depth=None, time_limit=None)` |
| `mod1/evaluate.py` | E 的评估函数，被 `rule_based.py` 直接调用 | `evaluate_tiger(game)`、`evaluate_sheep(game)` |
| `mod1/minimax.py` | 旧四参数签名的兼容层，内部转成 `Game` 再调上面的选步 | `get_best_move(board, player, phase, remaining_sheep, depth=3)` |
| `mod1/__init__.py` | 版本入口，对 adapter 只暴露三个名字 | `NAME`、`choose_move(game)`、`evaluate(game)` |

排序不影响选步正确性，只影响剪枝效率；同深度实测快 3~4 倍。

### mod2（MCTS，已完成）

`mod2/` 与 `mod1/` 完全独立，只共用 A 的规则，对外暴露同样的三个名字：

| 文件 | 职责 | 对外接口 |
|---|---|---|
| `mod2/mcts.py` | UCB1 选择 → 扩展 → 随机模拟 → 回传；模拟里虎方 70% 优先吃子，封顶 80 手后按吃子进度估分 | `choose_move(game, max_depth=None, time_limit=None)`（`max_depth` 复用为模拟封顶手数）、`evaluate(game)` |
| `mod2/__init__.py` | 版本入口 | `NAME = "mod2"`、`choose_move`、`evaluate` |
| `engines/mcts.py` | 一行转发壳 → `mod2.mcts` | — |

切换方式：`$env:TIGER_ENGINE='mcts'` 就用 MCTS，不设仍是 `rule_based`（mod1）。
C 的 `engines/adapter.py` 白名单里本来就有 `mcts`，所以这一版**不需要 C 改任何东西**。

### 以后加第三版（神经网络）

照抄 `mod2/` 的结构建 `mod3/`，暴露 `NAME` / `choose_move` / `evaluate`，再在 `engines/` 下加一行转发壳。
adapter 的白名单里已经有 `cnn` / `alphazero`，用这两个名字连白名单都不用改；用别的名字要 C 补一行。
前端"自选模式"还没接线，要联动时由 B 加下拉、C 把引擎名从请求传到 `compute()`。

## 我（D）动过别人文件的地方

以下改动都为了"合并后能直接跑"，不影响各组原有的设计与接口语义：

1. **`engines/adapter.py`**：最终**一字节未改**，是 C 交付的原版（`choose(game)` → `(走法, 引擎名)`，按 `TIGER_ENGINE` 导入 `engines.<名字>`，默认 `rule_based`）。
   过程中我曾把它改成注册表 + `choose(game, engine=...)`，后来全部还原。现在为了配合它"默认导入 `engines.rule_based`"的写法，我只新增了 `engines/rule_based.py` 一行转发壳（`from mod1.rule_based import choose_move, evaluate`），算法本体仍在 `mod1/`。
   默认引擎名因此还是 `rule_based`（不再是 `mock`），跑起来是真算法；要联调或对照，`$env:TIGER_ENGINE='mock'`。
2. **`tests/test_api.py:1,14-15,21`**：加 `import os`，`setUp` 里设 `TIGER_ENGINE=mock`，`tearDown` 里清除。
   原因：该测试原本断言返回的 `engine` 就是 `mock`，默认引擎改真后它会既失败又变慢；锁成 mock 后，接口测试与算法解耦。
3. **`README.md`**：覆盖为合并版说明。
   原因：原文件是 C 的后端说明，合并后首屏需要能直接看到启动方式和目录全貌；原内容在 `docs/C后端交接.md` 里仍在。
4. **`mod1/minimax.py`**：改写为兼容层（保留 A 文档里的 `get_best_move(board, player, phase, remaining_sheep, depth=3)` 四参数签名，内部构造 37 点 `Game` 再转调正式引擎）。
5. 根目录旧的 `mini_graph.py`、`evaluate.py`、`generate_moves.py`、`minimax.py` 已移除；D/E 的算法代码现在统一在 `mod1/`，原型代码在 `legacy/` 留档。

## 给 E：`evaluate.py` 的适配（5 处接口，权重未动）

E 的评估函数原先按旧 9 点原型的数据结构写，接 A 的 `Game` 只改了取数方式，打分逻辑、`120/40/12/18/6` 的权重、函数分层全部保持原样：

| 原来 | 现在 |
|---|---|
| `game.tigers` / `game.sheep`（两个 set） | `game.board`（37 长列表），新增 `_positions(board)` 现拆 |
| `game.adj[pos]` | `game.spec.adj[pos]` |
| `game.is_game_over()` | `game.is_over()` |
| `game.get_winner() == "tiger"/"sheep"` | `game.winner == TIGER` / `SHEEP` |

验证三个数：`evaluate_tiger(g) + evaluate_sheep(g) == 0` 恒成立；开局虎吃一子后 `evaluate_tiger` 从 `-164` 变 `-106`；`mod1.rule_based.evaluate()` 在非终局直接返回 `evaluate_tiger(game)`，终局另用 `±(WIN_SCORE - moves)` 保证"越快取胜越好"。

## 接口约定（现状已按此实现，最终以全组确认版为准）

- **选步函数**：`choose_move(game: Game, max_depth=None, time_limit=None) -> tuple | None`。传入的是 `Game` 拷贝，不是散参数；`None` 表示没有可走的步。
- **旧签名开关**：`adapter.py` 里 `TIGER_ENGINE_API=legacy` 会按 `(board, phase, player, sheep_in_hand)` 调引擎。注意 `mod1/rule_based.py` 与 `mod2/mcts.py` 目前都只实现 `Game` 版，这个开关对正式引擎无效——建议以后统一用 `Game` 版。
- **走法格式**：一律四元组/短元组，不采用文档里的 eat 三元组：
  - `("place", to)` 羊添子
  - `("move", frm, to)` 走子
  - `("eat", frm, over, to)` 虎跳吃，显式带被吃点，不再靠遍历邻居猜
- **估值视角**：两版都以**虎为极大方**。`mod1`：`WIN_SCORE = 1_000_000`，胜局 `WIN_SCORE - game.moves`，负局取负，和棋 0。
  `mod2`：同样是“越早赢分越高”，终局 `±(WIN - game.moves)`（`WIN = 10_000`），非终局 `round(吃子进度 * 1000)`，量纲比 mod1 小，跨版本不要直接比数值。

## 任务2 / 任务3 的分工（初稿，组内可改）

### 任务2：MCTS + 界面 + 棋谱

D 的算法部分（`mod2/`）已完成并可直接切换，剩余代码集中在 C 和 B：

| 人 | 任务2 要做的 | 状态 |
|---|---|---|
| C | `/api/ai` 把引擎名从请求传到 `compute()`（约 3 行）；新增棋谱存取接口（`/api/records`）+ 落盘格式 | 待做 |
| B | 下拉框加 "MCTS"；棋谱侧栏（着法列表、点击回跳）、导出/导入 | 待做（工作量最大） |
| A | 无必须改动；可顺手做"棋谱回放合法性校验"（用 `Game` 把棋谱重放一遍） | 空闲 |
| D | `mod2/` 的 MCTS 已交付 | 已完成 |
| E | 无必须改动 | 空闲 |

关键路径：**A 或 C 先给一个棋谱 JSON 样例**（3 步假数据也行），C、B、D 才能并行；否则大家会卡在"格式长什么样"。

### 任务3：神经网络（E 主笔）

| 人 | 任务3 要做的 |
|---|---|
| E | 建 `mod3/` 并主笔：网络结构、训练循环、推理；对外照 `NAME` / `choose_move(game)` / `evaluate(game)` 三个名字写 |
| D | 只做配套：`mod3/` 目录骨架 + `engines/` 一行转发壳 + 自对弈生成训练数据的脚本 + 接口联调 |
| 待定 | 训练框架（PyTorch / 纯 numpy）需要组内先确认，决定了 E 那部分的环境和工期 |

D 自己的工作量到此收口：任务2 已完成，任务3 只做骨架和联调，算法主笔交给 E。

## 已知问题与待办

1. **前端没有"人执大臣"模式**（B 的范围）：`templates/index.html:19-22` 只有"电脑（大臣）/真人双人"两个选项，`static/js/game.js:45-46` 把 `HUMAN_SIDE` 写死成王。底层其实已经通用（后端只根据 `state.turn` 选步），要做成"人执大臣"主要是前端改三处：模式推导、`maybeAI()` 的触发条件、悔棋回滚方。本轮未改。
2. **算法版本目录的命名约束**：`mod1`、`mod2` 这类名字能直接 `import`；如果以后想用 `v1`/`v2`、`algo_v1` 也行，但**不能用以数字开头**的目录名（`import 111.evaluate` 是语法错误）。
3. `docs/` 里的 `A给组员的说明.md`、`B原始README.md`、`C后端交接.md` 是各组原始材料，作为交付证据保留，不是运行所需。
4. 所有 `.py` 的编码统一 UTF-8；`.ps1` 若要写则必须带 BOM，那是 PowerShell 5.1 的坑，与 Python 无关。
5. **MCTS 在相同时间预算下棋力弱于 Alpha-Beta**：实测 0.15~0.2 秒/步时，MCTS 执虎 20 来手就被羊堵死（无合法走法），执羊则被虎吃满 10 子。原因是 1.5 秒内能跑的模拟次数撑不起 24 个根分支。要用它当强引擎，把 `TIGER_MCTS_TIME` 提到 2~3 秒，或用 `TIGER_MCTS_PLAYOUTS` 兜底；写报告时建议作为“同等时间预算下两种算法的取舍”来对比，而不是宣称 MCTS 更强。
