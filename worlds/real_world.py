# Take a thermal image of House1 and RGB image of WindTurbine1.

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
    "House1": (3.61, 3.90, 0.7),
    "House2": (2.6, -3.4, 0.7),
    "WindTurbine1": (3.81, -3.33, 0.75),
    "WindTurbine2": (4.07, -1.86, 0.75),
    "Tower": (2.20, 3.71, 1.0),
    "RoofTop2":(2.0, 2.0, 2.0),
    "RoofTop1":(5.0, 5.0, 2.0),
    "SolarPanel1":(3.4, 2.4, 2.0),
    "SolarPanel2":(5.0, 5.0, 2.0),
}

# Make drones face object
OBJECT_TO_YAW = {
    "Base1": 0,
    "Base2": 0,
    "House1": 90,
    "House2": 0,
    "WindTurbine1": 0,
    "WindTurbine2": 0,
    "Tower": 90,
    "RoofTop2": 0,
    "RoofTop1": 0,
}

# Drones in use
drone_names = ["Drone1", "Drone2"]

drones = {
    "Drone1": { # 4K or AI
        "pos": (2.08, 0.39, 0),
        "skills": ["CaptureRGBImage", "RecordVideo", "CaptureZoomImage"],
        "speed": 0.7
    },
    "Drone2": { # USA or Thermal
        "pos": (1.51, 0.04, 0),
        "skills": ["CaptureRGBImage", "CaptureThermalImage", "CaptureZoomImage", "RecordVideo", "DualSpectralInspect"],
        "speed": 0.5
    }
}


drone_configs = {
    "Drone1": {"namespace": "anafi1", "max_flight_time": 25.0, "flight_altitude": 1.5},
    "Drone2": {"namespace": "anafi2", "max_flight_time": 22.0, "flight_altitude": 2.0},
    "Drone3": {"namespace": "anafi", "max_flight_time": 18.0, "flight_altitude": 2.5},
    "Drone4": {"namespace": "anafi", "max_flight_time": 30.0, "flight_altitude": 3.5},
    "Drone5": {"namespace": "anafi", "max_flight_time": 20.0, "flight_altitude": 4.0},
    "Drone6": {"namespace": "anafi", "max_flight_time": 27.0, "flight_altitude": 4.5},
}

MAX_ALTITUDE = 4.0