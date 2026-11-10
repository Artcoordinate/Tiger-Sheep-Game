# C 的后端与 B 联调交接

本包基于你提供的“实践作业一_国王与大臣棋_前端UI与可视化.zip”集成。原压缩包和微信目录未修改。

## 启动

在本目录打开 PowerShell（Python 3.10 或更新）：

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python app.py
```

浏览器打开 http://127.0.0.1:5000 。集成版必须通过 Flask 访问，不能双击 HTML。默认 mock 引擎只用于联调，不代表 Minimax 已完成。

## B 需要知道的变化

保留 Canvas、样式、节点编号和现有交互。index.html 将 ai_stub.js 换成 api.js。game.js 的 doMove / maybeAI 改为 async/await：先向后端校验动作，成功才更新界面；AI 任务轮询时锁定点击，重开后忽略旧响应，失败显示错误。只替换同步函数而不修改调用方无法正确对接 fetch。

浏览器持有每盘状态和悔棋历史，后端无共享全局棋局，因此不同窗口互不串局。POST 请求必须带完整 state；GET /api/state 返回**新局初始状态**，不是服务器保存的“当前局”。这是为了兼容 B 已有悔棋、演示、双人模式。适用于本地课程演示；状态仅做结构、子力守恒、阶段和走法校验，不证明整盘历史可达，不能直接用作联网竞技服务器。

## 接口

全部同源 JSON。state 沿用 B 的字段：board（37 项）、turn（1 王/2 大臣）、phase、inHand、captured、ply。后端补充 lastMove、over、winner、reason、legalMoves。未结束 winner=null，和棋 winner=0。

| 方法与地址 | 输入 | 返回 |
|---|---|---|
| GET /api/state | 无 | `{state}` 初始局面 |
| POST /api/state | `{state}` | 校验后局面、合法动作、胜负 |
| POST /api/move | `{state,move}` | `{state}` 走后局面 |
| POST /api/ai | `{state}` | HTTP 202 `{taskId,status:"pending"}` |
| GET /api/tasks/任务ID | 无 | pending，或 done 加 move/state/engine |

move 使用 `{kind,from,over,to}`；kind 为 place/move/eat，放子时 from/over=-1，普通移动 over=-1。非法输入/走法 HTTP 400；媒体类型错误 415；队列满 429；任务不存在 404；算法失败 500，正文包含 error。

例如 `fetch('/api/move',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({state,move})})`，检查 response.ok 后读取 result.state。可直接复用 static/js/api.js 的 API.request。

## D/E 如何接入

把算法放入 engines/rule_based.py，推荐 `choose_move(game)`，返回 A 的 tuple 或 B 的动作对象；不要原地修改传入局面。通过 game.legal_moves/apply/undo 使用同一规则。

```powershell
$env:TIGER_ENGINE='rule_based'
python app.py
```

若 D 采用原四参数签名 `choose_move(board, phase, current_player, remaining_sheep)`，额外设置 `$env:TIGER_ENGINE_API='legacy'`。返回 ('place',to)、('move',from,to)、('eat',from,over,to)；旧三元组 eat 自动从合法动作补全 over。算法输出会再次校验，不合法返回任务失败，不会偷偷退回 mock。

后续可选择 mcts/cnn/alphazero，需先提供对应模块；目前没有实现这些算法。四参数签名没有步数和历史，完整 Game 签名更适合和棋处理。

## 算力与限制

两条工作线程，最多四个运行/排队任务，最多保留 256 条任务记录，完成任务超过五分钟在下次提交时清理。AI 计算不会在 Flask 请求中等待。浏览器最多轮询一分钟；请求超时和重开不会强制终止 Python 线程。D/E 必须给搜索设置深度/时间上限；需要硬终止或高并发时改用进程任务队列。当前只绑定本机，使用单进程演示服务，不支持多 worker 共享任务。

## 规则待 A 确认

压缩包中实际为竖向 **37 点、76 边**，与单独提供的横向 board.py、规则截图的 72 边不同。本包沿用与 B 画面一致的压缩包规则，没有擅自改边。沿用王先手、24 大臣（8 在场+16 待放）、吃满10胜、300步和棋、轮到任一方无合法走法则对方胜。长边可移动但不能作为跳吃的一段，这一点也需 A 对照教材确认。

core/rules.py 只调整了包导入路径以便 Flask 使用，规则逻辑保持原版。A 更改拓扑后运行 `python scripts/export_board.py` 同步前端，不要混用横向和竖向编号。

## 测试

```powershell
.venv\Scripts\python -m unittest discover -s tests -v
```

B 原有 templates/test.html 和 ai_stub.js 留作独立前端自测参考；正式首页使用后端 AI。docs/B原始README.md 属于 B 原始交付，集成版启动和接口以本说明为准。
