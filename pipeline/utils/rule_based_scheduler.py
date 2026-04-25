from typing import Dict, List, Tuple
from ortools.sat.python import cp_model


def get_schedule(subtasks: List[Dict], travel_times: Dict) -> Tuple[Dict[str, List[Dict]], float, str]:
    """
    Solves multi-drone scheduling using precomputed travel times.

    Args:
        subtasks: List of subtasks with:
            {
                "name": str,
                "skill": str,
                "object": str,
                "service_time": float,
                "drones": [eligible drone names]
            }

        travel_times: Dictionary with structure:
            {
                "drone_to_object": {
                    drone: {object: travel_time, ...},
                    ...
                },
                "drone_object_to_object": {
                    drone: {
                        from_object: {to_object: travel_time, ...},
                        ...
                    },
                    ...
                }
            }

    Returns:
        schedule: Per-drone ordered task list
        makespan: Total mission completion time
        status: "optimal" or "feasible"
    """
    model = cp_model.CpModel()

    TIME_SCALE = 10  # one decimal resolution

    tasks = [t["name"] for t in subtasks]

    # Build drone list from subtasks
    drone_set = set()
    for t in subtasks:
        drone_set.update(t["drones"])
    drone_list = sorted(drone_set)

    # Convenience maps
    eligible = {t["name"]: list(t["drones"]) for t in subtasks}
    service = {t["name"]: int(round(float(t["service_time"]) * TIME_SCALE)) for t in subtasks}
    obj_of = {t["name"]: t["object"] for t in subtasks}
    skill_of = {t["name"]: t["skill"] for t in subtasks}

    # Precompute travel times (scaled ints)
    start_travel = {}   # (d, t) -> int
    travel = {}         # (d, i, j) -> int

    horizon_bound = 0

    # Initial travel: drone start position -> task object
    for d in drone_list:
        for t in tasks:
            if d in eligible[t]:
                obj = obj_of[t]
                val = travel_times["drone_to_object"][d][obj]
                scaled = int(round(float(val) * TIME_SCALE))
                start_travel[(d, t)] = scaled
                horizon_bound = max(horizon_bound, scaled)

    # Inter-task travel: task object i -> task object j for same drone
    for d in drone_list:
        for i in tasks:
            for j in tasks:
                if i == j:
                    continue
                if d in eligible[i] and d in eligible[j]:
                    obj_i = obj_of[i]
                    obj_j = obj_of[j]
                    val = travel_times["drone_object_to_object"][d][obj_i][obj_j]
                    scaled = int(round(float(val) * TIME_SCALE))
                    travel[(d, i, j)] = scaled
                    horizon_bound = max(horizon_bound, scaled)

    # Safe horizon
    HORIZON = max(100000, 5 * horizon_bound + sum(service.values()) + 100)

    # Decision variables
    x = {}
    for t in tasks:
        for d in eligible[t]:
            x[(d, t)] = model.NewBoolVar(f"x_{d}_{t}")

    start = {t: model.NewIntVar(0, HORIZON, f"start_{t}") for t in tasks}
    finish = {t: model.NewIntVar(0, HORIZON, f"finish_{t}") for t in tasks}

    # Each task assigned to exactly one eligible drone
    for t in tasks:
        model.Add(sum(x[(d, t)] for d in eligible[t]) == 1)

    # Finish = start + service
    for t in tasks:
        model.Add(finish[t] == start[t] + service[t])

    # First-task arrival constraints
    for d in drone_list:
        Td = [t for t in tasks if d in eligible[t]]
        for i in Td:
            model.Add(start[i] >= start_travel[(d, i)]).OnlyEnforceIf(x[(d, i)])

    # Pairwise precedence constraints with sequence-dependent travel
    bigM = HORIZON
    for d in drone_list:
        Td = [t for t in tasks if d in eligible[t]]
        for i in Td:
            for j in Td:
                if i == j:
                    continue

                both = model.NewBoolVar(f"both_{d}_{i}_{j}")
                model.Add(both <= x[(d, i)])
                model.Add(both <= x[(d, j)])
                model.Add(both >= x[(d, i)] + x[(d, j)] - 1)

                y = model.NewBoolVar(f"y_{d}_{i}_before_{j}")

                tij = travel[(d, i, j)]
                tji = travel[(d, j, i)]

                # If both tasks are assigned to drone d, enforce one order
                model.Add(start[j] >= finish[i] + tij - bigM * (1 - y)).OnlyEnforceIf(both)
                model.Add(start[i] >= finish[j] + tji - bigM * y).OnlyEnforceIf(both)

    # Makespan
    makespan = model.NewIntVar(0, HORIZON, "makespan")
    for t in tasks:
        model.Add(makespan >= finish[t])

    model.Minimize(1000000 * makespan + sum(start[t] for t in tasks))

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 3
    solver.parameters.num_search_workers = 8

    status = solver.Solve(model)
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        raise RuntimeError("No feasible schedule found.")

    # Recover assignments
    schedule: Dict[str, List[Dict]] = {d: [] for d in drone_list}
    chosen_drone = {}

    for t in tasks:
        for d in eligible[t]:
            if solver.Value(x[(d, t)]) == 1:
                chosen_drone[t] = d
                break

    for t in tasks:
        d = chosen_drone[t]
        arr = solver.Value(start[t]) / TIME_SCALE
        fin = solver.Value(finish[t]) / TIME_SCALE
        schedule[d].append({
            "name": t,
            "object": obj_of[t],
            "skill": skill_of[t],
            "departure_time": None,
            "arrival_time": round(arr, 1),
            "finish_time": round(fin, 1),
        })

    # Sort tasks per drone and compute departure times
    for d, lst in schedule.items():
        if not lst:
            continue
        lst.sort(key=lambda r: r["arrival_time"])
        lst[0]["departure_time"] = 0.0
        for k in range(1, len(lst)):
            prev = lst[k - 1]
            lst[k]["departure_time"] = prev["finish_time"]

    solved_makespan = max(
        (r["finish_time"] for lst in schedule.values() for r in lst),
        default=0.0
    )
    status_out = "optimal" if status == cp_model.OPTIMAL else "feasible"

    return schedule, solved_makespan, status_out


if __name__ == "__main__":
    from travel_time_calculator import compute_travel_times
    from pprint import pprint

    objects = {
        "Base": (48, 99, 87),
        "House3": (92, 44, 92),
        "Tower": (39, 2, 75)
    }  
    
    drones = {
        "Drone1": {"skills": ["MeasureWind", "RecordVideo"], "pos": (41, 85, 28), "speed": 12},
        "Drone2": {"skills": ["CaptureRGBImage", "MeasureWind"], "pos": (96, 37, 33), "speed": 18},
        "Drone3": {"skills": ["CaptureThermalImage", "InspectStructure", "CaptureRGBImage"], "pos": (73, 12, 36), "speed": 15}
    }

    subtasks_with_drones = [
        {"name": "SubTask1", "skill": "RecordVideo", "object": "Tower", "service_time": 1.3, "drones": ["Drone1"]},
        {"name": "SubTask2", "skill": "RecordVideo", "object": "House3", "service_time": 1.3, "drones": ["Drone1"]},
        {"name": "SubTask3", "skill": "RecordVideo", "object": "Base", "service_time": 1.3, "drones": ["Drone1"]},
        {"name": "SubTask4", "skill": "CaptureRGBImage", "object": "Tower", "service_time": 3, "drones": ["Drone2", "Drone3"]},
        {"name": "SubTask5", "skill": "CaptureRGBImage", "object": "House3", "service_time": 3, "drones": ["Drone2", "Drone3"]},
        {"name": "SubTask6", "skill": "CaptureRGBImage", "object": "Base", "service_time": 3, "drones": ["Drone2", "Drone3"]}
    ]

    travel_times = compute_travel_times(objects, drones, subtasks_with_drones)
    schedule, ms, status = get_schedule(subtasks_with_drones, travel_times)
    print("New schedule")
    pprint(schedule)
    print(f"Status: {status}")
    print(f"Makespan: {ms}")