import random

class SimDroneInterface:
    def __init__(self, namespace="anafi", max_flight_time=25):
        self.namespace = namespace
        self.max_flight_time = max_flight_time

    def _generate_values():
        operational_states = ["LANDED", "LANDING", "TAKINGOFF", "HOVERING", "FLYING"]
        all_states = ["EMERGENCY", "DISCONNECTED", "CONNECTING"] + operational_states

        # Bias toward operational states
        drone_state = random.choices(
            all_states,
            weights=[1, 1, 1, 4, 4, 4, 4, 4],
            k=1
        )[0]

        bat_perc = int(random.triangular(50, 100, 60))
        bat_health = int(random.triangular(60, 100, 60))

        link_qual = random.choices(
            [0, 1, 2, 3, 4, 5],
            weights=[1, 1, 1, 3, 10, 10],
            k=1
        )[0]

        return drone_state, bat_perc, bat_health, link_qual
    
    def admit_task_from_live_telemetry(
        self,
        model,
        flight_dur: float,
        task_dur: float,
    ):
        from onboard_llm.task_admission_llm import onboard_task_admission, Telemetry
        if not self.telemetry_ready():
            return None, "Telemetry not ready", None

        drone_state, bat_perc, bat_health, link_qual = self._generate_values()
        t = Telemetry(
            max_flight=self.max_flight,
            bat_perc=bat_perc,
            bat_health=bat_health,
            link_qual=link_qual,
            drone_state=drone_state,
            flight_dur=flight_dur,
            task_dur=task_dur,
        )

        self.get_logger().info(
            f"Admission check | "
            f"state={drone_state} | "
            f"battery={bat_perc}% | "
            f"health={bat_health}% | "
            f"link={link_qual}"
        )

        return onboard_task_admission(model=model, t=t)