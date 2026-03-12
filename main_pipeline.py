import argparse
import sys
import time
import ast
import csv
import os
import matplotlib.pyplot as plt
from pprint import pprint

# --- Imports ---
from worlds.test_world import skills, objects, drones
from test_tasks import task_list

from pipeline.decomposer import messages as decomposer_prompt
from pipeline.allocator import messages as allocator_prompt
from pipeline.scheduler import messages as scheduler_prompt

from pipeline.utils.travel_time import compute_travel_times
from pipeline.utils.schedule_validator import validate_schedule
from pipeline.utils.decomposer_validator import validate_decomposer
from pipeline.utils.inference import LM
from pipeline.utils.drone_visualizer import animate_schedule
from pipeline.utils.randomizer import randomizer
from pipeline.utils.vrp_allocator import solve_vrp
from pipeline.utils.compare_schedules import schedules_equal

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

# Inference --------------------------------------------------------------------------------
def pipeline(model, task, skills, objects, drones, solution = None, calculate_vrp = None):
    ## Decomposer
    decomposer_message = build_message(decomposer_prompt, f'task = {task}\n\nskills = {skills}\n\nobjects = {objects}')
    decomposed_task_str = LM(model=model, messages=decomposer_message)
    print(f'\n\nDecomposed task: {decomposed_task_str}')
    decomposed_task = str_to_code(decomposed_task_str)
    
    if not decomposed_task: 
        return {'schedule': None, 'makespan': None, 'schedule_vrp': None, 'makespan_VRP': None, 'error': 'ERROR: decomposed_task conversion failed'}
    
    if solution:
        error = validate_decomposer(decomposed_task, solution, skills)
        if error: 
            return {'schedule': None, 'makespan': None, 'schedule_vrp': None, 'makespan_VRP': None, 'error': error}
    
    # Allocator
    allocator_message = build_message(allocator_prompt, f'drones = {drones}\n\nsubtasks = {decomposed_task}')
    subtasks_with_drones_str = LM(model=model, messages=allocator_message)
    print(f'\n\nAllocated task: {subtasks_with_drones_str}')
    subtasks_with_drones = str_to_code(subtasks_with_drones_str)
    
    if not subtasks_with_drones: 
        return {'schedule': None, 'makespan': None, 'schedule_vrp': None, 'makespan_VRP': None, 'error': 'ERROR: subtasks_with_drones conversion failed'}
    
    travel_times = compute_travel_times(objects, drones, subtasks_with_drones)

    # Scheduler
    scheduler_message = build_message(scheduler_prompt, f'subtasks_with_drones = {subtasks_with_drones_str}\n\ntravel_times = {travel_times}')
    schedule_str = LM(model=model, messages=scheduler_message)
    print(f'\n\nScheduled task: {schedule_str}')
    schedule = str_to_code(schedule_str)
    
    if not schedule: 
        return {'schedule': None, 'makespan': None, 'schedule_vrp': None, 'makespan_VRP': None, 'error': 'ERROR: schedule conversion failed'}     
    
    error, makespan = validate_schedule(skills, objects, drones, subtasks_with_drones, travel_times, schedule)
    if error: 
        return {'schedule': None, 'makespan': None, 'schedule_vrp': None, 'makespan_VRP': None, 'error': error}

    # Calculate with VRP (Vehicle Routing Problem)
    if calculate_vrp:
        schedule_vrp, makespan_vrp, status = solve_vrp(objects, drones, subtasks_with_drones)
        print('\n\nSchedule by VRP:')
        pprint(schedule_vrp, sort_dicts=False)
        print(f'\n\nSchedule is {status}')
        
        identical_schedule = schedules_equal(schedule, schedule_vrp)
        if identical_schedule: 
            print('\n\nSchedules are identical.')
        else: 
            print('\n\nSchedules are different.')
            
        print(f'\n\nMakespan:\n\tLLM: {makespan}\n\tVRP: {makespan_vrp}\n')
        
        return {'schedule': schedule, 'makespan': makespan, 'schedule_vrp': schedule_vrp, 'makespan_VRP': makespan_vrp, 'error': None}
    else:
        return {'schedule': schedule, 'makespan': makespan, 'schedule_vrp': None, 'makespan_VRP': None, 'error': None}


if __name__ == '__main__':
    # --- Parse Command Line Arguments ---
    parser = argparse.ArgumentParser(description="Run pipeline tests on tasks.")
    parser.add_argument(
        "--model", 
        type=str, 
        default="gpt-5-mini", 
        help="Model to use (default: gpt-5-mini)"
    )
    parser.add_argument(
        "--task_id", 
        type=str, 
        default=None, 
        help="Run a specific task ID (e.g., Task1). If not set, runs all tasks."
    )
    parser.add_argument(
        "--save", 
        action="store_true",
        help="Save results to CSV."
    )
    parser.add_argument(
        "--vrp", 
        action="store_true",
        help="Calculate VRP solution for comparison."
    )
    parser.add_argument(
        "--visualize", 
        action="store_true", 
        help="Generate and save a GIF animation of the schedule."
    )
    args = parser.parse_args()

    # --- Setup ---
    CSV_PATH = os.path.join('results', 'test_results.csv')
    FIELDNAMES = ['model', 'task_id', 'LLM_makespan', 'VRP_makespan', 'LLM_inference_time', 'LLM_error']

    # Filter tasks if specific ID requested
    tasks_to_run = task_list
    if args.task_id:
        tasks_to_run = [t for t in task_list if t['id'] == args.task_id]
        if not tasks_to_run:
            print(f"Error: Task ID '{args.task_id}' not found in task_list.")
            sys.exit(1)

    print(f"Running {len(tasks_to_run)} task(s) using model: {args.model}")

    # --- Execution Loop ---
    for task in tasks_to_run:
        print('='*90 + f"\n{task['id']}: {task['task']}")
        
        startTime = time.time()
        
        # Execute Pipeline
        results = pipeline(
            args.model, 
            task['task'], 
            skills, 
            objects, 
            drones, 
            solution=task.get('solution'), 
            calculate_vrp=args.vrp
        )
        
        endTime = time.time()
        inference_time = round(endTime - startTime, 1)

        # Save to CSV
        if args.save:
            row = {
                'model': args.model, 
                'task_id': task['id'], 
                'LLM_makespan': results['makespan'], 
                'VRP_makespan': results['makespan_VRP'], 
                'LLM_inference_time': inference_time, 
                'LLM_error': results['error']
            }
            append_row_csv(True, CSV_PATH, row, FIELDNAMES)
            print(f"Result saved to {CSV_PATH}")

        # Visualization
        if args.visualize and results['schedule']:
            print("Generating animation...")
            save_dir = os.path.join('results', 'animations')
            os.makedirs(save_dir, exist_ok=True)
            
            save_path = os.path.join(save_dir, f"{task['id']}.gif")
            
            animate_schedule(
                objects, 
                drones, 
                results['schedule'], 
                dt=0.1, 
                extra_hold=1.5, 
                save_path=save_path
            )
            print(f"Animation saved to {save_path}")