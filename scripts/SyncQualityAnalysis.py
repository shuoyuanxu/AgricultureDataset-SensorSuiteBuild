#!/usr/bin/env python3
"""
Analyze time synchronization quality of cameras and LiDARs from a ROS bag file.
Topics are configured in the TOPICS dict below.

Usage: python3 SyncQualityAnalysis.py <bagname>.bag [--bag-time]
"""

import sys
import os
import argparse
import numpy as np
from collections import defaultdict

try:
    import rosbag
except ImportError:
    print("Could not import rosbag. Run in a ROS1 environment: source /opt/ros/noetic/setup.bash", file=sys.stderr)
    sys.exit(1)

TOPICS = {
    'cameras': [
        '/forwardRight/image_raw/compressed',
        '/forwardLeft/image_raw/compressed',
    ],
    'lidars': [
        '/ouster/points',
        '/velodyne_points',
    ],
}


def extract_timestamps(bag_file, use_header_time=True):
    print(f"Reading: {bag_file}  ({'header' if use_header_time else 'bag'} time)")

    timestamps = defaultdict(list)
    all_topics = TOPICS['cameras'] + TOPICS['lidars']

    with rosbag.Bag(bag_file) as bag:
        for topic, msg, t in bag.read_messages(topics=all_topics):
            if use_header_time:
                timestamps[topic].append(msg.header.stamp.to_sec())
            else:
                timestamps[topic].append(t.to_sec())

    for topic in timestamps:
        timestamps[topic] = np.array(timestamps[topic])
        print(f"  {topic}: {len(timestamps[topic])} messages")

    return timestamps


def find_closest_pairs(ts1, ts2, max_time_diff=0.05):
    matched_ts1, matched_ts2, time_diffs = [], [], []
    used = set()
    for t1 in ts1:
        diffs = np.abs(ts2 - t1)
        for idx in np.argsort(diffs):
            if idx not in used and diffs[idx] <= max_time_diff:
                matched_ts1.append(t1)
                matched_ts2.append(ts2[idx])
                time_diffs.append(ts2[idx] - t1)
                used.add(idx)
                break
    return np.array(matched_ts1), np.array(matched_ts2), np.array(time_diffs)


def print_rate_stats(topic, ts):
    if len(ts) < 2:
        print(f"  {topic}: too few messages")
        return
    diffs = np.diff(ts)
    print(f"\n{topic}:")
    print(f"  Messages  : {len(ts)}")
    print(f"  Rate      : {1.0 / np.mean(diffs):.2f} Hz")
    print(f"  Period    : {np.mean(diffs)*1000:.2f} ± {np.std(diffs)*1000:.2f} ms")
    print(f"  Min/Max   : {np.min(diffs)*1000:.2f} / {np.max(diffs)*1000:.2f} ms")


def print_sync_stats(label, ts_ref, ts_other, ref_name):
    _, _, diffs = find_closest_pairs(ts_ref, ts_other, max_time_diff=0.05)
    diffs_ms = diffs * 1000
    match_rate = len(diffs_ms) / len(ts_ref) * 100
    print(f"\n{label} vs {ref_name}:")
    print(f"  Matched   : {len(diffs_ms)} / {len(ts_ref)} ({match_rate:.1f}%)")
    print(f"  Mean(sig) : {np.mean(diffs_ms):+.2f} ms")
    print(f"  Mean ABS  : {np.mean(np.abs(diffs_ms)):.2f} ms")
    print(f"  Std       : {np.std(diffs_ms):.2f} ms")
    print(f"  Max ABS   : {np.max(np.abs(diffs_ms)):.2f} ms")
    print(f"  95th pct  : {np.percentile(np.abs(diffs_ms), 95):.2f} ms")


def analyze(timestamps):
    cameras = [t for t in TOPICS['cameras'] if t in timestamps]
    lidars = [t for t in TOPICS['lidars'] if t in timestamps]

    print("\n" + "=" * 70)
    print("1. FRAME RATES")
    print("=" * 70)
    for topic in timestamps:
        print_rate_stats(topic, timestamps[topic])

    if len(cameras) > 1:
        print("\n" + "=" * 70)
        print("2. CAMERA SYNCHRONIZATION")
        print("=" * 70)
        ref = cameras[0]
        for cam in cameras[1:]:
            print_sync_stats(cam, timestamps[ref], timestamps[cam], ref)

    if len(lidars) == 2:
        print("\n" + "=" * 70)
        print("3. LIDAR SYNCHRONIZATION")
        print("=" * 70)
        print_sync_stats(lidars[1], timestamps[lidars[0]], timestamps[lidars[1]], lidars[0])

    if cameras and lidars:
        print("\n" + "=" * 70)
        print("4. CAMERA-LIDAR SYNCHRONIZATION")
        print("=" * 70)
        ref = cameras[0]
        for lidar in lidars:
            print_sync_stats(lidar, timestamps[ref], timestamps[lidar], ref)

    if lidars and len(lidars) >= 1:
        ref_lidar = lidars[0]
        others = [t for t in cameras + lidars if t != ref_lidar]
        if others:
            print("\n" + "=" * 70)
            print(f"5. ALL SENSORS vs {ref_lidar} (reference)")
            print("=" * 70)
            for topic in others:
                print_sync_stats(topic, timestamps[ref_lidar], timestamps[topic], ref_lidar)


def main():
    parser = argparse.ArgumentParser(
        description='Analyze camera/LiDAR time sync quality from a ROS bag file.'
    )
    parser.add_argument('bag_file', help='Path to ROS bag file')
    parser.add_argument('--bag-time', action='store_true',
                        help='Use bag recording time instead of header time')
    args = parser.parse_args()

    if not os.path.exists(args.bag_file):
        print(f"ERROR: File not found: {args.bag_file}", file=sys.stderr)
        sys.exit(1)

    timestamps = extract_timestamps(args.bag_file, use_header_time=not args.bag_time)

    if not timestamps:
        print("No messages found on configured topics. Check TOPICS in script.", file=sys.stderr)
        sys.exit(1)

    analyze(timestamps)
    print("\n" + "=" * 70)
    print("Analysis complete.")
    print("=" * 70)


if __name__ == '__main__':
    main()
