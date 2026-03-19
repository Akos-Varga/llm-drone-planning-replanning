import queue
import random
import time

from common import IDLE, BUSY, COMPLETED, DRONE_FAILED, TASK_FAILED

# =============================================================================
# Message / command types
# =============================================================================
ASSIGN_TASK = "ASSIGN_TASK"
ACK = "ACK"
REJECTED = "REJECTED"
START_TASK = "START_TASK"
CANCEL_TASK = "CANCEL_TASK"
STATE_CHANGED = "STATE_CHANGED"
COMPLETED_EVENT = "COMPLETED"
TASK_FAILED_EVENT = "TASK_FAILED"
DRONE_FAILED_EVENT = "DRONE_FAILED"
STOP = "STOP"


def drone_worker(
    drone_name,
    event_queue,
    command_queue,
    ack_probability=0.9,
    finish_offset_range=(-0.5, 0.8),
    p_drone_fail=0.3,
    p_task_fail=0.05,
):
    """
    Independent drone process.

    Protocol:
    1. Planner sends ASSIGN_TASK(task, proposal_id)
    2. Drone randomly sends ACK or REJECTED with the same proposal_id
    3. If planner receives ACK from all selected drones, planner sends START_TASK(task, proposal_id)
    4. Drone executes task
    5. Drone sends runtime events

    Notes:
    - proposal_id prevents stale ACK/REJECT events from being mistaken for a new round
    - event["time"] is only debug metadata
    """

    state = IDLE
    proposed_task = None
    proposed_task_id = None
    current_task = None

    while True:
        try:
            cmd = command_queue.get(timeout=0.1)
        except queue.Empty:
            continue

        cmd_type = cmd.get("type")

        # ---------------------------------------------------------------------
        # Stop worker
        # ---------------------------------------------------------------------
        if cmd_type == STOP:
            event_queue.put({
                "type": STATE_CHANGED,
                "drone": drone_name,
                "state": state,
                "subtask": None if current_task is None else current_task["name"],
                "proposal_id": proposed_task_id,
                "message": "Stopping drone worker",
                "time": time.monotonic(),
            })
            break

        # ---------------------------------------------------------------------
        # Proposal phase: planner asks for ACK / REJECTED
        # ---------------------------------------------------------------------
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

            if random.random() <= ack_probability:
                proposed_task = task
                proposed_task_id = proposal_id
                event_queue.put({
                    "type": ACK,
                    "drone": drone_name,
                    "state": state,
                    "subtask": task["name"],
                    "proposal_id": proposal_id,
                    "message": f"ACK for {task['name']}",
                    "time": time.monotonic(),
                })
            else:
                event_queue.put({
                    "type": REJECTED,
                    "drone": drone_name,
                    "state": state,
                    "subtask": task["name"],
                    "proposal_id": proposal_id,
                    "message": f"Rejected {task['name']}",
                    "time": time.monotonic(),
                })
            continue

        # ---------------------------------------------------------------------
        # Planner cancels a previously ACKed proposal
        # ---------------------------------------------------------------------
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

        # ---------------------------------------------------------------------
        # Start execution only after planner confirms the round
        # ---------------------------------------------------------------------
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

            event_queue.put({
                "type": STATE_CHANGED,
                "drone": drone_name,
                "state": state,
                "subtask": current_task["name"],
                "proposal_id": current_proposal_id,
                "message": f"Started {current_task['name']}",
                "time": time.monotonic(),
            })

            # -----------------------------------------------------------------
            # Simulate execution
            # -----------------------------------------------------------------
            planned_finish = float(current_task["finish_time"])
            finish_offset = round(random.uniform(*finish_offset_range), 2)
            actual_finish = max(0.0, round(planned_finish + finish_offset, 2))

            time.sleep(actual_finish)

            # -----------------------------------------------------------------
            # Optional failures at task end
            # -----------------------------------------------------------------
            fail_roll = random.random()

            if fail_roll < p_drone_fail:
                failed_subtask = current_task["name"]
                state = DRONE_FAILED
                event_queue.put({
                    "type": DRONE_FAILED_EVENT,
                    "drone": drone_name,
                    "state": state,
                    "subtask": failed_subtask,
                    "proposal_id": current_proposal_id,
                    "message": f"Drone failure during {failed_subtask}",
                    "planned_finish_time": round(planned_finish, 2),
                    "actual_finish_time": actual_finish,
                    "finish_offset": finish_offset,
                    "time": time.monotonic(),
                })
                current_task = None
                continue

            if fail_roll < p_drone_fail + p_task_fail:
                failed_subtask = current_task["name"]
                state = TASK_FAILED
                event_queue.put({
                    "type": TASK_FAILED_EVENT,
                    "drone": drone_name,
                    "state": state,
                    "subtask": failed_subtask,
                    "proposal_id": current_proposal_id,
                    "message": f"Task failure during {failed_subtask}",
                    "planned_finish_time": round(planned_finish, 2),
                    "actual_finish_time": actual_finish,
                    "finish_offset": finish_offset,
                    "time": time.monotonic(),
                })

                current_task = None
                state = IDLE
                event_queue.put({
                    "type": STATE_CHANGED,
                    "drone": drone_name,
                    "state": state,
                    "subtask": None,
                    "proposal_id": current_proposal_id,
                    "message": "Ready for next task after task failure",
                    "time": time.monotonic(),
                })
                continue

            # -----------------------------------------------------------------
            # Success at task end
            # -----------------------------------------------------------------
            finished_subtask = current_task["name"]
            state = COMPLETED
            event_queue.put({
                "type": COMPLETED_EVENT,
                "drone": drone_name,
                "state": state,
                "subtask": finished_subtask,
                "proposal_id": current_proposal_id,
                "message": f"Completed {finished_subtask}",
                "planned_finish_time": round(planned_finish, 2),
                "actual_finish_time": actual_finish,
                "finish_offset": finish_offset,
                "time": time.monotonic(),
            })

            current_task = None
            state = IDLE
            event_queue.put({
                "type": STATE_CHANGED,
                "drone": drone_name,
                "state": state,
                "subtask": None,
                "proposal_id": current_proposal_id,
                "message": "Ready for next task",
                "time": time.monotonic(),
            })