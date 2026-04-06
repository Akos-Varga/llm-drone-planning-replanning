import random
from onboard_inference import onboard_LLM

def task_admission(max_flight, bat_perc, bat_health, link_qual, drone_state, flight_dur, task_dur):
    OPERATIONAL_STATES = {"LANDED", "LANDING", "TAKINGOFF", "HOVERING", "FLYING"}

    drone_state_ok = drone_state in OPERATIONAL_STATES
    link_qual_ok = link_qual > 3

    available_time = max_flight * (bat_perc / 100) * (bat_health / 100)
    required_time = flight_dur + task_dur

    SAFETY_MARGIN = 1.0 
    flight_ok = available_time * SAFETY_MARGIN >= required_time

    return drone_state_ok, link_qual_ok, flight_ok

def generate_values():
    operational_states = ["LANDED", "LANDING", "TAKINGOFF", "HOVERING", "FLYING"]
    all_states = ["EMERGENCY", "DISCONNECTED", "CONNECTING"] + operational_states

    # Bias toward operational states
    drone_state = random.choices(
        all_states,
        weights=[1, 1, 1, 4, 4, 4, 4, 4],
        k=1
    )[0]

    max_flight = random.randint(20, 30)

    bat_perc = int(random.triangular(50, 100, 60))
    bat_health = int(random.triangular(60, 100, 60))

    link_qual = random.choices(
        [0, 1, 2, 3, 4, 5],
        weights=[1, 1, 1, 3, 10, 10],
        k=1
    )[0]

    # Bias toward shorter missions
    flight_dur = int(random.triangular(1, 10, 8))
    task_dur = int(random.triangular(1, 10, 8))

    return max_flight, bat_perc, bat_health, link_qual, drone_state, flight_dur, task_dur


if __name__ == "__main__":
    model = "qwen3:4b"
    inference_times = []
    TEST_NUM = 20
    random.seed(21)
    results = {
        "accept": {"correct": 0, "total": 0},
        "drone_state_err": {"correct": 0, "total": 0},
        "link_qual_err": {"correct": 0, "total": 0},
        "flight_time_err": {"correct": 0, "total": 0},
    }
    while (results['drone_state_err']['total'] < TEST_NUM 
           or results['link_qual_err']['total'] < TEST_NUM 
           or results['flight_time_err']['total'] < TEST_NUM 
           or results['accept']['total'] < TEST_NUM
           ):
        max_flight, bat_perc, bat_health, link_qual, drone_state, flight_dur, task_dur = generate_values()
        drone_state_ok, link_qual_ok, flight_ok = task_admission(max_flight, bat_perc, bat_health, link_qual, drone_state, flight_dur, task_dur)

        if not drone_state_ok and link_qual_ok and flight_ok and results['drone_state_err']['total'] < TEST_NUM:
            print("======================================\n\n")
            print(f"""
                max_flight_time: {max_flight}
                battery_percentage: {bat_perc}
                battery_health: {bat_health}
                link_quality: {link_qual}
                drone_state: {drone_state}
                flight_duration: {flight_dur}
                task_duration: {task_dur}
                """)
            print("DRONE STATE ERROR\n\n")
            results['drone_state_err']['total'] += 1
            accept, reason, error, inference_time = onboard_LLM(model, max_flight, bat_perc, bat_health, link_qual, drone_state, flight_dur, task_dur)
            inference_times.append(inference_time)
            print(f"Inference time: {inference_time:.2f}")
            print(f"{reason}\n\n")
            if not accept and not error:
                results['drone_state_err']['correct'] += 1
            continue

        if drone_state_ok and not link_qual_ok and flight_ok and results['link_qual_err']['total'] < TEST_NUM:
            print("======================================\n\n")
            print(f"""
                max_flight_time: {max_flight}
                battery_percentage: {bat_perc}
                battery_health: {bat_health}
                link_quality: {link_qual}
                drone_state: {drone_state}
                flight_duration: {flight_dur}
                task_duration: {task_dur}
                """)
            print("LINK QUALITY ERRROR\n\n")
            results['link_qual_err']['total'] += 1
            accept, reason, error, inference_time = onboard_LLM(model, max_flight, bat_perc, bat_health, link_qual, drone_state, flight_dur, task_dur)
            inference_times.append(inference_time)
            print(f"Inference time: {inference_time:.2f}")
            print(f"{reason}\n\n")
            if not accept and not error:
                results['link_qual_err']['correct'] += 1
            continue

        if drone_state_ok and link_qual_ok and not flight_ok and results['flight_time_err']['total'] < TEST_NUM:
            print("======================================\n\n")
            print(f"""
                max_flight_time: {max_flight}
                battery_percentage: {bat_perc}
                battery_health: {bat_health}
                link_quality: {link_qual}
                drone_state: {drone_state}
                flight_duration: {flight_dur}
                task_duration: {task_dur}
                """)
            print("FLIGHT TIME ERROR\n\n")
            results['flight_time_err']['total'] += 1
            accept, reason, error, inference_time = onboard_LLM(model, max_flight, bat_perc, bat_health, link_qual, drone_state, flight_dur, task_dur)
            inference_times.append(inference_time)
            print(f"Inference time: {inference_time:.2f}")
            print(f"{reason}\n\n")
            if not accept and not error:
                results['flight_time_err']['correct'] += 1
            continue

        if drone_state_ok and link_qual_ok and flight_ok and results['accept']['total'] < TEST_NUM:
            print("======================================\n\n")
            print(f"""
                max_flight_time: {max_flight}
                battery_percentage: {bat_perc}
                battery_health: {bat_health}
                link_quality: {link_qual}
                drone_state: {drone_state}
                flight_duration: {flight_dur}
                task_duration: {task_dur}
                """)
            print("EXECUTABLE MISSION\n\n")
            results['accept']['total'] += 1
            accept, reason, error, inference_time = onboard_LLM(model, max_flight, bat_perc, bat_health, link_qual, drone_state, flight_dur, task_dur)
            inference_times.append(inference_time)
            print(f"Inference time: {inference_time:.2f}")
            print(f"{reason}\n\n")
            if accept and not error:
                results['accept']['correct'] += 1

    for item, value in results.items():
        print(f"{item} total: {value['total']} correct: {value['correct']}")
        avg_inf = sum(inference_times) / len(inference_times)
    print(f"Average inference: {avg_inf:.2f}")
    max_value = max(inference_times)
    print(f"Max inference: {max_value:.2f}")
        