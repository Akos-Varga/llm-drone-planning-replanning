import multiprocessing as mp
from drone_process import drone_worker
from planner_process import planner_loop

if __name__ == "__main__":
    mp.set_start_method("spawn", force=True)

    model = "gpt-5-mini"
    task = (
        "Document the condition of all houses with video and inspect each rooftop, "
        "while measuring wind levels near the Base and Tower, in addition take an RGB image of Tower."
    )

    event_queue = mp.Queue()

    drone_names = ["Drone1", "Drone2", "Drone3", "Drone4", "Drone5", "Drone6"]
    drone_namespaces = {
        "Drone1": "anafi",
        "Drone2": "anafi",
        "Drone3": "anafi",
        "Drone4": "anafi",
        "Drone5": "anafi",
        "Drone6": "anafi",
    }

    command_queues = {name: mp.Queue() for name in drone_names}

    processes = []
    try:
        for name in drone_names:
            p = mp.Process(
                target=drone_worker,
                args=(
                    name,
                    drone_namespaces[name],
                    event_queue,
                    command_queues[name],
                ),
                kwargs={
                    "max_flight_time": 25.0,
                }
            )
            p.start()
            processes.append(p)

        planner_loop(event_queue, command_queues, model, task)

    finally:
        for name in drone_names:
            command_queues[name].put({"type": "STOP"})

        for p in processes:
            p.join()