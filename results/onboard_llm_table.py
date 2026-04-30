import os
import pandas as pd

# ===================== Input data =====================

# Columns: number of correctly solved tasks out of 20
data = {
    "qwen3:0.6b": [18, 8, 6, 16],
    "gemma3:1b": [20, 15, 0, 0],
    "qwen3:1.7b": [20, 20, 20, 20],
    "qwen2.5:3b": [7, 20, 20, 9],
    "llama3.2:3b": [13, 20, 18, 0],
    "phi4-mini:3.8b": [20, 20, 20, 1],
    "gemma3:4b": [14, 20, 9, 0],
}

# Columns: average and maximum inference time
inference_times = {
    "qwen3:0.6b": [7.99, 24.75],
    "gemma3:1b": [0.76, 2.83],
    "qwen3:1.7b": [3.60, 7.45],
    "qwen2.5:3b": [1.02, 6.44],
    "llama3.2:3b": [1.25, 14.24],
    "phi4-mini:3.8b": [1.52, 7.72],
    "gemma3:4b": [1.20, 9.12],
}

# ===================== Output directory =====================

output_dir = os.path.join("results", "tables")
os.makedirs(output_dir, exist_ok=True)

# ===================== Build accuracy table =====================

accuracy_columns = [
    "Acceptable task",
    "Drone state error",
    "Link quality error",
    "Flight time error",
]

accuracy_df = pd.DataFrame.from_dict(
    data,
    orient="index",
    columns=accuracy_columns
)

accuracy_df.index.name = "Model"

# ===================== Build inference-time table =====================

inference_df = pd.DataFrame.from_dict(
    inference_times,
    orient="index",
    columns=["Average inference time (s)", "Maximum inference time (s)"]
)

inference_df.index.name = "Model"
inference_df = inference_df.round(2)

# ===================== Helper to write centered LaTeX tables =====================

def write_latex_table(df, path, caption, label):
    latex_body = df.to_latex(
        index=True,
        escape=False,
        na_rep="--",
        float_format="%.2f"
    )

    full_latex = f"""\\begin{{table}}[t]
\\centering
\\caption{{{caption}}}
\\label{{{label}}}
{latex_body}
\\end{{table}}
"""

    with open(path, "w", encoding="utf-8") as f:
        f.write(full_latex)

# ===================== Save LaTeX tables =====================

write_latex_table(
    df=accuracy_df,
    path=os.path.join(output_dir, "task_admission_accuracy.tex"),
    caption="Task admission accuracy across failure categories. Each value indicates the number of correctly solved cases out of 20.",
    label="tab:task_admission_accuracy"
)

write_latex_table(
    df=inference_df,
    path=os.path.join(output_dir, "task_admission_inference_time.tex"),
    caption="Average and maximum inference time for the task admission module.",
    label="tab:task_admission_inference_time"
)

# ===================== Print preview =====================

print("\nTask admission accuracy:")
print(accuracy_df)

print("\nTask admission inference time:")
print(inference_df)

print(f"\nSaved tables to: {output_dir}")