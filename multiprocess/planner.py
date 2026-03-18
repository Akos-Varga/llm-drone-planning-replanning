import ast
import csv
import os

# --- Imports ---
from worlds.test_world import skills, objects, drones
from pipeline.decomposer import messages as decomposer_prompt
from pipeline.allocator import messages as allocator_prompt
from pipeline.scheduler import messages as scheduler_prompt

from pipeline.utils.travel_time import compute_travel_times
from pipeline.utils.schedule_validator import validate_schedule
from pipeline.utils.inference import LM

from onboard_llm.task_admission import accept_task

import queue

from common import IDLE, BUSY, COMPLETED, DRONE_FAILED, TASK_FAILED


# Message builder --------------------------------------------------------------------------
def build_message(prompt, content):
     return [*prompt, {'role': 'user', 'content': content}]

# Helpers  ---------------------------------------------------------------------------------
def str_to_code(s):
    try:
      s = s.strip()
      if s.endswith('```'):
          s = s[:s.rfind('```')].strip()
      rhs = s.split('=',1)[1]
      rhs = '\n'.join(line.split('#', 1)[0] for line in rhs.splitlines())
      return ast.literal_eval(rhs)
    except (SyntaxError, ValueError):
        return None
    
def append_row_csv(save, path, row, fieldnames):
    if save:
        os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
        write_header = not os.path.exists(path)
        with open(path, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            if write_header: 
                writer.writeheader()
            writer.writerow(row)
    
# Pipeline --------------------------------------------------------------------------------
def pipeline_decomposer(model, task, skills, objects):
    """Returns decomposed task."""
    decomposer_message = build_message(decomposer_prompt, f'task = {task}\n\nskills = {skills}\n\nobjects = {objects}')
    decomposed_task_str = LM(model=model, messages=decomposer_message)
    print(f'\n\nDecomposed task: {decomposed_task_str}')
    return str_to_code(decomposed_task_str)

def pipeline_allocator(model, drones, decomposed_task):
    """Returns allocated task."""
    allocator_message = build_message(allocator_prompt, f'drones = {drones}\n\nsubtasks = {decomposed_task}')
    subtasks_with_drones_str = LM(model=model, messages=allocator_message)
    print(f'\n\nAllocated task: {subtasks_with_drones_str}')
    return str_to_code(subtasks_with_drones_str)

def pipeline_scheduler(model, subtasks_with_drones, travel_times):
    """Returns scheduled task."""
    scheduler_message = build_message(scheduler_prompt, f'subtasks_with_drones = {subtasks_with_drones}\n\ntravel_times = {travel_times}')
    schedule_str = LM(model=model, messages=scheduler_message)
    print(f'\n\nScheduled task: {schedule_str}')
    return str_to_code(schedule_str)

# Drone simulator functions ----------------------------------------------------------------
def remove_drone_from_subtask(subtasks, task, drone):
    for subtask in subtasks:
        if subtask["name"] == task["name"]:
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
        schedule[drone] = [
            t for t in tasks if t["name"] != task["name"]
        ]

def offset_travel_times(travel_times, drone_status):
    """Offset `travel_times["drone_to_object"]` with remaining busy time for relevant busy drones only."""
    drone_to_object = travel_times.get("drone_to_object", {})

    for drone, info in drone_status.items():
        if not info["busy"]:
            continue

        if drone not in drone_to_object:
            continue

        for obj in drone_to_object[drone]:
            drone_to_object[drone][obj] = round(
                drone_to_object[drone][obj] + info["available_time"], 1
            )

def next_event_time(drone_status):
    """Returns next time a drone is available."""
    busy_times = [
        info["available_time"]
        for info in drone_status.values()
        if info["busy"]
    ]
    return min(busy_times) if busy_times else None

def assign_mission(drone_status, drone, subtask):
    """Sets params in `drone_status`."""
    drone_status[drone]["busy"] = True
    drone_status[drone]["subtask"] = subtask["name"]
    drone_status[drone]["available_time"] = subtask["finish_time"]

def update_finished_drones(drone_status, current_time):
    for drone, info in drone_status.items():
        if info["busy"] and info["available_time"] <= current_time:
            print(f'{drone} completed {info["subtask"]} at t={current_time:.1f}')
            info["busy"] = False
            info["subtask"] = None

def drone_status_reset(drone_status, current_time):
    """Sets `available_time` to 0 for idle drones and to `available_time - current_time` for busy drones."""
    for info in drone_status.values():
        if info["busy"]:
            info["available_time"] -= current_time
        else:
            info["available_time"] = 0

def update_drone_pos(drones, drone, objects, task):
    drones[drone]["pos"] = objects[task["object"]]

def assign_idle_drones(schedule, drone_status, subtasks_with_drones):
    accepted = []
    rejected_any = False

    for drone, tasks in schedule.items():
        if drone_status[drone]["busy"] or not tasks:
            continue

        first_task = tasks[0]

        if accept_task():
            print(f'{drone} accepted {first_task["name"]}')
            accepted.append((drone, first_task))
        else:
            print(f'{drone} rejected {first_task["name"]}')
            remove_drone_from_subtask(subtasks_with_drones, first_task, drone)
            rejected_any = True

    if rejected_any:
        return True

    for drone, first_task in accepted:
        assign_mission(drone_status, drone, first_task)
        update_drone_pos(drones, drone, objects, first_task)
        remove_subtask_from_allocated(subtasks_with_drones, first_task)
        remove_subtask_from_schedule(schedule, first_task)

    return False

# Inference --------------------------------------------------------------------------------
model = "gpt-5-mini"
task =  "Record videos of all solar panels, capture an RGB and thermal image of House1, and inspect the Tower."

current_time = 0.0 # For simulation only

def planner_loop(event_queue, command_queues):

    drone_status = {
        drone: {"state": IDLE, "subtask": None}
        for drone in command_queues
    }
    
    #Decomposer
    decomposed_task = pipeline_decomposer(model=model, task=task, skills=skills, objects=objects)

    # Allocator
    if decomposed_task:
        subtasks_with_drones = pipeline_allocator(model=model, drones=drones, decomposed_task=decomposed_task)
        if subtasks_with_drones:
            needs_replan = True
            while True:
                if not subtasks_with_drones and not any(info["busy"] for info in drone_status.values()):
                    print("All subtasks are completed.")
                    break

                if any(not subtask["drones"] for subtask in subtasks_with_drones):
                    print("Stopping: at least one subtask has no drones allocated.")
                    break

                # Scheduler
                if needs_replan:
                    needs_replan = False
                    drone_status_reset(drone_status, current_time)
                    travel_times = compute_travel_times(objects, drones, subtasks_with_drones)
                    offset_travel_times(travel_times, drone_status)
                    schedule = pipeline_scheduler(model=model, subtasks_with_drones=subtasks_with_drones, travel_times=travel_times)
                    error, makespan = validate_schedule(skills, objects, drones, subtasks_with_drones, travel_times, schedule)
                    if error:
                        print(error)
                        break
                    print(f"VALID SCHEDULE! Makespan: {makespan}")

                    if not schedule:
                        print("Stopping: scheduler could not produce a schedule.")
                        break

                rejected_any = assign_idle_drones(schedule, drone_status, subtasks_with_drones)

                if rejected_any:
                    needs_replan = True
                    continue # Create new schedule if an idle drone has rejected a task

                next_time = next_event_time(drone_status)

                if next_time is None:
                    print("No busy drones and no further assignments possible.")
                    break

                current_time = next_time

                update_finished_drones(drone_status, current_time)
        
        else:
            print("ERROR during task allocation.")
    else:
        print("ERROR during task decomposition.")
