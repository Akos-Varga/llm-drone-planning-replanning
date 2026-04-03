from pprint import pprint

def compute_allocation(drones, decomposed_task):
    """
    Rule-based allocation:
    assign each subtask all drones that have the required skill.

    Args:
        drones (dict): mapping drone name -> drone info
        decomposed_task (list): list of subtasks, each with at least
            "name", "skill", "object", "service_time"

    Returns:
        subtasks_with_drones (list): subtasks with "drones"
    """

    subtasks_with_drones = []
    for subtask in decomposed_task:
        required_skill = subtask["skill"]
        eligible_drones = [
            drone_name for drone_name, drone_info in drones.items()
            if required_skill in drone_info.get("skills", [])
        ]

        allocated_subtask = subtask.copy()
        allocated_subtask["drones"] = eligible_drones
        subtasks_with_drones.append(allocated_subtask)
    
    return subtasks_with_drones

if __name__ == "__main__":
    drones = {
        "Drone1": {"skills": ["CaptureRGBImage", "CaptureThermalImage"], "pos": (23, 77, 47), "speed": 14},
        "Drone2": {"skills": ["CaptureThermalImage"], "pos": (64, 12, 84), "speed": 17},
        "Drone3": {"skills": ["CaptureRGBImage"], "pos": (89, 45, 31), "speed": 11},
        "Drone4": {"skills": ["CaptureRGBImage", "CaptureThermalImage", "InspectStructure"], "pos": (35, 58, 42), "speed": 19},
        "Drone5": {"skills": ["RecordVideo"], "pos": (10, 91, 20), "speed": 13}
    }

    decomposed_task = [
        {"name": "SubTask1", "skill": "CaptureRGBImage", "object": "RoofTop1", "service_time": 2.3},
        {"name": "SubTask2", "skill": "CaptureThermalImage", "object": "RoofTop2", "service_time": 1.6},
        {"name": "SubTask3", "skill": "CaptureRGBImage", "object": "House1", "service_time": 2.3}
    ]

    subtasks_with_drones = compute_allocation(drones, decomposed_task)
    print("Allocation:")
    pprint(subtasks_with_drones, sort_dicts=False)