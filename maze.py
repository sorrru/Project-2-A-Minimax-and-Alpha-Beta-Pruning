"""实验二题一：用 A* 求四方向、单位代价迷宫的最短路径。

运行：python maze.py
只使用 Python 标准库，兼容 Python 3.10。
"""

import heapq
from dataclasses import dataclass
from itertools import count
from typing import Literal

Position = tuple[int, int]
Heuristic = Literal["zero", "manhattan"]


@dataclass
class SearchResult:
    path: list[Position]
    expanded_nodes: int


def search_maze(
    start: Position,
    end: Position,
    grid: list[list[str]],
    *,
    heuristic: Heuristic = "manhattan",
) -> SearchResult:
    """返回路径及扩展节点数；无路可达时 path=[]。

    扩展节点数：从队列取出有效非终点状态、展开其邻居的次数。
    比较两种启发函数时固定邻居顺序（右、下、左、上），同 f 按入队先后处理。
    """
    if heuristic not in ("zero", "manhattan"):
        raise ValueError("heuristic 必须为 zero 或 manhattan")
    if len(grid) == 0:
        return SearchResult([], 0)
    rows, cols = len(grid), len(grid[0])
    if any(len(row) != cols for row in grid):
        raise ValueError("地图必须为矩形")
    for row, col in (start, end):
        if not (0 <= row < rows and 0 <= col < cols):
            return SearchResult([], 0)
        if grid[row][col] == "X":
            return SearchResult([], 0)

    def h(position: Position) -> int:
        if heuristic == "zero":
            return 0
        return abs(position[0] - end[0]) + abs(position[1] - end[1])

    # 堆元素：(f=g+h, 入队序号, g, 坐标)。序号避免坐标排序影响平局规则。
    order = count()
    frontier = [(h(start), next(order), 0, start)]
    best_g = {start: 0}
    parent: dict[Position, Position] = {}
    expanded = 0

    while frontier:
        _, _, g, current = heapq.heappop(frontier)
        if g != best_g[current]:
            continue  # 跳过后来发现更短路径的旧队列项。
        if current == end:
            path = [current]
            while current != start:
                current = parent[current]
                path.append(current)
            path.reverse()
            return SearchResult(path, expanded)

        expanded += 1
        row, col = current
        for dr, dc in ((0, 1), (1, 0), (0, -1), (-1, 0)):
            neighbor = (row + dr, col + dc)
            nr, nc = neighbor
            if not (0 <= nr < rows and 0 <= nc < cols):
                continue
            if grid[nr][nc] == "X":
                continue
            new_g = g + 1
            if neighbor in best_g and new_g >= best_g[neighbor]:
                continue
            best_g[neighbor] = new_g
            parent[neighbor] = current
            heapq.heappush(
                frontier, (new_g + h(neighbor), next(order), new_g, neighbor)
            )

    return SearchResult([], expanded)


def astar(start: Position, end: Position, grid: list[list[str]]) -> list[Position]:
    """题目要求的接口：只返回坐标序列，无解返回 []。"""
    return search_maze(start, end, grid).path


def main() -> None:
    grid = [
        ["S", ".", ".", "X", "."],
        [".", "X", ".", ".", "."],
        [".", "X", ".", "X", "."],
        [".", ".", ".", "X", "E"],
        ["X", "X", ".", ".", "."],
    ]
    start, end = (0, 0), (3, 4)
    for heuristic in ("zero", "manhattan"):
        result = search_maze(start, end, grid, heuristic=heuristic)
        print(f"启发函数：{heuristic}")
        print(f"路径：{result.path}")
        print(f"移动步数：{len(result.path) - 1 if result.path else -1}")
        print(f"扩展节点数（不含终点）：{result.expanded_nodes}")
        print()


if __name__ == "__main__":
    main()
