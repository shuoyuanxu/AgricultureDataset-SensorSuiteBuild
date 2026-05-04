#!/usr/bin/env python3
"""
Extract GPS data from a ROS bag and save to CSV.
Prints fix/RTK status summary to terminal.
Saves plots: trajectory coloured by fix type, fix status over time, horizontal accuracy.

Usage: python3 GetGPS.py <bagname>.bag <topicname>
"""

import sys
import csv
import math
from collections import Counter
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

try:
    import rosbag
except ImportError:
    print("Could not import rosbag. Run in a ROS1 environment: source /opt/ros/noetic/setup.bash", file=sys.stderr)
    sys.exit(1)

# sensor_msgs/NavSatStatus status values
STATUS_LABELS = {
    -1: 'No Fix',
     0: 'Fix',
     1: 'SBAS Fix',
     2: 'GBAS / RTK Fix',
}
STATUS_COLORS = {
    -1: 'red',
     0: 'orange',
     1: 'gold',
     2: 'limegreen',
}
RTK_STATUS = 2  # GBAS/RTK fix in NavSatFix


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


def print_fix_summary(rows):
    status_key = next((k for k in rows[0] if k == 'status.status'), None)
    cov_type_key = next((k for k in rows[0] if 'covariance_type' in k), None)

    print("\n" + "=" * 60)
    print("GPS FIX STATUS SUMMARY")
    print("=" * 60)
    print(f"  Total messages : {len(rows)}")

    if status_key:
        statuses = [r.get(status_key) for r in rows if isinstance(r.get(status_key), (int, float))]
        counts = Counter(int(s) for s in statuses)
        total = len(statuses)

        print(f"\n  Fix type distribution ({total} msgs with status):")
        for code in sorted(counts):
            label = STATUS_LABELS.get(code, f'Unknown ({code})')
            pct = counts[code] / total * 100
            bar = '#' * int(pct / 2)
            print(f"    {code:3d}  {label:<18} {counts[code]:5d}  ({pct:5.1f}%)  {bar}")

        rtk_count = counts.get(RTK_STATUS, 0)
        rtk_pct = rtk_count / total * 100 if total else 0
        print(f"\n  RTK fix (status={RTK_STATUS}) : {rtk_count} / {total} msgs  ({rtk_pct:.1f}%)")

        if rtk_pct == 0:
            print("  WARNING: No RTK fixes detected in this bag.")
        elif rtk_pct < 50:
            print("  WARNING: RTK fix coverage is below 50%.")
        else:
            print("  OK: Good RTK fix coverage.")
    else:
        print("  (no status.status field found in messages)")

    # Horizontal accuracy from position covariance XX/YY (variance in m^2)
    cov_xx_key = next((k for k in rows[0] if 'position_covariance.0' in k), None)
    cov_yy_key = next((k for k in rows[0] if 'position_covariance.4' in k), None)
    if cov_xx_key and cov_yy_key:
        hacc = []
        for r in rows:
            xx = r.get(cov_xx_key)
            yy = r.get(cov_yy_key)
            if isinstance(xx, (int, float)) and isinstance(yy, (int, float)) and xx >= 0 and yy >= 0:
                hacc.append(math.sqrt((xx + yy) / 2))
        if hacc:
            print(f"\n  Horizontal accuracy (1-sigma from covariance):")
            print(f"    Mean  : {sum(hacc)/len(hacc):.3f} m")
            print(f"    Min   : {min(hacc):.3f} m")
            print(f"    Max   : {max(hacc):.3f} m")

    if cov_type_key:
        cov_types = Counter(
            int(r[cov_type_key]) for r in rows
            if isinstance(r.get(cov_type_key), (int, float))
        )
        cov_type_labels = {0: 'Unknown', 1: 'Approximated', 2: 'Diagonal Known', 3: 'Known'}
        print(f"\n  Covariance type distribution:")
        for code in sorted(cov_types):
            label = cov_type_labels.get(code, str(code))
            print(f"    {code}  {label:<20} {cov_types[code]} msgs")

    print("=" * 60)


def plot_gps(bag_path, topic, rows):
    stem = bag_path.stem
    topic_tag = topic.replace('/', '_').strip('_')

    lat_key = next((k for k in rows[0] if 'latitude' in k.lower()), None)
    lon_key = next((k for k in rows[0] if 'longitude' in k.lower()), None)
    alt_key = next((k for k in rows[0] if 'altitude' in k.lower()), None)
    status_key = next((k for k in rows[0] if k == 'status.status'), None)
    cov_xx_key = next((k for k in rows[0] if 'position_covariance.0' in k), None)
    cov_yy_key = next((k for k in rows[0] if 'position_covariance.4' in k), None)

    times = [r['bag_time'] for r in rows]
    t0 = times[0]
    rel_times = [t - t0 for t in times]

    has_status = status_key is not None
    has_cov = cov_xx_key is not None and cov_yy_key is not None
    has_alt = alt_key is not None

    n_cols = max(1 + int(has_alt), 1 + int(has_cov))
    fig = plt.figure(figsize=(7 * n_cols, 10))
    gs = fig.add_gridspec(2, n_cols, hspace=0.4, wspace=0.35)

    # Trajectory coloured by fix status
    ax_traj = fig.add_subplot(gs[0, 0])
    if lat_key and lon_key:
        statuses_raw = [r.get(status_key) for r in rows] if has_status else [None] * len(rows)
        for i in range(len(rows) - 1):
            lat0, lon0 = rows[i].get(lat_key), rows[i].get(lon_key)
            lat1, lon1 = rows[i+1].get(lat_key), rows[i+1].get(lon_key)
            if not all(isinstance(v, (int, float)) for v in [lat0, lon0, lat1, lon1]):
                continue
            status = statuses_raw[i]
            color = STATUS_COLORS.get(int(status) if isinstance(status, (int, float)) else None, 'steelblue')
            ax_traj.plot([lon0, lon1], [lat0, lat1], color=color, linewidth=1.2)

        if has_status:
            legend_handles = [
                mpatches.Patch(color=STATUS_COLORS[k], label=f"{k}: {STATUS_LABELS[k]}")
                for k in sorted(STATUS_COLORS)
            ]
            ax_traj.legend(handles=legend_handles, fontsize=7, loc='best')

    ax_traj.set_xlabel('Longitude')
    ax_traj.set_ylabel('Latitude')
    ax_traj.set_title('GPS Trajectory (coloured by fix type)')
    ax_traj.grid(True)

    # Altitude over time
    if has_alt and n_cols > 1:
        ax_alt = fig.add_subplot(gs[0, 1])
        alts = [(t, r.get(alt_key)) for t, r in zip(rel_times, rows)
                if isinstance(r.get(alt_key), (int, float))]
        if alts:
            vt, va = zip(*alts)
            ax_alt.plot(vt, va, linewidth=0.9)
        ax_alt.set_xlabel('Time (s)')
        ax_alt.set_ylabel('Altitude (m)')
        ax_alt.set_title('Altitude Over Time')
        ax_alt.grid(True)

    # Fix status over time
    ax_status = fig.add_subplot(gs[1, 0])
    if has_status:
        status_vals = [(t, r.get(status_key)) for t, r in zip(rel_times, rows)
                       if isinstance(r.get(status_key), (int, float))]
        if status_vals:
            vt, vs = zip(*status_vals)
            vs_int = [int(s) for s in vs]
            colors = [STATUS_COLORS.get(s, 'steelblue') for s in vs_int]
            ax_status.scatter(vt, vs_int, c=colors, s=8, zorder=3)
            ax_status.step(vt, vs_int, where='post', color='grey', linewidth=0.6, alpha=0.5)
            ax_status.set_yticks(sorted(STATUS_LABELS))
            ax_status.set_yticklabels(
                [f"{k}: {STATUS_LABELS[k]}" for k in sorted(STATUS_LABELS)], fontsize=8
            )
            ax_status.axhline(RTK_STATUS, color='limegreen', linestyle='--', linewidth=0.8, alpha=0.7)
    ax_status.set_xlabel('Time (s)')
    ax_status.set_title('Fix Status Over Time')
    ax_status.grid(True, axis='x')

    # Horizontal accuracy over time
    if has_cov:
        ax_acc = fig.add_subplot(gs[1, 1])
        hacc_pts = []
        for t, r in zip(rel_times, rows):
            xx = r.get(cov_xx_key)
            yy = r.get(cov_yy_key)
            if isinstance(xx, (int, float)) and isinstance(yy, (int, float)) and xx >= 0 and yy >= 0:
                hacc_pts.append((t, math.sqrt((xx + yy) / 2)))
        if hacc_pts:
            vt, va = zip(*hacc_pts)
            ax_acc.plot(vt, va, linewidth=0.9, color='steelblue')
        ax_acc.set_xlabel('Time (s)')
        ax_acc.set_ylabel('Horiz. accuracy 1σ (m)')
        ax_acc.set_title('Horizontal Position Accuracy Over Time')
        ax_acc.grid(True)

    plot_file = f"{stem}_{topic_tag}_gps.png"
    plt.savefig(plot_file, dpi=150, bbox_inches='tight')
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
    rows, _ = extract_gps(bag_path, topic)

    if not rows:
        print("No messages found on that topic.")
        sys.exit(1)

    print_fix_summary(rows)
    plot_gps(bag_path, topic, rows)


if __name__ == "__main__":
    main()
