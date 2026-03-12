def validate_decomposer(decomposed_task, solution, skills):
    # Check number of entries are the same
    if len(solution) != len(decomposed_task):
        return "DECOMPOSER ERROR: Subtask number mismatch"
    
    # Check if task names are the same
    expected_names = {s["name"] for s in solution}
    actual_names = {s["name"] for s in decomposed_task}
    if expected_names != actual_names:
        return "DECOMPOSER ERROR: Subtask name mismatch"
    
    for subtask in decomposed_task:
        if subtask["service_time"] != skills[subtask["skill"]]:
            return f"DECOMPOSER ERROR: Wrong service time for {subtask["name"]}."
    
    # Check if skill and objects are the same
    expected_set = {(s["skill"], s["object"]) for s in solution}
    actual_set = {(s["skill"], s["object"]) for s in decomposed_task}
    if expected_set != actual_set:
        return "DECOMPOSER ERROR: Skill-object mismatch"
    
    return None

if __name__ == "__main__":
    solution = [
    {"name": "SubTask1", "skill": "CaptureRGBImage", "object": "SolarPanel1"},
    {"name": "SubTask2", "skill": "CaptureThermalImage", "object": "SolarPanel1"},
    {"name": "SubTask3", "skill": "CaptureRGBImage", "object": "SolarPanel2"},
    {"name": "SubTask4", "skill": "CaptureThermalImage", "object": "SolarPanel2"},
    {"name": "SubTask5", "skill": "CaptureThermalImage", "object": "SolarPanel2"}
    ]
    subtasks = [
    {"name": "SubTask1", "skill": "CaptureRGBImage", "object": "SolarPanel1", "service_time": 2.4},
    {"name": "SubTask2", "skill": "CaptureThermalImage", "object": "SolarPanel1", "service_time": 1},
    {"name": "SubTask3", "skill": "CaptureRGBImage", "object": "SolarPanel2", "service_time": 2.4},
    {"name": "SubTask4", "skill": "CaptureThermalImage", "object": "SolarPanel2", "service_time": 1},
    {"name": "SubTask5", "skill": "CaptureThermalImage", "object": "SolarPanel2", "service_time": 1}
    ]
    skills = {
        "CaptureRGBImage": 2.4,
        "CaptureThermalImage": 1
    }

    err = validate_decomposer(subtasks, solution, skills)

    if err:
        print(err)
    else:
        print("OK")
