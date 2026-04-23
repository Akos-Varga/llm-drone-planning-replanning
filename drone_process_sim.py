import queue
import time

from common import *
from simulated_drone_interface import SimDroneInterface
from worlds.test_world import objects, OBJECT_TO_YAW

LLM_RECHECK_PERIOD = 10.0

def drone_worker_sim(
    drone_name,
    namespace,
    event_queue,
    command_queue,
    max_flight_time,
):
    node = SimDroneInterface(namespace, max_flight_time)

    state = IDLE
    proposed_task = None
    proposed_task_id = None
    current_task = None
    current_proposal_id = None
    last_llm_check_time = None
    pose_sent = False

    def wait_for_telemetry(timeout=3.0):
        deadline = time.monotonic() + timeout
        while not node.telemetry_ready():
            if time.monotonic() > deadline:
                return False
            time.sleep(0.05)
        return True
    
    def run_admission_check(task):
        return node.admit_task_from_live_telemetry(
            model="qwen3:1.7b",
            flight_dur=float(task["arrival_time"]) - float(task["departure_time"]),
            task_dur=float(task["finish_time"]) - float(task["arrival_time"]),
        )

    try:
        while True:
            try:
                cmd = command_queue.get_nowait()
            except queue.Empty:
                cmd = None

            if cmd is not None:
                cmd_type = cmd.get("type")

                # -----------------------------------------------------------------
                # Stop worker
                # -----------------------------------------------------------------
                if cmd_type == STOP:
                    event_queue.put({
                        "type": STATE_CHANGED,
                        "drone": drone_name,
                        "state": state,
                        "subtask": None if current_task is None else current_task["name"],
                        "proposal_id": proposed_task_id,
                        "message": "Stopping simulated drone worker",
                        "time": time.monotonic(),
                    })
                    break

                # -----------------------------------------------------------------
                # Proposal phase: planner asks for ACK / REJECTED
                # -----------------------------------------------------------------
                if cmd_type == ASSIGN_TASK:
                    task = cmd["task"]
                    proposal_id = cmd.get("proposal_id")

                    if state != IDLE or proposed_task is not None or current_task is not None:
                        event_queue.put({
                            "type": REJECTED,
                            "drone": drone_name,
                            "state": state,
                            "subtask": task["name"],
                            "proposal_id": proposal_id,
                            "message": "Drone is not available for proposal",
                            "time": time.monotonic(),
                        })
                        continue

                    if not wait_for_telemetry(timeout=3.0):
                        event_queue.put({
                            "type": REJECTED,
                            "drone": drone_name,
                            "state": state,
                            "subtask": task["name"],
                            "proposal_id": proposal_id,
                            "message": "Admission rejected: telemetry not ready",
                            "time": time.monotonic(),
                        })
                        continue
                        
                    decision, reason, _ = run_admission_check(task)

                    if decision == "ok":
                        proposed_task = task
                        proposed_task_id = proposal_id

                        event_queue.put({
                            "type": ACK,
                            "drone": drone_name,
                            "state": state,
                            "subtask": task["name"],
                            "proposal_id": proposal_id,
                            "message": f"ACK for {task['name']} | Reason: {reason}",
                            "time": time.monotonic(),
                        })
                        continue

                    if decision == "task_failure":
                        event_queue.put({
                            "type": TASK_FAILED_EVENT,
                            "drone": drone_name,
                            "state": state,
                            "subtask": task["name"],
                            "proposal_id": proposal_id,
                            "message": f"Admission task failure: {reason}",
                            "time": time.monotonic(),
                        })
                        continue

                    if decision == "drone_failure":
                        state = DRONE_FAILED
                        event_queue.put({
                            "type": DRONE_FAILED_EVENT,
                            "drone": drone_name,
                            "state": state,
                            "subtask": task["name"],
                            "proposal_id": proposal_id,
                            "message": f"Admission drone failure: {reason}",
                            "time": time.monotonic(),
                        })
                        continue

                    event_queue.put({
                        "type": REJECTED,
                        "drone": drone_name,
                        "state": state,
                        "subtask": task["name"],
                        "proposal_id": proposal_id,
                        "message": f"Admission rejected due to error/unknown decision: {reason}",
                        "time": time.monotonic(),
                    })
                    continue

                # -----------------------------------------------------------------
                # Planner cancels a previously ACKed proposal
                # -----------------------------------------------------------------
                if cmd_type == CANCEL_TASK:
                    task_name = cmd.get("task_name")
                    proposal_id = cmd.get("proposal_id")

                    if (
                        proposed_task is not None
                        and proposed_task["name"] == task_name
                        and proposed_task_id == proposal_id
                    ):
                        proposed_task = None
                        proposed_task_id = None
                        event_queue.put({
                            "type": STATE_CHANGED,
                            "drone": drone_name,
                            "state": state,
                            "subtask": None,
                            "proposal_id": proposal_id,
                            "message": f"Cancelled proposal for {task_name}",
                            "time": time.monotonic(),
                        })
                    continue

                # -----------------------------------------------------------------
                # Start execution only after planner confirms the round
                # -----------------------------------------------------------------
                if cmd_type == START_TASK:
                    task = cmd["task"]
                    proposal_id = cmd.get("proposal_id")

                    if (
                        proposed_task is None
                        or proposed_task["name"] != task["name"]
                        or proposed_task_id != proposal_id
                    ):
                        event_queue.put({
                            "type": REJECTED,
                            "drone": drone_name,
                            "state": state,
                            "subtask": task["name"],
                            "proposal_id": proposal_id,
                            "message": f"Cannot start {task['name']} without matching ACKed proposal",
                            "time": time.monotonic(),
                        })
                        continue

                    current_task = proposed_task
                    current_proposal_id = proposed_task_id
                    proposed_task = None
                    proposed_task_id = None
                    state = BUSY
                    last_llm_check_time = time.monotonic()
                    pose_sent = False

                    event_queue.put({
                        "type": STATE_CHANGED,
                        "drone": drone_name,
                        "state": state,
                        "subtask": current_task["name"],
                        "object": current_task["object"],
                        "proposal_id": current_proposal_id,
                        "message": f"Started {current_task['name']}",
                        "time": time.monotonic(),
                    })

            # -----------------------------------------------------------------
            # Execution
            # -----------------------------------------------------------------
            if state == BUSY and current_task is not None:
                target_pos = objects[current_task["object"]]
                target_yaw = OBJECT_TO_YAW[current_task["object"]]
                execution_time = float(current_task["finish_time"]) - float(current_task["arrival_time"])
                flight_time = float(current_task["arrival_time"] - current_task["departure_time"])

                if not pose_sent:
                    node.send_pose(target_pos, target_yaw, flight_time, execution_time)
                    pose_sent = True

                now = time.monotonic()

                if now - last_llm_check_time >= LLM_RECHECK_PERIOD:
                    if not wait_for_telemetry(timeout=3.0):
                        state = DRONE_FAILED
                        event_queue.put({
                            "type": DRONE_FAILED_EVENT,
                            "drone": drone_name,
                            "state": state,
                            "subtask": current_task["name"],
                            "proposal_id": current_proposal_id,
                            "message": "Telemetry not ready during runtime recheck",
                            "time": time.monotonic(),
                        })
                        current_task = None
                        current_proposal_id = None
                        continue
                    print("Inflight check")
                    decision, reason, _ = run_admission_check(current_task)
                    last_llm_check_time = now

                    if decision == "ok":
                        pass

                    elif decision == "task_failure":
                        failed_subtask = current_task["name"]
                        state = TASK_FAILED
                        event_queue.put({
                            "type": TASK_FAILED_EVENT,
                            "drone": drone_name,
                            "state": state,
                            "subtask": failed_subtask,
                            "proposal_id": current_proposal_id,
                            "message": f"Runtime task failure: {reason}",
                            "time": time.monotonic(),
                        })

                        current_task = None
                        current_proposal_id = None
                        state = IDLE
                        event_queue.put({
                            "type": STATE_CHANGED,
                            "drone": drone_name,
                            "state": state,
                            "subtask": None,
                            "proposal_id": None,
                            "message": "Ready for next task after task failure",
                            "time": time.monotonic(),
                        })
                        continue

                    elif decision == "drone_failure":
                        failed_subtask = current_task["name"]
                        state = DRONE_FAILED
                        event_queue.put({
                            "type": DRONE_FAILED_EVENT,
                            "drone": drone_name,
                            "state": state,
                            "subtask": failed_subtask,
                            "proposal_id": current_proposal_id,
                            "message": f"Runtime drone failure: {reason}",
                            "time": time.monotonic(),
                        })

                        current_task = None
                        current_proposal_id = None
                        continue

                if node.is_arrived():
                    finished_subtask = current_task["name"]
                    state = COMPLETED
                    event_queue.put({
                        "type": COMPLETED_EVENT,
                        "drone": drone_name,
                        "state": state,
                        "subtask": finished_subtask,
                        "proposal_id": current_proposal_id,
                        "message": f"Completed {finished_subtask}",
                        "time": time.monotonic(),
                    })

                    current_task = None
                    current_proposal_id = None
                    state = IDLE
                    event_queue.put({
                        "type": STATE_CHANGED,
                        "drone": drone_name,
                        "state": state,
                        "subtask": None,
                        "proposal_id": None,
                        "message": "Ready for next task",
                        "time": time.monotonic(),
                    })

            time.sleep(0.05)

    finally:
        node.destroy_node()