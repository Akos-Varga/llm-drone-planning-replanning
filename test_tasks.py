# Skills: "CaptureRGBImage", "CaptureThermalImage", "RecordVideo", "InspectStructure", "MeasureWind"
# Objects: House1-3, SolarPanel1-2, Tower, Base, Rooftop1-2

task_list = [
    # === 1-subtask tasks ===
    {"id": "Task1", "task": "Inspect the Tower for structural integrity.", "solution": [
        {"name": "SubTask1", "skill": "InspectStructure", "object": "Tower"}
    ]},
    {"id": "Task2", "task": "Take an RGB image of the Base.", "solution": [
        {"name": "SubTask1", "skill": "CaptureRGBImage", "object": "Base"}
    ]},
    {"id": "Task3", "task": "Acquire a thermal image of House3.", "solution": [
        {"name": "SubTask1", "skill": "CaptureThermalImage", "object": "House3"}
    ]},

    # === 2-subtask tasks ===
    {"id": "Task4", "task": "Inspect RoofTop1 and measure wind conditions at RoofTop2.", "solution": [
        {"name": "SubTask1", "skill": "InspectStructure", "object": "RoofTop1"},
        {"name": "SubTask2", "skill": "MeasureWind", "object": "RoofTop2"}
    ]},
    {"id": "Task5", "task": "Record a video of House2 and collect a thermal image of House1.", "solution": [
        {"name": "SubTask1", "skill": "RecordVideo", "object": "House2"},
        {"name": "SubTask2", "skill": "CaptureThermalImage", "object": "House1"}
    ]},
    {"id": "Task6", "task": "Measure wind at SolarPanel2 and at the Base.", "solution": [
        {"name": "SubTask1", "skill": "MeasureWind", "object": "SolarPanel2"},
        {"name": "SubTask2", "skill": "MeasureWind", "object": "Base"}
    ]},

    # === 3-subtask tasks ===
    {"id": "Task7", "task": "Capture RGB images of all solar panels and inspect the Tower.", "solution": [
        {"name": "SubTask1", "skill": "CaptureRGBImage", "object": "SolarPanel1"},
        {"name": "SubTask2", "skill": "CaptureRGBImage", "object": "SolarPanel2"},
        {"name": "SubTask3", "skill": "InspectStructure", "object": "Tower"}
    ]},
    {"id": "Task8", "task": "Take thermal images of House1 and House3, followed by an inspection of RoofTop2.", "solution": [
        {"name": "SubTask1", "skill": "CaptureThermalImage", "object": "House1"},
        {"name": "SubTask2", "skill": "CaptureThermalImage", "object": "House3"},
        {"name": "SubTask3", "skill": "InspectStructure", "object": "RoofTop2"}
    ]},
    {"id": "Task9", "task": "Record a video of the Base and obtain both RGB and thermal images of RoofTop1.", "solution": [
        {"name": "SubTask1", "skill": "RecordVideo", "object": "Base"},
        {"name": "SubTask2", "skill": "CaptureRGBImage", "object": "RoofTop1"},
        {"name": "SubTask3", "skill": "CaptureThermalImage", "object": "RoofTop1"}
    ]},

    # === 4-subtask tasks ===
    {"id": "Task10", "task": "Collect RGB and thermal imagery for all solar panels.", "solution": [
        {"name": "SubTask1", "skill": "CaptureRGBImage", "object": "SolarPanel1"},
        {"name": "SubTask2", "skill": "CaptureThermalImage", "object": "SolarPanel1"},
        {"name": "SubTask3", "skill": "CaptureRGBImage", "object": "SolarPanel2"},
        {"name": "SubTask4", "skill": "CaptureThermalImage", "object": "SolarPanel2"}
    ]},
    {"id": "Task11", "task": "Inspect House1 and House2, and measure wind levels at the Tower and Base.", "solution": [
        {"name": "SubTask1", "skill": "InspectStructure", "object": "House1"},
        {"name": "SubTask2", "skill": "InspectStructure", "object": "House2"},
        {"name": "SubTask3", "skill": "MeasureWind", "object": "Tower"},
        {"name": "SubTask4", "skill": "MeasureWind", "object": "Base"}
    ]},
    {"id": "Task12", "task": "Record videos of both rooftops and take RGB images of each.", "solution": [
        {"name": "SubTask1", "skill": "RecordVideo", "object": "RoofTop1"},
        {"name": "SubTask2", "skill": "RecordVideo", "object": "RoofTop2"},
        {"name": "SubTask3", "skill": "CaptureRGBImage", "object": "RoofTop1"},
        {"name": "SubTask4", "skill": "CaptureRGBImage", "object": "RoofTop2"}
    ]},

    # === 5-subtask tasks ===
    {"id": "Task13", "task": "Take RGB images of House1 and House2, collect a thermal image of House2, inspect RoofTop1, and measure wind at the Tower.", "solution": [
        {"name": "SubTask1", "skill": "CaptureRGBImage", "object": "House1"},
        {"name": "SubTask2", "skill": "CaptureRGBImage", "object": "House2"},
        {"name": "SubTask3", "skill": "CaptureThermalImage", "object": "House2"},
        {"name": "SubTask4", "skill": "InspectStructure", "object": "RoofTop1"},
        {"name": "SubTask5", "skill": "MeasureWind", "object": "Tower"}
    ]},
    {"id": "Task14", "task": "Record videos of all solar panels, capture an RGB and thermal image of House1, and inspect the Tower.", "solution": [
        {"name": "SubTask1", "skill": "RecordVideo", "object": "SolarPanel1"},
        {"name": "SubTask2", "skill": "RecordVideo", "object": "SolarPanel2"},
        {"name": "SubTask3", "skill": "CaptureRGBImage", "object": "House1"},
        {"name": "SubTask4", "skill": "CaptureThermalImage", "object": "House1"},
        {"name": "SubTask5", "skill": "InspectStructure", "object": "Tower"}
    ]},
    {"id": "Task15", "task": "Take thermal images of both rooftops and the Tower, measure wind at the Base, and capture an RGB image of House3.", "solution": [
        {"name": "SubTask1", "skill": "CaptureThermalImage", "object": "RoofTop1"},
        {"name": "SubTask2", "skill": "CaptureThermalImage", "object": "RoofTop2"},
        {"name": "SubTask3", "skill": "CaptureThermalImage", "object": "Tower"},
        {"name": "SubTask4", "skill": "MeasureWind", "object": "Base"},
        {"name": "SubTask5", "skill": "CaptureRGBImage", "object": "House3"}
    ]},

    # === 6-subtask tasks ===
    {"id": "Task16", "task": "For all houses, collect both RGB and thermal imagery.", "solution": [
        {"name": "SubTask1", "skill": "CaptureRGBImage", "object": "House1"},
        {"name": "SubTask2", "skill": "CaptureThermalImage", "object": "House1"},
        {"name": "SubTask3", "skill": "CaptureRGBImage", "object": "House2"},
        {"name": "SubTask4", "skill": "CaptureThermalImage", "object": "House2"},
        {"name": "SubTask5", "skill": "CaptureRGBImage", "object": "House3"},
        {"name": "SubTask6", "skill": "CaptureThermalImage", "object": "House3"}
    ]},
    {"id": "Task17", "task": "Inspect both rooftops and all solar panels, and measure wind at the Tower and Base.", "solution": [
        {"name": "SubTask1", "skill": "InspectStructure", "object": "RoofTop1"},
        {"name": "SubTask2", "skill": "InspectStructure", "object": "RoofTop2"},
        {"name": "SubTask3", "skill": "InspectStructure", "object": "SolarPanel1"},
        {"name": "SubTask4", "skill": "InspectStructure", "object": "SolarPanel2"},
        {"name": "SubTask5", "skill": "MeasureWind", "object": "Tower"},
        {"name": "SubTask6", "skill": "MeasureWind", "object": "Base"}
    ]},
    {"id": "Task18", "task": "Record videos of all houses and collect thermal images of both rooftops and the Tower.", "solution": [
        {"name": "SubTask1", "skill": "RecordVideo", "object": "House1"},
        {"name": "SubTask2", "skill": "RecordVideo", "object": "House2"},
        {"name": "SubTask3", "skill": "RecordVideo", "object": "House3"},
        {"name": "SubTask4", "skill": "CaptureThermalImage", "object": "RoofTop1"},
        {"name": "SubTask5", "skill": "CaptureThermalImage", "object": "RoofTop2"},
        {"name": "SubTask6", "skill": "CaptureThermalImage", "object": "Tower"}
    ]},

        # === 7-subtask tasks ===
    {"id": "Task19", "task": "Survey all houses for both RGB and thermal data, and conduct a structural inspection on Rooftop1.", "solution": [
        {"name": "SubTask1", "skill": "CaptureRGBImage", "object": "House1"},
        {"name": "SubTask2", "skill": "CaptureThermalImage", "object": "House1"},
        {"name": "SubTask3", "skill": "CaptureRGBImage", "object": "House2"},
        {"name": "SubTask4", "skill": "CaptureThermalImage", "object": "House2"},
        {"name": "SubTask5", "skill": "CaptureRGBImage", "object": "House3"},
        {"name": "SubTask6", "skill": "CaptureThermalImage", "object": "House3"},
        {"name": "SubTask7", "skill": "InspectStructure", "object": "RoofTop1"}
    ]},

    {"id": "Task20", "task": "Collect RGB and thermal data from both rooftops, assess the Tower’s structure, and log wind speeds at all solar panels.", "solution": [
        {"name": "SubTask1", "skill": "CaptureRGBImage", "object": "RoofTop1"},
        {"name": "SubTask2", "skill": "CaptureThermalImage", "object": "RoofTop1"},
        {"name": "SubTask3", "skill": "CaptureRGBImage", "object": "RoofTop2"},
        {"name": "SubTask4", "skill": "CaptureThermalImage", "object": "RoofTop2"},
        {"name": "SubTask5", "skill": "InspectStructure", "object": "Tower"},
        {"name": "SubTask6", "skill": "MeasureWind", "object": "SolarPanel1"},
        {"name": "SubTask7", "skill": "MeasureWind", "object": "SolarPanel2"}
    ]},

    {"id": "Task21", "task": "Inspect both solar panels and rooftops, record a video of the Base, and gather RGB and thermal images of the Tower.", "solution": [
        {"name": "SubTask1", "skill": "InspectStructure", "object": "SolarPanel1"},
        {"name": "SubTask2", "skill": "InspectStructure", "object": "SolarPanel2"},
        {"name": "SubTask3", "skill": "InspectStructure", "object": "RoofTop1"},
        {"name": "SubTask4", "skill": "InspectStructure", "object": "RoofTop2"},
        {"name": "SubTask5", "skill": "RecordVideo", "object": "Base"},
        {"name": "SubTask6", "skill": "CaptureRGBImage", "object": "Tower"},
        {"name": "SubTask7", "skill": "CaptureThermalImage", "object": "Tower"}
    ]},

    # === 8-subtask tasks ===
    {"id": "Task22", "task": "Acquire both RGB and infrared imagery of House1, House2, SolarPanel1 and Rooftop1.", "solution": [
        {"name": "SubTask1", "skill": "CaptureRGBImage", "object": "House1"},
        {"name": "SubTask2", "skill": "CaptureThermalImage", "object": "House1"},
        {"name": "SubTask3", "skill": "CaptureRGBImage", "object": "House2"},
        {"name": "SubTask4", "skill": "CaptureThermalImage", "object": "House2"},
        {"name": "SubTask5", "skill": "CaptureRGBImage", "object": "SolarPanel1"},
        {"name": "SubTask6", "skill": "CaptureThermalImage", "object": "SolarPanel1"},
        {"name": "SubTask7", "skill": "CaptureRGBImage", "object": "RoofTop1"},
        {"name": "SubTask8", "skill": "CaptureThermalImage", "object": "RoofTop1"}
    ]},

    {"id": "Task23", "task": "Document the condition of all houses with video and inspect each rooftop, while measuring wind levels near the Base and Tower, in addition take an RGB image of Tower", "solution": [
        {"name": "SubTask1", "skill": "RecordVideo", "object": "House1"},
        {"name": "SubTask2", "skill": "RecordVideo", "object": "House2"},
        {"name": "SubTask3", "skill": "RecordVideo", "object": "House3"},
        {"name": "SubTask4", "skill": "InspectStructure", "object": "RoofTop1"},
        {"name": "SubTask5", "skill": "InspectStructure", "object": "RoofTop2"},
        {"name": "SubTask6", "skill": "MeasureWind", "object": "Tower"},
        {"name": "SubTask7", "skill": "MeasureWind", "object": "Base"},
        {"name": "SubTask8", "skill": "CaptureRGBImage", "object": "Tower"}
    ]},

    {"id": "Task24", "task": "Capture RGB and thermal imagery of all houses, and record videos for all rooftops.", "solution": [
        {"name": "SubTask1", "skill": "CaptureRGBImage", "object": "House1"},
        {"name": "SubTask2", "skill": "CaptureThermalImage", "object": "House1"},
        {"name": "SubTask3", "skill": "CaptureRGBImage", "object": "House2"},
        {"name": "SubTask4", "skill": "CaptureThermalImage", "object": "House2"},
        {"name": "SubTask5", "skill": "CaptureRGBImage", "object": "House3"},
        {"name": "SubTask6", "skill": "CaptureThermalImage", "object": "House3"},
        {"name": "SubTask7", "skill": "RecordVideo", "object": "RoofTop1"},
        {"name": "SubTask8", "skill": "RecordVideo", "object": "RoofTop2"}
    ]},

    # === 9-subtask tasks ===
    {"id": "Task25", "task": "Record videos of all houses, inspect all rooftops, and measure wind conditions at the Base, Tower, and both solar panels.", "solution": [
        {"name": "SubTask1", "skill": "RecordVideo", "object": "House1"},
        {"name": "SubTask2", "skill": "RecordVideo", "object": "House2"},
        {"name": "SubTask3", "skill": "RecordVideo", "object": "House3"},
        {"name": "SubTask4", "skill": "InspectStructure", "object": "RoofTop1"},
        {"name": "SubTask5", "skill": "InspectStructure", "object": "RoofTop2"},
        {"name": "SubTask6", "skill": "MeasureWind", "object": "Base"},
        {"name": "SubTask7", "skill": "MeasureWind", "object": "Tower"},
        {"name": "SubTask8", "skill": "MeasureWind", "object": "SolarPanel1"},
        {"name": "SubTask9", "skill": "MeasureWind", "object": "SolarPanel2"}
    ]},

    {"id": "Task26", "task": "Inspect every structure including rooftops, towers, and solar panels, and gather RGB and thermal imagery for House3 and 1.", "solution": [
        {"name": "SubTask1", "skill": "InspectStructure", "object": "RoofTop1"},
        {"name": "SubTask2", "skill": "InspectStructure", "object": "RoofTop2"},
        {"name": "SubTask3", "skill": "InspectStructure", "object": "Tower"},
        {"name": "SubTask4", "skill": "InspectStructure", "object": "SolarPanel1"},
        {"name": "SubTask5", "skill": "InspectStructure", "object": "SolarPanel2"},
        {"name": "SubTask6", "skill": "CaptureRGBImage", "object": "House3"},
        {"name": "SubTask7", "skill": "CaptureThermalImage", "object": "House3"},
        {"name": "SubTask8", "skill": "CaptureRGBImage", "object": "House1"},
        {"name": "SubTask9", "skill": "CaptureThermalImage", "object": "House1"}
    ]},

    {"id": "Task27", "task": "Record videos of all solar panels, rooftops, and the Tower, then measure wind across every house and the Base.", "solution": [
        {"name": "SubTask1", "skill": "RecordVideo", "object": "SolarPanel1"},
        {"name": "SubTask2", "skill": "RecordVideo", "object": "SolarPanel2"},
        {"name": "SubTask3", "skill": "RecordVideo", "object": "RoofTop1"},
        {"name": "SubTask4", "skill": "RecordVideo", "object": "RoofTop2"},
        {"name": "SubTask5", "skill": "RecordVideo", "object": "Tower"},
        {"name": "SubTask6", "skill": "MeasureWind", "object": "House1"},
        {"name": "SubTask7", "skill": "MeasureWind", "object": "House2"},
        {"name": "SubTask8", "skill": "MeasureWind", "object": "House3"},
        {"name": "SubTask9", "skill": "MeasureWind", "object": "Base"}
    ]},

    # === 10-subtask tasks ===
    {"id": "Task28", "task": "Take RGB and thermal images of all houses and rooftops.", "solution": [
        {"name": "SubTask1", "skill": "CaptureRGBImage", "object": "House1"},
        {"name": "SubTask2", "skill": "CaptureThermalImage", "object": "House1"},
        {"name": "SubTask3", "skill": "CaptureRGBImage", "object": "House2"},
        {"name": "SubTask4", "skill": "CaptureThermalImage", "object": "House2"},
        {"name": "SubTask5", "skill": "CaptureRGBImage", "object": "House3"},
        {"name": "SubTask6", "skill": "CaptureThermalImage", "object": "House3"},
        {"name": "SubTask7", "skill": "CaptureRGBImage", "object": "RoofTop1"},
        {"name": "SubTask8", "skill": "CaptureThermalImage", "object": "RoofTop1"},
        {"name": "SubTask9", "skill": "CaptureRGBImage", "object": "RoofTop2"},
        {"name": "SubTask10", "skill": "CaptureThermalImage", "object": "RoofTop2"},
    ]},

    {"id": "Task29", "task": "Record videos for all solarpanels and rooftops, take thermal imagery of each, and inspect the Tower and Base.", "solution": [
        {"name": "SubTask1", "skill": "RecordVideo", "object": "SolarPanel1"},
        {"name": "SubTask2", "skill": "RecordVideo", "object": "SolarPanel2"},
        {"name": "SubTask3", "skill": "RecordVideo", "object": "RoofTop1"},
        {"name": "SubTask4", "skill": "RecordVideo", "object": "RoofTop2"},
        {"name": "SubTask5", "skill": "CaptureThermalImage", "object": "SolarPanel1"},
        {"name": "SubTask6", "skill": "CaptureThermalImage", "object": "SolarPanel2"},
        {"name": "SubTask7", "skill": "CaptureThermalImage", "object": "RoofTop1"},
        {"name": "SubTask8", "skill": "CaptureThermalImage", "object": "RoofTop2"},
        {"name": "SubTask9", "skill": "InspectStructure", "object": "Tower"},
        {"name": "SubTask10", "skill": "InspectStructure", "object": "Base"}
    ]},

    {"id": "Task30", "task": "Capture RGB imagery of every object, and log the windspeed on RoofTop1.", "solution": [
        {"name": "SubTask1", "skill": "CaptureRGBImage", "object": "House1"},
        {"name": "SubTask2", "skill": "CaptureRGBImage", "object": "House2"},
        {"name": "SubTask3", "skill": "CaptureRGBImage", "object": "House3"},
        {"name": "SubTask4", "skill": "CaptureRGBImage", "object": "SolarPanel1"},
        {"name": "SubTask5", "skill": "CaptureRGBImage", "object": "SolarPanel2"},
        {"name": "SubTask6", "skill": "CaptureRGBImage", "object": "RoofTop1"},
        {"name": "SubTask7", "skill": "CaptureRGBImage", "object": "RoofTop2"},
        {"name": "SubTask8", "skill": "CaptureRGBImage", "object": "Base"},
        {"name": "SubTask9", "skill": "CaptureRGBImage", "object": "Tower"},
        {"name": "SubTask10", "skill": "MeasureWind", "object": "RoofTop1"}
    ]}

]

if __name__ == "__main__":
    print(task_list[0]["solution"])