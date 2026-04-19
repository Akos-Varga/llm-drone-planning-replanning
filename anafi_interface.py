import math
import time
import rclpy
from rclpy.node import Node
from std_msgs.msg import String, UInt8, Header
from geometry_msgs.msg import PoseStamped
from anafi_autonomy.msg import PoseCommand, KeyboardCommand
from rcl_interfaces.msg import ParameterValue, Parameter as ParameterMsg
from rcl_interfaces.srv import SetParameters

class SimplePose:
    def __init__(self, d):
        self.x = d["x"]
        self.y = d["y"]
        self.z = d["z"]
        self.qx = d["qx"]
        self.qy = d["qy"]
        self.qz = d["qz"]
        self.qw = d["qw"]

    @property
    def yaw(self):
        """Compute yaw from quaternion."""
        # yaw = atan2(2(wz + xy), 1 - 2(y² + z²))
        siny_cosp = 2.0 * (self.qw * self.qz + self.qx * self.qy)
        cosy_cosp = 1.0 - 2.0 * (self.qy * self.qy + self.qz * self.qz)
        return math.degrees(math.atan2(siny_cosp, cosy_cosp))


class AnafiInterface(Node):
    def __init__(self, namespace="anafi", max_flight_time = 25):
        super().__init__(f"{namespace}_interface")
        self.namespace = namespace
        self.max_flight_time = max_flight_time

        # pose state
        self.current_pose = None

        # telemetry state
        self.battery_percentage = None
        self.battery_health = None
        self.link_quality = None
        self.drone_state = None

        # arrival tolerances
        self.pos_tolerance = 0.1 # m
        self.yaw_tolerance = 5.0 # deg

        # current goal
        self.goal_x = None
        self.goal_y = None
        self.goal_z = None
        self.goal_yaw = None
        self.execution_time = None
        self.arrived_since = None
        self.goal_active = False

        # publishers
        self.pos_pub = self.create_publisher(PoseCommand, f"{self.namespace}/drone/reference/pose", 10)
        self.get_logger().info(f"Publishing PoseCommand → {self.namespace}/drone/reference/pose")
        self.keyboard_pub = self.create_publisher(KeyboardCommand, f"{self.namespace}/keyboard/command", 10)
        self.get_logger().info(f"Publishing keyboard commands → {self.namespace}/keyboard/command")

        # subscribers
        self.create_subscription(PoseStamped, f"{self.namespace}/drone/pose", self._pose_cb, 10)
        self.get_logger().info(f"Subscribed to PoseStamped → {self.namespace}/drone/pose")
        self.create_subscription(UInt8, f"{self.namespace}/battery/percentage", self._battery_percentage_cb, 10)
        self.create_subscription(UInt8, f"{self.namespace}/battery/health", self._battery_health_cb, 10)
        self.create_subscription(UInt8, f"{self.namespace}/link/quality", self._link_quality_cb, 10)
        self.create_subscription(String, f"{self.namespace}/drone/state", self._drone_state_cb, 10)

        # service client
        self.anafi_node_name = f"{self.namespace}/anafi"
        self.set_param_client = self.create_client(SetParameters, f"{self.anafi_node_name}/set_parameters")
        while not self.set_param_client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info(f"Waiting for parameter service: {self.anafi_node_name}/set_parameters") 

        self.get_logger().info(f"Parameter client connected to {self.anafi_node_name}")

    def _battery_percentage_cb(self, msg):
        self.battery_percentage = int(msg.data)

    def _battery_health_cb(self, msg):
        self.battery_health = int(msg.data)

    def _link_quality_cb(self, msg):
        self.link_quality = int(msg.data)

    def _drone_state_cb(self, msg):
        self.drone_state = msg.data

    def _pose_cb(self, msg: PoseStamped):
        self.current_pose = {
            "x": msg.pose.position.x,
            "y": msg.pose.position.y,
            "z": msg.pose.position.z,
            "qx": msg.pose.orientation.x,
            "qy": msg.pose.orientation.y,
            "qz": msg.pose.orientation.z,
            "qw": msg.pose.orientation.w,
        }

    def telemetry_ready(self) -> bool:
        return all(v is not None for v in [
            self.battery_percentage,
            self.battery_health,
            self.link_quality,
            self.drone_state,
        ])

    def get_telemetry(self) -> dict:
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
        from onboard_llm.task_admission_llm import onboard_task_admission, Telemetry
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

        self.get_logger().info(
            f"Admission check | "
            f"state={telemetry['drone_state']} | "
            f"battery={telemetry['battery_percentage']}% | "
            f"health={telemetry['battery_health']}% | "
            f"link={telemetry['link_quality']}"
        )

        return onboard_task_admission(model=model, t=t)
    
    def get_pose(self) -> SimplePose | None:
        if self.current_pose is None:
            return None
        return SimplePose(self.current_pose)
    
    def send_pose(self, pos, yaw_deg, execution_time):
        (self.goal_x, self.goal_y, self.goal_z) = pos
        self.goal_yaw = yaw_deg
        self.execution_time = execution_time

        self.arrived_since = None
        self.goal_active = True

        msg = PoseCommand()
        msg.header = Header()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = "map"

        msg.x = self.goal_x
        msg.y = self.goal_y
        msg.z = self.goal_z
        msg.yaw = self.goal_yaw

        self.pos_pub.publish(msg)

        self.get_logger().info(
            f"Sent PoseCommand: x={msg.x:.2f}, y={msg.y:.2f}, z={msg.z:.2f}, yaw={msg.yaw:.1f}°"
        )

    def is_arrived(self):
        if not self.goal_active:
            return False

        current = self.get_pose()
        if current is None:
            self.arrived_since = None
            return False

        dx = self.goal_x - current.x
        dy = self.goal_y - current.y
        dz = self.goal_z - current.z
        dist_err = math.sqrt(dx**2 + dy**2 + dz**2)

        yaw_err = abs((self.goal_yaw - current.yaw + 180) % 360 - 180)

        within_tolerance = (
            dist_err <= self.pos_tolerance and
            yaw_err <= self.yaw_tolerance
        )

        now = time.monotonic()

        self.get_logger().debug(
            f"{self.namespace} dist_err={dist_err:.2f}, yaw_err={yaw_err:.1f}"
        )

        if within_tolerance:
            if self.arrived_since is None:
                self.arrived_since = now

            if (now - self.arrived_since) >= self.execution_time:
                self.goal_active = False
                self.get_logger().info(
                    f"{self.namespace} arrived "
                    f"[{self.goal_x}, {self.goal_y}, {self.goal_z}]"
                )
                return True
        else:
            self.arrived_since = None

        return False     
    
    def _set_param(self, name: str, value: float, timeout: float = 3.0):
        param_msg = ParameterMsg()
        param_msg.name = name
        param_msg.value = ParameterValue()
        param_msg.value.type = 3  # DOUBLE
        param_msg.value.double_value = float(value)

        request = SetParameters.Request()
        request.parameters = [param_msg]

        future = self.set_param_client.call_async(request)

        deadline = time.monotonic() + timeout
        while rclpy.ok() and not future.done():
            if time.monotonic() > deadline:
                self.get_logger().error(f"Timed out setting parameter {name}")
                return False
            time.sleep(0.01)

        if future.result() is None:
            self.get_logger().error("Parameter service call failed")
            return False

        result = future.result().results[0]
        if result.successful:
            self.get_logger().info(f"Set {name} → {value}")
            return True
        else:
            self.get_logger().warn(f"Failed to set {name}: {result.reason}")
            return False
                
    def set_speed(self, speed: float):
        self._set_param("drone/max_horizontal_speed", speed)
        self._set_param("drone/max_vertical_speed", speed)

    def set_max_altitude(self, altitude: float):
        self._set_param("drone/max_altitude", altitude)

    # ---------------- Arm, Takeoff, Land and Offboard ----------------

    def arm(self):
        msg = KeyboardCommand()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = "body"
        msg.drone_action = 1
        self.keyboard_pub.publish(msg)
        self.get_logger().info("Sent ARM command (drone_action=1)")

    def disarm(self):
        msg = KeyboardCommand()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = "body"
        msg.drone_action = 5
        self.keyboard_pub.publish(msg)
        self.get_logger().info("Sent DISARM command (drone_action=5)")
    
    def takeoff(self):
        msg = KeyboardCommand()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = "body"
        msg.drone_action = 2
        self.keyboard_pub.publish(msg)
        self.get_logger().info("Sent TAKEOFF command (drone_action=2)")

    def land(self):
        msg = KeyboardCommand()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = "body"
        msg.drone_action = 4
        self.keyboard_pub.publish(msg)
        self.get_logger().info("Sent LAND command (drone_action=4)")

    def offboard(self):
        msg = KeyboardCommand()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = "body"
        msg.drone_action = 102
        self.keyboard_pub.publish(msg)
        self.get_logger().info("Sent OFFBOARD command (drone_action=102)")


def task_acceptance_test():
    rclpy.init()
    node = AnafiInterface("anafi", 25)

    try:
        # Wait for telemetry BEFORE calling admission
        timeout = 3.0
        deadline = time.monotonic() + timeout

        while rclpy.ok() and not node.telemetry_ready():
            if time.monotonic() > deadline:
                print("Telemetry not ready within timeout")
                break

            rclpy.spin_once(node, timeout_sec=0.1)

        if not node.telemetry_ready():
            print("Cannot proceed without telemetry")
        else:
            decision, reason, inference_time = node.admit_task_from_live_telemetry(
                model="qwen3:1.7b",
                flight_dur=5.0,
                task_dur=5.0,
            )

            if not decision:
                print(reason)
            else:
                print(f"ACCEPT | Reason: {reason}" if decision else f"REJECT | Reason: {reason}")
                if inference_time is not None:
                    print(f"Inference time: {inference_time:.3f}")

    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    task_acceptance_test()
