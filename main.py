import threading
import rclpy
import time
import argparse
from rclpy.executors import MultiThreadedExecutor
from publisher import PosePublisher
from worlds.real_world import skills, objects, drones, DRONE_TO_NODE,OBJECT_TO_YAW, MAX_ALTITUDE
from main_pipeline import pipeline

def wait_for_first_pose(node: PosePublisher):
    node.get_logger().info(f"[{node.drone_name}] Waiting for first pose...")
    while rclpy.ok() and node.get_pose() is None:
        time.sleep(0.1)
    node.get_logger().info(f"[{node.drone_name}] Got first pose!")

def wait_for_subscriber(node: PosePublisher):
    node.get_logger().info(f"[{node.drone_name}] Waiting for cmd subscriber...")
    while rclpy.ok() and node.publisher.get_subscription_count() == 0:
        time.sleep(0.1)
    node.get_logger().info(f"[{node.drone_name}] Got subscriber!")

def fly_mission(node: PosePublisher, altitude, drone_schedule, skills, objects):
    wait_for_first_pose(node)
    wait_for_subscriber(node)
    node.arm()
    time.sleep(1)
    node.takeoff()
    time.sleep(5)
    node.offboard()
    for subtask in drone_schedule:
        node.move_and_execute(goal=objects[subtask['object']], altitude=altitude, t=skills[subtask['skill']], obj=subtask['object'], skill=subtask['skill'], yaw_to_obj=OBJECT_TO_YAW[subtask['object']])
    node.move_and_execute(goal=objects[f"Base{int(node.drone_name[-1])}"], altitude=altitude, t=0.0, obj=f"Base{int(node.drone_name[-1])}", skill="ReturnToBase", yaw_to_obj=OBJECT_TO_YAW[f"Base{int(node.drone_name[-1])}"])
    node.get_logger().info(f"[{node.drone_name}]: Mission complete.")
    node.land()


if __name__ == "__main__":
    # --- Parse Command Line Arguments ---
    parser = argparse.ArgumentParser(description="Run drone mission with a specific model and task.")
    parser.add_argument(
        "--model", 
        type=str, 
        default="gpt-5-mini", 
        help="The LLM model to use (default: gpt-5-mini)"
    )
    parser.add_argument(
        "--task", 
        type=str, 
        required=True, 
        help="The task description string."
    )
    args = parser.parse_args()

    rclpy.init()

    pose_publishers = {}
    flight_altitudes = {}

    for i, drone_name in enumerate(drones.keys()):
        node = PosePublisher(drone_name, DRONE_TO_NODE)
        pose_publishers[drone_name] = node
        node.set_max_altitude(MAX_ALTITUDE)
        planned_altitude = i * 0.5 + 2.5
        if planned_altitude > MAX_ALTITUDE:
            raise ValueError(f"[{drone_name}] Planned altitude {planned_altitude:.2f} m exceeds max allowable altitude {MAX_ALTITUDE:.2f} m")
        flight_altitudes[drone_name] = planned_altitude
        node.set_speed(drones[drone_name]['speed'])

    # ---- Create executor and spin in a separate thread ----
    executor = MultiThreadedExecutor()

    for node in pose_publishers.values():
        executor.add_node(node)

    def spin_executor():
        try:
            executor.spin()
        finally:
            for n in pose_publishers.values():
                executor.remove_node(n)

    spin_thread = threading.Thread(target=spin_executor, daemon=True)
    spin_thread.start()

    for drone_name, node in pose_publishers.items():
        wait_for_first_pose(node)

    # --- Plan mission ---
    print(f"Planning mission using model: {args.model}")
    print(f"Task: {args.task}")

    results = pipeline(args.model, args.task, skills, objects, drones)
    schedule = results['schedule']

    threads = []

    for drone_name, drone_schedule in schedule.items():
        if not drone_schedule:
            continue

        node = pose_publishers[drone_name]

        t = threading.Thread(
            target=fly_mission,
            args=(node, flight_altitudes[drone_name], drone_schedule, skills, objects),
            daemon=True,
        )
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    # Cleanup
    for node in pose_publishers.values():
        node.destroy_node()

    executor.shutdown()
    rclpy.shutdown()