import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import re

# ===================== Load data =====================

csv_path = os.path.join("results", "test_results.csv")
df = pd.read_csv(csv_path)

vrp_per_task = df.groupby("task_id")["VRP_makespan"].first()

# ===================== Helpers =====================

def natural_sort_key(s):
    match = re.search(r'\d+', str(s))
    return int(match.group())

def task_number(task_id):
    return int(re.search(r'\d+', task_id).group())

def num_subtasks(task_id):
    return (task_number(task_id) - 1) // 3 + 1

# ===================== Pivot tables =====================

llm_pivot = df.pivot_table(
    index="task_id",
    columns="model",
    values="LLM_makespan",
    aggfunc="first"
)

llm_pivot = llm_pivot.reindex(
    sorted(llm_pivot.index, key=natural_sort_key)
)

desired_order = ["gpt-5", "gpt-5-mini", "gpt-4o", "gpt-4.1"]
llm_pivot = llm_pivot[desired_order]

plot_df = llm_pivot.copy()
plot_df["VRP"] = vrp_per_task.reindex(plot_df.index)

# ===================== Inference time =====================

inference_pivot = df.pivot_table(
    index="task_id",
    columns="model",
    values="LLM_inference_time",
    aggfunc="first"
)

inference_pivot = inference_pivot.reindex(
    sorted(inference_pivot.index, key=natural_sort_key)
)
inference_pivot = inference_pivot[desired_order]

# ===================== Plotting =====================

fig, axes = plt.subplots(
    2, 1,
    figsize=(max(10, plot_df.shape[0] * 0.8), 12),
    sharex=False
)

n_tasks = plot_df.shape[0]
n_series = plot_df.shape[1]
x = np.arange(n_tasks)
width = 0.8 / n_series
tasks = plot_df.index.tolist()

# ===== UPPER: Makespan =====
ax = axes[0]

for i, col in enumerate(plot_df.columns):
    ax.bar(
        x + i * width - (n_series - 1) * width / 2,
        plot_df[col].values,
        width,
        label=str(col)
    )

ax.set_xticks(x)
ax.set_xticklabels(tasks)
ax.set_ylabel("Makespan (s)")
ax.set_title("LLM and VRP Makespan by Task")
ax.grid(True, axis="y", linestyle="--", alpha=0.7)
ax.legend(title="Model", bbox_to_anchor=(1.02, 1), loc="upper left")

# ===== LOWER: Inference Time =====
ax2 = axes[1]

for i, col in enumerate(inference_pivot.columns):
    ax2.bar(
        x + i * width - (n_series - 1) * width / 2,
        inference_pivot[col].values,
        width,
        label=str(col)
    )

ax2.set_xticks(x)
ax2.set_xticklabels(tasks)
ax2.set_ylabel("Inference Time (s)")
ax2.set_title("LLM Inference Time by Task")
ax2.grid(True, axis="y", linestyle="--", alpha=0.7)
ax2.legend(title="Model", bbox_to_anchor=(1.02, 1), loc="upper left")

# ===================== Subtask grouping visuals =====================

current_bottom, current_top = ax.get_ylim()
ax.set_ylim(current_bottom, current_top * 1.15)

max_y = ax.get_ylim()[1]

current_subtask = None
group_start = 0

for i, task in enumerate(tasks):
    s = num_subtasks(task)

    # Vertical separator at group boundary
    if current_subtask is not None and s != current_subtask:
        ax.axvline(i - 0.5, color="black", linestyle=":", alpha=0.6)
        ax2.axvline(i - 0.5, color="black", linestyle=":", alpha=0.6)

        center = (group_start + i - 1) / 2
        ax.text(
            center,
            max_y * 0.97,
            f"{current_subtask} subtask{'s' if current_subtask > 1 else ''}",
            ha="center",
            va="top",
            fontsize=11,
            fontweight="bold"
        )

        group_start = i

    current_subtask = s

# Last group label
center = (group_start + len(tasks) - 1) / 2
ax.text(
    center,
    max_y * 0.97,
    f"{current_subtask} subtask{'s' if current_subtask > 1 else ''}",
    ha="center",
    va="top",
    fontsize=11,
    fontweight="bold"
)

# ===================== Save =====================

os.makedirs(os.path.join("results", "visuals"), exist_ok=True)
fig.tight_layout()
fig.savefig(
    os.path.join("results", "visuals", "llm_combined_plots.jpg"),
    dpi=200,
    bbox_inches="tight"
)
plt.close(fig)