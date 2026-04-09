import random
from task_admission_llm import onboard_task_admission, Telemetry

def task_admission(t: Telemetry):
    OPERATIONAL_STATES = {"LANDED", "LANDING", "TAKINGOFF", "HOVERING", "FLYING"}

    drone_state_ok = t.drone_state in OPERATIONAL_STATES
    link_qual_ok = t.link_qual > 3

    available_time = t.max_flight * (t.bat_perc / 100) * (t.bat_health / 100)
    required_time = t.flight_dur + t.task_dur

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

    return Telemetry(
        max_flight=max_flight,
        bat_perc=bat_perc,
        bat_health=bat_health,
        link_qual=link_qual,
        drone_state=drone_state,
        flight_dur=flight_dur,
        task_dur=task_dur
    )

def test_helper(model: str, t: Telemetry, results, error_type, inference_times):
    print("======================================\n\n")
    print(f"""
        max_flight_time: {t.max_flight}
        battery_percentage: {t.bat_perc}
        battery_health: {t.bat_health}
        link_quality: {t.link_qual}
        drone_state: {t.drone_state}
        flight_duration: {t.flight_dur}
        task_duration: {t.task_dur}
        """)
    print(f"TEST CASE: {error_type}\n")
    results[error_type]['total'] += 1
    decision, reason, inference_time = onboard_task_admission(model, t)
    inference_times.append(inference_time)
    print(f"Inference time: {inference_time:.2f}")
    if not decision:
        print(f"{reason}\n\n")
        return
    if (
        (error_type == "accept" and decision == "ok") 
        or (error_type == "drone_state_err" and decision == "drone_failure")
        or (error_type == "link_qual_err" and decision == "drone_failure")
        or (error_type == "flight_time_err" and decision == "task_failure")
        ):
            results[error_type]['correct'] += 1
    print(f"{decision} | {reason}\n\n")
    

if __name__ == "__main__":
    model = "qwen3:0.6b"
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
        t = generate_values()
        drone_state_ok, link_qual_ok, flight_ok = task_admission(t)

        if not drone_state_ok and link_qual_ok and flight_ok and results['drone_state_err']['total'] < TEST_NUM:
            test_helper(model, t, results, 'drone_state_err', inference_times)
            continue

        if drone_state_ok and not link_qual_ok and flight_ok and results['link_qual_err']['total'] < TEST_NUM:
            test_helper(model, t, results, 'link_qual_err', inference_times)
            continue

        if drone_state_ok and link_qual_ok and not flight_ok and results['flight_time_err']['total'] < TEST_NUM:
            test_helper(model, t, results, 'flight_time_err', inference_times)
            continue

        if drone_state_ok and link_qual_ok and flight_ok and results['accept']['total'] < TEST_NUM:
            test_helper(model, t, results, 'accept', inference_times)

    for item, value in results.items():
        print(f"{item} total: {value['total']} correct: {value['correct']}")
        avg_inf = sum(inference_times) / len(inference_times)
    print(f"Average inference: {avg_inf:.2f}")
    max_value = max(inference_times)
    print(f"Max inference: {max_value:.2f}")
        