import pandas as pd
import os
import re

# ===================== Load data =====================

csv_path = os.path.join("results", "test_results.csv")
df = pd.read_csv(csv_path)

output_dir = os.path.join("results", "tables")
os.makedirs(output_dir, exist_ok=True)

desired_order = ["gpt-5", "gpt-5-mini", "gpt-4o", "gpt-4.1"]

pretty_names = {
    "gpt-5": "GPT-5",
    "gpt-5-mini": "GPT-5-mini",
    "gpt-4o": "GPT-4o",
    "gpt-4.1": "GPT-4.1",
}

# ===================== Helpers =====================

def task_number(task_id):
    return int(re.search(r"\d+", str(task_id)).group())

def num_subtasks(task_id):
    # Assumes Task1-Task3 = 1 subtask, Task4-Task6 = 2 subtasks, etc.
    return (task_number(task_id) - 1) // 3 + 1

def make_mean_count_table(dataframe, value_col):
    mean_table = dataframe.pivot_table(
        index="num_subtasks",
        columns="model",
        values=value_col,
        aggfunc="mean"
    ).reindex(columns=desired_order)

    count_table = dataframe.pivot_table(
        index="num_subtasks",
        columns="model",
        values=value_col,
        aggfunc="count"
    ).reindex(columns=desired_order)

    formatted = mean_table.copy().astype(object)

    for subtasks in mean_table.index:
        total = 3  # each subtask group has 3 tasks

        for model in desired_order:
            value = mean_table.loc[subtasks, model]
            count = count_table.loc[subtasks, model]

            if pd.isna(value):
                formatted.loc[subtasks, model] = f"-- (0/{total})"
            else:
                formatted.loc[subtasks, model] = f"{value:.2f} ({int(count)}/{total})"

    formatted.index.name = "Subtasks"
    formatted = formatted.rename(columns=pretty_names)

    return formatted

def write_centered_latex_table(table, path, caption, label):
    latex = table.to_latex(
        index=True,
        escape=False,
        na_rep="--"
    )

    latex = latex.replace(
        "\\begin{tabular}",
        "\\centering\n\\begin{tabular}"
    )

    full_latex = f"""\\begin{{table}}[t]
\\centering
\\caption{{{caption}}}
\\label{{{label}}}
{latex}
\\end{{table}}
"""

    with open(path, "w", encoding="utf-8") as f:
        f.write(full_latex)

# ===================== Derived columns =====================

df["num_subtasks"] = df["task_id"].apply(num_subtasks)

df["vrp_gap_percent"] = (
    (df["LLM_makespan"] - df["VRP_makespan"]) / df["VRP_makespan"]
) * 100

df = df[df["model"].isin(desired_order)].copy()

# ===================== Build tables =====================

avg_inference_table = make_mean_count_table(df, "LLM_inference_time")
avg_vrp_gap_table = make_mean_count_table(df, "vrp_gap_percent")

# ===================== Save LaTeX only =====================

write_centered_latex_table(
    table=avg_inference_table,
    path=os.path.join(output_dir, "avg_inference_time_by_subtasks.tex"),
    caption="Average inference time by number of subtasks. Values in parentheses indicate solved cases over three tasks.",
    label="tab:avg_inference_time_by_subtasks"
)

write_centered_latex_table(
    table=avg_vrp_gap_table,
    path=os.path.join(output_dir, "avg_vrp_gap_by_subtasks.tex"),
    caption="Average makespan difference from the VRP baseline by number of subtasks. Values in parentheses indicate solved cases over three tasks.",
    label="tab:avg_vrp_gap_by_subtasks"
)

# ===================== Print preview =====================

print("\nAverage inference time by number of subtasks:")
print(avg_inference_table)

print("\nAverage makespan difference from VRP by number of subtasks (%):")
print(avg_vrp_gap_table)