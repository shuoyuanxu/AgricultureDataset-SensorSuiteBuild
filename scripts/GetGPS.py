#!/usr/bin/env python3
import sys
import csv
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path

try:
    import rosbag
except ImportError:
    print("Could not import rosbag. Run in a ROS1 environment: source /opt/ros/noetic/setup.bash", file=sys.stderr)
    sys.exit(1)


def is_primitive(x):
    return isinstance(x, (str, int, float, bool)) or x is None


def flatten_msg(obj, prefix="", out=None):
    if out is None:
        out = {}
    key = prefix[:-1] if prefix.endswith(".") else prefix
    if hasattr(obj, "secs") and hasattr(obj, "nsecs"):
        out[key] = obj.secs + obj.nsecs * 1e-9
        return out
    if is_primitive(obj):
        out[key] = obj
        return out
    if isinstance(obj, (list, tuple)):
        for i, item in enumerate(obj):
            flatten_msg(item, f"{prefix}{i}.", out)
        return out
    if hasattr(obj, "__slots__"):
        for slot in obj.__slots__:
            try:
                value = getattr(obj, slot)
            except Exception:
                value = ""
            flatten_msg(value, f"{prefix}{slot}.", out)
        return out
    out[key] = str(obj)
    return out


def extract_gps(bag_path, topic):
    rows = []
    fieldnames = {"bag_time", "topic", "msg_type"}

    with rosbag.Bag(str(bag_path), "r") as bag:
        for t_topic, msg, t in bag.read_messages(topics=[topic]):
            row = {
                "bag_time": t.to_sec(),
                "topic": t_topic,
                "msg_type": getattr(msg, "_type", type(msg).__name__),
            }
            row.update(flatten_msg(msg))
            rows.append(row)
            fieldnames.update(row.keys())

    fieldnames = ["bag_time", "topic", "msg_type"] + sorted(
        k for k in fieldnames if k not in {"bag_time", "topic", "msg_type"}
    )

    stem = bag_path.stem
    topic_tag = topic.replace('/', '_').strip('_')
    out_csv = Path(f"{stem}_{topic_tag}_gps.csv")
    with out_csv.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in fieldnames})

    print(f"Saved: {out_csv} ({len(rows)} rows)")
    return rows, list(fieldnames)


def plot_gps(bag_path, topic, rows):
    stem = bag_path.stem
    topic_tag = topic.replace('/', '_').strip('_')

    first = rows[0]
    lat_key = next((k for k in first if 'latitude' in k.lower()), None)
    lon_key = next((k for k in first if 'longitude' in k.lower()), None)
    alt_key = next((k for k in first if 'altitude' in k.lower()), None)

    times = [r['bag_time'] for r in rows]
    t0 = times[0]
    rel_times = [t - t0 for t in times]

    if lat_key and lon_key:
        lats = [r.get(lat_key, None) for r in rows]
        lons = [r.get(lon_key, None) for r in rows]
        valid = [(t, la, lo) for t, la, lo in zip(rel_times, lats, lons)
                 if isinstance(la, (int, float)) and isinstance(lo, (int, float))]
        vt, vlat, vlon = zip(*valid) if valid else ([], [], [])

        n_plots = 3 if alt_key else 2
        fig, axes = plt.subplots(1, n_plots, figsize=(6 * n_plots, 5))

        axes[0].plot(vlon, vlat, linewidth=0.8)
        axes[0].set_xlabel('Longitude')
        axes[0].set_ylabel('Latitude')
        axes[0].set_title('GPS Trajectory')
        axes[0].grid(True)

        axes[1].plot(vt, vlat, label='Latitude')
        axes[1].plot(vt, vlon, label='Longitude')
        axes[1].set_xlabel('Time (s)')
        axes[1].set_title('Lat/Lon Over Time')
        axes[1].legend()
        axes[1].grid(True)

        if alt_key:
            alts = [r.get(alt_key, None) for r in rows]
            valid_alt = [(t, a) for t, a in zip(rel_times, alts) if isinstance(a, (int, float))]
            if valid_alt:
                vt_a, va = zip(*valid_alt)
                axes[2].plot(vt_a, va)
                axes[2].set_xlabel('Time (s)')
                axes[2].set_ylabel('Altitude (m)')
                axes[2].set_title('Altitude Over Time')
                axes[2].grid(True)
    else:
        numeric_keys = [k for k in first if isinstance(first.get(k), (int, float)) and k != 'bag_time']
        fig, ax = plt.subplots(figsize=(10, 5))
        for key in numeric_keys[:6]:
            vals = [r.get(key, None) for r in rows]
            ax.plot(rel_times, vals, label=key)
        ax.set_xlabel('Time (s)')
        ax.set_title(f'GPS Data: {topic}')
        ax.legend()
        ax.grid(True)

    plt.tight_layout()
    plot_file = f"{stem}_{topic_tag}_gps.png"
    plt.savefig(plot_file, dpi=150)
    print(f"Saved: {plot_file}")


def main():
    if len(sys.argv) != 3:
        print("Usage: python3 GetGPS.py <bagname>.bag <topicname>")
        sys.exit(1)

    bag_path = Path(sys.argv[1])
    topic = sys.argv[2]

    if not bag_path.exists():
        print(f"ERROR: Bag file not found: {bag_path}", file=sys.stderr)
        sys.exit(1)

    print(f"Extracting GPS from {bag_path}, topic: {topic}")
    rows, fieldnames = extract_gps(bag_path, topic)

    if not rows:
        print("No messages found on that topic.")
        sys.exit(1)

    plot_gps(bag_path, topic, rows)


if __name__ == "__main__":
    main()
