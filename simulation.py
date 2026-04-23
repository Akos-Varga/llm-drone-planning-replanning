import json
import re
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.lines import Line2D

from worlds.test_world import drones, objects


# ------------------------------------------------------------
# 2. World -> 2D positions
# ------------------------------------------------------------
object_positions = {name: (pos[0], pos[1]) for name, pos in objects.items()}
drone_start_positions = {name: (info["pos"][0], info["pos"][1]) for name, info in drones.items()}
all_drones = sorted(drone_start_positions.keys())


# ------------------------------------------------------------
# 3. Colors
# ------------------------------------------------------------
state_colors = {
    "IDLE": "green",
    "FLYING": "blue",
    "EXECUTING": "purple",
    "DRONE_FAILED": "red",
    "TASK_FAILED": "orange",
}
default_color = "gray"


# ------------------------------------------------------------
# 4. Parse events
# ------------------------------------------------------------
events = []
with open("logs/events.jsonl", "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        events.append(json.loads(line))

events.sort(key=lambda e: e["time"])
if not events:
    raise ValueError("No [EVENT] lines found.")


# ------------------------------------------------------------
# 5. Helper to extract object from "Arrived at X"
# ------------------------------------------------------------
def extract_arrival_object(message: str):
    m = re.search(r"Arrived at (.+)$", message)
    return m.group(1).strip() if m else None


# ------------------------------------------------------------
# 6. Build segments and task metadata
# ------------------------------------------------------------
segments = []
last_position = dict(drone_start_positions)

# Current active task per drone
active_tasks = {}
# active_tasks[drone] = {
#   "subtask": ...,
#   "object": ...,
#   "skill": None or str,
#   "start_time": ...,
#   "start_pos": ...,
#   "target_pos": ...,
#   "arrived_time": None or float,
# }

for ev in events:
    drone = ev["drone"]
    ev_type = ev["type"]
    t = ev["time"]
    subtask = ev.get("subtask")

    if ev_type == "STATE_CHANGED" and ev.get("state") == "BUSY" and subtask is not None:
        obj_name = ev.get("object")
        if obj_name is None or obj_name not in object_positions:
            continue

        active_tasks[drone] = {
            "subtask": subtask,
            "object": obj_name,
            "skill": None,
            "start_time": t,
            "start_pos": last_position[drone],
            "target_pos": object_positions[obj_name],
            "arrived_time": None,
        }

    elif ev_type == "ARRIVED" and drone in active_tasks:
        task = active_tasks[drone]

        task["arrived_time"] = t
        if ev.get("skill") is not None:
            task["skill"] = ev["skill"]

        # fallback if object was not in ARRIVED structured fields
        arrival_obj = extract_arrival_object(ev.get("message", ""))
        if arrival_obj is not None and task["object"] is None:
            task["object"] = arrival_obj

        segments.append({
            "drone": drone,
            "phase": "FLYING",
            "subtask": task["subtask"],
            "object": task["object"],
            "skill": task["skill"],
            "t0": task["start_time"],
            "t1": t,
            "start": task["start_pos"],
            "end": task["target_pos"],
        })

        last_position[drone] = task["target_pos"]

    elif ev_type == "COMPLETED" and drone in active_tasks:
        task = active_tasks.pop(drone)

        if task["arrived_time"] is not None:
            segments.append({
                "drone": drone,
                "phase": "EXECUTING",
                "subtask": task["subtask"],
                "object": task["object"],
                "skill": task["skill"],
                "t0": task["arrived_time"],
                "t1": t,
                "start": task["target_pos"],
                "end": task["target_pos"],
            })
            last_position[drone] = task["target_pos"]
        else:
            # fallback if ARRIVED is missing
            segments.append({
                "drone": drone,
                "phase": "FLYING",
                "subtask": task["subtask"],
                "object": task["object"],
                "skill": task["skill"],
                "t0": task["start_time"],
                "t1": t,
                "start": task["start_pos"],
                "end": task["target_pos"],
            })
            last_position[drone] = task["target_pos"]

    elif ev_type in ("DRONE_FAILED", "TASK_FAILED"):
        if drone in active_tasks:
            task = active_tasks.pop(drone)

            if task["arrived_time"] is not None:
                fail_pos = task["target_pos"]
                fail_start = task["target_pos"]
            else:
                # conservative approximation for pre-arrival failure
                sx, sy = task["start_pos"]
                ex, ey = task["target_pos"]
                fail_pos = ((sx + ex) / 2.0, (sy + ey) / 2.0)
                fail_start = task["start_pos"]

            segments.append({
                "drone": drone,
                "phase": ev_type,
                "subtask": task["subtask"],
                "object": task["object"],
                "skill": task["skill"],
                "t0": task["start_time"],
                "t1": t,
                "start": fail_start,
                "end": fail_pos,
            })
            last_position[drone] = fail_pos


# ------------------------------------------------------------
# 7. Visual state timeline
# ------------------------------------------------------------
drone_state_events = {drone: [] for drone in all_drones}
initial_t = events[0]["time"] - 1e-6

for drone in all_drones:
    drone_state_events[drone].append((initial_t, "IDLE"))

for ev in events:
    drone = ev["drone"]
    t = ev["time"]
    ev_type = ev["type"]

    if ev_type == "STATE_CHANGED":
        state = ev.get("state")
        if state == "BUSY":
            drone_state_events[drone].append((t, "FLYING"))
        elif state == "IDLE":
            drone_state_events[drone].append((t, "IDLE"))

    elif ev_type == "ARRIVED":
        drone_state_events[drone].append((t, "EXECUTING"))

    elif ev_type == "DRONE_FAILED":
        drone_state_events[drone].append((t, "DRONE_FAILED"))

    elif ev_type == "TASK_FAILED":
        drone_state_events[drone].append((t, "TASK_FAILED"))

for drone in all_drones:
    drone_state_events[drone].sort(key=lambda x: x[0])


# ------------------------------------------------------------
# 8. Helpers
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
            if seg["phase"] == "EXECUTING":
                return seg["start"]

            sx, sy = seg["start"]
            ex, ey = seg["end"]
            alpha = (t - seg["t0"]) / max(seg["t1"] - seg["t0"], 1e-9)
            return (
                sx + alpha * (ex - sx),
                sy + alpha * (ey - sy),
            )

        pos = seg["end"]

    return pos


def drone_activity_label_at(drone, t):
    state = drone_state_at(drone, t)
    drone_segments = [s for s in segments if s["drone"] == drone]
    drone_segments.sort(key=lambda s: s["t0"])

    active_seg = None
    for seg in drone_segments:
        if seg["t0"] <= t <= seg["t1"]:
            active_seg = seg
            break

    if state == "FLYING" and active_seg is not None:
        goal = active_seg.get("object")
        return f"{drone} → {goal}" if goal else drone

    if state == "EXECUTING" and active_seg is not None:
        skill = active_seg.get("skill")
        return f"{drone} | {skill}" if skill else drone

    if state == "DRONE_FAILED":
        return f"{drone} | FAILED"

    if state == "TASK_FAILED":
        return f"{drone} | TASK FAIL"

    return drone


# ------------------------------------------------------------
# 9. Timeline
# ------------------------------------------------------------
t_min = min(ev["time"] for ev in events)
t_max = max(ev["time"] for ev in events)
fps = 20
timeline = np.linspace(t_min, t_max, int((t_max - t_min) * fps) + 1)


# ------------------------------------------------------------
# 10. Plot
# ------------------------------------------------------------
fig, ax = plt.subplots(figsize=(11, 8))

obj_x = [xy[0] for xy in object_positions.values()]
obj_y = [xy[1] for xy in object_positions.values()]
ax.scatter(obj_x, obj_y, s=120, c="black", zorder=2)

for name, (x, y) in object_positions.items():
    ax.text(
        x, y + 5.0, name,
        fontsize=8,
        bbox=dict(facecolor="white", alpha=0.8, edgecolor="none", pad=1.5)
    )

drone_scatter = ax.scatter([], [], s=150, zorder=3)
drone_labels = {drone: ax.text(0, 0, "", fontsize=8) for drone in all_drones}
time_text = ax.text(0.02, 0.98, "", transform=ax.transAxes, va="top", fontsize=11)

all_x = obj_x + [xy[0] for xy in drone_start_positions.values()]
all_y = obj_y + [xy[1] for xy in drone_start_positions.values()]
margin = 8

ax.set_xlim(min(all_x) - margin, max(all_x) + margin)
ax.set_ylim(min(all_y) - margin, max(all_y) + margin)
ax.set_xlabel("X")
ax.set_ylabel("Y")
ax.set_title("2D Drone Execution Visualization")
ax.grid(True)

legend_elements = [
    Line2D([0], [0], marker='o', color='w', label='Object', markerfacecolor='black', markersize=9),
    Line2D([0], [0], marker='o', color='w', label='Idle', markerfacecolor='green', markersize=9),
    Line2D([0], [0], marker='o', color='w', label='Flying', markerfacecolor='blue', markersize=9),
    Line2D([0], [0], marker='o', color='w', label='Executing', markerfacecolor='purple', markersize=9),
    Line2D([0], [0], marker='o', color='w', label='Drone failure', markerfacecolor='red', markersize=9),
    Line2D([0], [0], marker='o', color='w', label='Task failure', markerfacecolor='orange', markersize=9),
]
ax.legend(handles=legend_elements, loc="upper right")


# ------------------------------------------------------------
# 11. Animation update
# ------------------------------------------------------------
def update(frame_idx):
    t = timeline[frame_idx]

    positions = []
    colors = []

    for drone in all_drones:
        positions.append(drone_position_at(drone, t))
        state = drone_state_at(drone, t)
        colors.append(state_colors.get(state, default_color))

    positions = np.array(positions)
    drone_scatter.set_offsets(positions)
    drone_scatter.set_color(colors)

    # Group drones that are at the same / very close position
    groups = []
    tolerance = 0.5  # adjust if needed

    for i, (x, y) in enumerate(positions):
        placed = False
        for group in groups:
            gx, gy = group["center"]
            if abs(x - gx) <= tolerance and abs(y - gy) <= tolerance:
                group["members"].append(i)
                placed = True
                break
        if not placed:
            groups.append({
                "center": (x, y),
                "members": [i]
            })

    # Assign label positions with offsets inside each group
    for group in groups:
        members = group["members"]
        n = len(members)

        for k, i in enumerate(members):
            drone = all_drones[i]
            x, y = positions[i]
            label = drone_activity_label_at(drone, t)

            # stack labels vertically around the point
            dx = 0.8
            dy = 0.8 + (k - (n - 1) / 2) * 3.0

            drone_labels[drone].set_position((x + dx, y + dy))
            drone_labels[drone].set_text(label)
            drone_labels[drone].set_bbox(dict(facecolor="white", alpha=0.7, edgecolor="none", pad=1.5))

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

# Optional save
# anim.save("drone_execution_with_labels.mp4", fps=fps, dpi=150)
# anim.save("drone_execution_with_labels.gif", fps=fps, dpi=120)