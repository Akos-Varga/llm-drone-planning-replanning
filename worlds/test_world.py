skills = {
    'CaptureRGBImage': 1.1,
    'CaptureThermalImage': 2.4,
    'InspectStructure': 1.3,
    'MeasureWind': 2.7,
    'RecordVideo': 1.5
}

objects = {
    'Base': (75, 0, 53),
    'House1': (45, 70, 29),
    'House2': (78, 44, 53),
    'House3': (40, 40, 90),
    'RoofTop1': (4, 99, 39),
    'RoofTop2': (84, 37, 90),
    'SolarPanel1': (84, 82, 21),
    'SolarPanel2': (72, 8, 84),
    'Tower': (53, 91, 57)
}

drones = {
    'Drone1': {'pos': (34, 89, 13), 'skills': ['CaptureThermalImage'], 'speed': 19},
    'Drone2': {'pos': (89, 17, 9), 'skills': ['MeasureWind', 'CaptureRGBImage'], 'speed': 19},
    'Drone3': {'pos': (42, 72, 57), 'skills': ['CaptureRGBImage', 'CaptureThermalImage'], 'speed': 15},
    'Drone4': {'pos': (49, 87, 76), 'skills': ['CaptureRGBImage', 'RecordVideo'], 'speed': 13},
    'Drone5': {'pos': (64, 37, 95), 'skills': ['CaptureThermalImage', 'InspectStructure'], 'speed': 19},
    'Drone6': {'pos': (73, 98, 58), 'skills': ['MeasureWind', 'InspectStructure', 'RecordVideo'], 'speed': 11}
}
