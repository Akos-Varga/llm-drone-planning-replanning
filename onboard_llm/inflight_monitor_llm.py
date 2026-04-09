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

def get_resp(model, max_flight, bat_perc, bat_health, link_qual, drone_state, remaining_time, moving_to_target):
    """Decides using LLM if the task should be accepted or rejected by the drone."""
    schema = {
        "type": "object",
        "properties": {
            "decision": {
                "type": "string",
                "enum": ["ok", "task_failure", "drone_failure"]
            },
            "reason": {
                "type": "string"
            }
        },
        "required": ["decision", "reason"]
    }

    SYSTEM_PROMPT = f"""
    You are an onboard runtime monitoring module for a drone.

    Your job is to classify the current situation of the drone into one of:
    - ok
    - task_failure
    - drone_failure

    Use only the policy below.

    You will receive:
    - max_flight_time: maximum time the drone can spend in the air with full battery and health, in minutes
    - battery_percentage: current battery level in percent (0 to 100)
    - battery_health: battery condition in percent (0 to 100)
    - link_quality: radio/link quality from 0 to 5 (0 - worst, 5 - best)
    - drone_state: one of CONNECTING, LANDED, TAKINGOFF, HOVERING, FLYING, LANDING, EMERGENCY, DISCONNECTED
    - remaining_flight_time: estimated remaining flight time, in minutes
    - moving_toward_target: boolean (True/False)

    Policy:

    1. Output "drone_failure" if:
    - drone_state is CONNECTING, EMERGENCY, or DISCONNECTED
    - link_quality <= 1
    - battery_percentage <= 5
    - battery_health <= 20

    2. Compute available_flight_time = max_flight_time * (battery_percentage / 100) * (battery_health / 100)

    3. Output "task_failure" if:
    - available_flight_time < remaining_task_time
    - moving_toward_target is False

    4. Output "ok" if none of the above conditions apply.

    Return JSON only:
    {schema}

    The reason must be short and refer only to the triggered rule or say that no rule was triggered.
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
                remaining_flight_time: {remaining_time}
                moving_toward_target: {moving_to_target}
                """
            }
        ],
        format=schema
    )

    end = time.perf_counter()
    resp = response.message.content

    return resp, end - start

def onboard_inflight_monitor(model, max_flight, bat_perc, bat_health, link_qual, drone_state, flight_dur, task_dur):
    response, inference_time = get_resp(model, max_flight, bat_perc, bat_health, link_qual, drone_state, flight_dur, task_dur)
    decision, reason, error = parse_llm_response(response)
    return decision, reason, error, inference_time
