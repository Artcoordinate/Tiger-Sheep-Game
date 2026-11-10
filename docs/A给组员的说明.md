# 37 格棋盘 + 规则引擎：给 D / B / C 的说明（A 出品）

> 结论先放前面：
> - 棋盘：37 个点、76 条连线；开局 2 虎、8 羊，中心空。
> - 方向：和课本图 2-1 一样竖着，9 行 × 5 列，上下各一个王宫。
> - 规则：`rules.py` 里的 `Game` 类，已经处理添子/走子、跳吃、围死、300 步和棋。
> - 测试：`python test_all.py`，16 项全部通过。
> - 图：`图/37格棋盘_初始布局.png`、`图/37格棋盘_编号.png`。

---

## 一、给 D（算法 / Minimax）

### 1. 先换掉迷你棋盘

你现在的 `mini_graph.py` 是 9 个点的测试棋盘，正式版请用 `board.py`：

```python
from board import BOARD_37, TIGER, SHEEP, EMPTY
```

`BOARD_37` 里有：

```python
BOARD_37.points      # 37 个 (row, col)，顺序就是数组下标 0..36
BOARD_37.index       # {(row, col): 下标}
BOARD_37.coords      # 37 个 (x, y) 像素坐标，B 画图用
BOARD_37.edges       # 76 条连线，每条是 (下标, 下标)
BOARD_37.adj         # 邻接表：BOARD_37.adj[i] = [和 i 相连的点...]
BOARD_37.initial     # 开局数组，长度 37
```

开局数组：

```python
[0, 0, 0,
 0, 0, 0,
 0, 0, 1, 0, 0,
 0, 2, 2, 2, 0,
 0, 2, 0, 2, 0,
 0, 2, 2, 2, 0,
 0, 0, 1, 0, 0,
 0, 0, 0,
 0, 0, 0]
```

其中 `1=虎`，`2=羊`，`0=空`。

### 2. 规则不要自己再写一遍，直接用 `Game`

```python
from rules import Game

g = Game()
moves = g.legal_moves()      # 当前玩家的所有合法走法
g.apply(move)                # 走一步（检查合法性、切换玩家、判断胜负）
g.undo()                     # 悔棋（搜索里用）
g.is_over()                  # 是否结束
g.winner                     # None=没结束，1=虎胜，2=羊胜，0=和棋
```

`Game` 已经处理：

- 羊在前 16 手只能 `place`，不能走；
- 第 16 只羊放完后自动进入走子阶段；
- 虎跳吃必须“紧挨着的羊 + 正对面的空点”，不会拐弯；
- 不允许连跳（一次只吃一只）；
- 虎吃满 10 只羊 → 虎胜；
- 轮到虎走、虎没有任何合法走法 → 羊胜；
- 总步数 300 → 和棋。

### 3. 走法的三种格式

```python
("place", to)             # 羊添子：把羊放到 to
("move", frm, to)         # 走一步：从 frm 到 to
("eat", frm, over, to)    # 虎跳吃：从 frm 跳过 over，落到 to
```

`frm / over / to` 都是 0..36 的下标。

### 4. Minimax 建议改成这样

你原来的 `minimax(board, depth, alpha, beta, is_maximizing, phase, remaining_sheep)` 把“棋盘”和“阶段”分开传，搜索时容易忘记更新阶段。建议直接传 `Game`：

```python
def minimax(game, depth, alpha, beta, maximizing):
    if depth == 0 or game.is_over():
        return evaluate(game)

    moves = game.legal_moves()
    if maximizing:
        value = -10**9
        for move in moves:
            game.apply(move)
            value = max(value, minimax(game, depth - 1, alpha, beta, False))
            game.undo()
            alpha = max(alpha, value)
            if alpha >= beta:
                break
        return value
    else:
        value = 10**9
        for move in moves:
            game.apply(move)
            value = min(value, minimax(game, depth - 1, alpha, beta, True))
            game.undo()
            beta = min(beta, value)
            if alpha >= beta:
                break
        return value
```

### 5. 评估函数可以用的东西

```python
game.captured          # 虎已经吃了几只羊
game.sheep_in_hand     # 羊手里还有几只
game.phase             # 1=添子，2=走子
game.board             # 当前棋盘
len(game.legal_moves(TIGER))   # 虎的机动性
len(game.legal_moves(SHEEP))   # 羊的机动性
```

简单版：

```python
def evaluate(game):
    if game.winner == 1:
        return 100000
    if game.winner == 2:
        return -100000
    if game.winner == 0:
        return 0
    score = game.captured * 1000
    score += len(game.legal_moves(1)) * 10
    score -= len(game.legal_moves(2)) * 3
    return score
```

---

## 二、给 B（前端 / 可视化）

### 1. 坐标直接用 `board.py`

```python
from board import BOARD_37

for i, (x, y) in enumerate(BOARD_37.coords):
    print(i, BOARD_37.points[i], x, y)
```

坐标已经是像素坐标：

- 棋盘画布 **408 × 648**（竖版，和课本图同方向）；
- 左上角留 60 像素边距；
- 一格 72 像素；
- `x = 60 + 72 * col`，`y = 60 + 72 * row`。

### 2. 画线

```python
for i, j in BOARD_37.edges:
    x1, y1 = BOARD_37.coords[i]
    x2, y2 = BOARD_37.coords[j]
    # 画线 (x1,y1) -> (x2,y2)
```

`edges` 是 76 条单位线段，直接画就行；每个小格的斜线都在里面。

### 3. 画棋子

```python
for i, value in enumerate(BOARD_37.initial):
    x, y = BOARD_37.coords[i]
    if value == 1:
        ...
    elif value == 2:
        ...
```

开局图 `图/37格棋盘_初始布局.png`，编号图 `图/37格棋盘_编号.png`。

### 4. 点击

鼠标点击 `(mx, my)` 后，找最近的 `coords[i]`：

```python
best_i, best_d = None, 999
for i, (x, y) in enumerate(BOARD_37.coords):
    d = (mx - x) ** 2 + (my - y) ** 2
    if d < best_d:
        best_i, best_d = i, d
if best_d <= 30 ** 2:
    ...
```

### 5. 方向

`board.py` 已经是**竖版**（上下王宫，9 行 × 5 列），和课本图 2-1 一致，不用再旋转。

---

## 三、给 C（后端 / Flask）

### 1. 状态

```python
from rules import Game

g = Game()

@app.get("/api/state")
def state():
    return g.state_dict()
```

`state_dict()` 返回：

```json
{
  "board": [0, 0, ...],
  "phase": 1,
  "player": 1,
  "sheep_in_hand": 16,
  "captured": 0,
  "moves": 0,
  "winner": null,
  "end_reason": "",
  "status": "轮到 虎 走 | 添子阶段 | ...",
  "legal_moves": [["place", 0], ["move", 8, 9], ...]
}
```

### 2. 走子

前端 POST：

```json
{"move": ["place", 18]}
```

后端：

```python
data = request.get_json()
move = tuple(data["move"])
g.apply(move)          # 不合法抛 ValueError，返回 400
return g.state_dict()
```

三种动作：

```json
["place", 18]
["move", 8, 9]
["eat", 8, 12, 16]
```

> JSON 里元组会变成数组，`tuple(...)` 转一下。

### 3. 新局 / 悔棋

```python
g = Game()       # 新局
g.undo()         # 悔棋
```

### 4. 注意

- `Game` 不是线程安全的；Flask 多用户时，每个用户一个 `Game` 实例。
- AI 思考可能比较久，建议放线程里跑，前端显示“思考中”。

---

## 四、给组长 / 文档

A 这边的测试结果：

```
通过 16 项，失败 0 项
```

可以直接写进报告“测试”部分。测试用例表在 `实验一_A部分_文档.docx` 里。

分工说明可以写：

> A 负责棋盘与规则：按课本图 2-1 定义 37 格棋盘的 37 个节点、76 条连线与坐标系统；实现 `rules.py` 规则引擎（添子/走子两阶段、虎跳吃、围死判负、300 步和棋）；编写 16 项自动化测试；绘制棋盘拓扑图与开局图；负责实验文档的需求、设计、测试部分。

---

## 五、最后提醒 D 的三个坑

1. **跳吃别写错**：必须是 `虎 - 羊 - 空` 在一条直线上，且羊在正中间；不能“邻居的邻居”就吃。
2. **添子阶段**：羊只能 `place`，不能 `move`；第 16 只放完才进入走子阶段。
3. **300 步和棋**：搜索里要有步数上限，别让 AI 无限循环。

这三条 `rules.py` 都处理了，D 直接调用 `Game.legal_moves()` 就不会踩。
