messages = [{"role": "system", "content": """
You decompose a natural-language drone task into a list of subtasks. Only output Python code.

INPUT FORMAT:
task = <short description>

skills = {
    <SkillName>: <ServiceTime>,
    ...
}

objects = {
    <ObjectName>: (<x>, <y>, <z>),
    ...
}

OUTPUT FORMAT:
subtasks = [
    {"name": <SubTaskName>, "skill": <SkillName>, "object": <ObjectName>, service_time: <ServiceTime>},
    ...
]"""
},

# Example 1 ------------------------------------------------------------------------------------------
{"role": "user", "content": """
task = "Take RGB image of RoofTop1, thermal image of RoofTop2 and RGB image of House1."

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
}"""
},
{"role": "assistant", "content": """
subtasks = [
    {"name": "SubTask1", "skill": "CaptureRGBImage", "object": "RoofTop1", "service_time": 2.3},
    {"name": "SubTask2", "skill": "CaptureThermalImage", "object": "RoofTop2", "service_time": 1.6},
    {"name": "SubTask3", "skill": "CaptureRGBImage", "object": "House1", "service_time": 2.3}
]"""
},

# Example 2 --------------------------------------------------------------------------------------------
{"role": "user", "content": """
task = "Inspect the structure of the Tower and measure the wind speed at House2 and House3."

skills = {
    "RecordVideo": 2.4,
    "InspectStructure": 2,
    "MeasureWind": 2.2
}

objects = {
    "House2": (12, 87, 66),
    "RoofTop1": (45, 33, 85),
    "Tower": (78, 62, 81),
    "House3": (9, 14, 15),
    "SolarPanel2": (65, 90, 85)
}"""
},
{"role": "assistant", "content": """
subtasks = [
    {"name": "SubTask1", "skill": "InspectStructure", "object": "Tower", "service_time": 2},
    {"name": "SubTask2", "skill": "MeasureWind", "object": "House2", "service_time": 2.2},
    {"name": "SubTask3", "skill": "MeasureWind", "object": "House3", "service_time": 2.2}
]"""
},

# Example 3 --------------------------------------------------------------------------------------------
{"role":"user", "content": """
task = "Record video and take RGB image of Tower, House3 and Base."

skills = {
    "CaptureRGBImage": 3,
    "CaptureThermalImage": 2.5,
    "MeasureWind": 2,
    "RecordVideo": 1.3
}

objects = {
    "Base": (48, 99, 87),
    "House3": (92, 44, 92),
    "Tower": (39, 2, 75)
}"""
},
{"role":"assistant", "content": """
subtasks = [
    {"name": "SubTask1", "skill": "RecordVideo", "object": "Tower", "service_time": 1.3},
    {"name": "SubTask2", "skill": "RecordVideo", "object": "House3", "service_time": 1.3},
    {"name": "SubTask3", "skill": "RecordVideo", "object": "Base", "service_time": 1.3},
    {"name": "SubTask4", "skill": "CaptureRGBImage", "object": "Tower", "service_time": 3},
    {"name": "SubTask5", "skill": "CaptureRGBImage", "object": "House3", "service_time": 3},
    {"name": "SubTask6", "skill": "CaptureRGBImage", "object": "Base", "service_time": 3}
]"""
}
]
