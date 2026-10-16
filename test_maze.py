"""以独立 BFS 为参照核验最短路径，运行：python -m unittest -v。"""

import random
import unittest
from collections import deque

from maze import astar, search_maze


def bfs_distance(grid: list[list[str]]) -> int:
    end = (len(grid) - 1, len(grid[0]) - 1)
    queue = deque([((0, 0), 0)])
    visited = {(0, 0)}
    while queue:
        (row, col), distance = queue.popleft()
        if (row, col) == end:
            return distance
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = row + dr, col + dc
            if (0 <= nr < len(grid) and 0 <= nc < len(grid[0])
                    and grid[nr][nc] != "X" and (nr, nc) not in visited):
                visited.add((nr, nc))
                queue.append(((nr, nc), distance + 1))
    return -1


class MazeTests(unittest.TestCase):
    def test_course_example(self) -> None:
        grid = [list(row) for row in ("S..X.", ".X...", ".X.X.", "...XE", "XX...")]
        path = astar((0, 0), (3, 4), grid)
        self.assertEqual(path[0], (0, 0))
        self.assertEqual(path[-1], (3, 4))
        self.assertEqual(len(path) - 1, 7)

    def test_unreachable(self) -> None:
        self.assertEqual(astar((0, 0), (0, 2), [list("SXE")]), [])

    def test_same_start_end(self) -> None:
        result = search_maze((0, 0), (0, 0), [["S"]])
        self.assertEqual(result.path, [(0, 0)])
        self.assertEqual(result.expanded_nodes, 0)

    def test_invalid_endpoint(self) -> None:
        self.assertEqual(astar((0, 0), (0, 1), [["S", "X"]]), [])
        self.assertEqual(astar((-1, 0), (0, 0), [["S"]]), [])
        self.assertEqual(astar((0, 0), (0, 0), []), [])

    def test_seeded_maps_against_bfs(self) -> None:
        rng = random.Random(42)
        for case in range(100):
            grid = [["X" if rng.random() < 0.3 else "." for _ in range(7)]
                    for _ in range(6)]
            grid[0][0], grid[-1][-1] = "S", "E"
            expected = bfs_distance(grid)
            for heuristic in ("zero", "manhattan"):
                with self.subTest(case=case, heuristic=heuristic):
                    path = search_maze((0, 0), (5, 6), grid, heuristic=heuristic).path
                    self.assertEqual(len(path) - 1 if path else -1, expected)
                    if path:
                        self.assertEqual(path[0], (0, 0))
                        self.assertEqual(path[-1], (5, 6))
                    for row, col in path:
                        self.assertNotEqual(grid[row][col], "X")
                    for a, b in zip(path, path[1:]):
                        self.assertEqual(abs(a[0] - b[0]) + abs(a[1] - b[1]), 1)


if __name__ == "__main__":
    unittest.main()
