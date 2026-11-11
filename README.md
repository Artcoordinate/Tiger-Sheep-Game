# 国王与大臣棋（虎羊棋）——完整集成版

37 点完整棋盘 + Flask 后端 + 浏览器前端 + D 的 Alpha-Beta 搜索。
原来那套 9 点迷你棋盘原型已归档到 `legacy/`，根目录只留兼容入口。

## 运行

```powershell
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python app.py
```

浏览器打开 http://127.0.0.1:5000 （必须走 Flask，不能双击 HTML）。
换角标/换端口：`$env:PORT` 不生效，直接改 `app.py` 末尾的 `app.run(port=...)`。

## 目录

| 路径 | 内容 |
|---|---|
| `core/board.py`、`core/rules.py` | A 的棋盘拓扑与规则，37 点 / 76 边，`Game` 表示整盘 |
| `app.py`、`backend.py` | C 的 Flask 接口与状态边界（校验 37 长、子力守恒、phase 一致） |
| `mod1/` | **D 的算法（第一版）**：Alpha-Beta + 迭代加深 + 限时，内含 `rule_based.py`（搜索）、`generate_moves.py`（生成+排序）、`evaluate.py`（E 的评估）、`minimax.py`（旧签名兼容） |
| `engines/adapter.py` | C 的引擎选择层（原样未改）：`choose(game)` 按 `TIGER_ENGINE` 动态导入 `engines.<名字>`，返回 `(走法, 引擎名)` |
| `engines/rule_based.py` | 一行转发壳 → `mod1.rule_based`，只为满足 adapter 的默认导入名 |
| `engines/mock.py` | 联调用假引擎（接口测试专用） |
| `static/`、`templates/` | B 的 Canvas 前端，`api.js` 轮询异步 AI 任务 |
| `scripts/export_board.py` | `core/board.py` → `static/js/board_data.js`，改棋盘后重跑 |
| `tests/` | 16 项测试：5 项接口 + 11 项引擎 |
| `legacy/` | 旧 9 点原型存档，只做参考 |

算法按版本目录组织：`mod1/` 是第一版，以后加 MCTS 版就建 `mod2/`，对外同样暴露
`NAME`、`choose_move(game)`、`evaluate(game)`；再在 `engines/` 下加一个同名一行转发壳
（如 `engines/mcts.py` 里写 `from mod2.rule_based import choose_move, evaluate`），
`$env:TIGER_ENGINE` 指向它就能切换，adapter 不用改。注意 adapter 有引擎名白名单，
新名字要 C 在 `engines/adapter.py` 里补一个。

## 引擎参数

```powershell
$env:TIGER_ENGINE = "mock"        # 默认 rule_based（即 mod1）；mock 仅联调
$env:TIGER_DEPTH = "5"            # 迭代加深上限，默认 4
$env:TIGER_TIME_LIMIT = "2.0"     # 每步软时间上限（秒），默认 1.0
$env:TIGER_ENGINE_API = "legacy"  # 走老的四参数引擎签名
```

超时或终局返回 `None`（前端显示"无可用走法"）。搜索用 `Game.copy()`，不改调用方棋局。

## 验证

```powershell
.venv\Scripts\python -m unittest discover -s tests -v
.venv\Scripts\python scripts/export_board.py
```

当前状态：13/13 通过；`export_board.py` 体检通过且重复运行字节不变；
HTTP 冒烟（首页 200、`/api/state`、`/api/move` 跳吃、`/api/ai` 轮询）通过，
规则引擎白虎开局 0.33s 内选中跳吃，自对弈 40 手无异常。

细节与坑见 [集成说明](docs/集成说明.md)。
