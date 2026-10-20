"""Bounded read-only ROS graph inspection in a dedicated Domain context."""
import argparse
import json
import os
from pathlib import Path
import time
from console_support import read_json

def main():
    import rclpy
    from rclpy.context import Context
    from rclpy.executors import SingleThreadedExecutor
    p=argparse.ArgumentParser();p.add_argument('--config',type=Path,required=True);args=p.parse_args()
    config=read_json(args.config);os.environ.update(ROS_LOCALHOST_ONLY='1' if config['localhost_only'] else '0',RMW_IMPLEMENTATION=config['rmw']);ctx=Context();rclpy.init(context=ctx,domain_id=config['domain_id']);node=rclpy.create_node('robot_station_graph_probe',context=ctx);executor=SingleThreadedExecutor(context=ctx);executor.add_node(node)
    try:
        until=time.monotonic()+1.5
        while time.monotonic()<until:executor.spin_once(timeout_sec=.1)
        topics=dict(node.get_topic_names_and_types());rows=[]
        for camera,row in config['topics'].items():
            publishers=[]
            for pub in node.get_publishers_info_by_topic(row['topic']):
                reliability=pub.qos_profile.reliability.name.lower();durability=pub.qos_profile.durability.name.lower()
                compatible=pub.topic_type==row['message_type'] and not(row['reliability']=='reliable' and reliability=='best_effort')
                publishers.append({'node':pub.node_name,'namespace':pub.node_namespace,'type':pub.topic_type,'reliability':reliability,'durability':durability,'depth':pub.qos_profile.depth,'compatible':compatible})
            rows.append({'camera':camera,'topic':row['topic'],'expected_type':row['message_type'],'requested_reliability':row['reliability'],'advertised_types':topics.get(row['topic'],[]),'publishers':publishers,'reason':'未发现发布者：检查 Domain、网卡、话题和发布节点' if not publishers else '类型或 QoS 不兼容' if not any(v['compatible'] for v in publishers) else '发现兼容发布者；实际帧见桥接状态'})
        print(json.dumps({'ok':True,'domain_id':config['domain_id'],'topics':rows}))
    finally:executor.shutdown();node.destroy_node();ctx.shutdown()

if __name__=='__main__':main()
