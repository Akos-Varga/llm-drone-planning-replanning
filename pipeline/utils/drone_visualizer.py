# Fix texts going out of screen
# Show task description as title
# Show time

from typing import Dict, Tuple, List, Any, Optional

import matplotlib.pyplot as plt
from matplotlib.patches import Circle
from matplotlib.animation import FuncAnimation, PillowWriter

Pos = Tuple[float, float]
Objects = Dict[str, Pos]
Drones = Dict[str, Dict[str, Any]]
Schedule = Dict[str, List[Dict[str, Any]]]


def _assign_colors(names: List[str]) -> List[str]:
    palette = [
        "tab:blue", "tab:orange", "tab:green", "tab:red", "tab:purple", "tab:brown",
        "tab:pink", "tab:gray", "tab:olive", "tab:cyan"
    ]
    return [palette[i % len(palette)] for i, _ in enumerate(names)]


def _build_segments(objects: Objects, drones: Drones, schedule: Schedule):
    segments: Dict[str, List[Dict[str, Any]]] = {}
    object_active_until: Dict[str, float] = {}
    drone_active_until: Dict[str, float] = {}
    total_time = 0.0

    scheduled_objects: Dict[str, Pos] = {}
    scheduled_drones: Dict[str, Dict[str, Any]] = {}

    for d, tasks in schedule.items():
        if tasks:
            scheduled_drones[d] = drones[d]
            for t in tasks:
                scheduled_objects[t["object"]] = objects[t["object"]]

    start_positions: Dict[str, Pos] = {
        name: info.get("pos", (0.0, 0.0)) for name, info in drones.items()
    }

    for drone_name, tasks in schedule.items():
        tasks_sorted = sorted(tasks, key=lambda t: t["departure_time"]) if tasks else []
        segs: List[Dict[str, Any]] = []
        current_pos = start_positions.get(drone_name, (0.0, 0.0))

        max_end = 0.0
        prev_finish = 0.0
        for t in tasks_sorted:
            obj_name = t["object"]
            departure_t = float(t["departure_time"])
            arrival_t = float(t["arrival_time"])
            finish_t = float(t["finish_time"])
            target_pos = objects[obj_name]

            if departure_t > prev_finish:
                segs.append({
                    "kind": "hold",
                    "start_time": prev_finish,
                    "end_time": departure_t,
                    "start_pos": current_pos,
                    "end_pos": current_pos,
                })

            segs.append({
                "kind": "move",
                "start_time": departure_t,
                "end_time": arrival_t,
                "start_pos": current_pos,
                "end_pos": target_pos,
                "object": obj_name,
                "skill": t["skill"],
            })
            current_pos = target_pos

            segs.append({
                "kind": "execute",
                "start_time": arrival_t,
                "end_time": finish_t,
                "start_pos": target_pos,
                "end_pos": target_pos,
                "object": obj_name,
                "skill": t["skill"],
            })

            max_end = max(max_end, finish_t)
            prev_finish = finish_t

            if obj_name not in object_active_until or object_active_until[obj_name] < finish_t:
                object_active_until[obj_name] = finish_t

        segments[drone_name] = segs
        drone_active_until[drone_name] = segs[-1]["end_time"] if segs else -float("inf")
        total_time = max(total_time, max_end)

    return (
        segments,
        total_time,
        object_active_until,
        drone_active_until,
        start_positions,
        scheduled_objects,
        scheduled_drones,
    )


def _pos_on_segment(seg: Dict[str, Any], t: float) -> Pos:
    t0, t1 = seg["start_time"], seg["end_time"]
    x0, y0 = seg["start_pos"]
    x1, y1 = seg["end_pos"]

    if t1 <= t0 or t <= t0:
        return (x0, y0)
    if t >= t1:
        return (x1, y1)

    u = (t - t0) / (t1 - t0)
    return (x0 + u * (x1 - x0), y0 + u * (y1 - y0))


def _pos_at_time(segments_for_drone: List[Dict[str, Any]], fallback_pos: Pos, t: float) -> Pos:
    if not segments_for_drone:
        return fallback_pos
    for seg in segments_for_drone:
        if seg["start_time"] <= t <= seg["end_time"]:
            return _pos_on_segment(seg, t)
    if t < segments_for_drone[0]["start_time"]:
        return segments_for_drone[0]["start_pos"]
    return segments_for_drone[-1]["end_pos"]


def _task_at_time(segments_for_drone: List[Dict[str, Any]], t: float) -> str:
    if not segments_for_drone:
        return "Idle"
    for seg in segments_for_drone:
        if seg["start_time"] <= t <= seg["end_time"]:
            if seg["kind"] == "move":
                return f"Move to: {seg['object']}"
            elif seg["kind"] == "execute":
                return f"Execute: {seg['skill']}"
            return "Holding"
    if t < segments_for_drone[0]["start_time"]:
        return "Holding"
    return "Idle"


def _seg_at_time(segments_for_drone: List[Dict[str, Any]], t: float) -> Optional[Dict[str, Any]]:
    if not segments_for_drone:
        return None
    for seg in segments_for_drone:
        if seg["start_time"] <= t <= seg["end_time"]:
            return seg
    return None


def animate_schedule(
    objects: Objects,
    drones: Drones,
    schedule: Schedule,
    *,
    world_size: int = 100,
    dt: float = 0.1,
    extra_hold: float = 2.0,
    save_path: Optional[str] = None,
):
    # Remove z dimension for viz
    objects = {k:v[:2] for k, v in objects.items()}
    for d in drones: drones[d]["pos"] = drones[d]["pos"][:2]

    (
        segments,
        total_time,
        object_active_until,
        drone_active_until,
        start_positions,
        scheduled_objects,
        scheduled_drones,
    ) = _build_segments(objects, drones, schedule)

    total = total_time + extra_hold
    frames = int(total / dt) + 1

    fig, ax = plt.subplots(figsize=(6, 6))
    ax.set_xlim(0, world_size * 1.3)
    ax.set_ylim(0, world_size * 1.3)
    ax.set_aspect('equal', adjustable='box')
    ax.grid(True, linestyle="--", linewidth=0.5, alpha=0.3)
    ax.set_title("Drone & Object Map")
    time_text = ax.text(0.02, 1.02, "", transform=ax.transAxes, va="bottom")

    object_patches: Dict[str, Circle] = {}
    object_labels: Dict[str, Any] = {}
    object_colors = _assign_colors(list(scheduled_objects.keys()))

    for i, (name, (x, y)) in enumerate(scheduled_objects.items()):
        c = Circle((x, y), radius=2.0, alpha=0.6, ec="black", fc=object_colors[i])
        c.set_visible(False)
        ax.add_patch(c)
        lbl = ax.text(x - 5.0, y - 5.0, name, fontsize=8)
        lbl.set_visible(False)
        object_patches[name] = c
        object_labels[name] = lbl

    drone_patches: Dict[str, Circle] = {}
    drone_labels: Dict[str, Any] = {}
    drone_colors = _assign_colors(list(scheduled_drones.keys()))
    for i, (name, _) in enumerate(scheduled_drones.items()):
        x, y = start_positions.get(name, (0.0, 0.0))
        c = Circle((x, y), radius=1.5, alpha=0.9, ec="black", fc=drone_colors[i])
        c.set_visible(False)
        ax.add_patch(c)
        lbl = ax.text(x + 1.8, y + 1.8, f"{name}\nIdle", fontsize=8, fontweight="bold", linespacing=1.3)
        lbl.set_visible(False)
        drone_patches[name] = c
        drone_labels[name] = lbl

    def _object_visible_now(obj_name: str, t: float) -> bool:
        last = object_active_until.get(obj_name, -float("inf"))
        return t <= last

    def _drone_visible_now(drone_name: str, t: float) -> bool:
        last = drone_active_until.get(drone_name, -float("inf"))
        return t <= last

    def _update(frame_idx: int):
        t = frame_idx * dt
        artists = []

        for name, patch in object_patches.items():
            vis = _object_visible_now(name, t)
            patch.set_visible(vis)
            lbl = object_labels[name]
            lbl.set_visible(vis)
            artists.extend([patch, lbl])

        from collections import defaultdict
        exec_groups: Dict[str, List[str]] = defaultdict(list)
        active_seg: Dict[str, Optional[Dict[str, Any]]] = {}
        for name in drone_patches.keys():
            seg = _seg_at_time(segments.get(name, []), t)
            active_seg[name] = seg
            if seg is not None and seg.get("kind") == "execute":
                exec_groups[seg.get("object")].append(name)

        for obj in exec_groups:
            exec_groups[obj].sort()

        corner_offsets = [
            (1.8, 1.8, "left", "bottom"),
            (-1.8, 1.8, "right", "bottom"),
            (1.8, -1.8, "left", "top"),
            (-1.8, -1.8, "right", "top"),
        ]

        for name, patch in drone_patches.items():
            is_on = _drone_visible_now(name, t)
            patch.set_visible(is_on)
            lbl = drone_labels[name]
            lbl.set_visible(is_on)
            if not is_on:
                continue

            pos = _pos_at_time(segments.get(name, []), start_positions.get(name, (0.0, 0.0)), t)
            x, y = pos
            patch.center = (x, y)

            task = _task_at_time(segments.get(name, []), t)
            lbl.set_text(f"{name}\n{task}")

            seg = active_seg.get(name)
            dx, dy, ha, va = (1.8, 1.8, "left", "bottom")
            if seg is not None and seg.get("kind") == "execute":
                group = exec_groups.get(seg.get("object"), [])
                if len(group) > 1:
                    idx = group.index(name) % len(corner_offsets)
                    dx, dy, ha, va = corner_offsets[idx]

            lbl.set_position((x + dx, y + dy))
            lbl.set_ha(ha)
            lbl.set_va(va)

            artists.extend([patch, lbl])

        time_text.set_text(f"t = {t:0.1f}s")
        artists.append(time_text)
        return artists

    anim = FuncAnimation(fig, _update, frames=frames, interval=int(dt * 1000), blit=True)

    if save_path:
        writer = PillowWriter(fps=int(1.0 / dt))
        anim.save(save_path, writer=writer)

    return anim

# ------------------------------------------------------------------
# Example usage
# ------------------------------------------------------------------
if __name__ == "__main__":
    import os

    objects = {
        "House1": (12, 87, 52),
        "RoofTop1": (45, 33, 42),
        "RoofTop2": (78, 62, 31),
        "SolarPanel1": (9, 14, 25),
        "SolarPanel2": (65, 90, 74)
    }   
    
    drones = {
        "Drone1": {"skills": ["CaptureRGBImage", "CaptureThermalImage"], "pos": (23, 77, 47), "speed": 14},
        "Drone2": {"skills": ["CaptureThermalImage"], "pos": (64, 12, 84), "speed": 17},
        "Drone3": {"skills": ["CaptureRGBImage"], "pos": (89, 45, 31), "speed": 11},
        "Drone4": {"skills": ["CaptureRGBImage", "CaptureThermalImage", "InspectStructure"], "pos": (35, 58, 42), "speed": 19},
        "Drone5": {"skills": ["RecordVideo"], "pos": (10, 91, 20), "speed": 13}
    }  

    schedule = {
        "Drone4": [
            {"name": "SubTask1", "object": "RoofTop1", "skill": "CaptureRGBImage", "departure_time": 0.0, "arrival_time": 1.4, "finish_time": 3.7}
        ],
        "Drone2": [
            {"name": "SubTask2", "object": "RoofTop2", "skill": "CaptureThermalImage", "departure_time": 0.0, "arrival_time": 4.4, "finish_time": 6.0}
        ],
        "Drone1": [
            {"name": "SubTask3", "object": "House1", "skill": "CaptureRGBImage", "departure_time": 0.0, "arrival_time": 1.1, "finish_time": 3.4}
        ],
        "Drone3": []
    }

    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "saved_gifs")
    os.makedirs(out_dir, exist_ok=True)

    anim = animate_schedule(objects, drones, schedule, dt=0.1, extra_hold=1.5)
    plt.show()
