import multiprocessing as mp
from planner_process import planner_loop
import argparse

parser = argparse.ArgumentParser(
    description="Run a drone mission",
    formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument(
    "--task", 
    type=str, 
    default="Record video of both wind turbines, take thermal image of House1 and measure wind at the Tower.", 
    help="Task to execute."
    )
parser.add_argument(
    "--real",
    action="store_true",
    help="Run on the real drone environment instead of simulation."
)
parser.add_argument(
    "--rule_based_allocation",
    action="store_true",
    help="Rule based calculation of allocation instead of LLM."
)

parser.add_argument(
    "--rule_based_schedule",
    action="store_true",
    help="Rule based schedule of allocation instead of LLM."
)

args = parser.parse_args()

model = "gpt-5-mini"
task = args.task
use_sim = not args.real
rule_based_allocation = args.rule_based_allocation
rule_based_schedule = args.rule_based_schedule

if __name__ == "__main__":
    if use_sim:
        from worlds.test_world import skills, objects, OBJECT_TO_YAW, drones, drone_names, drone_configs
        from drone_process_sim import drone_worker_sim
    else:
        from worlds.real_world import skills, objects, OBJECT_TO_YAW, drones, drone_names, drone_configs, MAX_ALTITUDE
        from drone_process import drone_worker

    worker_target = drone_worker_sim if use_sim else drone_worker
    
    mp.set_start_method("spawn", force=True)

    event_queue = mp.Queue()
    command_queues = {name: mp.Queue() for name in drone_names}

    processes = []
    try:
        for name in drone_names:
            cfg = drone_configs[name]
            worker_kwargs = dict(
                drone_name=name,
                namespace=cfg["namespace"],
                event_queue=event_queue,
                command_queue=command_queues[name],
                max_flight_time=cfg["max_flight_time"],
                objects=objects,
                object_to_yaw=OBJECT_TO_YAW,
            )

            if not use_sim:
                worker_kwargs.update(
                    flight_altitude=cfg["flight_altitude"],
                    speed=drones[name]["speed"],
                    max_altitude=MAX_ALTITUDE,
                )

            p = mp.Process(
                target=worker_target,
                kwargs=worker_kwargs,
            )
            p.start()
            processes.append(p)

        planner_loop(
            event_queue, 
            command_queues, 
            model, 
            task, 
            skills, 
            objects, 
            drones,
            rule_based_allocation = args.rule_based_allocation,
            rule_based_schedule = args.rule_based_schedule,
            )

    finally:
        for name in drone_names:
            command_queues[name].put({"type": "STOP"})

        for p in processes:
            p.join()