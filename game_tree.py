"""实验二题三：Minimax 与 Alpha-beta。运行：python game_tree.py。"""

from dataclasses import dataclass, field
from math import inf
from typing import Literal


@dataclass
class TreeNode:
    value: int | None = None
    children: list["TreeNode"] = field(default_factory=list)


@dataclass
class SearchStats:
    visited_nodes: int = 0
    evaluated_leaves: int = 0
    cutoffs: int = 0


@dataclass
class GameResult:
    value: int
    stats: SearchStats


def search_tree(
    root: TreeNode,
    *,
    pruning: bool = True,
    order: Literal["original", "reverse"] = "original",
) -> GameResult:
    """根为 MAX，逐层交替；original 严格从左到右，不做缓存。

    visited_nodes 含根、内部节点和叶子；evaluated_leaves 只计访问的叶子。
    cutoffs 只计确实跳过至少一个后续子树的剪枝事件，不等于跳过节点数。
    示例构建中的共享节点按每次递归访问计数，不去重。
    """
    if order not in ("original", "reverse"):
        raise ValueError("order 必须为 original 或 reverse")
    stats = SearchStats()

    def visit(node: TreeNode, maximizing: bool, alpha: float, beta: float) -> int:
        stats.visited_nodes += 1
        if len(node.children) == 0:
            if node.value is None:
                raise ValueError("叶子必须有 value")
            stats.evaluated_leaves += 1
            return node.value
        if node.value is not None:
            raise ValueError("内部节点不能同时有 value 和 children")

        children = node.children if order == "original" else node.children[::-1]
        best = -inf if maximizing else inf
        for index, child in enumerate(children):
            value = visit(child, not maximizing, alpha, beta)
            if maximizing:
                best = max(best, value)
                alpha = max(alpha, best)
            else:
                best = min(best, value)
                beta = min(beta, best)
            if pruning and alpha >= beta:
                if index + 1 < len(children):
                    stats.cutoffs += 1
                break
        return int(best)

    value = visit(root, True, -inf, inf)
    return GameResult(value, stats)


def minimax(root: TreeNode) -> int:
    """完整 Minimax 的根节点最优得分。"""
    return search_tree(root, pruning=False).value


def alpha_beta(root: TreeNode) -> int:
    """题目要求的接口：根为 MAX，按从左到右顺序搜索，返回最佳得分。"""
    return search_tree(root).value


def course_tree() -> TreeNode:
    """按 PDF 的 JSON/构建代码还原：左右 MIN 都引用 max2 分支。"""
    max1 = TreeNode(children=[TreeNode(3), TreeNode(5)])
    max2 = TreeNode(children=[TreeNode(6), TreeNode(9)])
    max3 = TreeNode(children=[TreeNode(1), TreeNode(2)])
    min1 = TreeNode(children=[max1, max2])
    min2 = TreeNode(children=[max2, max3])
    return TreeNode(children=[min1, min2])


def ordering_example() -> TreeNode:
    """自设对照：MAX 的三个 MIN 分支分别为 [3,5]、[2,9]、[1,8]。"""
    return TreeNode(children=[
        TreeNode(children=[TreeNode(3), TreeNode(5)]),
        TreeNode(children=[TreeNode(2), TreeNode(9)]),
        TreeNode(children=[TreeNode(1), TreeNode(8)]),
    ])


def main() -> None:
    for name, root in (("老师样例", course_tree()), ("自设访问顺序对照", ordering_example())):
        print(name)
        for pruning, order in ((False, "original"), (True, "original"), (True, "reverse")):
            result = search_tree(root, pruning=pruning, order=order)
            stats = result.stats
            algorithm = "Alpha-beta" if pruning else "Minimax"
            print(f"{algorithm} / {order}：最佳得分={result.value}，"
                  f"访问节点={stats.visited_nodes}，叶子求值={stats.evaluated_leaves}，"
                  f"有效剪枝事件={stats.cutoffs}")
        print()


if __name__ == "__main__":
    main()
