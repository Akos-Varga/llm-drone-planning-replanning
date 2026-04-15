import matplotlib.pyplot as plt
import numpy as np

data = {
    "qwen3:0.6b": [18, 8, 6, 16], # Avg: 7.99, max: 239.60
    "gemma3:1b": [20, 15, 0, 0], # Avg: 0.76, max: 2.83
    "qwen3:1.7b": [20, 20, 20, 20], # Avg: 3.60, max: 7.45
    "qwen2.5:3b": [7, 20, 20, 9], # Avg: 1.02, max: 6.44
    "llama3.2:3b": [13, 20, 18, 0], # Avg: 1.25, max: 14.24
    "phi4-mini:3.8b": [20, 20, 20, 1], # Avg: 1.52, max: 7.72
    "gemma3:4b": [14, 20, 9, 0], # Avg: 1.20, max: 9.12
}

# Slightly cleaner x-axis labels for publication
label_map = {
    "qwen3:0.6b": "Qwen3\n0.6B",
    "gemma3:1b": "Gemma3\n1B",
    "qwen3:1.7b": "Qwen3\n1.7B",
    "qwen2.5:3b": "Qwen2.5\n3B",
    "llama3.2:3b": "Llama3.2\n3B",
    "phi4-mini:3.8b": "Phi4-mini\n3.8B",
    "gemma3:4b": "Gemma3\n4B",
}

models = list(data.keys())
display_labels = [label_map[m] for m in models]
values = np.array(list(data.values()))

categories = [
    "Accept",
    "Drone state",
    "Link quality",
    "Flight time"
]

x = np.arange(len(models))
width = 0.72
bottom = np.zeros(len(models))

# IEEE-like sizing and typography
plt.rcParams.update({
    "font.family": "serif",
    "font.size": 8,
    "axes.labelsize": 8,
    "axes.titlesize": 8,
    "legend.fontsize": 7,
    "xtick.labelsize": 7,
    "ytick.labelsize": 7,
})

fig, ax = plt.subplots(figsize=(7.1, 3.2))

for i in range(values.shape[1]):
    bars = ax.bar(
        x,
        values[:, i],
        width=width,
        bottom=bottom,
        label=categories[i],
        edgecolor="black",
        linewidth=0.5
    )

    for j, bar in enumerate(bars):
        val = values[j, i]
        if val >= 4:
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bottom[j] + val / 2,
                f"{int(val)}",
                ha="center",
                va="center",
                fontsize=7
            )

    bottom += values[:, i]

# Totals on top
totals = values.sum(axis=1)
for i, total in enumerate(totals):
    ax.text(
        x[i],
        total + 1.0,
        f"{int(total)}",
        ha="center",
        va="bottom",
        fontsize=7,
        fontweight="bold"
    )

ax.set_xticks(x)
ax.set_xticklabels(display_labels)
ax.set_ylabel("Solved tasks")
ax.set_xlabel("Model")

ax.set_ylim(0, max(totals) + 8)
ax.grid(axis="y", linestyle="--", linewidth=0.5, alpha=0.7)
ax.set_axisbelow(True)

# Compact legend above the plot
ax.legend(
    ncol=4,
    loc="upper center",
    bbox_to_anchor=(0.5, 1.18),
    frameon=False,
    columnspacing=1.0,
    handletextpad=0.4
)

# Cleaner frame
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

plt.tight_layout()

plt.savefig("onboard_llm/stacked_task_performance_3_output.png", dpi=600, bbox_inches="tight")

plt.show()