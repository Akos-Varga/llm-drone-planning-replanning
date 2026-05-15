import queue
import time
import rclpy

from common import *
from anafi_interface import AnafiInterface

LLM_RECHECK_PERIOD = 10.0

def drone_worker(
    model_name,
    drone_name,
    namespace,
    event_queue,
    command_queue,
    max_flight_time,
    objects,
    object_to_yaw,
    flight_altitude,
    speed,
    max_altitude,
):

    rclpy.init()
    node = AnafiInterface(namespace, max_flight_time)
    node.set_speed(speed)
    node.set_max_altitude(max_altitude)

    state = IDLE
    proposed_task = None
    proposed_task_id = None
    current_task = None
    current_proposal_id = None
    last_llm_check_time = None
    pose_sent = False
    arrived_sent = False
    flight_started = False
    execution_phase = None

    def wait_for_telemetry(timeout=3.0):
        deadline = time.monotonic() + timeout
        while rclpy.ok() and not node.telemetry_ready():
            if time.monotonic() > deadline:
                return False
            rclpy.spin_once(node, timeout_sec=0.1)
        return node.telemetry_ready()

    def run_admission_check(task):
        return node.admit_task_from_live_telemetry(
            model=model_name,
            flight_dur=float(task["arrival_time"]) - float(task["departure_time"]),
            task_dur=float(task["finish_time"]) - float(task["arrival_time"]),
        )

    try:
        while rclpy.ok():
            rclpy.spin_once(node, timeout_sec=0.05)
            
            try:
                cmd = command_queue.get_nowait()
            except queue.Empty:
                cmd = None

            if cmd is not None:

                cmd_type = cmd.get("type")

                # ---------------------------------------------------------------------
                # Stop worker
                # ---------------------------------------------------------------------
                if cmd_type == STOP:
                    if flight_started:
                        node.land()
                        time.sleep(3.0)

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

                        if flight_started:
                            node.land()
                            time.sleep(3.0)
                        
                        break

                    # None / error / unknown decision
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
                    last_llm_check_time = time.monotonic()
                    pose_sent = False
                    arrived_sent = False
                    execution_phase = None
            
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
            # Execution
            # -----------------------------------------------------------------
            if state == BUSY and current_task is not None:
                target_pos = objects[current_task["object"]]
                target_yaw = object_to_yaw[current_task["object"]]
                execution_time = current_task["finish_time"] - current_task["arrival_time"] 

                current_pose = node.get_pose()
                if current_pose is None:
                    continue

                ascend_pos = (
                    current_pose.x,
                    current_pose.y,
                    flight_altitude,
                )

                cruise_pos = (
                    target_pos[0],
                    target_pos[1],
                    flight_altitude,
                )

                work_pos = target_pos

                if not pose_sent:
                    if not flight_started:
                        node.arm()
                        time.sleep(1.0)

                        node.takeoff()
                        time.sleep(3.0)

                        node.offboard()
                        time.sleep(1.0)

                        flight_started  = True

                    node.send_pose(ascend_pos, target_yaw, 0.0)
                    pose_sent = True
                    execution_phase = "ASCEND"

                if execution_phase == "ASCEND" and node.has_arrived():
                    node.send_pose(cruise_pos, target_yaw, 0.0)
                    execution_phase = "CRUISE"

                if execution_phase == "CRUISE" and node.has_arrived():
                    node.send_pose(work_pos, target_yaw, execution_time)
                    execution_phase = "WORK"

                # --- ARRIVAL ---
                if execution_phase == "WORK" and not arrived_sent and node.has_arrived():
                    arrived_sent = True

                    event_queue.put({
                        "type": ARRIVED_EVENT,
                        "drone": drone_name,
                        "state": state,
                        "subtask": current_task["name"],
                        "skill": current_task["skill"],
                        "proposal_id": current_proposal_id,
                        "message": f"Arrived at {current_task['object']}",
                        "time": time.monotonic(),
                    })

                # --- INFLIGHT CHECK ---
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

                        if flight_started:
                            node.land()
                            time.sleep(3.0)

                        # current_task = None
                        # current_proposal_id = None
                        break
                    
                    print("Inflight check")
                    decision, reason, _ = run_admission_check(current_task)
                    last_llm_check_time = now

                    if decision == "ok":
                        event_queue.put({
                            "type": RUNTIME_CHECK_OK,
                            "drone": drone_name,
                            "state": state,
                            "subtask": current_task["name"],
                            "proposal_id": current_proposal_id,
                            "message": f"Runtime check OK for {current_task['name']} | Reason: {reason}",
                            "time": time.monotonic(),
                        })

                    elif decision == "task_failure":
                        failed_subtask = current_task["name"]
                        event_queue.put({
                            "type": REJECTED,
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

                        if flight_started:
                            node.land()
                            time.sleep(3.0)

                        # current_task = None
                        # current_proposal_id = None
                        break

                # --- COMPLETION ---
                if execution_phase == "WORK" and arrived_sent and node.is_completed():
                    finished_subtask = current_task["name"]
                    state = COMPLETED

                    event_queue.put({
                        "type": COMPLETED_EVENT,
                        "drone": drone_name,
                        "state": state,
                        "subtask": finished_subtask,
                        "proposal_id": current_proposal_id,
                        "message": f"Completed {finished_subtask}",
                        "time": time.monotonic()
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
        rclpy.shutdown()