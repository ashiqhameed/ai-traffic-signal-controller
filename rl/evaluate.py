"""
Compare all policies on identical, unseen traffic and write the results.

    python rl/train.py      # once, to create rl/models/
    python rl/evaluate.py   # writes rl/results/results.md and comparison.png

Every policy is run on the same EVAL_EPISODES seeds (disjoint from training
seeds), so differences come from the policy, not from luckier traffic.
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from policies import LinearQAgent, fixed_time, longest_queue, priority_heuristic
from traffic_env import SCENARIOS, Intersection
from train import MODEL_DIR

EVAL_EPISODES = 300
EVAL_SEED_OFFSET = 1_000_000
RESULTS_DIR = os.path.join(os.path.dirname(__file__), "results")


def run_policy(policy, scenario):
    env = Intersection(scenario)
    rows = []
    for i in range(EVAL_EPISODES):
        env.reset(seed=EVAL_SEED_OFFSET + i)
        while not env.done:
            env.step(policy(env))
        rows.append(env.episode_metrics())
    return {k: np.array([r[k] for r in rows], dtype=float) for k in rows[0]}


def ci95(x):
    return 1.96 * x.std(ddof=1) / np.sqrt(len(x))


def main():
    os.makedirs(RESULTS_DIR, exist_ok=True)
    policy_names = ["Fixed-time", "Priority heuristic (original)", "Longest queue first", "Q-learning agent"]
    all_results = {}
    for scenario in SCENARIOS:
        agent = LinearQAgent.load(os.path.join(MODEL_DIR, f"weights_{scenario}.npy"))
        policies = [fixed_time, priority_heuristic, longest_queue, agent.policy]
        all_results[scenario] = {n: run_policy(p, scenario) for n, p in zip(policy_names, policies)}

    lines = ["# Results", "",
             f"{EVAL_EPISODES} evaluation episodes x 200 cycles (~17 simulated minutes each) per policy, "
             "on traffic the agent never saw in training. ± is a 95% confidence interval.", ""]
    for scenario, res in all_results.items():
        base = res["Priority heuristic (original)"]["mean_wait"]
        lines += [f"## {scenario.replace('_', ' ').title()} — {SCENARIOS[scenario]['description']}", "",
                  "| Policy | Mean wait / car (s) | 95th pct wait (s) | vs. original heuristic |",
                  "|---|---|---|---|"]
        for name, r in res.items():
            diff = (r["mean_wait"] - base) / base  # paired: same seeds for every policy
            vs = "—" if name.startswith("Priority") else f"{diff.mean():+.1%} ± {ci95(diff):.1%}"
            lines.append(f"| {name} | {r['mean_wait'].mean():.2f} ± {ci95(r['mean_wait']):.2f} "
                         f"| {r['p95_wait'].mean():.1f} ± {ci95(r['p95_wait']):.1f} | {vs} |")
        lines.append("")
    with open(os.path.join(RESULTS_DIR, "results.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("\n".join(lines))

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))
    colors = ["#9e9e9e", "#4C72B0", "#8172B3", "#DD8452"]
    x = np.arange(len(SCENARIOS))
    width = 0.2
    for ax, metric, title in [(axes[0], "mean_wait", "Mean wait per car"),
                              (axes[1], "p95_wait", "95th-percentile wait")]:
        for i, name in enumerate(policy_names):
            vals = [all_results[s][name][metric] for s in SCENARIOS]
            ax.bar(x + (i - 1.5) * width, [v.mean() for v in vals], width,
                   yerr=[ci95(v) for v in vals], capsize=3, color=colors[i], label=name)
        ax.set_xticks(x, [s.replace("_", " ").title() for s in SCENARIOS])
        ax.set(title=title, ylabel="seconds")
        ax.spines[["top", "right"]].set_visible(False)
    # Fixed-time in rush hour dwarfs the others; clip so the rest stay readable
    for ax, metric in [(axes[0], "mean_wait"), (axes[1], "p95_wait")]:
        top = max(all_results[s][n][metric].mean() for s in SCENARIOS for n in policy_names[1:])
        ax.set_ylim(0, top * 1.6)
    plt.tight_layout(rect=(0, 0.1, 1, 1))
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=4, frameon=False, fontsize=9,
               bbox_to_anchor=(0.5, 0.02))
    fig.text(0.5, -0.01, "Fixed-time bars are clipped in rush hour — see results.md for exact values.",
             ha="center", fontsize=8, color="#666")
    plt.savefig(os.path.join(RESULTS_DIR, "comparison.png"), dpi=120, bbox_inches="tight")


if __name__ == "__main__":
    main()
