import multiprocessing as mp
from planner_process import planner_loop
import argparse
import copy

if __name__ == "__main__":
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
        "--planner-model",
        type=str,
        default="gpt-5-mini",
        help="GPT model for pipeline inference."
    )
    parser.add_argument(
        "--admission-model",
        type=str,
        default="qwen3:1.7b",
        help="Ollama model for task admission inference."
    )
    parser.add_argument(
        "--real",
        action="store_true",
        help="Run on the real drone environment instead of simulation."
    )
    parser.add_argument(
        "--vis",
        action="store_true",
        help="Create mission visualization after simulation. Only valid without --real."
    )
    parser.add_argument(
        "--rule-alloc",
        action="store_true",
        help="Rule based calculation of allocation instead of LLM."
    )
    parser.add_argument(
        "--rule-sched",
        action="store_true",
        help="Rule based schedule of allocation instead of LLM."
    )

    args = parser.parse_args()

    if args.real and args.vis:
        parser.error("--visualize can only be used in simulation mode. Do not use it with --real.")

    use_sim = not args.real
    if use_sim:
        from worlds.test_world import skills, objects, OBJECT_TO_YAW, drones, drone_names, drone_configs
        from drone_process_sim import drone_worker_sim
    else:
        from worlds.real_world import skills, objects, OBJECT_TO_YAW, drones, drone_names, drone_configs, MAX_ALTITUDE
        from drone_process import drone_worker

    runtime_drones = copy.deepcopy(drones)

    worker_target = drone_worker_sim if use_sim else drone_worker
    
    mp.set_start_method("spawn", force=True)

    event_queue = mp.Queue()
    command_queues = {name: mp.Queue() for name in drone_names}

    processes = []
    try:
        for name in drone_names:
            cfg = drone_configs[name]
            worker_kwargs = dict(
                model_name=args.admission_model,
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
            
            # Start a worker process for each drone
            p = mp.Process(
                target=worker_target,
                kwargs=worker_kwargs,
            )
            p.start()
            processes.append(p)
        
        # Start planner loop
        planner_loop(
            event_queue, 
            command_queues, 
            args.planner_model, 
            args.task, 
            skills, 
            objects, 
            runtime_drones,
            rule_based_allocation = args.rule_alloc,
            rule_based_schedule = args.rule_sched,
            )

    finally:
        for name in drone_names:
            command_queues[name].put({"type": "STOP"})

        for p in processes:
            p.join()

    if args.vis:
        from simulation import create_visualization

        create_visualization(
            mission_descr=args.task,
            drones=drones,
            objects=objects,
            event_log_path="logs/events.jsonl",
            output_video_path="logs/drone_execution.mp4",
        )