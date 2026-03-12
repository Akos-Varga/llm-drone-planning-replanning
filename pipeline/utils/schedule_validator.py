def validate_schedule(skills, objects, drones, subtasks_with_drones, travel_times, schedule):
    # Check if drones and objects are valid
    for drone, tasks in schedule.items():
        if drone not in drones:
            return f"SCHEDULER ERROR: {drone} is not in drone list.", None
        for task in tasks:
            if task["object"] not in objects:
                return f"SCHEDULER ERROR: Object: {task["object"]} is invalid in {task["name"]}.", None

    # Check if schedule has all subtasks ONCE   
    for subtask_allocator in subtasks_with_drones:
        found = 0
        for _, info in schedule.items():
            for subtask_schedule in info:
                if subtask_allocator["name"] == subtask_schedule["name"]:
                    found +=1
        if found == 0:
            return f"SCHEDULER ERROR: {subtask_allocator["name"]} is not found in schedule.", None
        if found > 1:
            return f"SCHEDULER ERROR: {subtask_allocator["name"]} is found multiple times in the schedule.", None

    # Check if drone has skill 
    for drone, tasks in schedule.items():
        for task in tasks:
            if task["skill"] not in drones[drone]["skills"]:
                return f"SCHEDULER ERROR: {task["skill"]} is not a valid skill for {drone}", None

    # Check if timing is good
    makespan = 0
    for drone, tasks in schedule.items():
        startObject = ""
        prevEndTime = 0
        for task in tasks:
            endObject = task["object"]
            if prevEndTime > task["departure_time"]:
                return f"SCHEDULER ERROR: Departure before previous task is finished for {task["name"]}", None
            if startObject == "" and travel_times["drone_to_object"][drone][endObject] != round(task["arrival_time"] - task["departure_time"], 1):
                return f"SCHEDULER ERROR: Invalid traveltime for {task["name"]}. Expected: {travel_times["drone_to_object"][drone][endObject]} Got: {round(task["arrival_time"] - task["departure_time"], 1)}", None
            if startObject != "" and travel_times["drone_object_to_object"][drone][startObject][endObject] != round(task["arrival_time"] - task["departure_time"], 1):
                return f"SCHEDULER ERROR: Invalid traveltime for {task["name"]}. Expected: {travel_times["drone_object_to_object"][drone][startObject][endObject]} Got: {round(task["arrival_time"] - task["departure_time"], 1)}", None
            if round(task["finish_time"] - task["arrival_time"], 1) != skills[task["skill"]]:
                return f"SCHEDULER ERROR: Invalid service time for {task["name"]}. Expected {skills[task["skill"]]} Got: {round(task["finish_time"] - task["arrival_time"], 1)}", None
            startObject = endObject
            prevEndTime = task["finish_time"]
        makespan = max(makespan, prevEndTime)

    return None, makespan



if __name__ == "__main__":
    from travel_time import compute_travel_times
    
    skills = {
        'CaptureRGBImage': 2.3,
        'CaptureThermalImage': 1.6,
        'RecordVideo': 2.2,
        'InspectStructure': 1.6,
        'MeasureWind': 0.7
    }

    objects = {
        "House1": (12, 87, 52),
        "RoofTop1": (45, 33, 42),
        "RoofTop2": (78, 62, 31),
        "SolarPanel1": (9, 14, 25),
        "SolarPanel2": (65, 90, 74)
    }   
    
    drones = {
        "Drone1": {"skills": ["CaptureRGBImage", "CaptureThermalImage"], "pos": (23, 77, 47), "speed": 14},
        "Drone2": {"skills": ["CaptureThermalImage"], "pos": (64, 12, 84), "speed": 17},
        "Drone3": {"skills": ["CaptureRGBImage"], "pos": (89, 45, 31), "speed": 11},
        "Drone4": {"skills": ["CaptureRGBImage", "CaptureThermalImage", "InspectStructure"], "pos": (35, 58, 42), "speed": 19},
        "Drone5": {"skills": ["RecordVideo"], "pos": (10, 91, 20), "speed": 13}
    }

    subtasks_with_drones = [
        {"name": "SubTask1", "skill": "CaptureRGBImage", "object": "RoofTop1", "service_time": 2.3, "drones": ["Drone1", "Drone3", "Drone4"]},
        {"name": "SubTask2", "skill": "CaptureThermalImage", "object": "RoofTop2", "service_time": 1.6, "drones": ["Drone1", "Drone2", "Drone4"]},
        {"name": "SubTask3", "skill": "CaptureRGBImage", "object": "House1", "service_time": 2.3, "drones": ["Drone1", "Drone3", "Drone4"]}
    ]   

    schedule = {
        "Drone4": [
            {"name": "SubTask1", "object": "RoofTop1", "skill": "CaptureRGBImage", "departure_time": 0.0, "arrival_time": 1.4, "finish_time": 3.7}
        ],
        "Drone2": [
            {"name": "SubTask2", "object": "RoofTop2", "skill": "CaptureThermalImage", "departure_time": 0.0, "arrival_time": 4.4, "finish_time": 6.0}
        ],
        "Drone1": [
            {"name": "SubTask3", "object": "House1", "skill": "CaptureRGBImage", "departure_time": 0.0, "arrival_time": 1.1, "finish_time": 3.4}
        ],
        "Drone3": []
    }

    travel_times = compute_travel_times(objects, drones, subtasks_with_drones)
    # print(travel_times)

    error, makespan = validate_schedule(skills, objects, drones, subtasks_with_drones, travel_times, schedule)

    if error:
        print(error)
    else:
        print(f"Makespan: {makespan}")
