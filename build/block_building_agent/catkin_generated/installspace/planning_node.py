#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Block Planning ROS Node
订阅：/vision/blocks_info
发布：/planning/construction_plan
"""
import rospy
import json
from std_msgs.msg import String
from block_building_agent.graph.builder import construction_app


class BlockPlanningNode:
    def __init__(self):
        rospy.init_node('block_planning_node', anonymous=True)
        rospy.loginfo("Block Planning Node Started")
        
        rospy.Subscriber('/vision/blocks_info', String, self.vision_callback)
        self.plan_pub = rospy.Publisher('/planning/construction_plan', String, queue_size=10)
        
        rospy.loginfo("Waiting for blocks info...")
    
    def vision_callback(self, msg):
        try:
            rospy.loginfo("Received blocks info")
            blocks_info = json.loads(msg.data)
            rospy.loginfo("Starting LangGraph invocation...")
            
            result = construction_app.invoke({
                "input_blocks": blocks_info,
                "iteration_count": 0,
                "max_iterations": 3,
                "is_valid": False,
                "build_validation_feedback": "",
                "build_validation_errors": [],
                "current_plan": [],
                "final_plan": None,
                "messages": []
            })
            
            plan_data = result.get('final_plan') or result.get('current_plan') or []
            rospy.loginfo(f"Plan data: {plan_data}")
            
            plan_msg = String()
            plan_msg.data = json.dumps(plan_data, ensure_ascii=False)
            self.plan_pub.publish(plan_msg)
            rospy.loginfo("Published construction plan")
            
        except Exception as e:
            rospy.logerr(f"Error: {e}")
            import traceback
            rospy.logerr(traceback.format_exc())
    
    def run(self):
        rospy.spin()


if __name__ == '__main__':
    try:
        node = BlockPlanningNode()
        node.run()
    except rospy.ROSInterruptException:
        pass
    except Exception as e:
        rospy.logerr(f"Fatal: {e}")
        import sys
        sys.exit(1)