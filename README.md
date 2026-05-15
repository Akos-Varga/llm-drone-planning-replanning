# Hierarchical LLM-Based Planning and Replanning for Autonomous Multi-Drone Systems

This repository contains code for running **LLM-based multi-agent planning** for autonomous drones in two modes:

1. **Evaluation in a simulation environment**
2. **Execution on a real team of drones**

The README focuses on how to run the code, required setup, folder structure, and command-line arguments.

---

## Repository Structure

```
LLM-DRONE-PLANNING-REPLANNING/
├── pipeline/                  # LLM-based planning pipeline for task decomposition, allocation, and scheduling
├── task_admission/            # Local task admission logic for checking whether assigned tasks can be executed
├── worlds/                    # World definitions, drone configurations, objects, and skill mappings
│   ├── real_world.py           # Configuration for real-drone experiments
│   └── test_world.py           # Configuration for simulation experiments
├── report/                    # Thesis/report-related files
├── videos/                    # Recorded mission videos or simulation outputs
├── main.py                    # Main entry point for running a mission
├── planner_process.py         # Planner process that runs the planning/replanning pipeline
├── drone_process.py           # Drone worker process for real-drone execution
├── drone_process_sim.py       # Drone worker process for simulation
├── anafi_interface.py         # Interface for communicating with Parrot Anafi drones
├── simulated_drone_interface.py # Interface for simulated drone behavior
├── simulation.py              # Simulation environment and execution logic
├── common.py                  # Shared utilities, data structures, and helper functions
├── test_tasks.py              # Example mission commands or test cases
├── requirements.txt           # Python dependencies
├── README.md                  # Project documentation
└── .env                       # Environment variables and API keys
```

---

## Requirements

- **Python ≥ 3.9**
- Internet access for LLM API calls
- For simulation: no physical drone setup is required
- For real-drone execution:
  - **Ubuntu 22.04**
  - **ROS 2 Humble** installed and configured
  - **[`anafi_autonomy`](https://github.com/andriyukr/anafi_autonomy)** installed and configured for communication with Parrot Anafi drones

Install Python dependencies:

```bash
pip install -r requirements.txt
```

---

## Setup OpenAI API key

Create a `.env` file in the project root:

```bash
OPENAI_API_KEY=your_api_key_here
```

----

## Running the code

| Argument | Description |
|--------|------------|
| `--task` | Description of task to execute (default: `Record video of both wind turbines, take thermal image of House1 and measure wind at the Tower.`) |
| `--real` | Run on the real drone environment instead of simulation. (default: False) |
| `--rule_based_allocation` | Rule based calculation of allocation instead of LLM. (default: False) |
| `--rule_based_schedule` | Rule based schedule of allocation instead of LLM. (default: False) |

---

## Safety Disclaimer

This software controls physical robots. The authors assume **no responsibility** for damage, injury, or regulatory violations. Always test in simulation first and follow local aviation laws.