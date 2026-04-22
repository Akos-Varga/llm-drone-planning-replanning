import math
import time

class SimDroneInterface:
    def __init__(self, name, max_flight_time=25.0, max_speed=1.0, yaw_speed=45.0):
        self.name = name
        self.max_flight_time = float(max_flight_time)

        self.position = [0.0, 0.0, 0.0]
        self.yaw = 0.0

        self.target_position = self.position[:]
        self.target_yaw = self.yaw

        self.max_speed = float(max_speed)
        self.yaw_speed = float(yaw_speed)

        self._telemetry_ready = True
        self.battery_percentage = 100.0
        self.battery_health = 100.0
        self.link_quality = 5
        self.drone_state = "LANDED"

        self._service_time = 0.0
        self._arrival_hold_start = None

    def telemetry_ready(self):
        return self._telemetry_ready
    
    def get_telemetry(self):
        return {
            "battery_percentage": self.battery_percentage,
            "battery_health": self.battery_health,
            "link_quality": self.link_quality,
            "state": self.drone_state,
        }

    def send_pose(self, target_pos, target_yaw, execution_time=0.0):
        self.target_position = list(target_pos)
        self.target_yaw = float(target_yaw)
        self._service_time = max(0.0, float(execution_time))
        self._arrival_hold_start = None
        self.drone_state = "FLYING"

    def step(self, dt):
        dx = self.target_position[0] - self.position[0]
        dy = self.target_position[1] - self.position[1]
        dz = self.target_position[2] - self.position[2]
        dist = math.sqrt(dx * dx + dy * dy + dz * dz)

        if dist > 1e-6:
            step_dist = min(self.max_speed * dt, dist)
            self.position[0] += step_dist * dx / dist
            self.position[1] += step_dist * dy / dist
            self.position[2] += step_dist * dz / dist
            self.drone_state = "FLYING"
            self._arrival_hold_start = None
        else:
            if self._arrival_hold_start is None:
                self._arrival_hold_start = time.monotonic()
            self.drone_state = "HOVERING"

        yaw_diff = self.target_yaw - self.yaw
        if abs(yaw_diff) > 1e-6:
            yaw_step = min(self.yaw_speed * dt, abs(yaw_diff))
            self.yaw += yaw_step if yaw_diff > 0 else -yaw_step

    def is_arrived(self, pos_tol=0.2, yaw_tol=5.0):
        pos_err = math.dist(self.position, self.target_position)
        yaw_err = abs(self.yaw - self.target_yaw)

        if pos_err > pos_tol or yaw_err > yaw_tol:
            return False

        if self._arrival_hold_start is None:
            return False

        return (time.monotonic() - self._arrival_hold_start) >= self._service_time

    def destroy_node(self):
        pass