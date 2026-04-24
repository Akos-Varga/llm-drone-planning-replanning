import json
import re
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, FFMpegWriter
from matplotlib.lines import Line2D

from worlds.test_world import drones, objects
from main import task as mission_descr


# ------------------------------------------------------------
# 1. Settings
# ------------------------------------------------------------
EVENT_LOG_PATH = "logs/events.jsonl"
OUTPUT_VIDEO_PATH = "logs/drone_execution_with_labels.mp4"

fps = 20
FAILED_DRONE_VISIBLE_SECONDS = 4.0


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
seen = set()

with open(EVENT_LOG_PATH, "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue

        ev = json.loads(line)

        # Remove exact duplicate events
        key = json.dumps(ev, sort_keys=True)
        if key in seen:
            continue

        seen.add(key)
        events.append(ev)

events.sort(key=lambda e: e["time"])

if not events:
    raise ValueError("No events found.")


# ------------------------------------------------------------
# 5. Helpers
# ------------------------------------------------------------
def extract_arrival_object(message: str):
    m = re.search(r"Arrived at (.+)$", message or "")
    return m.group(1).strip() if m else None


def subtask_sort_key(subtask):
    return int(re.sub(r"\D", "", subtask) or 0)


def admission_status_label(ev):
    ev_type = ev.get("type")
    drone = ev.get("drone", "Planner")
    msg = ev.get("message", "")

    if ev_type == "ACK":
        return f"✓ {drone} ACK"

    if ev_type in ("REJECT", "NACK"):
        return f"✗ {drone} REJECT"

    if ev_type == "RUNTIME_CHECK_OK":
        return f"✓ {drone} IN-FLIGHT OK"

    if ev_type == "RUNTIME_CHECK_REJECT":
        return f"✗ {drone} IN-FLIGHT REJECT"

    if ev_type == "DRONE_FAILED":
        if "admission" in msg.lower():
            return f"✗ {drone} ADMISSION FAIL"
        return f"✗ {drone} RUNTIME FAIL"

    if ev_type == "TASK_FAILED":
        return f"✗ {drone} TASK FAIL"

    return None


def failed_drones_at(t):
    failed = {}

    for ev in events:
        if ev["time"] > t:
            break

        if ev.get("type") == "DRONE_FAILED":
            drone = ev.get("drone")
            if drone:
                failed[drone] = {
                    "time": ev["time"],
                    "subtask": ev.get("subtask"),
                    "message": ev.get("message", ""),
                }

    return failed


# ------------------------------------------------------------
# 6. Build subtask metadata
# ------------------------------------------------------------
subtask_info = {}

for ev in events:
    subtask = ev.get("subtask")
    if not subtask:
        continue

    subtask_info.setdefault(subtask, {"object": None, "skill": None})

    if ev.get("object") is not None:
        subtask_info[subtask]["object"] = ev["object"]

    if ev.get("skill") is not None:
        subtask_info[subtask]["skill"] = ev["skill"]

    arrival_obj = extract_arrival_object(ev.get("message", ""))
    if arrival_obj is not None:
        subtask_info[subtask]["object"] = arrival_obj


# ------------------------------------------------------------
# 7. Build movement / execution segments
# ------------------------------------------------------------
segments = []
last_position = dict(drone_start_positions)
active_tasks = {}

for ev in events:
    drone = ev.get("drone")
    if drone not in all_drones:
        continue

    ev_type = ev["type"]
    t = ev["time"]
    subtask = ev.get("subtask")

    if ev_type == "STATE_CHANGED" and ev.get("state") == "BUSY" and subtask is not None:
        obj_name = ev.get("object") or subtask_info.get(subtask, {}).get("object")

        if obj_name is None or obj_name not in object_positions:
            continue

        active_tasks[drone] = {
            "subtask": subtask,
            "object": obj_name,
            "skill": subtask_info.get(subtask, {}).get("skill"),
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

        arrival_obj = extract_arrival_object(ev.get("message", ""))
        if arrival_obj is not None:
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
        else:
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
# 8. Drone state timeline
# ------------------------------------------------------------
drone_state_events = {drone: [] for drone in all_drones}
initial_t = events[0]["time"] - 1e-6

for drone in all_drones:
    drone_state_events[drone].append((initial_t, "IDLE"))

for ev in events:
    drone = ev.get("drone")
    if drone not in all_drones:
        continue

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
# 9. Animation state helpers
# ------------------------------------------------------------
def drone_state_at(drone, t):
    current = "IDLE"
    failed_time = None

    for ts, st in drone_state_events[drone]:
        if ts <= t:
            current = st
            if st == "DRONE_FAILED":
                failed_time = ts
        else:
            break

    if current == "DRONE_FAILED" and failed_time is not None:
        if t - failed_time > FAILED_DRONE_VISIBLE_SECONDS:
            return "HIDDEN_FAILED"

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


def subtask_statuses_at(t):
    statuses = {}

    for ev in events:
        if ev["time"] > t:
            break

        subtask = ev.get("subtask")
        if not subtask:
            continue

        label = admission_status_label(ev)
        if label is None:
            continue

        statuses.setdefault(subtask, [])

        # Avoid exact repeated labels caused by duplicate-ish log events
        if not statuses[subtask] or statuses[subtask][-1] != label:
            statuses[subtask].append(label)

    return statuses


def visible_pending_subtasks_at(t):
    completed = {
        ev.get("subtask")
        for ev in events
        if ev["time"] <= t and ev.get("type") == "COMPLETED"
    }

    statuses = subtask_statuses_at(t)
    pending = []

    for subtask in sorted(subtask_info.keys(), key=subtask_sort_key):
        if subtask in completed:
            continue

        obj = subtask_info[subtask].get("object") or "UnknownObject"
        all_status = statuses.get(subtask, [])

        if all_status:
            pending.append(f"{subtask}: {obj}\n   " + "\n   ".join(all_status))
        else:
            pending.append(f"{subtask}: {obj}")

    return pending


# ------------------------------------------------------------
# 10. Timeline
# ------------------------------------------------------------
t_min = min(ev["time"] for ev in events)
t_max = max(ev["time"] for ev in events)

timeline = np.linspace(
    t_min,
    t_max,
    int((t_max - t_min) * fps) + 1
)


# ------------------------------------------------------------
# 11. Plot
# ------------------------------------------------------------
fig, (ax, side_ax) = plt.subplots(
    1,
    2,
    figsize=(19, 8),
    gridspec_kw={"width_ratios": [3.6, 1.5]}
)

obj_x = [xy[0] for xy in object_positions.values()]
obj_y = [xy[1] for xy in object_positions.values()]

ax.scatter(obj_x, obj_y, s=120, c="black", zorder=2)

for name, (x, y) in object_positions.items():
    ax.text(
        x,
        y + 5.0,
        name,
        fontsize=8,
        bbox=dict(facecolor="white", alpha=0.8, edgecolor="none", pad=1.5),
    )

drone_scatter = ax.scatter([], [], s=150, zorder=3)
drone_labels = {drone: ax.text(0, 0, "", fontsize=8) for drone in all_drones}

time_text = ax.text(
    0.02,
    0.98,
    "",
    transform=ax.transAxes,
    va="top",
    fontsize=11,
)

all_x = obj_x + [xy[0] for xy in drone_start_positions.values()]
all_y = obj_y + [xy[1] for xy in drone_start_positions.values()]

margin = 8
ax.set_xlim(min(all_x) - margin, max(all_x) + margin)
ax.set_ylim(min(all_y) - margin, max(all_y) + margin)

ax.set_xlabel("X")
ax.set_ylabel("Y")
ax.set_title(mission_descr)
ax.grid(True)

legend_elements = [
    Line2D([0], [0], marker="o", color="w", label="Object", markerfacecolor="black", markersize=9),
    Line2D([0], [0], marker="o", color="w", label="Idle", markerfacecolor="green", markersize=9),
    Line2D([0], [0], marker="o", color="w", label="Flying", markerfacecolor="blue", markersize=9),
    Line2D([0], [0], marker="o", color="w", label="Executing", markerfacecolor="purple", markersize=9),
    Line2D([0], [0], marker="o", color="w", label="Drone failure", markerfacecolor="red", markersize=9),
    Line2D([0], [0], marker="o", color="w", label="Task failure", markerfacecolor="orange", markersize=9),
]

ax.legend(
    handles=legend_elements,
    loc="upper left",
    bbox_to_anchor=(1.01, 1.0),
    borderaxespad=0.0,
    fontsize=8,
)


# ------------------------------------------------------------
# 12. Side panel
# ------------------------------------------------------------
side_ax.axis("off")
side_ax.set_title("Mission Status", fontsize=13, fontweight="bold")

task_list_text = side_ax.text(
    0.02,
    0.96,
    "",
    transform=side_ax.transAxes,
    va="top",
    fontsize=8,
    family="monospace",
)

failed_drones_text = side_ax.text(
    0.02,
    0.30,
    "",
    transform=side_ax.transAxes,
    va="top",
    fontsize=8,
    family="monospace",
)


# ------------------------------------------------------------
# 13. Animation update
# ------------------------------------------------------------
def update(frame_idx):
    t = timeline[frame_idx]

    positions = []
    colors = []
    visible_drone_indices = []

    for i, drone in enumerate(all_drones):
        state = drone_state_at(drone, t)

        if state == "HIDDEN_FAILED":
            positions.append((np.nan, np.nan))
            colors.append(default_color)
            drone_labels[drone].set_text("")
        else:
            positions.append(drone_position_at(drone, t))
            colors.append(state_colors.get(state, default_color))
            visible_drone_indices.append(i)

    positions = np.array(positions)
    drone_scatter.set_offsets(positions)
    drone_scatter.set_color(colors)

    # Group drones at nearly same position so labels do not overlap
    groups = []
    tolerance = 0.5

    for i in visible_drone_indices:
        x, y = positions[i]

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
                "members": [i],
            })

    for group in groups:
        members = group["members"]
        n = len(members)

        for k, i in enumerate(members):
            drone = all_drones[i]
            x, y = positions[i]
            label = drone_activity_label_at(drone, t)

            dx = 0.8
            dy = 0.8 + (k - (n - 1) / 2) * 3.0

            drone_labels[drone].set_position((x + dx, y + dy))
            drone_labels[drone].set_text(label)
            drone_labels[drone].set_bbox(
                dict(facecolor="white", alpha=0.7, edgecolor="none", pad=1.5)
            )

    time_text.set_text(f"Time: {t - t_min:.2f} s")

    # Pending subtasks with ACK/REJECT/failure status beside each subtask
    pending = visible_pending_subtasks_at(t)

    task_lines = ["PENDING SUBTASKS", "-" * 30]

    if pending:
        task_lines.extend(pending)
    else:
        task_lines.append("All subtasks completed")

    task_list_text.set_text("\n".join(task_lines))

    # Failed drone list remains on the side
    failed = failed_drones_at(t)
    failed_lines = ["FAILED DRONES", "-" * 30]

    if failed:
        for drone, info in failed.items():
            rel_time = info["time"] - t_min
            subtask = info["subtask"] or "-"
            failed_lines.append(f"{drone}: {subtask} at {rel_time:.2f}s")
    else:
        failed_lines.append("None")

    failed_drones_text.set_text("\n".join(failed_lines))

    return [
        drone_scatter,
        time_text,
        task_list_text,
        failed_drones_text,
        *drone_labels.values(),
    ]


ani = FuncAnimation(
    fig,
    update,
    frames=len(timeline),
    interval=1000 / fps,
    blit=False,
)

writer = FFMpegWriter(fps=fps, bitrate=1800)

ani.save(
    OUTPUT_VIDEO_PATH,
    writer=writer,
    dpi=120,
)

plt.close(fig)