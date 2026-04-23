import ast
import csv
import os
import queue
import time
import json
import itertools
from pprint import pprint

# --- Imports ---
from worlds.test_world import skills, objects, drones # CHANGE TO TEST WORLD IN LAB
from pipeline.decomposer import messages as decomposer_prompt
from pipeline.allocator import messages as allocator_prompt
from pipeline.scheduler import messages as scheduler_prompt

from pipeline.utils.rule_based_allocator import compute_allocation
from pipeline.utils.rule_based_scheduler import get_schedule
from pipeline.utils.travel_time_calculator import compute_travel_times
from pipeline.utils.schedule_validator import validate_schedule
from pipeline.utils.inference import LM

from common import *

# =============================================================================
# Parameters
# =============================================================================
ACK_TIMEOUT_SECONDS = 60.0
EVENT_WAIT_SECONDS = 0.5


# =============================================================================
# Message builder
# =============================================================================
def build_message(prompt, content):
    return [*prompt, {"role": "user", "content": content}]


# =============================================================================
# Helpers
# =============================================================================
def init_event_log(path):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        pass  # clear file


def append_event_log(path, event):
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(event) + "\n")

def planner_now(start_time):
    return time.monotonic() - start_time


def str_to_code(s):
    try:
        s = s.strip()
        if s.endswith("```"):
            s = s[: s.rfind("```")].strip()
        rhs = s.split("=", 1)[1]
        rhs = "\n".join(line.split("#", 1)[0] for line in rhs.splitlines())
        return ast.literal_eval(rhs)
    except (SyntaxError, ValueError, IndexError, AttributeError):
        return None


def append_row_csv(save, path, row, fieldnames):
    if save:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        write_header = not os.path.exists(path)
        with open(path, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            if write_header:
                writer.writeheader()
            writer.writerow(row)


# =============================================================================
# Pipeline
# =============================================================================
def pipeline_decomposer(model, task, skills, objects):
    """Returns decomposed task."""
    decomposer_message = build_message(
        decomposer_prompt,
        f"task = {task}\n\nskills = {skills}\n\nobjects = {objects}",
    )
    decomposed_task_str = LM(model=model, messages=decomposer_message)
    print(f"\n\nDecomposed task: {decomposed_task_str}")
    return str_to_code(decomposed_task_str)


def pipeline_allocator(model, drones, decomposed_task, rule_based=False):
    """Returns allocated task."""
    if rule_based:
        subtasks_with_drones = compute_allocation(drones, decomposed_task)
    else:
        allocator_message = build_message(
            allocator_prompt,
            f"drones = {drones}\n\nsubtasks = {decomposed_task}",
        )
        subtasks_with_drones_str = LM(model=model, messages=allocator_message)
        subtasks_with_drones = str_to_code(subtasks_with_drones_str)

    return subtasks_with_drones


def pipeline_scheduler(model, subtasks_with_drones, travel_times, rule_based=False):
    """Returns scheduled task."""
    if rule_based:
        schedule, _, _ = get_schedule(subtasks_with_drones, travel_times)
    else:
        scheduler_message = build_message(
            scheduler_prompt,
            f"subtasks_with_drones = {subtasks_with_drones}\n\ntravel_times = {travel_times}",
        )
        schedule_str = LM(model=model, messages=scheduler_message)
        schedule = str_to_code(schedule_str)
    print(f"\n\nScheduled task:")
    pprint(schedule, sort_dicts=False)
    return schedule


# =============================================================================
# Subtask / schedule helpers
# =============================================================================
def remove_drone_from_subtask(subtasks, task, drone):
    for subtask in subtasks:
        if subtask["name"] == task["name"] and drone in subtask["drones"]:
            subtask["drones"].remove(drone)


def remove_drone_from_all_subtasks(subtasks, drone):
    for subtask in subtasks:
        if drone in subtask["drones"]:
            subtask["drones"].remove(drone)


def remove_subtask_from_allocated(subtasks_with_drones, task):
    subtasks_with_drones[:] = [
        t for t in subtasks_with_drones
        if t["name"] != task["name"]
    ]


def remove_subtask_from_schedule(schedule, task):
    """Remove a subtask from all drone schedules."""
    for drone, tasks in schedule.items():
        schedule[drone] = [t for t in tasks if t["name"] != task["name"]]


def update_drone_pos(drones_dict, drone, objects_dict, task):
    drones_dict[drone]["pos"] = objects_dict[task["object"]]


# =============================================================================
# Planner-side drone state
# =============================================================================
def init_drone_status(drones_dict):
    return {
        drone: {
            "state": IDLE,
            "subtask": None,
            "available_time": 0.0,   # planner-relative time
            "waiting_ack": False,
            "proposal_id": None,
        }
        for drone in drones_dict
    }


def busy_exists(drone_status):
    return any(info["state"] == BUSY for info in drone_status.values())


def offset_travel_times(travel_times, drone_status, current_time):
    """
    Offset travel times by remaining busy time of relevant BUSY drones.
    `available_time` is stored as planner-relative time.
    """
    drone_to_object = travel_times.get("drone_to_object", {})

    for drone, info in drone_status.items():
        if info["state"] != BUSY:
            continue
        if drone not in drone_to_object:
            continue

        remaining = max(0.0, info["available_time"] - current_time)
        for obj in drone_to_object[drone]:
            drone_to_object[drone][obj] = round(
                drone_to_object[drone][obj] + remaining, 1
            )


def commit_started_task(drone_status, drone, task, current_time):
    """
    Planner marks a task as actually started after all selected drones ACK.
    """
    drone_status[drone]["state"] = BUSY
    drone_status[drone]["subtask"] = task["name"]
    drone_status[drone]["available_time"] = current_time + float(task["finish_time"]) - float(task["departure_time"])
    drone_status[drone]["waiting_ack"] = False
    drone_status[drone]["proposal_id"] = None


def clear_drone_to_idle(drone_status, drone, current_time):
    drone_status[drone]["state"] = IDLE
    drone_status[drone]["subtask"] = None
    drone_status[drone]["available_time"] = current_time
    drone_status[drone]["waiting_ack"] = False
    drone_status[drone]["proposal_id"] = None


# =============================================================================
# Runtime event handling
# =============================================================================
def reinsert_failed_task(subtasks_with_drones, task_catalog, task_name):
    if task_name not in task_catalog:
        return

    exists = any(t["name"] == task_name for t in subtasks_with_drones)
    if not exists:
        subtasks_with_drones.append(task_catalog[task_name].copy())
        print(f"[PLANNER] Reinserted failed task {task_name}")


def handle_runtime_event(event, drone_status, subtasks_with_drones, task_catalog, current_time):
    """
    Handle non-ACK runtime events.

    Returns:
        needs_replan
    """
    needs_replan = False
    event_type = event["type"]
    drone = event["drone"]

    print(f"[EVENT] {event}")
    append_event_log("logs/events.jsonl", event)

    if event_type == STATE_CHANGED:
        new_state = event["state"]
        event_proposal_id = event.get("proposal_id")

        drone_status[drone]["state"] = new_state
        drone_status[drone]["subtask"] = event.get("subtask")

        if new_state == BUSY:
            drone_status[drone]["waiting_ack"] = False

        elif new_state == IDLE:
            current_proposal_id = drone_status[drone]["proposal_id"]

            # Do not let an old cancel/idle event erase a newer pending proposal
            if (
                current_proposal_id is None
                or event_proposal_id is None
                or event_proposal_id == current_proposal_id
                or not drone_status[drone]["waiting_ack"]
            ):
                drone_status[drone]["waiting_ack"] = False
                drone_status[drone]["proposal_id"] = None
                drone_status[drone]["available_time"] = current_time
                needs_replan = False
            else:
                print(
                    f"[PLANNER] Ignoring stale IDLE/STATE_CHANGED from {drone}: "
                    f"event proposal_id={event_proposal_id}, "
                    f"expected={current_proposal_id}"
                )

    elif event_type == COMPLETED_EVENT:
        # Usually followed by STATE_CHANGED->IDLE.
        # We record state but do not force immediate replan here.
        drone_status[drone]["state"] = COMPLETED
        drone_status[drone]["subtask"] = event.get("subtask")

    elif event_type == DRONE_FAILED_EVENT:
        failed_task = event.get("subtask")
        drone_status[drone]["state"] = DRONE_FAILED
        drone_status[drone]["subtask"] = failed_task
        drone_status[drone]["available_time"] = float("inf")
        drone_status[drone]["proposal_id"] = None
        drone_status[drone]["waiting_ack"] = False

        remove_drone_from_all_subtasks(subtasks_with_drones, drone)

        if failed_task:
            reinsert_failed_task(subtasks_with_drones, task_catalog, failed_task)
            remove_drone_from_all_subtasks(subtasks_with_drones, drone)

        print(f"[PLANNER] {drone} removed from future allocation.")
        needs_replan = True

    elif event_type == REJECTED:
        task_name = event.get("subtask")

        if task_name is not None:
            reinsert_failed_task(subtasks_with_drones, task_catalog, task_name)

            for subtask in subtasks_with_drones:
                if subtask["name"] == task_name:
                    remove_drone_from_subtask(subtasks_with_drones, subtask, drone)
                    break

        clear_drone_to_idle(drone_status, drone, current_time)
        needs_replan = True

    return needs_replan


# =============================================================================
# ACK collection / dispatch
# =============================================================================
def build_assignment_round(schedule, drone_status):
    """
    Pick the first scheduled task of each IDLE drone.
    Returns:
        proposals: {drone: task}
    """
    proposals = {}
    for drone, tasks in schedule.items():
        if drone_status[drone]["state"] != IDLE:
            continue
        if not tasks:
            continue
        proposals[drone] = tasks[0]
    return proposals


def wait_for_all_acks(
    proposals,
    proposal_round_id,
    event_queue,
    command_queues,
    drone_status,
    subtasks_with_drones,
    task_catalog,
    start_time,
):
    """
    Send ASSIGN_TASK proposals and wait until every proposed drone sends ACK.
    If any drone rejects or times out, cancel ACKed proposals and force replanning.

    ACK/REJECT messages are matched by:
      - drone
      - proposal_id
      - subtask name

    Returns:
        ok, acked, needs_replan
    """
    if not proposals:
        return True, {}, False

    for drone, task in proposals.items():
        proposal_id = f"{proposal_round_id}:{drone}:{task['name']}"
        drone_status[drone]["waiting_ack"] = True
        drone_status[drone]["proposal_id"] = proposal_id

        command_queues[drone].put({
            "type": ASSIGN_TASK,
            "task": task,
            "proposal_id": proposal_id,
        })

    pending = set(proposals.keys())
    acked = {}
    rejected_any = False
    deadline = time.monotonic() + ACK_TIMEOUT_SECONDS
    needs_replan = False

    while pending and time.monotonic() < deadline:
        timeout = max(0.0, deadline - time.monotonic())

        try:
            event = event_queue.get(timeout=min(0.2, timeout))
        except queue.Empty:
            continue

        event_type = event["type"]
        drone = event.get("drone")
        event_subtask = event.get("subtask")
        event_proposal_id = event.get("proposal_id")
        event_message = event.get("message")

        if drone in pending:
            expected_task = proposals[drone]
            expected_proposal_id = drone_status[drone]["proposal_id"]

            if (
                event_type == ACK
                and event_proposal_id == expected_proposal_id
                and event_subtask == expected_task["name"]
            ):
                print(f"[PLANNER] ACK from {drone} for {event_subtask} | Reason: {event_message}")
                acked[drone] = proposals[drone]
                pending.remove(drone)
                drone_status[drone]["waiting_ack"] = False
                continue

            if (
                event_type == REJECTED
                and event_proposal_id == expected_proposal_id
                and event_subtask == expected_task["name"]
            ):
                print(f"[PLANNER] REJECT from {drone} for {expected_task['name']} | Reason: {event_message}")
                remove_drone_from_subtask(subtasks_with_drones, expected_task, drone)
                clear_drone_to_idle(drone_status, drone, planner_now(start_time))
                pending.remove(drone)
                rejected_any = True
                continue

            if (
                event_type == DRONE_FAILED_EVENT
                and event_proposal_id == expected_proposal_id
                and event_subtask == expected_task["name"]
            ):
                print(f"[PLANNER] PROPOSAL DRONE FAILURE from {drone} for {expected_task['name']} | Reason: {event_message}")

                # Mark this proposal as resolved before runtime handling
                pending.remove(drone)

                replan_from_event = handle_runtime_event(
                    event,
                    drone_status,
                    subtasks_with_drones,
                    task_catalog,
                    planner_now(start_time),
                )
                needs_replan = needs_replan or replan_from_event
                rejected_any = True
                continue

            if event_type in (ACK, REJECTED, DRONE_FAILED_EVENT):
                print(
                    f"[PLANNER] Ignoring stale {event_type} from {drone}: "
                    f"event proposal_id={event_proposal_id}, "
                    f"expected={expected_proposal_id}, subtask={event_subtask}"
                )
                continue

        # Any other runtime event should still be processed while waiting.
        replan_from_event = handle_runtime_event(
            event,
            drone_status,
            subtasks_with_drones,
            task_catalog,
            planner_now(start_time),
        )
        needs_replan = needs_replan or replan_from_event

    if pending:
        for drone in list(pending):
            task = proposals[drone]
            print(f"[PLANNER] ACK timeout from {drone} for {task['name']}")
            remove_drone_from_subtask(subtasks_with_drones, task, drone)
            clear_drone_to_idle(drone_status, drone, planner_now(start_time))
        rejected_any = True

    if rejected_any:
        for drone, task in acked.items():
            cancel_proposal_id = f"{proposal_round_id}:{drone}:{task['name']}"
            command_queues[drone].put({
                "type": CANCEL_TASK,
                "task_name": task["name"],
                "proposal_id": cancel_proposal_id,
            })
            clear_drone_to_idle(drone_status, drone, planner_now(start_time))

        return False, {}, True

    return True, acked, needs_replan


def start_acked_tasks(
    acked,
    proposal_round_id,
    command_queues,
    drone_status,
    subtasks_with_drones,
    schedule,
    drones_dict,
    objects_dict,
    start_time,
):
    """
    All selected drones ACKed. Start them and commit planner state.
    """
    for drone, task in acked.items():
        proposal_id = f"{proposal_round_id}:{drone}:{task['name']}"
        command_queues[drone].put({
            "type": START_TASK,
            "task": task,
            "proposal_id": proposal_id,
        })

        commit_started_task(drone_status, drone, task, planner_now(start_time))
        update_drone_pos(drones_dict, drone, objects_dict, task)
        remove_subtask_from_allocated(subtasks_with_drones, task)
        remove_subtask_from_schedule(schedule, task)


def dispatch_round_and_wait_for_ack(
    schedule,
    proposal_round_id,
    event_queue,
    command_queues,
    drone_status,
    subtasks_with_drones,
    task_catalog,
    drones_dict,
    objects_dict,
    start_time,
):
    """
    Propose tasks to all currently IDLE scheduled drones.
    Wait for ACK from all of them.
    - if all ACK: START_TASK for all and commit
    - otherwise: replan

    Returns:
        needs_replan
    """
    proposals = build_assignment_round(schedule, drone_status)
    if not proposals:
        return False

    ok, acked, needs_replan = wait_for_all_acks(
        proposals=proposals,
        proposal_round_id=proposal_round_id,
        event_queue=event_queue,
        command_queues=command_queues,
        drone_status=drone_status,
        subtasks_with_drones=subtasks_with_drones,
        task_catalog=task_catalog,
        start_time=start_time,
    )

    if not ok:
        return True

    start_acked_tasks(
        acked=acked,
        proposal_round_id=proposal_round_id,
        command_queues=command_queues,
        drone_status=drone_status,
        subtasks_with_drones=subtasks_with_drones,
        schedule=schedule,
        drones_dict=drones_dict,
        objects_dict=objects_dict,
        start_time=start_time,
    )
    return needs_replan


def drain_ready_events(event_queue, drone_status, subtasks_with_drones, task_catalog, start_time):
        needs_replan = False

        while True:
            try:
                event = event_queue.get_nowait()
            except queue.Empty:
                break

            event_forces_replan = handle_runtime_event(
                event,
                drone_status,
                subtasks_with_drones,
                task_catalog,
                planner_now(start_time),
            )
            needs_replan = needs_replan or event_forces_replan

        return needs_replan


# =============================================================================
# Planner loop
# =============================================================================
def planner_loop(event_queue, command_queues, model, task):
    start_time = time.monotonic()
    init_event_log("logs/events.jsonl")

    current_time = 0.0
    round_counter = itertools.count(1)

    drone_status = init_drone_status(drones)

    # --- Decomposer ---
    decomposed_task = pipeline_decomposer(
        model=model,
        task=task,
        skills=skills,
        objects=objects,
    )

    if not decomposed_task:
        print("ERROR during task decomposition.")
        for q in command_queues.values():
            q.put({"type": STOP})
        return

    # --- Allocator ---
    subtasks_with_drones = pipeline_allocator(
        model=model,
        drones=drones,
        decomposed_task=decomposed_task,
        rule_based=True
    )

    task_catalog = {subtask["name"]: subtask.copy() for subtask in subtasks_with_drones}

    if not subtasks_with_drones:
        print("ERROR during task allocation.")
        for q in command_queues.values():
            q.put({"type": STOP})
        return

    needs_replan = True
    schedule = None

    while True:
        drained_replan = drain_ready_events(
            event_queue=event_queue,
            drone_status=drone_status,
            subtasks_with_drones=subtasks_with_drones,
            task_catalog=task_catalog,
            start_time=start_time,
        )
        if drained_replan:
            needs_replan = True
        current_time = planner_now(start_time)

        if not subtasks_with_drones and not busy_exists(drone_status):
            print("All subtasks are completed.")
            for q in command_queues.values():
                q.put({"type": STOP})
            break

        if any(not subtask["drones"] for subtask in subtasks_with_drones):
            print("Stopping: at least one subtask has no drones allocated.")
            for q in command_queues.values():
                q.put({"type": STOP})
            break

        # ---------------------------------------------------------------------
        # Replan if needed
        # ---------------------------------------------------------------------
        if needs_replan:
            needs_replan = False

            if not subtasks_with_drones:
                continue

            travel_times = compute_travel_times(objects, drones, subtasks_with_drones)
            offset_travel_times(travel_times, drone_status, current_time)
            print("\n\nNew allocated tasks:")
            pprint(subtasks_with_drones, sort_dicts=False)

            schedule = pipeline_scheduler(
                model=model,
                subtasks_with_drones=subtasks_with_drones,
                travel_times=travel_times,
                rule_based=True
            )

            if not schedule:
                print("Stopping: scheduler could not produce a schedule.")
                for q in command_queues.values():
                    q.put({"type": STOP})
                break

            error, makespan = validate_schedule(
                skills,
                objects,
                drones,
                subtasks_with_drones,
                travel_times,
                schedule,
            )

            if error:
                print(error)
                for q in command_queues.values():
                    q.put({"type": STOP})
                break

            print(f"VALID SCHEDULE! Makespan: {makespan}")

        # ---------------------------------------------------------------------
        # Send proposals to all IDLE scheduled drones and wait for ACK from all
        # ---------------------------------------------------------------------
        proposal_round_id = next(round_counter)

        replan_after_dispatch = dispatch_round_and_wait_for_ack(
            schedule=schedule,
            proposal_round_id=proposal_round_id,
            event_queue=event_queue,
            command_queues=command_queues,
            drone_status=drone_status,
            subtasks_with_drones=subtasks_with_drones,
            task_catalog=task_catalog,
            drones_dict=drones,
            objects_dict=objects,
            start_time=start_time,
        )

        if replan_after_dispatch:
            needs_replan = True
            continue

        # ---------------------------------------------------------------------
        # Reactive wait for next runtime event
        # ---------------------------------------------------------------------
        try:
            event = event_queue.get(timeout=EVENT_WAIT_SECONDS)
        except queue.Empty:
            continue

        event_forces_replan = handle_runtime_event(
            event,
            drone_status,
            subtasks_with_drones,
            task_catalog,
            planner_now(start_time),
        )

        if event_forces_replan:
            needs_replan = True