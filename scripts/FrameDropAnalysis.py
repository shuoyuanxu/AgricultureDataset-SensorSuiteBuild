#!/usr/bin/env python3
"""
Analyze frame drops in an image topic from a ROS bag file.

Usage: python3 FrameDropAnalysis.py <bagname>.bag <topicname> [expected_fps] [drop_threshold]
"""

import sys
import numpy as np

try:
    import rosbag
except ImportError:
    print("Could not import rosbag. Run in a ROS1 environment: source /opt/ros/noetic/setup.bash", file=sys.stderr)
    sys.exit(1)


def analyze_frame_drops(bag_path, topic, expected_fps=10.0, drop_threshold=5.0):
    print(f"Bag     : {bag_path}")
    print(f"Topic   : {topic}")
    print(f"Expected: {expected_fps} Hz  |  Drop threshold: {drop_threshold}x expected interval")
    print("=" * 70)

    timestamps = []
    with rosbag.Bag(bag_path, 'r') as bag:
        for _, msg, t in bag.read_messages(topics=[topic]):
            timestamps.append(t.to_sec())

    if len(timestamps) < 2:
        print(f"ERROR: Only {len(timestamps)} message(s) found on {topic}")
        sys.exit(1)

    timestamps = np.array(timestamps)
    dt = np.diff(timestamps)
    expected_dt = 1.0 / expected_fps
    drop_threshold_time = expected_dt * drop_threshold

    print(f"\nTotal frames : {len(timestamps)}")
    print(f"Duration     : {timestamps[-1] - timestamps[0]:.2f} s")
    print(f"Actual FPS   : {1.0 / np.mean(dt):.2f} Hz")
    print(f"Mean interval: {np.mean(dt)*1000:.2f} ms")
    print(f"Median       : {np.median(dt)*1000:.2f} ms")
    print(f"Std deviation: {np.std(dt)*1000:.2f} ms")
    print(f"Min / Max    : {np.min(dt)*1000:.2f} / {np.max(dt)*1000:.2f} ms")

    drops = np.where(dt > drop_threshold_time)[0]
    if len(drops) == 0:
        print(f"\nNo significant frame drops detected (threshold: {drop_threshold_time*1000:.1f} ms)")
        return

    print(f"\nFrame drops detected: {len(drops)}  (threshold: {drop_threshold_time*1000:.1f} ms)")
    for i, idx in enumerate(drops):
        gap_ms = dt[idx] * 1000
        time_at = timestamps[idx] - timestamps[0]
        frames_lost = int(dt[idx] / expected_dt) - 1
        print(f"  {i+1:3d}. t={time_at:.2f}s  gap={gap_ms:.1f} ms  (~{frames_lost} frames lost)")
        if i == 9 and len(drops) > 10:
            print(f"  ... and {len(drops) - 10} more")
            break


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python3 FrameDropAnalysis.py <bagname>.bag <topicname> [expected_fps] [drop_threshold]")
        print("  expected_fps   : default 10.0")
        print("  drop_threshold : multiplier to detect drops (default 5.0)")
        sys.exit(1)

    bag_path = sys.argv[1]
    topic = sys.argv[2]
    expected_fps = float(sys.argv[3]) if len(sys.argv) > 3 else 10.0
    drop_threshold = float(sys.argv[4]) if len(sys.argv) > 4 else 5.0

    analyze_frame_drops(bag_path, topic, expected_fps, drop_threshold)
