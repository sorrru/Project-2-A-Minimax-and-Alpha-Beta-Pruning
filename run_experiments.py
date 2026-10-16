"""统一验证、实验和数据留存。运行：python run_experiments.py。

仅使用标准库。结果保存到脚本旁的 results/，可从任意工作目录运行。
"""

import csv
import hashlib
import json
import platform
import statistics
import subprocess
import sys
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from time import perf_counter_ns
from zoneinfo import ZoneInfo

from game_tree import course_tree, ordering_example, search_tree
from maze import search_maze
from treasure_game import (NAMES, POSITIONS, VALUES, GameState, course_grid,
                           distance_matrix, search_treasures, take_treasure)
from weighted_terrain import search_weighted


def measure(function, repeats: int = 21):
    """预热一次；记录全部计时样本。排序/队列等算法内部开销计入耗时。"""
    result = function()
    samples = []
    for _ in range(repeats):
        start = perf_counter_ns()
        repeated = function()
        samples.append((perf_counter_ns() - start) / 1_000_000)
        if repeated != result:
            raise RuntimeError("相同输入的输出或节点计数发生变化")
    return result, {"repeats": repeats, "median_ms": statistics.median(samples),
                    "min_ms": min(samples), "max_ms": max(samples), "samples_ms": samples}


def main() -> None:
    base = Path(__file__).resolve().parent
    output = base / "results"
    output.mkdir(exist_ok=True)
    test_run = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", str(base), "-v"],
        cwd=base, text=True, capture_output=True, check=False,
    )
    (output / "tests.log").write_text(test_run.stdout + test_run.stderr, encoding="utf-8")
    if test_run.returncode != 0:
        raise SystemExit("测试未通过，停止生成实验结果；详情见 results/tests.log")
    print("正确性测试通过，开始记录实验。")

    records = []

    def record(task, case, algorithm, setting, function, **extra):
        result, timing = measure(function)
        records.append({"task": task, "case": case, "algorithm": algorithm,
                        "setting": setting, "result": asdict(result), "timing": timing,
                        **extra})

    maze_cases = [
        ("course", (0, 0), (3, 4),
         [list(row) for row in ("S..X.", ".X...", ".X.X.", "...XE", "XX...")]),
        ("open_12x12", (0, 0), (11, 11), [["."] * 12 for _ in range(12)]),
        ("unreachable", (0, 0), (0, 2), [list("SXE")]),
    ]
    for case, start, end, grid in maze_cases:
        for heuristic in ("zero", "manhattan"):
            record("maze", case, "A*", heuristic,
                   lambda: search_maze(start, end, grid, heuristic=heuristic),
                   input={"start": start, "end": end, "grid": grid})

    weighted_cases = [
        ("course", (0, 0), (4, 4),
         [["S", 1, 1, 8, 1], [1, 8, 3, 1, 1], [1, 8, 1, 8, 1],
          [1, 1, 1, 8, 1], [8, 8, 1, 1, "E"]]),
        ("cheaper_detour", (0, 0), (0, 2), [["S", 9, "E"], [1, 1, 1]]),
        ("zero_cost_corridor", (0, 0), (0, 3), [["S", 0, 0, "E"]]),
    ]
    for case, start, end, grid in weighted_cases:
        for heuristic in ("zero", "adjusted_manhattan"):
            record("weighted", case, "A*", heuristic,
                   lambda: search_weighted(start, end, grid, heuristic=heuristic),
                   input={"start": start, "end": end, "grid": grid})

    for case, tree in (("course", course_tree()), ("ordering_example", ordering_example())):
        for pruning, order in ((False, "original"), (True, "original"), (True, "reverse")):
            record("tree", case, "Alpha-beta" if pruning else "Minimax", order,
                   lambda: search_tree(tree, pruning=pruning, order=order), input=asdict(tree))

    distances, matrix_timing = measure(distance_matrix)
    for depth in (2, 4):
        for pruning, order in ((False, "original"), (True, "original"),
                               (True, "reverse"), (True, "gain")):
            record("treasure", "course", "Alpha-beta" if pruning else "Minimax", order,
                   lambda: search_treasures(distances, depth, pruning=pruning, order=order),
                   depth=depth)

    # 独立完整搜索每个首步；不能把剪枝返回的界当作每条分支的精确值。
    first_moves = {}
    traces = {}
    for depth in (2, 4):
        first_moves[str(depth)] = {
            NAMES[target]: search_treasures(
                distances, depth - 1, pruning=False,
                initial_state=take_treasure(GameState(), target, distances),
            ).best_value for target in (2, 3, 4, 5)
        }
        state = GameState()
        trace = []
        for left in range(depth, 0, -1):
            decision = search_treasures(distances, left, pruning=False, initial_state=state)
            if decision.best_target is None:
                break
            target = NAMES.index(decision.best_target)
            updated = take_treasure(state, target, distances)
            trace.append({"player": state.player, "target": decision.best_target,
                          "state_after": asdict(updated), "utility": updated.utility})
            state = updated
        traces[str(depth)] = trace

    evidence = {
        "metadata": {
            "generated_at": datetime.now(ZoneInfo("Asia/Shanghai")).isoformat(),
            "python": sys.version, "executable": sys.executable,
            "platform": platform.platform(), "machine": platform.machine(),
            "timing": "预热1次，21次计时；时间单位ms。博弈计时不含距离矩阵预计算。",
            "search_counts": "A*扩展不含终点/过期项；博弈访问含根和叶子；剪枝事件须跳过后续子树。",
            "tie_break": "A*同f按入队先后，邻居右下左上；博弈同值保留当前顺序中首个选择。",
            "source_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                              for p in sorted(base.glob("*.py"))},
        },
        "experiments": records,
        "treasure_input": {"grid": course_grid(), "names": NAMES,
                           "positions": POSITIONS, "values": VALUES},
        "distance_matrix": distances, "distance_matrix_timing": matrix_timing,
        "first_move_values": first_moves, "optimal_play_traces": traces,
    }
    (output / "experiments.json").write_text(
        json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    columns = ["task", "case", "algorithm", "setting", "depth", "best_target", "value",
               "path_steps", "expanded_nodes", "visited_nodes", "evaluated_leaves", "cutoffs",
               "median_ms", "min_ms", "max_ms", "repeats"]
    with (output / "summary.csv").open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        for entry in records:
            result, timing = entry["result"], entry["timing"]
            stats = result.get("stats", {})
            path = result.get("path")
            writer.writerow({
                **{key: entry.get(key, "") for key in ("task", "case", "algorithm", "setting", "depth")},
                "best_target": result.get("best_target", ""),
                "value": result.get("cost", result.get("best_value", result.get("value", ""))),
                "path_steps": "" if path is None else len(path) - 1,
                "expanded_nodes": result.get("expanded_nodes", ""),
                **{key: stats.get(key, "") for key in ("visited_nodes", "evaluated_leaves", "cutoffs")},
                **{key: timing[key] for key in ("median_ms", "min_ms", "max_ms", "repeats")},
            })
    with (output / "distance_matrix.csv").open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["from/to", *NAMES])
        writer.writerows([[name, *row] for name, row in zip(NAMES, distances)])
    print(f"已保存 {len(records)} 组实验，每组计时 21 次：{output}")
    print("summary.csv：指标与耗时；experiments.json：完整输入/路径/计时/首步收益/对局过程。")
    print("distance_matrix.csv：距离矩阵；tests.log：正确性测试记录。")
    for depth, values in first_moves.items():
        print(f"H={depth} 各首步的精确收益差：{values}")


if __name__ == "__main__":
    main()
