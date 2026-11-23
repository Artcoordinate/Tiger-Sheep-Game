# C 实验二交付说明（2026-11-23）

## 交付范围和基线

本次以微信目录中的 Tiger-Sheep-Game(1).zip 为可核验代码基线，其中已经包含 mod1、mod2/mcts.py、engines/mcts.py 和24项测试；另对照《棋谱格式说明.md》及 B 转述的最新版完成情况。

该完整压缩包中的前端尚无 sgf.js 或棋谱侧栏；11月11日“B补丁_国王与大臣棋_修复111与人执大臣”也不是棋谱新版。因此本次只交付 C 后端，不覆盖 B 最新前端。没有读取远程 PR 或合并/推送 GitHub，不能据此断言 PR 已合入。

B 已表示完成：引擎下拉、棋谱侧栏回看、SGF 导出/导入，并顺手接入 /api/ai 的 engine 参数。**合并时先比较 B 的后端修改，若同等功能已完成，不要重复覆盖。**

## 发给组员什么

发“C实验二_后端提交包.zip”。其中代码按仓库相对路径放置：

| 文件 | 本次作用 |
|---|---|
| app.py | 接收每次请求的 engine；入队前校验；任务提交响应也返回实际 engine；引擎列表、可选棋谱校验接口 |
| engines/adapter.py | choose(game, engine=None)，不修改全局环境变量，兼容不传 engine 的原调用 |
| records.py | 新增 version=1 JSON 棋谱逐步重放校验，不落盘 |
| tests/test_mod2_api.py | 新增6项接口回归测试 |
| backend.py、requirements.txt、tests/test_api.py | 沿用完整压缩包版本，附作 C 完整代码参考，已有仓库无须覆盖相同内容 |
| 本说明、C代码修改对照.diff | 交接及与完整压缩包的差异 |

包不含前端文件、mod1/mod2 算法本体、A 规则、.venv 和缓存。必须合入已经有 core/、engines/、mod1/、mod2/、templates/、static/ 的完整仓库，不能把此补交包单独当完整游戏运行。

## 必需接口扩展

```json
POST /api/ai
{"state": {"board": [], "turn": 1, "phase": 1, "inHand": 16, "captured": 0, "ply": 0}, "engine": "mcts"}
```

上述 board 为格式占位，实际必须37项合法局面。可选 rule_based / mcts，mock 仅供联调。不传 engine（或 null）时使用 TIGER_ENGINE，环境变量未设置则默认 rule_based。空字符串、路径、未知引擎均400，**不入线程队列**。cnn/alphazero 未交付，暂不接受。

提交返回 HTTP202：

```json
{"taskId":"任务ID", "status":"pending", "engine":"mcts"}
```

继续沿用 GET /api/tasks/任务ID；完成时返回 status、move、state、engine，其中 engine 为实际调用名。每个任务捕获自己的 engine，不通过修改 os.environ 切换，避免并发请求互相影响。

旧 POST /api/move 和状态字段、动作格式均不变。GET /api/state 仍返回初始局面，当前对局和悔棋历史由浏览器持有。

GET /api/engines 返回 engines 数组和 default，供前端可选使用，不强制 B 改现有代码。

正式 mod1 和 mod2 均用 choose_move(game)。设置 TIGER_ENGINE_API=legacy 时提交正式引擎返回400并提示清除，避免后台才出现参数不匹配。

## 可选：棋谱 JSON 校验，不做存储

B 的 localStorage + SGF 文件已承担棋谱保存，本次不新增 /api/records 存储服务。新增独立可选接口，不要求 B 立即调用：

```javascript
fetch('/api/records/validate', {
  method: 'POST', headers: {'Content-Type':'application/json'},
  body: JSON.stringify({record})
});
```

record 采用 B 第一节字段：version=1、engine、mode、humanSide、result、reason、date、blackName、whiteName、moves。mode/humanSide 必须对应 ai/king、ai-king/minister、human/null。

每步含 side（king/minister）、kind、from、over、to。使用 A 的 Game 从初始局面重放，校验轮流行棋、合法动作及最终结果，报错包含第几步。未结束棋谱允许 result=null（本接口扩展）；结束后必须为 king_win / minister_win / draw，与重放所得胜负一致。reason 仅作文本，不与规则输出逐字比较。日期必须为 YYYY-MM-DD。

成功返回 valid、plies、complete、result、state；非法内容400。请求体上限从16KiB调整为256KiB，以容纳最多300步棋谱。该接口只接受 JSON，不解析 SGF、不保存文件，也不声称校验玩家姓名或引擎来源真实性。

SGF 解析、转义、集合文件和前端回放仍由 B 的 sgf.js 负责。B 文档中的 SGF 是借用SGF容器的自定义动作编码，不等同于普通围棋软件可直接播放的棋谱。

## 测试与限制

```powershell
.venv\Scripts\python -m unittest discover -s tests -v
```

实际在完整压缩包基线上合入 C 修改后：原24项 + 新6项，共30项通过。新增覆盖 MCTS 两方选步、默认引擎与单请求覆盖、非法引擎、棋谱轮次错误、结果伪造和完整对局重放。

现有 MCTS 的时间预算不是线程硬截止，模拟中按算法自身节奏检查时间；网页超时/重开不会终止后台线程。C 保留原两线程、最多四个运行/排队任务的限制。未修改 MCTS 算法、权重、随机性或强度。

没有拿到 B 棋谱新版实际压缩包，故不宣称完成其浏览器端到端验收。已核验的前端仍是老版；不要以 C 本地测试数代替 B 新包合并后的实际测试。

## 合并与启动

1. 保留已合入的 A 规则及 mod1/mod2 算法；确认 engines/mcts.py 转发 mod2.mcts。
2. 保留 B 最新前端及 docs/棋谱格式说明.md。
3. 对照 diff 合并 C 的 app.py / adapter.py；若 B 已完成 engine 贯通，仅补缺项。若采用 records/validate 路由，必须同时提交 records.py。
4. 加入 tests/test_mod2_api.py，运行全套测试。
5. 在项目根目录运行：

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
Remove-Item Env:TIGER_ENGINE_API -ErrorAction SilentlyContinue
.venv\Scripts\python app.py
```

访问 http://127.0.0.1:5000 。B 的算法下拉传 engine 即可切换；默认无需改变环境变量。部署、Git 提交和 PR 合并本次均未执行。
