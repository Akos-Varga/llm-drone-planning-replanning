import multiprocessing as mp
from drone_process_sim import drone_worker_sim
# from drone_process_droneless import drone_worker
from planner_process import planner_loop

if __name__ == "__main__":
    mp.set_start_method("spawn", force=True)

    # --- WARM-UP HERE ---
    # from onboard_llm.task_admission_llm import onboard_task_admission, Telemetry

    # warm_t = Telemetry(
    #     max_flight=25.0,
    #     bat_perc=100.0,
    #     bat_health=100.0,
    #     link_qual=5,
    #     drone_state="LANDED",
    #     flight_dur=1.0,
    #     task_dur=1.0,
    # )

    # print("Warming admission model...", flush=True)
    # _ = onboard_task_admission(model="qwen3:1.7b", t=warm_t)
    # print("Admission model warm.", flush=True)
    # --- END WARM-UP ---

    model = "gpt-5-mini"
    task = "Inspect RoofTop1 and measure wind conditions at RoofTop2."

    event_queue = mp.Queue()

    drone_names = ["Drone1", "Drone2", "Drone3", "Drone4", "Drone5", "Drone6"]

    drone_configs = {
        "Drone1": {"namespace": "anafi", "max_flight_time": 25.0},
        "Drone2": {"namespace": "anafi", "max_flight_time": 22.0},
        "Drone3": {"namespace": "anafi", "max_flight_time": 18.0},
        "Drone4": {"namespace": "anafi", "max_flight_time": 30.0},
        "Drone5": {"namespace": "anafi", "max_flight_time": 20.0},
        "Drone6": {"namespace": "anafi", "max_flight_time": 27.0},
    }

    command_queues = {name: mp.Queue() for name in drone_names}

    processes = []
    try:
        for name in drone_names:
            cfg = drone_configs[name]
            p = mp.Process(
                target=drone_worker_sim,
                # target=drone_worker,
                args=(
                    name,
                    cfg["namespace"],
                    event_queue,
                    command_queues[name],
                    cfg["max_flight_time"]
                )
            )
            p.start()
            processes.append(p)

        planner_loop(event_queue, command_queues, model, task)

    finally:
        for name in drone_names:
            command_queues[name].put({"type": "STOP"})

        for p in processes:
            p.join()