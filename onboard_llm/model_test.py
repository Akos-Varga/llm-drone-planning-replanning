import random
from task_admission import drone_pipeline, parse_llm_response

def accept_task():
    "Dummy simulation! Returns true with x% chance."
    return random.random() < 0.80

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
    random.seed(21)
    results = {
        "accept": {"correct": 0, "total": 0},
        "drone_state_err": {"correct": 0, "total": 0},
        "link_qual_err": {"correct": 0, "total": 0},
        "flight_time_err": {"correct": 0, "total": 0},
    }
    for i in range(50):
        print("======================================\n\n")
        max_flight, bat_perc, bat_health, link_qual, drone_state, flight_dur, task_dur = generate_values()
        print(f"""
            max_flight_time: {max_flight}
            battery_percentage: {bat_perc}
            battery_health: {bat_health}
            link_quality: {link_qual}
            drone_state: {drone_state}
            flight_duration: {flight_dur}
            task_duration: {task_dur}
            """)
        drone_state_ok, link_qual_ok, flight_ok = task_admission(max_flight, bat_perc, bat_health, link_qual, drone_state, flight_dur, task_dur)
        llm_response = drone_pipeline(max_flight, bat_perc, bat_health, link_qual, drone_state, flight_dur, task_dur)
        accept, reason, error = parse_llm_response(llm_response)
        if error:
            print(f"{reason}\n\n")
        if not drone_state_ok:
            print("DRONE STATE ERROR\n\n")
            results["drone_state_err"]["total"] += 1
            if not accept and not error:
                results["drone_state_err"]["correct"] += 1
            continue
        if not link_qual_ok:
            print("LINK QUALITY ERRROR\n\n")
            results["link_qual_err"]["total"] += 1
            if not accept and not error:
                results["link_qual_err"]["correct"] += 1
            continue
        if not flight_ok:
            print("FLIGHT TIME ERROR\n\n")
            results["flight_time_err"]["total"] += 1
            if not accept and not error:
                results["flight_time_err"]["correct"] += 1
            continue
        print("EXECUTABLE MISSION\n\n")
        results["accept"]["total"] += 1
        if accept and not error:
            results["accept"]["correct"] += 1

    for item, value in results.items():
        print(f"{item} total: {value["total"]} correct: {value["correct"]}")
        