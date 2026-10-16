# 实验二：搜索算法

Python 3.10+，仅使用标准库，无需安装第三方依赖或使用 GPU。

代码仓库：https://github.com/sorrru/Project-2-A-Minimax-and-Alpha-Beta-Pruning

## 运行

首次获取项目和创建环境：

```bash
git clone https://github.com/sorrru/Project-2-A-Minimax-and-Alpha-Beta-Pruning.git
cd Project-2-A-Minimax-and-Alpha-Beta-Pruning
conda create -n project2 python=3.10
conda activate project2
```

在项目目录执行（本机已有 `project1` 环境也可继续使用）：

```bash
python maze.py
python weighted_terrain.py
python game_tree.py
python treasure_game.py
python -m unittest -v
```

四个脚本对应四题老师样例；代码中的函数可接收相应地图、坐标或博弈树。
题四的地图、特殊点和价值定义在 `treasure_game.py` 中。

## 一键验证与记录

```bash
python run_experiments.py
```

先运行正确性测试，再保存全部四题及自设场景的 26 组实验到 `results/`：

- `tests.log`：测试记录，包括独立 BFS、Bellman-Ford、Dijkstra 和博弈序列穷举对照。
- `summary.csv`：算法、参数、代价/得分、节点数和计时摘要。
- `experiments.json`：完整输入与结果、路径、所有计时样本、首步分支精确值、最优对局过程、环境与代码哈希。
- `distance_matrix.csv`：题四的 6×6 最小代价矩阵。

每个配置先预热一次，再计时 21 次，记录中位数、最小值、最大值；小样例耗时易受系统调度影响，主要以节点数解释搜索开销。排序的内部开销计入时间；题四的距离矩阵预计算单独计时，不混入博弈比较。打印地图与写文件的时间不计入算法耗时。所有样例与访问顺序固定；随机正确性用例使用种子 42。

## 样例预期

| 题目 | 预期 |
|---|---|
| 迷宫 | 7 步，返回任意合法最短路径 |
| 加权地形 | 代价 7 |
| 博弈树 | 最优得分 5 |
| 宝藏竞争 H=2 | T2，收益差 -1 |
| 宝藏竞争 H=4 | T3，收益差 3 |

题三以要求中的 JSON/构建代码为准：左右 MIN 分支都包含叶子 [6,9] 的 MAX 子树；每次递归访问分别计数，不按共享 Python 对象去重。

## 代价与启发函数

- 题一四方向、每步 1：曼哈顿距离可采纳。
- 题二按进入目标格付费，起点初始代价为 0，S 作为普通格按 1、E 按 0。若普通格最低代价为 m、终点代价为 c，则非终点启发值为 `(曼哈顿距离-1)*m+c`，终点为 0。课程样例 m=1、c=0；普通格允许 0 时仍可使用该公式，可能退化为较弱启发。
- 题四 A/B/宝藏格均按 1，路过宝藏不自动收集，另一玩家不阻挡；地图不因收集改变。每轮只获取选择的宝藏，并更新行动方位置与累计收益。
- H 表示剩余行动次数，评价为当前 `Score_A-Score_B`，深度结束后不再追加未来收益。
- `original` 按原顺序；`reverse` 每层逆序；题四 `gain` 按当前行动方的即时收益降序。即时排序仅用于改变访问顺序，不改变评价函数，不保证对所有局面更快。
- 若拓展到不可达局面，程序跳过不可达目标，无合法行动时终止并返回当前收益差；这是自设边界约定，老师的连通地图不会触发。

## 指标定义与自设实验

A* 的扩展节点数不包含终点及过期队列项；同 f 时按入队先后处理，邻居固定右、下、左、上。博弈访问节点数包含根、内部节点、叶子；有效剪枝事件只计真正跳过后续子树的次数，不能当作跳过节点总数。所有比较都不使用博弈状态缓存。

额外实验包含：开放 12×12 迷宫、无解迷宫、绕远但更便宜的加权路径、零代价走廊、访问顺序效果明显的自设树，以及题四按即时收益排序。开放网格可以用于观察大量 f 平局时，曼哈顿距离不一定减少扩展数。

首步分支表均由各分支的完整 Minimax 单独计算；不能将 Alpha-beta 在剪枝时返回的界当作每个分支的精确值。

## 图表与报告

```bash
pip install -r requirements-report.txt
python analyze_results.py
python build_report.py
```

图表与报告的依赖版本见 `requirements-report.txt`；算法和测试不依赖第三方库。`analyze_results.py` 核对记录中的核心代码哈希，再从现有 JSON 生成 `results/figures/` 下的四张图和 `report.md`。它不会重新计时；若修改核心代码，须先重新运行实验。报告由脚本生成，手动编辑后再次运行会覆盖正文，因此定稿前应保留需要的手动修改。

`build_report.py` 从 Markdown 生成自包含的 `report.html`，再使用本机 Chrome 的无界面打印功能生成 `report.pdf`，不操作可见浏览器窗口。默认 Chrome 路径为 macOS 应用路径，可通过 `REPORT_CHROME` 指定。当前报告为 4 页；正文包含两张图，另外两张辅助图保存在 `results/figures/` 中。四页是当前排版结果，并非老师规定的页数上限。

## 当前完成范围

四题算法、样例、自设对照及正确性测试已实现，图表、Markdown、HTML 与 PDF 报告已生成。仓库保存代码、说明、报告 Markdown 源文件和小型实测材料；PDF、生成的 HTML、压缩包及缓存由 `.gitignore` 排除。报告 PDF 保留在本地另行提交，具体页数上限、提交格式和平台以老师后续通知为准。
