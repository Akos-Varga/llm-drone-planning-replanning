import time

from onboard_llm.task_admission_llm import onboard_task_admission, Telemetry

class SimDroneInterface:
    def __init__(self, namespace, max_flight_time):
        self.name = namespace
        self.max_flight_time = float(max_flight_time)

        self.position = [0.0, 0.0, 0.0]
        self.yaw = 0.0

        self.goal_x = None
        self.goal_y = None
        self.goal_z = None
        self.goal_yaw = None

        self._telemetry_ready = True
        self.battery_percentage = 100.0
        self.battery_health = 100.0
        self.link_quality = 5
        self.drone_state = "LANDED"

        self.execution_time = None
        self.goal_active = False
        self.departure_time = None

    def telemetry_ready(self):
        return self._telemetry_ready
    
    def get_telemetry(self):
        return {
            "battery_percentage": self.battery_percentage,
            "battery_health": self.battery_health,
            "link_quality": self.link_quality,
            "drone_state": self.drone_state,
        }
    
    def admit_task_from_live_telemetry(
        self,
        model,
        flight_dur: float,
        task_dur: float,
    ):
        if not self.telemetry_ready():
            return None, "Telemetry not ready", None

        telemetry = self.get_telemetry()
        t = Telemetry(
            max_flight=self.max_flight_time,
            bat_perc=telemetry["battery_percentage"],
            bat_health=telemetry["battery_health"],
            link_qual=telemetry["link_quality"],
            drone_state=telemetry["drone_state"],
            flight_dur=flight_dur,
            task_dur=task_dur,
        )

        print(
            f"Admission check | "
            f"state={telemetry['drone_state']} | "
            f"battery={telemetry['battery_percentage']}% | "
            f"health={telemetry['battery_health']}% | "
            f"link={telemetry['link_quality']}"
        )

        return onboard_task_admission(model=model, t=t)

    def send_pose(self, pos, yaw_deg, execution_time):
        (self.goal_x, self.goal_y, self.goal_z) = pos
        self.goal_yaw = yaw_deg
        self.execution_time = execution_time
        self.departure_time = time.monotonic()
        self.goal_active = True

    def is_arrived(self):
        if not self.goal_active:
            return False
        if time.monotonic() >= self.departure_time + self.execution_time:
            self.goal_active = False
            return True
        return False

    def destroy_node(self):
        pass