#!/usr/bin/env python3
import sys
import csv
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

try:
    import rosbag
except ImportError:
    print("Could not import rosbag. Run in a ROS1 environment: source /opt/ros/noetic/setup.bash", file=sys.stderr)
    sys.exit(1)


def extract_odom(bag_file, topic_name):
    xs, ys, zs, times = [], [], [], []
    t0 = None
    with rosbag.Bag(bag_file, 'r') as bag:
        for topic, msg, t in bag.read_messages(topics=[topic_name]):
            if t0 is None:
                t0 = t.to_sec()
            pos = msg.pose.pose.position
            xs.append(pos.x)
            ys.append(pos.y)
            zs.append(pos.z)
            times.append(t.to_sec() - t0)
    return xs, ys, zs, times


def save_csv(bag_file, topic_name, xs, ys, zs, times):
    stem = os.path.splitext(os.path.basename(bag_file))[0]
    topic_tag = topic_name.replace('/', '_').strip('_')
    csv_file = f"{stem}_{topic_tag}_odom.csv"
    with open(csv_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['time_s', 'x', 'y', 'z'])
        for row in zip(times, xs, ys, zs):
            writer.writerow(row)
    print(f"Saved: {csv_file} ({len(xs)} rows)")


def plot_odom(bag_file, topic_name, xs, ys, zs, times):
    stem = os.path.splitext(os.path.basename(bag_file))[0]
    topic_tag = topic_name.replace('/', '_').strip('_')

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    axes[0].plot(xs, ys, linewidth=0.8)
    axes[0].set_xlabel('X (m)')
    axes[0].set_ylabel('Y (m)')
    axes[0].set_title('Odometry Trajectory (XY)')
    axes[0].set_aspect('equal')
    axes[0].grid(True)

    axes[1].plot(times, xs, label='X')
    axes[1].plot(times, ys, label='Y')
    axes[1].plot(times, zs, label='Z')
    axes[1].set_xlabel('Time (s)')
    axes[1].set_ylabel('Position (m)')
    axes[1].set_title('Odometry Over Time')
    axes[1].legend()
    axes[1].grid(True)

    plt.tight_layout()
    plot_file = f"{stem}_{topic_tag}_odom.png"
    plt.savefig(plot_file, dpi=150)
    print(f"Saved: {plot_file}")


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: python3 ExtractOdom.py <bagname>.bag <topicname>")
        sys.exit(1)

    bag_file = sys.argv[1]
    topic_name = sys.argv[2]

    print(f"Extracting odometry from {bag_file}, topic: {topic_name}")
    xs, ys, zs, times = extract_odom(bag_file, topic_name)
    print(f"  Extracted {len(xs)} messages")

    if not xs:
        print("No messages found on that topic.")
        sys.exit(1)

    save_csv(bag_file, topic_name, xs, ys, zs, times)
    plot_odom(bag_file, topic_name, xs, ys, zs, times)
