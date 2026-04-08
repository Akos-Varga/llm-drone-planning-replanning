import time
import rclpy
from rclpy.node import Node
from std_msgs.msg import String, UInt8
from onboard_llm.task_admission_llm import onboard_LLM


class AnafiTelemetry(Node):
    def __init__(self, namespace="anafi"):
        super().__init__(f"{namespace}_telemetry")

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


def admit_task_from_live_telemetry(model, node: AnafiTelemetry, max_flight, flight_dur, task_dur, wait_timeout=3.0):
    """
    Reads the latest live telemetry from ROS topics, then calls drone_pipeline.
    """

    start_wait = time.time()
    while rclpy.ok() and not node.telemetry_ready():
        rclpy.spin_once(node, timeout_sec=0.1)
        if time.time() - start_wait > wait_timeout:
            raise RuntimeError("Timed out waiting for telemetry topics")

    telemetry = node.get_telemetry()

    return onboard_LLM(
        model=model,
        max_flight=max_flight,
        bat_perc=telemetry["battery_percentage"],
        bat_health=telemetry["battery_health"],
        link_qual=telemetry["link_quality"],
        drone_state=telemetry["drone_state"],
        flight_dur=flight_dur,
        task_dur=task_dur,
    )

if __name__ == "__main__":
    rclpy.init()

    node = AnafiTelemetry(namespace="anafi")

    try:
        max_flight_time_minutes = 25.0

        decision, reason, error, inference_time = admit_task_from_live_telemetry(
            model="qwen3:1.7b",
            node=node,
            max_flight=max_flight_time_minutes,
            flight_dur=1.0,
            task_dur=1.0,
        )

        if error:
            print(reason)
        else:
            print(f"ACCEPT | Reason: {reason}") if decision else print(f"REJECT | Reason: {reason}")
            print(f"Inference time: {inference_time:.3f}")


    finally:
        node.destroy_node()
        rclpy.shutdown()