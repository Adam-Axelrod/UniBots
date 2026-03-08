#!/usr/bin/env python3
import rclpy
from rclpy.node import Node

from std_msgs.msg import Float32, Float32MultiArray

from .world_model import WorldModel, ClusterInfo
from .fsm import BrainFSM, State


class BrainNode(Node):
    def __init__(self):
        super().__init__('brain_node')

        # Params
        self.declare_parameter('tick_hz', 10.0)
        self.declare_parameter('cluster_topic', '/ball/cluster')
        self.declare_parameter('range_topic', '/sensors/range_cm')
        self.declare_parameter('heading_topic', '/sensors/heading_deg')  # optional
        self.declare_parameter('print_every_tick', True)

        tick_hz = float(self.get_parameter('tick_hz').value)
        self.cluster_topic = str(self.get_parameter('cluster_topic').value)
        self.range_topic = str(self.get_parameter('range_topic').value)
        self.heading_topic = str(self.get_parameter('heading_topic').value)
        self.print_every_tick = bool(self.get_parameter('print_every_tick').value)

        # Latest sensor values
        self.last_cluster_raw = None   # list[float] or None
        self.last_range_cm = None      # float or None
        self.last_heading_deg = None   # float or None

        # Subscriptions
        self.create_subscription(Float32MultiArray, self.cluster_topic, self.cluster_cb, 10)
        self.create_subscription(Float32, self.range_topic, self.range_cb, 10)
        self.create_subscription(Float32, self.heading_topic, self.heading_cb, 10)

        # FSM
        self.fsm = BrainFSM()

        # Start time
        self.start_s = self.get_clock().now().nanoseconds * 1e-9

        # Tick timer
        period = 1.0 / max(tick_hz, 0.1)
        self.timer = self.create_timer(period, self.tick)

        self.get_logger().info(
            f"Brain PRINT mode @ {tick_hz:.1f}Hz | sub: {self.cluster_topic}, {self.range_topic}, {self.heading_topic}"
        )

        self._last_print_state = None

    def cluster_cb(self, msg: Float32MultiArray):
        self.last_cluster_raw = list(msg.data) if msg.data else None

    def range_cb(self, msg: Float32):
        self.last_range_cm = float(msg.data)

    def heading_cb(self, msg: Float32):
        self.last_heading_deg = float(msg.data)

    def _parse_cluster(self):
        """
        YOLO cluster message format:
          [side, cx, cy, count, num_clusters]
        or [] for none
        """
        if not self.last_cluster_raw:
            return None
        data = self.last_cluster_raw
        if len(data) < 5:
            return None
        return ClusterInfo(
            side=float(data[0]),
            cx=float(data[1]),
            cy=float(data[2]),
            count=float(data[3]),
            num_clusters=float(data[4]),
        )

    def _state_label(self, st: State) -> str:
        if st == State.ALIGN:
            return "align"
        if st == State.DRIVE:
            return "drive_fwd"
        if st == State.SEARCH:
            return "search"
        if st == State.AVOID:
            return "avoid"
        if st == State.GO_HOME:
            return "go_home"
        return str(st)

    def tick(self):
        now_s = self.get_clock().now().nanoseconds * 1e-9
        elapsed_s = now_s - self.start_s

        cluster = self._parse_cluster()

        wm = WorldModel(
            range_cm=self.last_range_cm,
            cluster=cluster,
            heading_deg=self.last_heading_deg,
            now_s=now_s,
            elapsed_s=elapsed_s,
        )

        state, _cmd = self.fsm.update(wm)

        # ---- Print continuously ----
        # (This will be ~10 lines/sec by default.)
        if self.print_every_tick:
            if cluster is None:
                cluster_str = "cluster=[]"
            else:
                cluster_str = (
                    f"cluster=[side={cluster.side:+.0f}, "
                    f"cx={cluster.cx:.1f}, cy={cluster.cy:.1f}, "
                    f"count={cluster.count:.0f}, nclusters={cluster.num_clusters:.0f}]"
                )

            dist_str = "range_cm=None" if wm.range_cm is None else f"range_cm={wm.range_cm:.1f}"
            head_str = "heading=None" if wm.heading_deg is None else f"heading={wm.heading_deg:.1f}"

            print(
                f"t={elapsed_s:6.1f}s  state={self._state_label(state):9s}  "
                f"{cluster_str}  {dist_str}  {head_str}"
            )


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
