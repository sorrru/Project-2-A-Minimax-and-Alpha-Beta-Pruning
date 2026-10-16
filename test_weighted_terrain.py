"""用独立的 Bellman-Ford 松弛核验加权 A*，包含零代价格。"""

import random
import unittest
from math import inf

from weighted_terrain import astar_cost, search_weighted


def reference_cost(grid: list[list[int | str]]) -> int:
    """随机用例的独立参照，仅接受整数和 X；不使用被测代价转换函数。"""
    rows, cols = len(grid), len(grid[0])
    distances = {(r, c): inf for r in range(rows) for c in range(cols)
                 if grid[r][c] != "X"}
    distances[(0, 0)] = 0
    for _ in range(len(distances) - 1):
        changed = False
        for (r, c), distance in list(distances.items()):
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                neighbor = (r + dr, c + dc)
                if neighbor not in distances:
                    continue
                candidate = distance + grid[neighbor[0]][neighbor[1]]
                if candidate < distances[neighbor]:
                    distances[neighbor] = candidate
                    changed = True
        if not changed:
            break
    result = distances[(rows - 1, cols - 1)]
    return -1 if result == inf else int(result)


class WeightedTests(unittest.TestCase):
    def test_course_example(self) -> None:
        grid = [["S", 1, 1, 8, 1], [1, 8, 3, 1, 1], [1, 8, 1, 8, 1],
                [1, 1, 1, 8, 1], [8, 8, 1, 1, "E"]]
        self.assertEqual(astar_cost((0, 0), (4, 4), grid), 7)

    def test_free_goal_and_numeric_goal(self) -> None:
        self.assertEqual(astar_cost((0, 0), (0, 1), [["S", "E"]]), 0)
        self.assertEqual(astar_cost((0, 0), (0, 1), [["S", "3"]]), 3)

    def test_unreachable_and_same_position(self) -> None:
        self.assertEqual(astar_cost((0, 0), (0, 2), [["S", "X", "E"]]), -1)
        self.assertEqual(astar_cost((0, 0), (0, 0), [["S"]]), 0)

    def test_cheaper_route_can_be_longer(self) -> None:
        grid = [["S", 9, "E"], [1, 1, 1]]
        result = search_weighted((0, 0), (0, 2), grid)
        self.assertEqual(result.cost, 3)
        self.assertEqual(len(result.path) - 1, 4)

    def test_invalid_input(self) -> None:
        with self.assertRaises(ValueError):
            astar_cost((0, 0), (0, 1), [["S", -1]])
        with self.assertRaises(ValueError):
            astar_cost((0, 0), (0, 1), [["S", "E"], [1]])

    def test_seeded_maps_against_reference(self) -> None:
        rng = random.Random(42)
        for case in range(100):
            grid = [["X" if rng.random() < 0.2 else rng.randrange(5)
                     for _ in range(5)] for _ in range(4)]
            grid[0][0], grid[-1][-1] = 1, rng.randrange(5)
            expected = reference_cost(grid)
            for heuristic in ("zero", "adjusted_manhattan"):
                with self.subTest(case=case, heuristic=heuristic):
                    result = search_weighted((0, 0), (3, 4), grid, heuristic=heuristic)
                    self.assertEqual(result.cost, expected)
                    if result.path:
                        self.assertEqual(result.path[0], (0, 0))
                        self.assertEqual(result.path[-1], (3, 4))
                        self.assertEqual(result.cost, sum(grid[r][c] for r, c in result.path[1:]))
                    for a, b in zip(result.path, result.path[1:]):
                        self.assertEqual(abs(a[0] - b[0]) + abs(a[1] - b[1]), 1)


if __name__ == "__main__":
    unittest.main()
