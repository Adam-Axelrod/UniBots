#!/usr/bin/env python3
import math
import rclpy
from rclpy.node import Node

from std_msgs.msg import Float32, Float32MultiArray
from geometry_msgs.msg import Twist

from .world_model import WorldModel, ClusterInfo, AprilTagInfo
from .fsm import BrainFSM, State
from . import params


class BrainNode(Node):

    def __init__(self):
        super().__init__('brain_node')

        # -------- Parameters --------
        self.declare_parameter('tick_hz', 10.0)
        self.declare_parameter('cluster_topic', '/ball/cluster')
        self.declare_parameter('range_topic', '/sensors/range')
        self.declare_parameter('heading_topic', '/sensors/heading_deg')
        self.declare_parameter('april_topic', '/apriltags/detections')
        self.declare_parameter('home_wall', 'North')
        self.declare_parameter('go_home_trigger_s', params.GO_HOME_TRIGGER_S)

        tick_hz = float(self.get_parameter('tick_hz').value)
        self.cluster_topic = str(self.get_parameter('cluster_topic').value)
        self.range_topic = str(self.get_parameter('range_topic').value)
        self.heading_topic = str(self.get_parameter('heading_topic').value)
        self.april_topic = str(self.get_parameter('april_topic').value)
        self.home_wall = str(self.get_parameter('home_wall').value)
        self.go_home_trigger_s = float(self.get_parameter('go_home_trigger_s').value)

        # -------- Sensor Storage --------
        self.last_cluster_raw = None
        self.last_range_cm = None
        self.last_heading_deg = None
        self.last_april_raw = None

        # -------- Subscribers --------
        self.create_subscription(
            Float32MultiArray,
            self.cluster_topic,
            self.cluster_cb,
            10
        )

        self.create_subscription(
            Float32,
            self.range_topic,
            self.range_cb,
            10
        )

        self.create_subscription(
            Float32,
            self.heading_topic,
            self.heading_cb,
            10
        )

        self.create_subscription(
            Float32MultiArray,
            self.april_topic,
            self.april_cb,
            10
        )

        # -------- Publisher --------
        self.cmd_pub = self.create_publisher(
            Twist,
            '/cmd_vel',
            10
        )

        # -------- FSM --------
        self.fsm = BrainFSM()

        # -------- Time --------
        self.start_s = self.get_clock().now().nanoseconds * 1e-9

        # -------- Timer --------
        period = 1.0 / max(tick_hz, 0.1)
        self.timer = self.create_timer(period, self.tick)

        self.get_logger().info(
            f"Brain node @ {tick_hz:.1f}Hz | sub: {self.cluster_topic}, {self.range_topic}, "
            f"{self.heading_topic}, {self.april_topic} | home_wall={self.home_wall}"
        )

    # --------------------------------
    # Sensor Callbacks
    # --------------------------------

    def cluster_cb(self, msg: Float32MultiArray):
        if len(msg.data) == 0:
            self.last_cluster_raw = None
        else:
            self.last_cluster_raw = list(msg.data)

    def range_cb(self, msg: Float32):
        val = float(msg.data)
        self.last_range_cm = None if math.isnan(val) else val

    def heading_cb(self, msg: Float32):
        val = float(msg.data)
        self.last_heading_deg = None if math.isnan(val) else val

    def april_cb(self, msg: Float32MultiArray):
        self.last_april_raw = list(msg.data) if msg.data else None

    # --------------------------------
    # Helper
    # --------------------------------

    def _parse_cluster(self):

        if self.last_cluster_raw is None:
            return None

        data = self.last_cluster_raw

        if len(data) < 5:
            return None

        return ClusterInfo(
            side=float(data[0]),
            cx=float(data[1]),
            cy=float(data[2]),
            count=float(data[3]),
            num_clusters=float(data[4])
        )

    def _parse_april_tags(self):
        """Parse Float32MultiArray: [num, id0, cx0, cy0, area0, c0x,c0y,c1x,c1y,c2x,c2y,c3x,c3y, ...]"""
        if self.last_april_raw is None or len(self.last_april_raw) < 1:
            return None
        data = self.last_april_raw
        n = int(data[0])
        if n == 0:
            return []
        tags = []
        i = 1
        floats_per_tag = 12
        for _ in range(n):
            if i + floats_per_tag > len(data):
                break
            tag_id = int(data[i])
            cx = float(data[i + 1])
            cy = float(data[i + 2])
            area = float(data[i + 3])
            corners = [
                (float(data[i + 4]), float(data[i + 5])),
                (float(data[i + 6]), float(data[i + 7])),
                (float(data[i + 8]), float(data[i + 9])),
                (float(data[i + 10]), float(data[i + 11])),
            ]
            tags.append(AprilTagInfo(tag_id=tag_id, center_x=cx, center_y=cy, area=area, corners=corners))
            i += floats_per_tag
        return tags

    def _state_label(self, st: State):

        if st == State.ALIGN:
            return "align"

        if st == State.DRIVE:
            return "drive"

        if st == State.SEARCH:
            return "search"

        if st == State.AVOID:
            return "avoid"

        if st == State.GO_HOME:
            return "go_home"

        return str(st)

    # --------------------------------
    # Main Loop
    # --------------------------------

    def tick(self):

        now_s = self.get_clock().now().nanoseconds * 1e-9
        elapsed_s = now_s - self.start_s

        cluster = self._parse_cluster()
        april_tags = self._parse_april_tags()

        # Trigger go-home when approaching end of match
        should_go_home = elapsed_s >= (params.RUN_TIME_S - self.go_home_trigger_s)
        if should_go_home and self.fsm.state != State.GO_HOME:
            self.fsm.state = State.GO_HOME
            self.fsm.enter_go_home()

        wm = WorldModel(
            range_cm=self.last_range_cm,
            cluster=cluster,
            heading_deg=self.last_heading_deg,
            april_tags=april_tags,
            home_wall=self.home_wall,
            should_go_home=should_go_home,
            now_s=now_s,
            elapsed_s=elapsed_s
        )

        state, cmd = self.fsm.update(wm)

        # -------- Publish Twist --------
        twist = Twist()
        twist.linear.x = cmd.linear_x
        twist.angular.z = cmd.angular_z

        self.cmd_pub.publish(twist)

        # -------- Debug Print --------
        if cluster is None:
            cluster_str = "cluster=[]"
        else:
            cluster_str = (
                f"cluster=[side={cluster.side:+.3f}, "
                f"cx={cluster.cx:.1f}, cy={cluster.cy:.1f}, "
                f"counting={cluster.count:.0f}, nclusters={cluster.num_clusters:.0f}]"
            )

        dist_str = "range=None" if wm.range_cm is None else f"range={wm.range_cm:.1f}"
        head_str = "heading=None" if wm.heading_deg is None else f"heading={wm.heading_deg:.1f}"

        print(
            f"t={elapsed_s:6.1f}s "
            f"state={self._state_label(state):9s} "
            f"{cluster_str} "
            f"{dist_str} "
            f"{head_str} "
            f"cmd=({cmd.linear_x:.2f},{cmd.angular_z:.2f})"
        )


# --------------------------------
# Main
# --------------------------------

def main(args=None):

    rclpy.init(args=args)

    node = BrainNode()

    try:
        rclpy.spin(node)

    except KeyboardInterrupt:
        pass

    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
