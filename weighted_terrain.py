"""实验二题二：加权地形 A*。运行：python weighted_terrain.py。

进入邻格时支付该格代价；S 按 1、E 按 0 处理，起点初始代价为 0。
支持非负整数地形及 X 障碍，只使用 Python 3.10 标准库。
"""

import heapq
from dataclasses import dataclass
from itertools import count
from typing import Literal

Position = tuple[int, int]
Cell = int | str


@dataclass
class WeightedResult:
    cost: int
    path: list[Position]
    expanded_nodes: int


def terrain_cost(cell: Cell) -> int | None:
    """None 表示障碍；S/E 是题二约定，不应用于题四的特殊格。"""
    if cell == "X":
        return None
    if cell == "S":
        return 1
    if cell == "E":
        return 0
    if isinstance(cell, int) and not isinstance(cell, bool) and cell >= 0:
        return cell
    if isinstance(cell, str) and cell.isdecimal():
        return int(cell)
    raise ValueError(f"无效地形：{cell!r}；只接受非负整数、S、E 或 X")


def search_weighted(
    start: Position,
    end: Position,
    grid: list[list[Cell]],
    *,
    heuristic: Literal["zero", "adjusted_manhattan"] = "adjusted_manhattan",
) -> WeightedResult:
    """返回最小代价、路径和扩展节点数；无解时 cost=-1。

    固定邻居顺序为右、下、左、上，同 f 按入队先后处理。
    扩展节点不含终点，不计过期堆项，与题一采用相同计数口径。
    """
    if heuristic not in ("zero", "adjusted_manhattan"):
        raise ValueError("未知启发函数")
    if len(grid) == 0:
        return WeightedResult(-1, [], 0)
    rows, cols = len(grid), len(grid[0])
    if any(len(row) != cols for row in grid):
        raise ValueError("地图必须为矩形")
    costs = [[terrain_cost(cell) for cell in row] for row in grid]
    for row, col in (start, end):
        if not (0 <= row < rows and 0 <= col < cols):
            return WeightedResult(-1, [], 0)
        if costs[row][col] is None:
            return WeightedResult(-1, [], 0)

    # 普通 Manhattan 在 E 进入代价为 0 时可能高估。
    # 剩余 L 步至少包括 L-1 个非终点格和最后一个终点格。
    others = [costs[r][c] for r in range(rows) for c in range(cols)
              if (r, c) != end and costs[r][c] is not None]
    minimum = min(others, default=0)
    goal_cost = costs[end[0]][end[1]]

    def h(position: Position) -> int:
        if heuristic == "zero" or position == end:
            return 0
        distance = abs(position[0] - end[0]) + abs(position[1] - end[1])
        return (distance - 1) * minimum + goal_cost

    sequence = count()
    frontier = [(h(start), next(sequence), 0, start)]
    best_g = {start: 0}
    parent: dict[Position, Position] = {}
    expanded = 0
    while frontier:
        _, _, g, current = heapq.heappop(frontier)
        if g != best_g[current]:
            continue
        if current == end:
            path = [current]
            while current != start:
                current = parent[current]
                path.append(current)
            path.reverse()
            return WeightedResult(g, path, expanded)
        expanded += 1
        row, col = current
        for dr, dc in ((0, 1), (1, 0), (0, -1), (-1, 0)):
            nr, nc = row + dr, col + dc
            if not (0 <= nr < rows and 0 <= nc < cols):
                continue
            step_cost = costs[nr][nc]
            if step_cost is None:
                continue
            neighbor = (nr, nc)
            new_g = g + step_cost
            if neighbor in best_g and new_g >= best_g[neighbor]:
                continue
            best_g[neighbor] = new_g
            parent[neighbor] = current
            heapq.heappush(
                frontier, (new_g + h(neighbor), next(sequence), new_g, neighbor)
            )
    return WeightedResult(-1, [], expanded)


def astar_cost(start: Position, end: Position, grid: list[list[Cell]]) -> int:
    """题目要求的接口：只返回最小总代价，无解返回 -1。"""
    return search_weighted(start, end, grid).cost


def main() -> None:
    grid = [
        ["S", 1, 1, 8, 1],
        [1, 8, 3, 1, 1],
        [1, 8, 1, 8, 1],
        [1, 1, 1, 8, 1],
        [8, 8, 1, 1, "E"],
    ]
    for heuristic in ("zero", "adjusted_manhattan"):
        result = search_weighted((0, 0), (4, 4), grid, heuristic=heuristic)
        steps = [terrain_cost(grid[r][c]) for r, c in result.path[1:]]
        print(f"启发函数：{heuristic}")
        print(f"路径：{result.path}")
        print(f"沿途进入代价（不计起点）：{steps}")
        print(f"最小总代价：{result.cost}")
        print(f"扩展节点数（不含终点）：{result.expanded_nodes}")
        print()


if __name__ == "__main__":
    main()
