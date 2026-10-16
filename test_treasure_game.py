"""题四验证：独立 Dijkstra 核验距离，穷举行动序列核验博弈值。"""

import heapq
import unittest
from itertools import permutations

from treasure_game import (NAMES, POSITIONS, VALUES, GameState, course_grid,
                           distance_matrix, search_treasures, take_treasure)


def reference_distances(start: tuple[int, int]) -> dict[tuple[int, int], int]:
    grid = course_grid()
    distances = {start: 0}
    queue = [(0, start)]
    while queue:
        cost, position = heapq.heappop(queue)
        if distances[position] != cost:
            continue
        r, c = position
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = r + dr, c + dc
            if not (0 <= nr < len(grid) and 0 <= nc < len(grid[0])):
                continue
            cell = grid[nr][nc]
            if cell == "X":
                continue
            step = cell if isinstance(cell, int) else 1
            candidate = cost + step
            if (nr, nc) not in distances or candidate < distances[(nr, nc)]:
                distances[(nr, nc)] = candidate
                heapq.heappush(queue, (candidate, (nr, nc)))
    return distances


def exhaustive_value(distances: list[list[int]], depth: int) -> tuple[int, set[str]]:
    """先列出全部行动序列并独立累计收益，再逐层归约，不调用被测状态更新。"""
    depth = min(depth, 4)
    values = {}
    for moves in permutations((2, 3, 4, 5), depth):
        positions = [0, 1]
        scores = [0, 0]
        for turn, target in enumerate(moves):
            player = turn % 2
            scores[player] += VALUES[target] - distances[positions[player]][target]
            positions[player] = target
        values[moves] = scores[0] - scores[1]
    for prefix_length in range(depth - 1, -1, -1):
        prefixes = {sequence[:prefix_length] for sequence in values
                    if len(sequence) == prefix_length + 1}
        for prefix in prefixes:
            candidates = [value for sequence, value in values.items()
                          if len(sequence) == prefix_length + 1 and sequence[:-1] == prefix]
            values[prefix] = max(candidates) if prefix_length % 2 == 0 else min(candidates)
    best = values[()]
    targets = {NAMES[t] for t in (2, 3, 4, 5) if values[(t,)] == best}
    return best, targets


class TreasureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.distances = distance_matrix()

    def test_all_pairs_against_independent_dijkstra(self) -> None:
        for i, start in enumerate(POSITIONS):
            expected = reference_distances(start)
            self.assertEqual(self.distances[i], [expected[end] for end in POSITIONS])

    def test_special_cells_cost_one(self) -> None:
        self.assertEqual(self.distances[0][3], 4)  # A -> T2，不得错误地免除终点代价。
        self.assertEqual(self.distances[1][4], 4)  # B -> T3。

    def test_course_expectations_and_orders(self) -> None:
        for depth, target, value in ((2, "T2", -1), (4, "T3", 3)):
            full = search_treasures(self.distances, depth, pruning=False)
            self.assertEqual((full.best_target, full.best_value), (target, value))
            for order in ("original", "reverse", "gain"):
                with self.subTest(depth=depth, order=order):
                    result = search_treasures(self.distances, depth, order=order)
                    self.assertEqual((result.best_target, result.best_value), (target, value))
                    self.assertLessEqual(result.stats.visited_nodes, full.stats.visited_nodes)

    def test_all_depths_against_exhaustive_sequences(self) -> None:
        for depth in range(1, 5):
            expected, optimal_targets = exhaustive_value(self.distances, depth)
            for pruning in (False, True):
                for order in ("original", "reverse", "gain"):
                    with self.subTest(depth=depth, pruning=pruning, order=order):
                        result = search_treasures(self.distances, depth, pruning=pruning, order=order)
                        self.assertEqual(result.best_value, expected)
                        self.assertIn(result.best_target, optimal_targets)

    def test_state_update(self) -> None:
        initial = GameState()
        after_a = take_treasure(initial, 3, self.distances)
        self.assertEqual(after_a.position_a, 3)
        self.assertEqual(after_a.position_b, 1)
        self.assertEqual(after_a.remaining, (2, 4, 5))
        self.assertEqual((after_a.score_a, after_a.score_b, after_a.player), (2, 0, "B"))
        after_b = take_treasure(after_a, 4, self.distances)
        self.assertEqual((after_b.position_a, after_b.position_b), (3, 4))
        self.assertEqual((after_b.score_a, after_b.score_b, after_b.utility), (2, 3, -1))
        self.assertEqual(initial, GameState())  # 子状态不能污染同层其他分支。
        with self.assertRaises(ValueError):
            take_treasure(after_a, 3, self.distances)

    def test_cutoff_and_terminal_states(self) -> None:
        state = GameState(score_a=-2, score_b=1)
        result = search_treasures(self.distances, 0, initial_state=state)
        self.assertEqual((result.best_target, result.best_value), (None, -3))
        finished = GameState(remaining=(), score_a=4, score_b=1)
        self.assertEqual(search_treasures(self.distances, 4, initial_state=finished).best_value, 3)
        self.assertEqual(search_treasures(self.distances, 8).best_value, 3)


if __name__ == "__main__":
    unittest.main()
