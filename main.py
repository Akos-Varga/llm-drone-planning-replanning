import multiprocessing as mp
from drone_process_sim import drone_worker_sim
# from drone_process_droneless import drone_worker
from planner_process import planner_loop
from worlds.test_world import drones

if __name__ == "__main__":
    mp.set_start_method("spawn", force=True)

    model = "gpt-5-mini"
    task = "For all houses, collect both RGB and thermal imagery."

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
                    cfg["max_flight_time"],                )
            )
            p.start()
            processes.append(p)

        planner_loop(event_queue, command_queues, model, task)

    finally:
        for name in drone_names:
            command_queues[name].put({"type": "STOP"})

        for p in processes:
            p.join()