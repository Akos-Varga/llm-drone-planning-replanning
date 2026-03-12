import math
from typing import Dict, List, Any

def schedules_equal(
    sched1: Dict[str, List[Dict[str, Any]]],
    sched2: Dict[str, List[Dict[str, Any]]],
    float_tol: float = 1e-3
) -> bool:
    """
    Compare two schedules for equality, ignoring drones with no assigned tasks.
    """
    # Filter out idle drones
    active1 = {d: tasks for d, tasks in sched1.items() if tasks}
    active2 = {d: tasks for d, tasks in sched2.items() if tasks}

    # Drone sets must match among active drones
    if set(active1.keys()) != set(active2.keys()):
        return False

    for drone in active1.keys():
        list1 = [t for t in active1[drone]]
        list2 = [t for t in active2[drone]]

        if len(list1) != len(list2):
            return False

        list1.sort(key=lambda t: t.get("name", ""))
        list2.sort(key=lambda t: t.get("name", ""))

        for t1, t2 in zip(list1, list2):
            if set(t1.keys()) != set(t2.keys()):
                return False
            for k in t1.keys():
                v1, v2 = t1[k], t2[k]
                if isinstance(v1, (float, int)) and isinstance(v2, (float, int)):
                    if not math.isclose(v1, v2, abs_tol=float_tol):
                        return False
                else:
                    if v1 != v2:
                        return False
    return True


if __name__ == "__main__":
    schedule_a = {
        "Drone1": [
            {"name": "SubTask1", "object": "RoofTop1", "skill": "CaptureRGBImage",
             "departure_time": 0.0, "arrival_time": 1.4, "finish_time": 3.7}
        ],
    }

    schedule_b = {
        "Drone1": [
            {"name": "SubTask1", "object": "RoofTop1", "skill": "CaptureRGBImage",
             "departure_time": 0.0, "arrival_time": 1.4, "finish_time": 3.7001}
        ],
        "Drone2": [],  # ignored since idle
    }

    print("Schedules identical:",
          schedules_equal(schedule_a, schedule_b))
