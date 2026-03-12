skills = {
    "CaptureRGBImage": 1.8,
    "CaptureThermalImage": 2.2,
    "CaptureZoomImage": 3.4,
    "DualSpectralInspect": 4.7,
    "RecordVideo": 5.0
}

objects = {
    "Base1": (0, 0, 0),
    "Base2": (-1.5, -1.5, 0),
    "House1": (2.2, 4.3, 0.5),
    "House2": (2.6, -3.4, 0.7),
    "WindTurbine1": (-3.4, -1.4, 1.4),
    "WindTurbine2": (-3.3, -3.5, 1.4),
    "Tower1": (-1.0, 4.1, 1.6),
    "Tower2": (-1.9, 1.0, 1.6)

}

drones = {
    "Drone1": {
        "pos": (0, 0, 0),
        "skills": ["CaptureRGBImage", "RecordVideo", "CaptureZoomImage"],
        "speed": 1.0
    },
    "Drone2": {
        "pos": (-1, -1, 0),
        "skills": ["CaptureRGBImage", "CaptureThermalImage", "CaptureZoomImage", "RecordVideo", "DualSpectralInspect"],
        "speed": 0.5
    },
    "Drone3": {
        "pos": (42, 72, 57),
        "skills": ["CaptureRGBImage", "CaptureThermalImage", "RecordVideo", "DualSpectralInspect"],
        "speed": 15
    }
}

# Match drone name from world with anafi topic name
DRONE_TO_NODE = {
    "Drone1": "anafi2",
    "Drone2": "anafi1",
}

# Make drones face object
OBJECT_TO_YAW = {
    "Base1": 0,
    "Base2": 0,
    "House1": 90,
    "House2": 0,
    "WindTurbine1": 180,
    "WindTurbine2": 180,
    "Tower1": 90,
    "Tower2": 180
}

MAX_ALTITUDE = 4.0