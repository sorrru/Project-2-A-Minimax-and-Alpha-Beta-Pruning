"""实验二题四：A* 距离矩阵 + Minimax / Alpha-beta。

运行：python treasure_game.py。所有特殊格进入代价为 1（不同于题二的 E）。
"""

from dataclasses import dataclass
from math import inf
from typing import Literal

from game_tree import SearchStats
from weighted_terrain import Cell, search_weighted

NAMES = ("A", "B", "T1", "T2", "T3", "T4")
POSITIONS = ((0, 0), (6, 6), (0, 6), (2, 2), (4, 4), (6, 0))
VALUES = (0, 0, 9, 6, 7, 7)


def course_grid() -> list[list[Cell]]:
    return [
        ["A", 1, 1, "X", 2, 1, "T1"],
        [1, "X", 6, "X", 1, "X", 1],
        [1, 1, "T2", 1, 1, 1, 1],
        ["X", 1, "X", 8, "X", 1, "X"],
        [1, 1, 1, 1, "T3", 1, 1],
        [1, "X", 9, "X", 1, "X", 1],
        ["T4", 1, 1, "X", 1, 1, "B"],
    ]


def distance_matrix() -> list[list[int]]:
    """分别用 A* 计算 30 个有向点对；对角为 0，不假设距离对称。

    路过宝藏不触发收集，寻路地图始终不变。距离预计算不计入博弈访问节点数。
    """
    numeric = [[1 if cell in NAMES else cell for cell in row] for row in course_grid()]
    return [[search_weighted(start, end, numeric).cost for end in POSITIONS]
            for start in POSITIONS]


@dataclass(frozen=True)
class GameState:
    # 位置是 NAMES / 距离矩阵的索引；剩余宝藏也是索引。
    position_a: int = 0
    position_b: int = 1
    remaining: tuple[int, ...] = (2, 3, 4, 5)
    score_a: int = 0
    score_b: int = 0
    player: Literal["A", "B"] = "A"

    @property
    def utility(self) -> int:
        return self.score_a - self.score_b


@dataclass
class TreasureResult:
    best_target: str | None
    best_value: int
    stats: SearchStats


def take_treasure(state: GameState, target: int, distances: list[list[int]]) -> GameState:
    """只收集本回合选定的宝藏；起点格不计费，移动后更新该玩家位置。"""
    if target not in state.remaining:
        raise ValueError("宝藏已被取得或不存在")
    source = state.position_a if state.player == "A" else state.position_b
    distance = distances[source][target]
    if distance < 0:
        raise ValueError("当前玩家无法到达该宝藏")
    gain = VALUES[target] - distance
    remaining = tuple(t for t in state.remaining if t != target)
    if state.player == "A":
        return GameState(target, state.position_b, remaining,
                         state.score_a + gain, state.score_b, "B")
    return GameState(state.position_a, target, remaining,
                     state.score_a, state.score_b + gain, "A")


def search_treasures(
    distances: list[list[int]],
    depth: int,
    *,
    pruning: bool = True,
    order: Literal["original", "reverse", "gain"] = "original",
    initial_state: GameState | None = None,
) -> TreasureResult:
    """H 为后续行动次数；到深度上限/宝藏取完时返回当前收益差。

    原序 T1,T2,T3,T4；逆序反转剩余列表；gain 按当前玩家即时收益降序。
    gain 是排序启发式，不是局面评价函数，也不保证剪枝一定增加。
    节点/叶子/剪枝统计口径与题三一致，不使用博弈状态缓存。
    """
    if depth < 0:
        raise ValueError("depth 必须非负")
    if order not in ("original", "reverse", "gain"):
        raise ValueError("未知访问顺序")
    stats = SearchStats()

    def visit(state: GameState, left: int, alpha: float, beta: float) -> tuple[int, int | None]:
        stats.visited_nodes += 1
        if left == 0 or len(state.remaining) == 0:
            stats.evaluated_leaves += 1
            return state.utility, None
        source = state.position_a if state.player == "A" else state.position_b
        targets = [t for t in state.remaining if distances[source][t] >= 0]
        if len(targets) == 0:
            # 自设不可达场景采用“无合法行动即终止”约定；课程地图不会触发。
            stats.evaluated_leaves += 1
            return state.utility, None
        if order == "reverse":
            targets.reverse()
        elif order == "gain":
            targets.sort(key=lambda t: -(VALUES[t] - distances[source][t]))

        maximizing = state.player == "A"
        best = -inf if maximizing else inf
        best_target = None
        for index, target in enumerate(targets):
            child = take_treasure(state, target, distances)
            value, _ = visit(child, left - 1, alpha, beta)
            if (maximizing and value > best) or (not maximizing and value < best):
                best, best_target = value, target
            if maximizing:
                alpha = max(alpha, best)
            else:
                beta = min(beta, best)
            if pruning and alpha >= beta:
                if index + 1 < len(targets):
                    stats.cutoffs += 1
                break
        return int(best), best_target

    state = GameState() if initial_state is None else initial_state
    value, target = visit(state, depth, -inf, inf)
    return TreasureResult(None if target is None else NAMES[target], value, stats)


def main() -> None:
    distances = distance_matrix()
    print("A* 最小移动代价矩阵（行：起点；列：终点）")
    print("    " + "".join(f"{name:>5}" for name in NAMES))
    for name, row in zip(NAMES, distances):
        print(f"{name:>4}" + "".join(f"{cost:>5}" for cost in row))
    for depth in (2, 4):
        print(f"\nH={depth}")
        for pruning, order in ((False, "original"), (True, "original"),
                               (True, "reverse"), (True, "gain")):
            result = search_treasures(distances, depth, pruning=pruning, order=order)
            stats = result.stats
            algorithm = "Alpha-beta" if pruning else "Minimax"
            print(f"{algorithm} / {order}：首步={result.best_target}，"
                  f"收益差={result.best_value}，访问节点={stats.visited_nodes}，"
                  f"叶子求值={stats.evaluated_leaves}，有效剪枝事件={stats.cutoffs}")


if __name__ == "__main__":
    main()
