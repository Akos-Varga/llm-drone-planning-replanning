from ollama import chat
import time
import random

### Probably a section here to retreive this data from actual drones/simulator

def accept_task():
    "Dummy simulation! Returns true with 75% chance."
    return random.random() < 0.80

if __name__ == '__main__':
    schema = {
        "type": "object",
        "properties": {
            "decision": {
                "type": "string",
                "enum": ["accept", "reject"]
            },
            "reason": {
                "type": "string"
            }
        },
        "required": ["decision", "reason"]
    }

    SYSTEM_PROMPT = f"""
    You are a task admission module for a drone.

    Your job is to decide whether the drone should ACCEPT or REJECT a task.

    The decision must be based on whether the drone can likely:
    1. Reach the destination
    2. Execute the assigned task safely for the requested duration

    You will receive:
    - battery_percentage (%) # 0 to 100, higher is better
    - battery_health (0 = bad, 100 = good)
    - link_quality (0 = bad, 5 = good)
    - drone_state (CONNECTING, LANDED, TAKINGOFF, HOVERING, FLYING, LANDING, EMERGENCY, DISCONNECTED)
    - distance_to_destination (m)
    - task_duration (s)

    Guidance:
    - battery_percentage below 15 is usually too low
    - battery_percentage from 15 to 35 is borderline and depends on distance and task duration
    - battery_percentage above 35 can be acceptable for short missions
    - link_quality 0 or 1 is poor and usually unsafe
    - link_quality 2 is borderline, only works for short distance missions
    - link_quality 3 to 5 is generally acceptable
    - HOVERING, FLYING, and LANDED are generally operational states
    - EMERGENCY and DISCONNECTED must be rejected

    Accept only if the drone is operational and conditions are sufficient to reach the destination and execute the task.

    Reject if:
    - drone_state prevents mission execution
    - battery or link quality is too low for the mission
    - the destination is unlikely reachable
    - the task duration is too long for the current conditions

    Return JSON only:
    {schema}
    """

    start = time.perf_counter()

    response = chat(
        model="gemma3:4b",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},

            # ACCEPT 1: strong overall conditions
            {
                "role": "user",
                "content": """
    battery_percentage: 85
    battery_health: 90
    link_quality: 4
    drone_state: HOVERING
    distance_to_destination: 6
    task_duration: 10
    """
            },
            {
                "role": "assistant",
                "content": """
    {"decision": "accept", "reason": "Battery, link quality, and drone state are sufficient, and the distance and task duration are feasible."}
    """
            },

            # REJECT 1: battery too low
            {
                "role": "user",
                "content": """
    battery_percentage: 10
    battery_health: 40
    link_quality: 4
    drone_state: HOVERING
    distance_to_destination: 20
    task_duration: 15
    """
            },
            {
                "role": "assistant",
                "content": """
    {"decision": "reject", "reason": "Battery level is too low to safely reach the destination and complete the task."}
    """
            },

            # ACCEPT 2: moderate link, short mission
            {
                "role": "user",
                "content": """
    battery_percentage: 80
    battery_health: 88
    link_quality: 2
    drone_state: FLYING
    distance_to_destination: 5
    task_duration: 20
    """
            },
            {
                "role": "assistant",
                "content": """
    {"decision": "accept", "reason": "The drone is operational, and the battery, link quality, distance, and task duration are sufficient for safe completion."}
    """
            },

            # REJECT 2: invalid state
            {
                "role": "user",
                "content": """
    battery_percentage: 90
    battery_health: 95
    link_quality: 5
    drone_state: EMERGENCY
    distance_to_destination: 5
    task_duration: 10
    """
            },
            {
                "role": "assistant",
                "content": """
    {"decision": "reject", "reason": "Drone is in an emergency state and cannot execute tasks."}
    """
            },

            # REJECT 3: duration too long for current conditions
            {
                "role": "user",
                "content": """
    battery_percentage: 55
    battery_health: 80
    link_quality: 3
    drone_state: HOVERING
    distance_to_destination: 8
    task_duration: 180
    """
            },
            {
                "role": "assistant",
                "content": """
    {"decision": "reject", "reason": "The requested task duration is too long for the current battery, link quality, and mission distance."}
    """
            },

            # ACCEPT 3: lower battery but very short mission
            {
                "role": "user",
                "content": """
    battery_percentage: 40
    battery_health: 75
    link_quality: 3
    drone_state: FLYING
    distance_to_destination: 11
    task_duration: 15
    """
            },
            {
                "role": "assistant",
                "content": """
    {"decision": "accept", "reason": "The drone is operational, and the short distance and short task duration make the mission feasible with the current battery and link quality."}
    """
            },        

            # Real query
            {
                "role": "user",
                "content": """
    battery_percentage: 38
    battery_health: 75
    link_quality: 4
    drone_state: LANDED
    distance_to_destination: 5
    task_duration: 10
    """
            }
        ],
        format=schema
    )

    end = time.perf_counter()

    print(response.message.content)
    print(f"Inference time: {end - start:.3f} seconds")