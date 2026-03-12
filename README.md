# Large Language Model–Based Multi-Agent Planning for Autonomous Drones

This repository contains code for running **LLM-based multi-agent planning** for autonomous drones in two modes:

1. **Offline evaluation on a test dataset (simulated world)**
2. **Online execution with real autonomous drones (ROS 2)**

The README focuses on **how to run the code**, required setup, folder structure, and command-line arguments.

---

## Repository Structure

```
.
├── main_pipeline.py        # Run planning on test dataset using the simulation environment
├── main.py                 # Run planning + execution on drones (ROS 2)
├── test_tasks.py           # Test task dataset
├── publisher.py            # ROS 2 drone interface
├── pipeline/               # LLM prompts, planners, validators, utilities
├── worlds/
│   ├── test_world/         # Simulated world (skills, objects, drones)
│   └── real_world/         # Real drone configuration
├── results/                # Generated CSVs and visualizations
└── README.md
```

---

## Requirements

- **Python ≥ 3.9**
- Internet access for LLM API calls
- (For drones) **ROS 2** installed and configured

Install Python dependencies:

```bash
pip install -r requirements.txt
```

---

## LLM API Key Setup

The LLM API key is loaded inside `pipeline/utils/inference.py` using `python-dotenv`:

```python
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
client = openai.OpenAI(api_key=api_key)
```

### Steps

1. Create a `.env` file in the project root:

```bash
OPENAI_API_KEY=your_api_key_here
```

2. `python-dotenv` is already included in `requirements.txt`.

---

## Running on the Test Dataset (Simulated World)

This mode runs the full planning pipeline on a **predefined test dataset** without controlling real drones.

### Entry Point

```bash
python main_pipeline.py
```

### Command-Line Arguments

| Argument | Description |
|--------|------------|
| `--model` | LLM model name (default: `gpt-5-mini`) |
| `--task_id` | Run a specific task (e.g., `Task1`) |
| `--save` | Save results to `results/test_results.csv` |
| `--vrp` | Compute VRP baseline for comparison |
| `--visualize` | Generate a GIF animation of the schedule |

### Examples

Run all tasks:

```bash
python main_pipeline.py --model gpt-5-mini
```

Run a single task with visualization:

```bash
python main_pipeline.py --task_id Task1 --visualize
```

Save results to CSV:

```bash
python main_pipeline.py --save
```

### Outputs

- CSV results: `results/test_results.csv`
- Animations (optional): `results/animations/*.gif`

---

## Running on Real Autonomous Drones (ROS 2)

**Warning:** This mode sends commands to drones. Only run in a controlled and safe environment.

### Prerequisites

- **ROS 2 (e.g., Humble)** installed
- Drone middleware running (PX4 / MAVROS / custom bridge)
- Correct configuration in: `worlds/real_world.py`

Source ROS 2 before running:

```bash
source /opt/ros/humble/setup.bash
```

### Entry Point

```bash
python main.py --task "<TASK DESCRIPTION>"
```

### Command-Line Arguments

| Argument | Description |
|--------|------------|
| `--task` | Natural language task description (required) |
| `--model` | LLM model name (default: `gpt-5-mini`) |

### Example

```bash
python main.py \
  --model gpt-5-mini \
  --task "Inspect the rooftop and tower."
```

### Notes

- One ROS 2 node is launched per drone
- Each drone executes its assigned schedule in parallel
- Altitudes are automatically staggered for safety

---

## Safety Disclaimer

This software controls physical robots. The authors assume **no responsibility** for damage, injury, or regulatory violations. Always test in simulation first and follow local aviation laws.