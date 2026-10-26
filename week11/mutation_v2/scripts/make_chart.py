"""Create a v1 vs v2 mutation-score chart for the report.

Usage:
    python week11/mutation_v2/scripts/make_chart.py \
        week7/mutation_v1_summary.json \
        week11/mutation_v2/mutation_v2_summary.json \
        week11/mutation_v2/v1_vs_v2.png
"""

import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402


def main():
    v1_path, v2_path, out = sys.argv[1:4]
    v1 = json.loads(Path(v1_path).read_text(encoding="utf-8"))
    v2 = json.loads(Path(v2_path).read_text(encoding="utf-8"))
    modules = [m for m in v2 if m != "TOTAL"]
    modules.sort(key=lambda m: v2[m]["score"], reverse=True)
    labels = ["TOTAL"] + modules
    a = [v1.get(m, {}).get("score", 0) for m in labels]
    b = [v2.get(m, {}).get("score", 0) for m in labels]

    x = range(len(labels))
    width = 0.38
    fig, ax = plt.subplots(figsize=(10, 4.8))
    ax.bar([i - width / 2 for i in x], a, width, label="v1 AI-only (Week 7)")
    ax.bar([i + width / 2 for i in x], b, width, label="v2 final hybrid (Week 11)")
    ax.set_ylabel("Mutation score (%)")
    ax.set_ylim(0, 100)
    ax.set_xticks(list(x))
    ax.set_xticklabels(labels, rotation=30, ha="right")
    ax.legend()
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(out, dpi=160)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
