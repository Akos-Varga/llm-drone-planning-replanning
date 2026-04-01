import matplotlib.pyplot as plt

# Data (model: correct out of 50)
data = {
    "qwen3:0.6b": 50,
    "gemma3:1b": 22,
    "qwen3:1.7b": 50,
    "qwen2.5:3b": 29,
    "llama3.2:3b": 31,
    "phi4-mini:3.8b": 32,
    "gemma3:4b": 32,
    "qwen3:4b": 50,
    "mistral:7b": 29,
    "qwen2.5:7b": 30,
    "mathstral:7b": 31,
    "llama3.1:8b": 30
}

# Extract data
models = list(data.keys())
percentages = [(v / 50) * 100 for v in data.values()]
sizes = [m.split(":")[1] for m in models]

# Unique sizes and assign colors automatically
unique_sizes = sorted(set(sizes), key=lambda x: float(x.replace("b", "")))
color_map = {size: i for i, size in enumerate(unique_sizes)}

# Assign colors based on size (no manual color specification)
colors = [color_map[size] for size in sizes]

# Plot
plt.figure(figsize=(12, 6))
bars = plt.bar(models, percentages)

# Apply colors using default colormap
for bar, color_idx in zip(bars, colors):
    bar.set_color(plt.cm.tab10(color_idx))

# Labels and title
plt.xlabel("LLM Models")
plt.ylabel("Correctly Solved Tasks (%)")
plt.title("LLM Task Performance (Grouped by Model Size)")
plt.xticks(rotation=45, ha="right")

# Value labels
for i, v in enumerate(percentages):
    plt.text(i, v + 1, f"{v:.0f}%", ha='center')

# Legend
handles = [
    plt.Rectangle((0, 0), 1, 1, color=plt.cm.tab10(color_map[size]))
    for size in unique_sizes
]
plt.legend(handles, unique_sizes, title="Model Size")

plt.tight_layout()

# Save plot
plt.savefig("onboard_llm/llm_performance.png", dpi=300)

plt.show()