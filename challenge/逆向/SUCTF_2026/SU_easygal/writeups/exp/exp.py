import json
import hashlib
from pathlib import Path

STORY_PATH = Path(r"Assets/Resources/Story/story.json")


def solve_story(path: Path):
    data = json.loads(path.read_text(encoding="utf-8"))
    nodes = data["nodes"]
    max_weight = int(data["meta"]["maxWeight"])
    true_value = int(data["meta"]["trueEndingValue"])

    neg_inf = -10**18

    # dp[w] = {
    #   "value": 当前 weight=w 时的最大 value
    #   "count": 达到该最大 value 的方案数
    #   "path": 若 count==1，则保存唯一路径 flag 列表，否则为 None
    #   "markers": 若 count==1，则保存唯一 marker 串，否则为 None
    # }
    dp = [
        {"value": neg_inf, "count": 0, "path": None, "markers": None}
        for _ in range(max_weight + 1)
    ]
    dp[0] = {"value": 0, "count": 1, "path": [], "markers": ""}

    for node in nodes:
        nxt = [
            {"value": neg_inf, "count": 0, "path": None, "markers": None}
            for _ in range(max_weight + 1)
        ]

        for w in range(max_weight + 1):
            state = dp[w]
            if state["count"] == 0:
                continue

            for choice in node["choices"]:
                nw = w + int(choice["weight"])
                if nw > max_weight:
                    continue

                nv = state["value"] + int(choice["value"])
                target = nxt[nw]

                if state["count"] == 1:
                    cand_path = state["path"] + [choice["flag"]]
                    cand_markers = state["markers"] + choice["marker"]
                else:
                    cand_path = None
                    cand_markers = None

                if nv > target["value"]:
                    target["value"] = nv
                    target["count"] = state["count"]
                    target["path"] = cand_path if state["count"] == 1 else None
                    target["markers"] = cand_markers if state["count"] == 1 else None
                elif nv == target["value"]:
                    target["count"] += state["count"]
                    target["path"] = None
                    target["markers"] = None

        dp = nxt

    best_value = max(s["value"] for s in dp if s["count"] > 0)

    optimal_count = 0
    unique_weight = None
    unique_path = None
    unique_markers = None

    for w, state in enumerate(dp):
        if state["count"] == 0 or state["value"] != best_value:
            continue
        optimal_count += state["count"]
        if optimal_count == state["count"] and state["count"] == 1:
            unique_weight = w
            unique_path = state["path"]
            unique_markers = state["markers"]
        else:
            unique_weight = None
            unique_path = None
            unique_markers = None

    print(f"NodeCount={len(nodes)}")
    print(f"MaxWeight={max_weight}")
    print(f"ConfiguredTrueEndingValue={true_value}")
    print(f"BestValue={best_value}")
    print(f"OptimalPathCount={optimal_count}")

    if best_value != true_value:
        raise RuntimeError(
            f"trueEndingValue mismatch: configured={true_value}, computed={best_value}"
        )
    if optimal_count != 1:
        raise RuntimeError(f"Not unique: optimal path count = {optimal_count}")

    flag = "SUCTF{" + hashlib.md5(unique_markers.encode("utf-8")).hexdigest() + "}"

    print(f"OptimalWeight={unique_weight}")
    print("UniquePath=" + ",".join(unique_path))
    print("MarkerString=" + unique_markers)
    print("Flag=" + flag)


if __name__ == "__main__":
    solve_story(STORY_PATH)
