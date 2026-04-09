from ollama import chat
import time
import json
from dataclasses import dataclass

@dataclass
class Telemetry:
    max_flight: int
    bat_perc: int
    bat_health: int
    link_qual: int
    drone_state: str
    flight_dur: int
    task_dur: int


def old_parse_llm_response(response_json):
    try:
        if not response_json:
            return False, "LLM response was empty.", True
        data = json.loads(response_json)
        return data["decision"] == "accept", data["reason"], False
    except json.JSONDecodeError as e:
        return False, f"Invalid JSON from LLM: {e}. Raw response: {response_json!r}", True
    except Exception as e:
         return False, f"Unexpected error while parsing LLM response: {e}", True
    
def parse_llm_response(response_json):
    try:
        if not response_json:
            return None, "LLM response was empty."
        data = json.loads(response_json)
        return data["decision"], data["reason"]
    except json.JSONDecodeError as e:
        return None, f"Invalid JSON from LLM: {e}. Raw response {response_json!r}"
    except Exception as e:
        return None, f"Unexpected error while parsing LLM response: {e}"

def get_resp(model, t : Telemetry):
    """Decides using LLM if the task should be accepted or rejected by the drone."""
    schema = {
        "type": "object",
        "properties": {
            "decision": {
                "type": "string",
                "enum": ["ok", "drone_failure", "task_failure"]
            },
            "reason": {
                "type": "string"
            }
        },
        "required": ["decision", "reason"]
    }

    SYSTEM_PROMPT = f"""
    You are a task admission module for a drone.

    Your job is to evaluate whether a task can be executed and classify the outcome into one of three categories:
    - ok: the task can be accepted
    - drone_failure: the drone is not in a suitable condition to execute the task
    - task_failure: the task requirements exceed the drone’s capabilities

    You will receive:
    - max_flight_time: maximum time the drone can fly with 100% battery and health, in minutes
    - battery_percentage: current battery level (0–100)
    - battery_health: battery condition (0–100)
    - link_quality: radio/link quality from 0 to 5 (higher is better)
    - drone_state: one of CONNECTING, LANDED, TAKINGOFF, HOVERING, FLYING, LANDING, EMERGENCY, DISCONNECTED
    - flight_duration: time to reach the destination, in minutes
    - task_duration: time to execute the task, in minutes

    Use only the policy below.

    Policy:
    1. Reject with drone_failure if drone_state is CONNECTING, EMERGENCY, or DISCONNECTED.
    2. Reject with drone_failure if link_quality <= 3.
    3. Compute available_flight_time = max_flight_time * (battery_percentage / 100) * (battery_health / 100).
    4. Compute required_mission_time = flight_duration + task_duration.
    5. Reject with task_failure if available_flight_time < required_mission_time.
    6. Otherwise return ok.

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
                max_flight_time: {t.max_flight}
                battery_percentage: {t.bat_perc}
                battery_health: {t.bat_health}
                link_quality: {t.link_qual}
                drone_state: {t.drone_state}
                flight_duration: {t.flight_dur}
                task_duration: {t.task_dur}
                """
            }
        ],
        options={
        "temperature": 0.0,
        "top_p": 1.0,
        "top_k": 1
        },
        format=schema,
    )

    end = time.perf_counter()
    resp = response.message.content

    return resp, end - start

def old_onboard_task_admission(model, t: Telemetry):
    response, inference_time = get_resp(model, t)
    decision, reason, error = parse_llm_response(response)
    return decision, reason, error, inference_time

def onboard_task_admission(model, t: Telemetry):
    response, inference_time = get_resp(model, t)
    decision, reason = parse_llm_response(response)
    return decision, reason, inference_time


    # - LANDED, TAKINGOFF, HOVERING, FLYING, and LANDING are normal operational states.


    # SYSTEM_PROMPT = f"""
    # You are a task admission module for a drone.

    # Your job is to decide whether the drone should ACCEPT or REJECT a task. Use only the policy below.

    # You will receive:
    # - max_flight_time: maximum time the drone can spend in the air with full battery percentage and health, in minutes
    # - battery_percentage: current battery level in percent (0 to 100)
    # - battery_health: battery condition in percent (0 to 100)
    # - link_quality: radio/link quality from 0 to 5 (0 - worst, 5 - best)
    # - drone_state: one of CONNECTING, LANDED, TAKINGOFF, HOVERING, FLYING, LANDING, EMERGENCY, DISCONNECTED
    # - flight_duration: flight time needed to reach the destination, in minutes
    # - task_duration: task execution time at the destination, in minutes

    # Policy:
    # 1. Reject if drone_state is CONNECTING, EMERGENCY, or DISCONNECTED.
    # 2. Reject if link_quality <= 3.
    # 3. Compute available_flight_time = max_flight_time * (battery_percentage / 100) * (battery_health / 100).
    # 4. Compute required_mission_time = flight_duration + task_duration.
    # 5. Reject if available_flight_time < required_mission_time.
    # 6. If none of the rejection rules apply, accept the task.

    # Return JSON only:
    # {schema}

    # The reason must be short and refer only to the triggered rule or say that no rejection rule was triggered.
    # """



# You are a task admission module for a drone. Your job is to decide whether the drone should ACCEPT or REJECT a task. 
# You will receive:
#  - max_flight_time: maximum time the drone can fly with 100% battery and health, in minutes
#  - battery_percentage: current battery level (0–100)
#  - battery_health: battery condition (0–100)
#  - link_quality: radio/link quality from 0 to 5 (higher is better)
#  - drone_state: one of CONNECTING, LANDED, TAKINGOFF, HOVERING, FLYING, LANDING, EMERGENCY, DISCONNECTED
#  - flight_duration: time to reach the destination, in minutes 
#   - task_duration: time to execute the task, in minutes 
# 
# Guidelines: 
# - The drone should only accept a task when it is connected and in a normal operational state. 
# - Link quality below 4 should result in rejection. 
# - The total required time is flight_duration + task_duration. 
# - The available flight time scales with both battery percentage and battery health. 
# - The task should only be accepted if the drone can complete it within the available flight time. 
# 
# Return JSON only: 
# {schema} 
# 
# The reason must be short. """



    # Guidelines:
    # - The drone must in an operational state to execute a task, otherwise it results in drone_failure.
    # - Link quality below 4 should result in drone_failure.
    # - The total required flight time is flight_duration + task_duration. 
    # - The available flight time scales with both battery percentage and battery health.
    # - If the drone cannot complete the task within the available flight time, it is a task_failure.
    # - If no issues arise, the result is ok.