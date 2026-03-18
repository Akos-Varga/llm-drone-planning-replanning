import queue
import random
import time

from common import IDLE, BUSY, COMPLETED, DRONE_FAILED, TASK_FAILED

# =============================================================================
# Drone process
# =============================================================================
def drone_worker(drone_name, event_queue, command_queue):
    """
    Simulates one drone running independently.
    It receives commands from the planner and sends events back.
    """
    state = IDLE
    current_task = None

    while True:
        try:
            cmd = command_queue.get(timeout=0.1)
        except queue.Empty:
            continue

        cmd_type = cmd.get("type")

        if cmd_type == "STOP":
            event_queue.put({
                "type": "STATE_CHANGED",
                "drone": drone_name,
                "state": state,
                "subtask": None if current_task is None else current_task["name"],
                "message": "Stopping drone worker",
            })
            break

        if cmd_type == "ASSIGN_TASK":
            if state != IDLE:
                event_queue.put({
                    "type": "REJECTED",
                    "drone": drone_name,
                    "state": state,
                    "subtask": None if current_task is None else current_task["name"],
                    "message": "Drone is not IDLE",
                })
                continue

            task = cmd["task"]
            current_task = task
            state = BUSY

            event_queue.put({
                "type": "STATE_CHANGED",
                "drone": drone_name,
                "state": state,
                "subtask": current_task["name"],
                "message": f"Accepted {current_task['name']}",
            })

            # Simulate travel
            planned_arrival = float(task["arrival_time"])
            service_time = float(task["service_time"])
            offset = random.uniform(-0.5, 0.8)
            actual_arrival = max(0.0, planned_arrival + offset)

            time.sleep(actual_arrival)

            event_queue.put({
                "type": "ARRIVED",
                "drone": drone_name,
                "state": state,
                "subtask": current_task["name"],
                "planned_arrival_time": round(planned_arrival, 2),
                "actual_arrival_time": round(actual_arrival, 2),
            })

            # Optional simulated failures
            fail_roll = random.random()

            if fail_roll < 0.03:
                failed_subtask = current_task["name"]

                state = DRONE_FAILED
                event_queue.put({
                    "type": "DRONE_FAILED",
                    "drone": drone_name,
                    "state": state,
                    "subtask": failed_subtask,
                })

                current_task = None
                continue

            if fail_roll < 0.08:
                failed_subtask = current_task["name"]

                state = TASK_FAILED
                event_queue.put({
                    "type": "TASK_FAILED",
                    "drone": drone_name,
                    "state": state,
                    "subtask": failed_subtask,
                })

                # Drone is still healthy, only the task failed
                current_task = None
                state = IDLE
                event_queue.put({
                    "type": "STATE_CHANGED",
                    "drone": drone_name,
                    "state": state,
                    "subtask": None,
                    "message": "Ready for next task after task failure",
                })
                continue

            # Simulate task execution
            time.sleep(service_time)

            state = COMPLETED
            event_queue.put({
                "type": "COMPLETED",
                "drone": drone_name,
                "state": state,
                "subtask": current_task["name"],
            })

            # Clear and return to IDLE
            current_task = None
            state = IDLE
            event_queue.put({
                "type": "STATE_CHANGED",
                "drone": drone_name,
                "state": state,
                "subtask": None,
                "message": "Ready for next task",
            })