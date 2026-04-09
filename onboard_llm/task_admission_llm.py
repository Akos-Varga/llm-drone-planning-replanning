from ollama import chat
import time
import json

def parse_llm_response(response_json):
    try:
        if not response_json:
            return False, "LLM response was empty.", True
        data = json.loads(response_json)
        return data["decision"] == "accept", data["reason"], False
    except json.JSONDecodeError as e:
        return False, f"Invalid JSON from LLM: {e}. Raw response: {response_json!r}", True
    except Exception as e:
         return False, f"Unexpected error while parsing LLM response: {e}", True

def get_resp(model, max_flight, bat_perc, bat_health, link_qual, drone_state, flight_dur, task_dur):
    """Decides using LLM if the task should be accepted or rejected by the drone."""
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

    Your job is to decide whether the drone should ACCEPT or REJECT a task. Use only the policy below.

    You will receive:
    - max_flight_time: maximum time the drone can spend in the air with full battery percentage and health, in minutes
    - battery_percentage: current battery level in percent (0 to 100)
    - battery_health: battery condition in percent (0 to 100)
    - link_quality: radio/link quality from 0 to 5 (0 - worst, 5 - best)
    - drone_state: one of CONNECTING, LANDED, TAKINGOFF, HOVERING, FLYING, LANDING, EMERGENCY, DISCONNECTED
    - flight_duration: flight time needed to reach the destination, in minutes
    - task_duration: task execution time at the destination, in minutes

    Policy:
    1. Reject if drone_state is CONNECTING, EMERGENCY, or DISCONNECTED.
    2. Reject if link_quality <= 3.
    3. Compute available_flight_time = max_flight_time * (battery_percentage / 100) * (battery_health / 100).
    4. Compute required_mission_time = flight_duration + task_duration.
    5. Reject if available_flight_time < required_mission_time.
    6. If none of the rejection rules apply, accept the task.

    Return JSON only:
    {schema}

    The reason must be short and refer only to the triggered rule or say that no rejection rule was triggered.
    """

    start = time.perf_counter()

    response = chat(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            # Real query
            {
                "role": "user",
                "content": f"""
                max_flight_time: {max_flight}
                battery_percentage: {bat_perc}
                battery_health: {bat_health}
                link_quality: {link_qual}
                drone_state: {drone_state}
                flight_duration: {flight_dur}
                task_duration: {task_dur}
                """
            }
        ],
        format=schema
    )

    end = time.perf_counter()
    resp = response.message.content

    return resp, end - start

def onboard_task_admission(model, max_flight, bat_perc, bat_health, link_qual, drone_state, flight_dur, task_dur):
    response, inference_time = get_resp(model, max_flight, bat_perc, bat_health, link_qual, drone_state, flight_dur, task_dur)
    decision, reason, error = parse_llm_response(response)
    return decision, reason, error, inference_time
