messages = [
{"role": "system", "content": """
You are a task scheduler for a multi-drone system. Only output Python code.

INPUT FORMAT:
subtasks_with_drones = [
    {"name": <SubTaskName>, "skill": <SkillName>, "object": <ObjectName>, "service_time": <ServiceTime>, "drones": [<DroneName>, ...]},
    ...
]
 
travel_times = {'drone_to_object':  {<DroneName>: {<ArrivalObjectName>: <TravelTime>, ...}, ...}, 'drone_object_to_object': {<DroneName>:{<DepartureObjectName>: {<ArrivalObjectName>: <TravelTime>, ...}, ...}, ...}}

CONSTRAINTS:
1) Each subtask appears exactly once in schedule across all drones.
3) Time semantics:
   a) departure_time is the departure time from the drone’s current location; departure_time >= 0.
   b) arrival_time is the arrival time at the task’s object.
   c) First task: arrival_time - departure_time == travel_times['drone_to_object'][Drone][Object].
   d) For consecutive tasks from object A to B on the same drone: arrival_time - departure_time == travel_times['drone_object_to_object'][Drone][A][B].
   e) finish_time is the time when the service is completed at the object: finish_time = arrival_time + service_time
4) For any single drone, services cannot overlap in time: current_finish_time ≤ next_departure_time
5) Objective: minimize makespan (max over all endTime).

OUTPUT FORMAT:
schedule = {
    <DroneName>: [
        {"name": <SubTaskName>, "object": <ObjectName>, "skill": <SkillName>, "departure_time": <DepartureTime>, "arrival_time": <ArrivalTime>, "finish_time": <FinishTime>},
        ...
    ],
    ...
}"""
},

# Example 1 ------------------------------------------------------------------------------------------
{"role": "user", "content": """
subtasks_with_drones = [
    {"name": "SubTask1", "skill": "CaptureRGBImage", "object": "RoofTop1", "service_time": 2.3, "drones": ["Drone1", "Drone3", "Drone4"]},
    {"name": "SubTask2", "skill": "CaptureThermalImage", "object": "RoofTop2", "service_time": 1.6, "drones": ["Drone1", "Drone2", "Drone4"]},
    {"name": "SubTask3", "skill": "CaptureRGBImage", "object": "House1", "service_time": 2.3, "drones": ["Drone1", "Drone3", "Drone4"]}
]

travel_times = {'drone_to_object': {'Drone1': {'RoofTop1': 3.5, 'RoofTop2': 4.2, 'House1': 1.1}, 'Drone3': {'RoofTop1': 4.3, 'House1': 8.2}, 'Drone4': {'RoofTop1': 1.4, 'RoofTop2': 2.3, 'House1': 2.0}, 'Drone2': {'RoofTop2': 4.4}}, 'drone_object_to_object': {'Drone1': {'RoofTop1': {'RoofTop1': 0.0, 'RoofTop2': 3.2, 'House1': 4.6}, 'RoofTop2': {'RoofTop1': 3.2, 'RoofTop2': 0.0, 'House1': 5.3}, 'House1': {'RoofTop1': 4.6, 'RoofTop2': 5.3, 'House1': 0.0}}, 'Drone3': {'RoofTop1': {'RoofTop1': 0.0, 'House1': 5.8}, 'House1': {'RoofTop1': 5.8, 'House1': 0.0}}, 'Drone4': {'RoofTop1': {'RoofTop1': 0.0, 'RoofTop2': 2.4, 'House1': 3.4}, 'RoofTop2': {'RoofTop1': 2.4, 'RoofTop2': 0.0, 'House1': 3.9}, 'House1': {'RoofTop1': 3.4, 'RoofTop2': 3.9, 'House1': 0.0}}, 'Drone2': {'RoofTop2': {'RoofTop2': 0.0}}}}"""
},
{"role": "assistant", "content": """
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
}"""
},

# Example 2 --------------------------------------------------------------------------------------------
{"role": "user", "content": """
subtasks_with_drones = [
    {"name": "SubTask1", "skill": "InspectStructure", "object": "Tower", "service_time": 2, "drones": ["Drone2", "Drone4", "Drone5"]},
    {"name": "SubTask2", "skill": "MeasureWind", "object": "House2", "service_time": 2.2, "drones": ["Drone1", "Drone3"]},
    {"name": "SubTask3", "skill": "MeasureWind", "object": "House3", "service_time": 2.2, "drones": ["Drone1", "Drone3"]}
]

travel_times = {'drone_to_object': {'Drone2': {'Tower': 5.8}, 'Drone4': {'Tower': 4.1}, 'Drone5': {'Tower': 4.1}, 'Drone1': {'House2': 4.0, 'House3': 4.1}, 'Drone3': {'House2': 3.8, 'House3': 0.9}}, 'drone_object_to_object': {'Drone2': {'Tower': {'Tower': 0.0}}, 'Drone4': {'Tower': {'Tower': 0.0}}, 'Drone5': {'Tower': {'Tower': 0.0}}, 'Drone1': {'House2': {'House2': 0.0, 'House3': 6.4}, 'House3': {'House2': 6.4, 'House3': 0.0}}, 'Drone3': {'House2': {'House2': 0.0, 'House3': 4.7}, 'House3': {'House2': 4.7, 'House3': 0.0}}}}"""
},
{"role": "assistant","content": """
schedule = {
    "Drone1": [
        {"name": "SubTask2", "object": "House2", "skill": "MeasureWind", "departure_time": 0.0, "arrival_time": 4.0, "finish_time": 6.2}
    ],
    "Drone2": [],
    "Drone3": [
        {"name": "SubTask3", "object": "House3", "skill": "MeasureWind", "departure_time": 0.0, "arrival_time": 0.9, "finish_time": 3.1}
    ],
    "Drone4": [
        {"name": "SubTask1", "object": "Tower", "skill": "InspectStructure", "departure_time": 0.0, "arrival_time": 4.1, "finish_time": 6.1}
    ],
    "Drone5": []
}"""
},

# Example 3 --------------------------------------------------------------------------------------------
{"role": "user", "content": """
subtasks_with_drones = [
    {"name": "SubTask1", "skill": "RecordVideo", "object": "Tower", "service_time": 0.5, "drones": ["Drone1"]},
    {"name": "SubTask2", "skill": "RecordVideo", "object": "House3", "service_time": 0.5, "drones": ["Drone1"]},
    {"name": "SubTask3", "skill": "RecordVideo", "object": "Base", "service_time": 0.5, "drones": ["Drone1"]},
    {"name": "SubTask4", "skill": "CaptureRGBImage", "object": "Tower", "service_time": 3, "drones": ["Drone2", "Drone3"]},
    {"name": "SubTask5", "skill": "CaptureRGBImage", "object": "House3", "service_time": 3, "drones": ["Drone2", "Drone3"]},
    {"name": "SubTask6", "skill": "CaptureRGBImage", "object": "Base", "service_time": 3, "drones": ["Drone2", "Drone3"]}
]
 
travel_times = {'drone_to_object': {'Drone1': {'Tower': 8.0, 'House3': 7.6, 'Base': 5.1}, 'Drone2': {'Tower': 4.4, 'House3': 3.3, 'Base': 5.3}, 'Drone3': {'Tower': 3.5, 'House3': 4.5, 'Base': 6.9}}, 'drone_object_to_object': {'Drone1': {'Tower': {'Tower': 0.0, 'House3': 5.8, 'Base': 8.2}, 'House3': {'Tower': 5.8, 'House3': 0.0, 'Base': 5.9}, 'Base': {'Tower': 8.2, 'House3': 5.9, 'Base': 0.0}}, 'Drone2': {'Tower': {'Tower': 0.0, 'House3': 3.9, 'Base': 5.5}, 'House3': {'Tower': 3.9, 'House3': 0.0, 'Base': 3.9}, 'Base': {'Tower': 5.5, 'House3': 3.9, 'Base': 0.0}}, 'Drone3': {'Tower': {'Tower': 0.0, 'House3': 4.6, 'Base': 6.5}, 'House3': {'Tower': 4.6, 'House3': 0.0, 'Base': 4.7}, 'Base': {'Tower': 6.5, 'House3': 4.7, 'Base': 0.0}}}}"""
},
{"role": "assistant", "content": """
schedule = {
    "Drone1": [
        {"name": "SubTask3", "object": "Base", "skill": "RecordVideo", "departure_time": 0.0, "arrival_time": 5.1, "finish_time": 5.6},
        {"name": "SubTask2", "object": "House3", "skill": "RecordVideo", "departure_time": 5.6, "arrival_time": 11.5, "finish_time": 12.0},
        {"name": "SubTask1", "object": "Tower", "skill": "RecordVideo", "departure_time": 12.0, "arrival_time": 17.8, "finish_time": 18.3}
    ],
    "Drone2": [
        {"name": "SubTask5", "object": "House3", "skill": "CaptureRGBImage", "departure_time": 0.0, "arrival_time": 3.3, "finish_time": 6.3},
        {"name": "SubTask4", "object": "Tower", "skill": "CaptureRGBImage", "departure_time": 6.3, "arrival_time": 10.2, "finish_time": 13.2}
    ],
    "Drone3": [
        {"name": "SubTask6", "object": "Base", "skill": "CaptureRGBImage", "departure_time": 0.0, "arrival_time": 6.9, "finish_time": 9.9}
    ]
}"""
},

# Example 4 --------------------------------------------------------------------------------------------
#{"role": "user", "content": """
#subtasks_with_drones = [
#    {"name": "SubTask1", "skill": "CaptureThermalImage", "object": "House2", "drones": ["Drone1", "Drone3", "Drone5"]},
#    {"name": "SubTask2", "skill": "CaptureThermalImage", "object": "House3", "drones": ["Drone1", "Drone3", "Drone5"]},
#    {"name": "SubTask3", "skill": "RecordVideo", "object": "SolarPanel1", "drones": ["Drone2", "Drone4"]},
#    {"name": "SubTask4", "skill": "RecordVideo", "object": "SolarPanel2", "drones": ["Drone2", "Drone4"]}
#]
# 
#travel_times = {'drone_to_object': {'Drone1': {'House2': 4.3, 'House3': 3.2}, 'Drone3': {'House2': 5.5, 'House3': 4.0}, 'Drone5': {'House2': 2.3, 'House3': 1.5}, 'Drone2': {'SolarPanel1': 3.1, 'SolarPanel2': 3.3}, 'Drone4': {'SolarPanel1': 4.8, 'SolarPanel2': 5.0}}, 'drone_object_to_object': {'Drone1': {'House2': {'House2': 0.0, 'House3': 1.3}, 'House3': {'House2': 1.3, 'House3': 0.0}}, 'Drone3': {'House2': {'House2': 0.0, 'House3': 1.5}, 'House3': {'House2': 1.5, 'House3': 0.0}}, 'Drone5': {'House2': {'House2': 0.0, 'House3': 2.0}, 'House3': {'House2': 2.0, 'House3': 0.0}}, 'Drone2': {'SolarPanel1': {'SolarPanel1': 0.0, 'SolarPanel2': 0.2}, 'SolarPanel2': {'SolarPanel1': 0.2, 'SolarPanel2': 0.0}}, 'Drone4': {'SolarPanel1': {'SolarPanel1': 0.0, 'SolarPanel2': 0.2}, 'SolarPanel2': {'SolarPanel1': 0.2, 'SolarPanel2': 0.0}}}}"""
#},
#{"role": "assistant", "content": """
## SubTask1 (House2): Drone1(start → House2)=4.3, Drone3(start → House2)=5.5, Drone5(start → House2)=2.3 → best: Drone5 (2.3)
## SubTask2 (House3): Drone1(start → House3)=3.2, Drone3(start → House3)=4.0, Drone5(House2 → House3)=2.3+2.0=4.3 → best: Drone1 (3.2)
## SubTask3 (SolarPanel1): Drone2(start → SolarPanel1)=3.1, Drone4(start → SolarPanel1)=4.8 → best: Drone2 (3.1)
## SubTask4 (SolarPanel2): Drone2(SolarPanel1 → SolarPanel2)=3.1+0.2=3.3, Drone4(start → SolarPanel2)=5.0 → best: Drone2 (3.3)
#
#schedule = {
#    "Drone1" : [
#        {"name": "SubTask2", "object": "House3", "skill": "CaptureThermalImage", "startTime": 0.0, "endTime": 3.2}
#    ],
#    "Drone2": [
#        {"name": "SubTask3", "object": "SolarPanel1", "skill": "RecordVideo", "startTime": 0.0, "endTime": 3.1},
#        {"name": "SubTask4", "object": "SolarPanel2", "skill": "RecordVideo", "startTime": 3.1, "endTime": 3.3}
#    ],
#    "Drone5": [
#        {"name": "SubTask1", "object": "House2", "skill": "CaptureThermalImage", "startTime": 0.0, "endTime": 2.3}
#    ]
#}
#"""
#},
#
## Example 5 --------------------------------------------------------------------------------------------
#{"role": "user", "content": """
#subtasks_with_drones = [
#    {"name": "SubTask1", "skill": "CaptureThermalImage", "object": "Tower", "drones": ["Drone1", "Drone3", "Drone5"]},
#    {"name": "SubTask2", "skill": "CaptureThermalImage", "object": "RoofTop1", "drones": ["Drone1", "Drone3", "Drone5"]}
#]
# 
#travel_times = {'drone_to_object': {'Drone1': {'Tower': 5.5, 'RoofTop1': 1.0}, 'Drone3': {'Tower': 4.1, 'RoofTop1': 3.3}, 'Drone5': {'Tower': 7.5, 'RoofTop1': 3.1}}, 'drone_object_to_object': {'Drone1': {'Tower': {'Tower': 0.0, 'RoofTop1': 5.6}, 'RoofTop1': {'Tower': 5.6, 'RoofTop1': 0.0}}, 'Drone3': {'Tower': {'Tower': 0.0, 'RoofTop1': 6.5}, 'RoofTop1': {'Tower': 6.5, 'RoofTop1': 0.0}}, 'Drone5': {'Tower': {'Tower': 0.0, 'RoofTop1': 8.4}, 'RoofTop1': {'Tower': 8.4, 'RoofTop1': 0.0}}}}"""
#},
#{"role": "assistant", "content": """
## SubTask1 (Tower): Drone1(start → Tower)=5.5, Drone3(start → Tower)=4.1, Drone5(start → Tower)=7.5 → best: Drone3 (4.1)
## SubTask2 (RoofTop1): Drone1(start → RoofTop1)=1.0, Drone3(Tower → RoofTop1)=4.1+6.5=10.6, Drone5(start → RoofTop1)=3.1 → best: Drone1 (1.0)
#schedule = {
#    "Drone1": [
#        {"name": "SubTask2", "object": "RoofTop1", "skill": "CaptureThermalImage", "startTime": 0.0, "endTime": 1.0}
#    ],
#    "Drone3": [
#        {"name": "SubTask1", "object": "Tower", "skill": "CaptureThermalImage", "startTime": 0.0, "endTime": 4.1}
#    ]
#}
#"""
#}
]
