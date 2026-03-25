import multiprocessing as mp
import random

from drone_process import drone_worker
from planner_process import planner_loop

if __name__ == "__main__":
    # random.seed(42)
    model = "gpt-5-mini"
    task = "Document the condition of all houses with video and inspect each rooftop, while measuring wind levels near the Base and Tower, in addition take an RGB image of Tower."

    event_queue = mp.Queue()

    drone_names = ["Drone1", "Drone2", "Drone3", "Drone4", "Drone5", "Drone6"]
    command_queues = {name: mp.Queue() for name in drone_names}

    processes = []
    for name in drone_names:
        p = mp.Process(
            target=drone_worker,
            args=(name, event_queue, command_queues[name]),
        )
        p.start()
        processes.append(p)

    planner_loop(event_queue, command_queues, model, task)

    for p in processes:
        p.join()