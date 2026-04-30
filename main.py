import multiprocessing as mp
from drone_process_sim import drone_worker_sim
from drone_process import drone_worker
from planner_process import planner_loop
# WindTurbine1, WindTurbine2, House1, Tower
# Record video of both wind turbines, take thermal image of House1 and measure wind at the Tower.
# Capture thermal and RGB image of the of the Tower, document the condition of WindTurbine1 with video and take an RGB image of House1.
model = "gpt-5-mini"
task = "Record video of both wind turbines, take thermal image of House1 and measure wind at the Tower."

if __name__ == "__main__":
    USE_SIM = True # Adjust

    if USE_SIM:
        from worlds.test_world import skills, objects, OBJECT_TO_YAW, drones, drone_names, drone_configs
    else:
        from worlds.real_world import skills, objects, OBJECT_TO_YAW, drones, drone_names, drone_configs, MAX_ALTITUDE

    worker_target = drone_worker_sim if USE_SIM else drone_worker
    
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

            if not USE_SIM:
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

        planner_loop(event_queue, command_queues, model, task, skills, objects, drones)

    finally:
        for name in drone_names:
            command_queues[name].put({"type": "STOP"})

        for p in processes:
            p.join()