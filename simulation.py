import ast
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.lines import Line2D

from worlds.test_world import drones, objects


# ------------------------------------------------------------
# 1. Paste your terminal log here
# ------------------------------------------------------------
log_text = r"""
[EVENT] {'type': 'STATE_CHANGED', 'drone': 'Drone3', 'state': 'BUSY', 'subtask': 'SubTask1', 'object': 'RoofTop1', 'proposal_id': '1:Drone3:SubTask1', 'message': 'Started SubTask1', 'time': 9329.761328529}
[EVENT] {'type': 'STATE_CHANGED', 'drone': 'Drone2', 'state': 'BUSY', 'subtask': 'SubTask7', 'object': 'SolarPanel2', 'proposal_id': '1:Drone2:SubTask7', 'message': 'Started SubTask7', 'time': 9329.764375185}
[EVENT] {'type': 'STATE_CHANGED', 'drone': 'Drone4', 'state': 'BUSY', 'subtask': 'SubTask3', 'object': 'RoofTop2', 'proposal_id': '1:Drone4:SubTask3', 'message': 'Started SubTask3', 'time': 9329.799210952}
[EVENT] {'type': 'STATE_CHANGED', 'drone': 'Drone5', 'state': 'BUSY', 'subtask': 'SubTask4', 'object': 'RoofTop2', 'proposal_id': '1:Drone5:SubTask4', 'message': 'Started SubTask4', 'time': 9329.806306629}
[EVENT] {'type': 'STATE_CHANGED', 'drone': 'Drone6', 'state': 'BUSY', 'subtask': 'SubTask5', 'object': 'Tower', 'proposal_id': '1:Drone6:SubTask5', 'message': 'Started SubTask5', 'time': 9329.810553441}
[EVENT] {'type': 'COMPLETED', 'drone': 'Drone6', 'state': 'COMPLETED', 'subtask': 'SubTask5', 'proposal_id': '1:Drone6:SubTask5', 'message': 'Completed SubTask5', 'time': 9333.524793571}
[EVENT] {'type': 'STATE_CHANGED', 'drone': 'Drone6', 'state': 'IDLE', 'subtask': None, 'proposal_id': None, 'message': 'Ready for next task', 'time': 9333.524813374}
[EVENT] {'type': 'COMPLETED', 'drone': 'Drone5', 'state': 'COMPLETED', 'subtask': 'SubTask4', 'proposal_id': '1:Drone5:SubTask4', 'message': 'Completed SubTask4', 'time': 9335.131478474}
[EVENT] {'type': 'STATE_CHANGED', 'drone': 'Drone5', 'state': 'IDLE', 'subtask': None, 'proposal_id': None, 'message': 'Ready for next task', 'time': 9335.131495334}
[EVENT] {'type': 'COMPLETED', 'drone': 'Drone3', 'state': 'COMPLETED', 'subtask': 'SubTask1', 'proposal_id': '1:Drone3:SubTask1', 'message': 'Completed SubTask1', 'time': 9335.883609184}
[EVENT] {'type': 'STATE_CHANGED', 'drone': 'Drone3', 'state': 'IDLE', 'subtask': None, 'proposal_id': None, 'message': 'Ready for next task', 'time': 9335.883626489}
[EVENT] {'type': 'STATE_CHANGED', 'drone': 'Drone6', 'state': 'BUSY', 'subtask': 'SubTask6', 'object': 'SolarPanel1', 'proposal_id': '14:Drone6:SubTask6', 'message': 'Started SubTask6', 'time': 9338.139209323}
[EVENT] {'type': 'COMPLETED', 'drone': 'Drone6', 'state': 'COMPLETED', 'subtask': 'SubTask6', 'proposal_id': '14:Drone6:SubTask6', 'message': 'Completed SubTask6', 'time': 9346.265439603}
[EVENT] {'type': 'STATE_CHANGED', 'drone': 'Drone6', 'state': 'IDLE', 'subtask': None, 'proposal_id': None, 'message': 'Ready for next task', 'time': 9346.265462268}
[EVENT] {'type': 'STATE_CHANGED', 'drone': 'Drone3', 'state': 'BUSY', 'subtask': 'SubTask2', 'object': 'RoofTop1', 'proposal_id': '15:Drone3:SubTask2', 'message': 'Started SubTask2', 'time': 9347.931303774}
[EVENT] {'type': 'DRONE_FAILED', 'drone': 'Drone2', 'state': 'DRONE_FAILED', 'subtask': 'SubTask7', 'proposal_id': '1:Drone2:SubTask7', 'message': 'Runtime drone failure: drone is in emergency state', 'time': 9348.206285909}
[EVENT] {'type': 'COMPLETED', 'drone': 'Drone4', 'state': 'COMPLETED', 'subtask': 'SubTask3', 'proposal_id': '1:Drone4:SubTask3', 'message': 'Completed SubTask3', 'time': 9348.921276836}
[EVENT] {'type': 'STATE_CHANGED', 'drone': 'Drone4', 'state': 'IDLE', 'subtask': None, 'proposal_id': None, 'message': 'Ready for next task', 'time': 9348.921291576}
[EVENT] {'type': 'COMPLETED', 'drone': 'Drone3', 'state': 'COMPLETED', 'subtask': 'SubTask2', 'proposal_id': '15:Drone3:SubTask2', 'message': 'Completed SubTask2', 'time': 9350.339689924}
[EVENT] {'type': 'STATE_CHANGED', 'drone': 'Drone3', 'state': 'IDLE', 'subtask': None, 'proposal_id': None, 'message': 'Ready for next task', 'time': 9350.339710585}
[EVENT] {'type': 'DRONE_FAILED', 'drone': 'Drone6', 'state': 'DRONE_FAILED', 'subtask': 'SubTask7', 'proposal_id': '17:Drone6:SubTask7', 'message': 'Admission drone failure: drone_state is EMERGENCY', 'time': 9350.680348874}
"""


# ------------------------------------------------------------
# 2. Convert world coordinates to 2D
# ------------------------------------------------------------
object_positions = {name: (pos[0], pos[1]) for name, pos in objects.items()}
drone_start_positions = {name: (info["pos"][0], info["pos"][1]) for name, info in drones.items()}
all_drones = sorted(drone_start_positions.keys())


# ------------------------------------------------------------
# 3. Color mapping
# ------------------------------------------------------------
state_colors = {
    "IDLE": "green",
    "BUSY": "blue",
    "DRONE_FAILED": "red",
    "TASK_FAILED": "orange",
}
default_color = "gray"


# ------------------------------------------------------------
# 4. Parse EVENT lines
# ------------------------------------------------------------
events = []
for line in log_text.splitlines():
    line = line.strip()
    if line.startswith("[EVENT]"):
        payload = line[len("[EVENT]"):].strip()
        events.append(ast.literal_eval(payload))

events.sort(key=lambda e: e["time"])

if not events:
    raise ValueError("No [EVENT] lines found in log_text.")


# ------------------------------------------------------------
# 5. Build motion segments from events
# ------------------------------------------------------------
# Each active task stores:
#   start time
#   start position
#   target object
# Then:
#   COMPLETED -> segment ends at target
#   DRONE_FAILED/TASK_FAILED -> segment ends at failure point
# ------------------------------------------------------------
active_tasks = {}
segments = []
last_position = dict(drone_start_positions)

for ev in events:
    drone = ev["drone"]
    ev_type = ev["type"]
    t = ev["time"]
    subtask = ev.get("subtask")

    # Task start
    if ev_type == "STATE_CHANGED" and ev.get("state") == "BUSY" and subtask is not None:
        obj_name = ev.get("object")
        if obj_name is None:
            continue

        active_tasks[drone] = {
            "subtask": subtask,
            "object": obj_name,
            "t0": t,
            "start": last_position[drone],
            "target": object_positions[obj_name],
        }

    # Task completed
    elif ev_type == "COMPLETED" and drone in active_tasks:
        task = active_tasks.pop(drone)

        seg = {
            "drone": drone,
            "subtask": task["subtask"],
            "object": task["object"],
            "t0": task["t0"],
            "t1": t,
            "start": task["start"],
            "end": task["target"],
            "end_reason": "COMPLETED",
        }
        segments.append(seg)
        last_position[drone] = task["target"]

    # Task or drone failure while moving/executing
    elif ev_type in ("DRONE_FAILED", "TASK_FAILED") and drone in active_tasks:
        task = active_tasks.pop(drone)

        total_dt = max(t - task["t0"], 1e-9)
        # At failure time, freeze the drone at interpolated position.
        # Since EVENT-only logs do not separate arrival and service,
        # we approximate with uniform motion from start to target.
        alpha = min(max((t - task["t0"]) / total_dt, 0.0), 1.0)

        sx, sy = task["start"]
        tx, ty = task["target"]
        fail_pos = (
            sx + alpha * (tx - sx),
            sy + alpha * (ty - sy),
        )

        seg = {
            "drone": drone,
            "subtask": task["subtask"],
            "object": task["object"],
            "t0": task["t0"],
            "t1": t,
            "start": task["start"],
            "end": fail_pos,
            "end_reason": ev_type,
        }
        segments.append(seg)
        last_position[drone] = fail_pos


# ------------------------------------------------------------
# 6. Build state timeline per drone
# ------------------------------------------------------------
drone_state_events = {drone: [] for drone in all_drones}

# default initial state
t0_global = events[0]["time"] - 1e-6
for drone in all_drones:
    drone_state_events[drone].append((t0_global, "IDLE"))

for ev in events:
    drone = ev["drone"]
    ev_type = ev["type"]
    state = ev.get("state")

    if ev_type == "STATE_CHANGED":
        if state == "BUSY":
            drone_state_events[drone].append((ev["time"], "BUSY"))
        elif state == "IDLE":
            drone_state_events[drone].append((ev["time"], "IDLE"))

    elif ev_type == "DRONE_FAILED":
        drone_state_events[drone].append((ev["time"], "DRONE_FAILED"))

    elif ev_type == "TASK_FAILED":
        drone_state_events[drone].append((ev["time"], "TASK_FAILED"))

for drone in all_drones:
    drone_state_events[drone].sort(key=lambda x: x[0])


# ------------------------------------------------------------
# 7. Position/state helpers
# ------------------------------------------------------------
def drone_state_at(drone, t):
    current = "IDLE"
    for ts, st in drone_state_events[drone]:
        if ts <= t:
            current = st
        else:
            break
    return current


def drone_position_at(drone, t):
    pos = drone_start_positions[drone]
    drone_segments = [s for s in segments if s["drone"] == drone]
    drone_segments.sort(key=lambda s: s["t0"])

    for seg in drone_segments:
        if t < seg["t0"]:
            return pos

        if seg["t0"] <= t <= seg["t1"]:
            alpha = (t - seg["t0"]) / max(seg["t1"] - seg["t0"], 1e-9)
            sx, sy = seg["start"]
            ex, ey = seg["end"]
            return (
                sx + alpha * (ex - sx),
                sy + alpha * (ey - sy),
            )

        pos = seg["end"]

    return pos


# ------------------------------------------------------------
# 8. Timeline
# ------------------------------------------------------------
t_min = min(e["time"] for e in events)
t_max = max(e["time"] for e in events)

fps = 20
timeline = np.linspace(t_min, t_max, int((t_max - t_min) * fps) + 1)


# ------------------------------------------------------------
# 9. Plot setup
# ------------------------------------------------------------
fig, ax = plt.subplots(figsize=(9, 8))

# Objects as black dots
obj_x = [xy[0] for xy in object_positions.values()]
obj_y = [xy[1] for xy in object_positions.values()]
ax.scatter(obj_x, obj_y, s=140, c="black", zorder=2)

for name, (x, y) in object_positions.items():
    ax.text(x + 1.2, y + 1.2, name, fontsize=9)

# Drone scatter
drone_scatter = ax.scatter([], [], s=140, zorder=3)

# Labels
drone_labels = {
    drone: ax.text(0, 0, drone, fontsize=9)
    for drone in all_drones
}

time_text = ax.text(
    0.02, 0.98, "",
    transform=ax.transAxes,
    va="top",
    fontsize=11
)

# Axes limits
all_x = obj_x + [xy[0] for xy in drone_start_positions.values()]
all_y = obj_y + [xy[1] for xy in drone_start_positions.values()]

margin = 8
ax.set_xlim(min(all_x) - margin, max(all_x) + margin)
ax.set_ylim(min(all_y) - margin, max(all_y) + margin)
ax.set_xlabel("X")
ax.set_ylabel("Y")
ax.set_title("2D Drone Execution from EVENT Logs")
ax.grid(True)

legend_elements = [
    Line2D([0], [0], marker='o', color='w', label='Object', markerfacecolor='black', markersize=10),
    Line2D([0], [0], marker='o', color='w', label='Idle', markerfacecolor='green', markersize=10),
    Line2D([0], [0], marker='o', color='w', label='Busy', markerfacecolor='blue', markersize=10),
    Line2D([0], [0], marker='o', color='w', label='Drone failure', markerfacecolor='red', markersize=10),
    Line2D([0], [0], marker='o', color='w', label='Task failure', markerfacecolor='orange', markersize=10),
]
ax.legend(handles=legend_elements, loc="upper right")


# ------------------------------------------------------------
# 10. Animation update
# ------------------------------------------------------------
def update(frame_idx):
    t = timeline[frame_idx]

    positions = []
    colors = []

    for drone in all_drones:
        pos = drone_position_at(drone, t)
        st = drone_state_at(drone, t)

        positions.append(pos)
        colors.append(state_colors.get(st, default_color))

    positions = np.array(positions)
    drone_scatter.set_offsets(positions)
    drone_scatter.set_color(colors)

    for i, drone in enumerate(all_drones):
        x, y = positions[i]
        drone_labels[drone].set_position((x + 0.8, y + 0.8))

    time_text.set_text(f"Time: {t - t_min:.2f} s")
    return [drone_scatter, time_text, *drone_labels.values()]


anim = FuncAnimation(
    fig,
    update,
    frames=len(timeline),
    interval=1000 / fps,
    blit=False
)

plt.show()

# Optional save:
# anim.save("drone_events_2d.mp4", fps=fps, dpi=150)
# anim.save("drone_events_2d.gif", fps=fps, dpi=120)