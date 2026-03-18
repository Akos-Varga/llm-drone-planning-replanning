import queue

from common import IDLE, BUSY, COMPLETED, DRONE_FAILED, TASK_FAILED

# =============================================================================
# Planner
# =============================================================================
def planner_loop(event_queue, command_queues):
    """
    Reactive planner:
    - listens for drone events
    - tracks drone states
    - sends tasks to IDLE drones
    """
    drone_status = {
        drone: {"state": IDLE, "subtask": None}
        for drone in command_queues
    }

    pending_tasks = [
        {
            "name": "SubTask1",
            "object": "House1",
            "skill": "CaptureRGBImage",
            "arrival_time": 1.5,
            "service_time": 1.0,
        },
        {
            "name": "SubTask2",
            "object": "House2",
            "skill": "CaptureThermalImage",
            "arrival_time": 2.0,
            "service_time": 1.3,
        },
        {
            "name": "SubTask3",
            "object": "Tower",
            "skill": "MeasureWind",
            "arrival_time": 1.0,
            "service_time": 1.5,
        },
        {
            "name": "SubTask4",
            "object": "RoofTop1",
            "skill": "InspectStructure",
            "arrival_time": 1.8,
            "service_time": 1.1,
        },
    ]

    def assign_tasks():
        for drone, info in drone_status.items():
            if info["state"] == IDLE and pending_tasks:
                task = pending_tasks.pop(0)
                command_queues[drone].put({
                    "type": "ASSIGN_TASK",
                    "task": task,
                })
                print(f"[PLANNER] Assigned {task['name']} to {drone}")

    # Initial assignment
    assign_tasks()

    while True:
        try:
            event = event_queue.get(timeout=1.0)
        except queue.Empty:
            all_idle = all(info["state"] == IDLE for info in drone_status.values())
            if not pending_tasks and all_idle:
                print("[PLANNER] All tasks completed.")
                for q in command_queues.values():
                    q.put({"type": "STOP"})
                break
            continue

        drone = event["drone"]
        event_type = event["type"]

        print(f"[EVENT] {event}")

        if event_type in {"STATE_CHANGED", "DRONE_FAILED", "TASK_FAILED"}:
            drone_status[drone]["state"] = event["state"]
            drone_status[drone]["subtask"] = event.get("subtask")

        elif event_type == "COMPLETED":
            drone_status[drone]["state"] = COMPLETED
            drone_status[drone]["subtask"] = event.get("subtask")

        elif event_type == "ARRIVED":
            # Arrival can trigger replanning if you want
            pass

        elif event_type == "REJECTED":
            pass

        # Assign new tasks whenever drones become IDLE
        if drone_status[drone]["state"] == IDLE:
            assign_tasks()

        # Example recovery behavior
        if event_type == "TASK_FAILED":
            failed_subtask = event.get("subtask")
            if failed_subtask is not None:
                pending_tasks.append({
                    "name": failed_subtask + "_retry",
                    "object": "Unknown",
                    "skill": "RetrySkill",
                    "arrival_time": 1.0,
                    "service_time": 1.0,
                })
                print(f"[PLANNER] Reinserted failed task {failed_subtask} as retry")

        if event_type == "DRONE_FAILED":
            print(f"[PLANNER] {drone} removed from future assignments")

