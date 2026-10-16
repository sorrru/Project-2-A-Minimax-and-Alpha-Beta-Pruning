"""运行：python -m unittest -v。"""

import random
import unittest

from game_tree import TreeNode, alpha_beta, course_tree, minimax, ordering_example, search_tree


class GameTreeTests(unittest.TestCase):
    def test_course_example(self) -> None:
        self.assertEqual(minimax(course_tree()), 5)
        self.assertEqual(alpha_beta(course_tree()), 5)
        self.assertEqual(search_tree(course_tree(), pruning=False).stats.visited_nodes, 15)

    def test_leaf_zero_and_negative_scores(self) -> None:
        for value in (0, -7, 6):
            with self.subTest(value=value):
                result = search_tree(TreeNode(value))
                self.assertEqual(result.value, value)
                self.assertEqual(result.stats.visited_nodes, 1)
                self.assertEqual(result.stats.evaluated_leaves, 1)
        self.assertEqual(alpha_beta(TreeNode(children=[TreeNode(-4), TreeNode(-2)])), -2)

    def test_order_affects_work_but_not_value(self) -> None:
        root = ordering_example()
        baseline = search_tree(root, pruning=False)
        forward = search_tree(root)
        reverse = search_tree(root, order="reverse")
        self.assertEqual([baseline.value, forward.value, reverse.value], [3, 3, 3])
        self.assertLess(forward.stats.visited_nodes, reverse.stats.visited_nodes)
        self.assertEqual(reverse.stats.visited_nodes, baseline.stats.visited_nodes)

    def test_equal_bounds_allow_pruning(self) -> None:
        root = TreeNode(children=[
            TreeNode(children=[TreeNode(3), TreeNode(4)]),
            TreeNode(children=[TreeNode(3), TreeNode(9)]),
        ])
        result = search_tree(root)
        self.assertEqual(result.value, 3)
        self.assertEqual(result.stats.evaluated_leaves, 3)
        self.assertEqual(result.stats.cutoffs, 1)

    def test_malformed_leaf(self) -> None:
        with self.assertRaises(ValueError):
            alpha_beta(TreeNode())

    def test_random_trees_agree_with_full_search(self) -> None:
        rng = random.Random(42)

        def generate(depth: int) -> TreeNode:
            if depth == 0 or rng.random() < 0.2:
                return TreeNode(rng.randrange(-10, 11))
            return TreeNode(children=[generate(depth - 1) for _ in range(rng.randrange(1, 5))])

        for case in range(100):
            root = generate(4)
            full = search_tree(root, pruning=False)
            for order in ("original", "reverse"):
                with self.subTest(case=case, order=order):
                    result = search_tree(root, order=order)
                    self.assertEqual(result.value, full.value)
                    self.assertLessEqual(result.stats.visited_nodes, full.stats.visited_nodes)
                    self.assertLessEqual(result.stats.evaluated_leaves, full.stats.evaluated_leaves)


if __name__ == "__main__":
    unittest.main()
