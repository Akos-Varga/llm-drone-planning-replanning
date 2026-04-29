import multiprocessing as mp
from drone_process_sim import drone_worker_sim
# from drone_process import drone_worker
from planner_process import planner_loop
from worlds.test_world import skills, objects, drones, drone_names, drone_configs # CHANGE TO TEST WORLD IN LAB

model = "gpt-5-mini"
task = "Document the condition of all houses with video and inspect each rooftop,\n while measuring wind levels near the Base and Tower, in addition take an RGB image of Tower"

if __name__ == "__main__":
    mp.set_start_method("spawn", force=True)

    event_queue = mp.Queue()
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
                    cfg["max_flight_time"],
                    cfg["flight_altitude"])
            )
            p.start()
            processes.append(p)

        planner_loop(event_queue, command_queues, model, task, skills, objects, drones)

    finally:
        for name in drone_names:
            command_queues[name].put({"type": "STOP"})

        for p in processes:
            p.join()