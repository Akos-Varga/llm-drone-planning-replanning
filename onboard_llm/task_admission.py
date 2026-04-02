from ollama import chat
import time
import json

import rclpy
from rclpy.node import Node
from std_msgs.msg import String, UInt8


class AnafiTelemetry(Node):
    def __init__(self, namespace="anafi"):
        super().__init__("anafi_telemetry")

        self.namespace = namespace

        self.battery_percentage = None
        self.battery_health = None
        self.link_quality = None
        self.drone_state = None

        self.create_subscription(
            UInt8,
            f"{self.namespace}/battery/percentage",
            self._battery_percentage_cb,
            10
        )

        self.create_subscription(
            UInt8,
            f"{self.namespace}/battery/health",
            self._battery_health_cb,
            10
        )

        self.create_subscription(
            UInt8,
            f"{self.namespace}/link/quality",
            self._link_quality_cb,
            10
        )

        self.create_subscription(
            String,
            f"{self.namespace}/drone/state",
            self._drone_state_cb,
            10
        )

        self.get_logger().info("Anafi telemetry subscriber started")

    def _battery_percentage_cb(self, msg):
        self.battery_percentage = int(msg.data)

    def _battery_health_cb(self, msg):
        self.battery_health = int(msg.data)

    def _link_quality_cb(self, msg):
        self.link_quality = int(msg.data)

    def _drone_state_cb(self, msg):
        self.drone_state = msg.data

    def telemetry_ready(self):
        return all(v is not None for v in [
            self.battery_percentage,
            self.battery_health,
            self.link_quality,
            self.drone_state,
        ])

    def get_telemetry(self):
        telemetry = {
            "battery_percentage": self.battery_percentage,
            "battery_health": self.battery_health,
            "link_quality": self.link_quality,
            "drone_state": self.drone_state,
        }

        self.get_logger().info(
            f"State: {telemetry['drone_state']} | "
            f"Battery: {telemetry['battery_percentage']}% | "
            f"Health: {telemetry['battery_health']}% | "
            f"Link: {telemetry['link_quality']}"
        )

        return telemetry

def parse_llm_response(response_json):
    try:
        if not response_json:
            return False, "LLM response was empty.", True
        data = json.loads(response_json)
        return data["decision"] == "accept", data["reason"], False
    except json.JSONDecodeError as e:
        return False, f"Invalid JSON from LLM: {e}. Raw response: {response_json!r}", True
    except Exception as e:
         return False, f"Unexpected error while parsing LLM response: {e}", True

def drone_pipeline(max_flight, bat_perc, bat_health, link_qual, drone_state, flight_dur, task_dur):
    """Decides using LLM if the task should be accepted or rejected by the drone."""
    schema = {
        "type": "object",
        "properties": {
            "decision": {
                "type": "string",
                "enum": ["accept", "reject"]
            },
            "reason": {
                "type": "string"
            }
        },
        "required": ["decision", "reason"]
    }

    SYSTEM_PROMPT = f"""
    You are a task admission module for a drone.

    Your job is to decide whether the drone should ACCEPT or REJECT a task. Use only the policy below.

    You will receive:
    - max_flight_time: maximum time the drone can spend in the air with full battery percentage and health, in minutes
    - battery_percentage: current battery level in percent (0 to 100)
    - battery_health: battery condition in percent (0 to 100)
    - link_quality: radio/link quality from 0 to 5 (0 - worst, 5 - best)
    - drone_state: one of CONNECTING, LANDED, TAKINGOFF, HOVERING, FLYING, LANDING, EMERGENCY, DISCONNECTED
    - flight_duration: flight time needed to reach the destination, in minutes
    - task_duration: task execution time at the destination, in minutes

    Policy:
    1. Reject if drone_state is CONNECTING, EMERGENCY, or DISCONNECTED.
    2. Reject if link_quality <= 3.
    3. Compute available_flight_time = max_flight_time * (battery_percentage / 100) * (battery_health / 100).
    4. Compute required_mission_time = flight_duration + task_duration.
    5. Reject if available_flight_time < required_mission_time.
    6. If none of the rejection rules apply, accept the task.

    Return JSON only:
    {schema}

    The reason must be short and refer only to the triggered rule or say that no rejection rule was triggered.
    """

    start = time.perf_counter()

    response = chat(
        model="qwen3:0.6b",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            # Real query
            {
                "role": "user",
                "content": f"""
                max_flight_time: {max_flight}
                battery_percentage: {bat_perc}
                battery_health: {bat_health}
                link_quality: {link_qual}
                drone_state: {drone_state}
                flight_duration: {flight_dur}
                task_duration: {task_dur}
                """
            }
        ],
        format=schema
    )

    end = time.perf_counter()
    resp = response.message.content

    print(f"\nInference time: {end - start:.3f} seconds")

    return resp


def admit_task_from_live_telemetry(node: AnafiTelemetry, max_flight, flight_dur, task_dur, wait_timeout=3.0):
    """
    Reads the latest live telemetry from ROS topics, then calls drone_pipeline.
    """

    start_wait = time.time()
    while rclpy.ok() and not node.telemetry_ready():
        rclpy.spin_once(node, timeout_sec=0.1)
        if time.time() - start_wait > wait_timeout:
            raise RuntimeError("Timed out waiting for telemetry topics")

    telemetry = node.get_telemetry()

    response = drone_pipeline(
        max_flight=max_flight,
        bat_perc=telemetry["battery_percentage"],
        bat_health=telemetry["battery_health"],
        link_qual=telemetry["link_quality"],
        drone_state=telemetry["drone_state"],
        flight_dur=flight_dur,
        task_dur=task_dur,
    )
    return parse_llm_response(response)

if __name__ == "__main__":
    rclpy.init()

    node = AnafiTelemetry(namespace="anafi")

    try:
        max_flight_time_minutes = 25.0

        decision, reason, error = admit_task_from_live_telemetry(
            node=node,
            max_flight=max_flight_time_minutes,
            flight_dur=1.0,
            task_dur=1.0,
        )

        if error:
            print(reason)
        else:
            print(f"ACCEPT | Reason: {reason}") if decision else print(f"REJECT | Reason: {reason}")


    finally:
        node.destroy_node()
        rclpy.shutdown()
