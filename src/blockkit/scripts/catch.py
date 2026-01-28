#!/usr/bin/env python3
# -*- coding=UTF-8 -*-
from std_msgs.msg import String, Bool, Empty
import time
import rospy, sys
from rm_msgs.msg import MoveJ_P, Arm_Current_State, Gripper_Set, Gripper_Pick, ArmState, MoveL, MoveJ, set_modbus_mode, write_register, write_single_register, Tool_Analog_Output
from geometry_msgs.msg import Pose
import numpy as np
from scipy.spatial.transform import Rotation as R
from blockkit.msg import ObjectInfo
from geometry_msgs.msg import TransformStamped, PointStamped
from geometry_msgs.msg import Point, Quaternion
import actionlib
from geometry_msgs.msg import Pose
from move_base_msgs.msg import MoveBaseAction, MoveBaseGoal
from actionlib import SimpleActionClient
from actionlib import GoalStatus

# 相机坐标系到机械臂末端坐标系的旋转矩阵，通过手眼标定得到
rotation_matrix = np.array([[0, 1, 0],
                            [-1, 0, 0],
                            [0, 0, 1]])
# 相机坐标系到机械臂末端坐标系的平移向量，通过手眼标定得到
translation_vector = np.array([-0.08039019, 0.03225555, -0.09756825])

# --- 新增或修改全局变量 ---
# 定义任务队列，每个元素是一个字典，包含目标类别和目标位置
# 先预定义一个任务列表，后续换成推算位置
task_queue = [
    {'target_class': 'cube', 'target_place': [0.5, 0.0, 0.1]},  # 
    {'target_class': 'cuboid', 'target_place': [0.5, 0.1, 0.1]},
    {'target_class': 'triangle', 'target_place': [0.5, 0.2, 0.1]},
]
# 当前正在执行的任务
current_task = None
# 标记是否正在执行任务
is_executing = False
# 标记是否完成所有任务
tasks_completed = False

# 相机坐标系物体到机械臂基坐标系转换函数
def convert(x, y, z, x1, y1, z1, rx, ry, rz):
    """
    函数功能：我们需要将旋转向量和平移向量转换为齐次变换矩阵，然后使用深度相机识别到的物体坐标（x, y, z）和
    机械臂末端的位姿（x1,y1,z1,rx,ry,rz）来计算物体相对于机械臂基座的位姿（x, y, z, rx, ry, rz）
    输入参数：深度相机识别到的物体坐标（x, y, z）和机械臂末端的位姿（x1,y1,z1,rx,ry,rz）
    返回值：物体在机械臂基座坐标系下的位置（x, y, z）
    """
    global rotation_matrix, translation_vector
    obj_camera_coordinates = np.array([x, y, z])

    # 机械臂末端的位姿，单位为弧度
    end_effector_pose = np.array([x1, y1, z1,
                                  rx, ry, rz])
    # 将旋转矩阵和平移向量转换为齐次变换矩阵
    T_camera_to_end_effector = np.eye(4)
    T_camera_to_end_effector[:3, :3] = rotation_matrix
    T_camera_to_end_effector[:3, 3] = translation_vector
    # 机械臂末端的位姿转换为齐次变换矩阵
    position = end_effector_pose[:3]
    orientation = R.from_euler('xyz', end_effector_pose[3:], degrees=False).as_matrix()
    T_base_to_end_effector = np.eye(4)
    T_base_to_end_effector[:3, :3] = orientation
    T_base_to_end_effector[:3, 3] = position
    # 计算物体相对于机械臂基座的位姿
    obj_camera_coordinates_homo = np.append(obj_camera_coordinates, [1])  # 将物体坐标转换为齐次坐标
    #obj_end_effector_coordinates_homo = np.linalg.inv(T_camera_to_end_effector).dot(obj_camera_coordinates_homo)
    obj_end_effector_coordinates_homo = T_camera_to_end_effector.dot(obj_camera_coordinates_homo)
    obj_base_coordinates_homo = T_base_to_end_effector.dot(obj_end_effector_coordinates_homo)
    obj_base_coordinates = obj_base_coordinates_homo[:3]  # 从齐次坐标中提取物体的x, y, z坐标
    # 计算物体的旋转
    obj_orientation_matrix = T_base_to_end_effector[:3, :3].dot(rotation_matrix)
    obj_orientation_euler = R.from_matrix(obj_orientation_matrix).as_euler('xyz', degrees=False)
    # 组合结果
    obj_base_pose = np.hstack((obj_base_coordinates, obj_orientation_euler))
    obj_base_pose[3:] = rx, ry, rz
    return obj_base_pose

# 接收到识别物体的回调函数
def object_pose_callback(data):
    """
    函数功能：每帧图像经过识别后的回调函数，检查是否检测到当前任务需要的物体。
              若检测到，则执行抓取-放置流程。
    输入参数：data (ObjectInfo) - 检测到的物体信息
    返回值：无
    """
    global current_task, is_executing, task_queue, tasks_completed

    # 如果没有当前任务或正在执行任务，则忽略
    if not current_task or is_executing or tasks_completed:
        return

    # 判断当前检测到的物体是否是当前任务的目标
    if data.object_class == current_task['target_class']:
        print(f"Detected target object: {data.object_class} at ({data.x}, {data.y}, {data.z})")

        # 设置执行标志
        is_executing = True

        try:
            # 1. 等待当前的机械臂位姿
            arm_pose_msg = rospy.wait_for_message("/rm_driver/Arm_Current_State", Arm_Current_State, timeout=10.0)
            arm_orientation_msg = rospy.wait_for_message("/rm_driver/ArmCurrentState", ArmState, timeout=10.0)

            # 2. 计算机械臂基坐标系下的物体坐标
            result = convert(data.x, data.y, data.z,
                             arm_pose_msg.Pose[0], arm_pose_msg.Pose[1], arm_pose_msg.Pose[2],
                             arm_pose_msg.Pose[3], arm_pose_msg.Pose[4], arm_pose_msg.Pose[5])
            print(f"Target {data.object_class} converted pose in base frame: {result[:3]}")

            # 3. 执行抓取-放置动作
            success = catch_and_place(result, arm_orientation_msg, current_task['target_place'])
            if success:
                print(f"Successfully handled task for {current_task['target_class']}")

                # 4. 更新任务
                if task_queue:
                    current_task = task_queue.pop(0) # 获取下一个任务
                    print(f"Moving to next task: Target Class {current_task['target_class']}, Place {current_task['target_place']}")
                else:
                    current_task = None
                    tasks_completed = True
                    print("All tasks completed!")
            else:
                print(f"Failed to handle task for {current_task['target_class']}. Stopping.")
                # 可以选择继续尝试当前任务，或跳过，或停止
                # 这里暂时停止
                tasks_completed = True
                current_task = None

        except rospy.ROSException as e:
            print(f"Error waiting for messages during task execution: {e}")
            # 可能需要重置或跳过当前任务
            if task_queue:
                 current_task = task_queue.pop(0)
            else:
                 current_task = None
                 tasks_completed = True

        finally:
            # 清除执行标志
            is_executing = False
    # else:
        # print(f"Ignoring detected object: {data.object_class}, expecting: {current_task['target_class'] if current_task else 'None'}")


def movej_type(joint, speed):
    '''
    函数功能：通过输入机械臂每个关节的数值（弧度），让机械臂以指定速度（0-1，最好小于0.5，否则太快）运动到指定姿态
    输入参数：[joint1,joint2,joint3,joint4,joint5,joint6]、speed
    返回值：bool - 发布消息是否成功
    '''
    try:
        moveJ_pub = rospy.Publisher("/rm_driver/MoveJ_Cmd", MoveJ, queue_size=1)
        rospy.sleep(0.5)
        move_joint = MoveJ()
        move_joint.joint = joint
        move_joint.speed = speed
        moveJ_pub.publish(move_joint)
        return True
    except Exception as e:
        rospy.logerr(f"Error publishing MoveJ command: {e}")
        return False


def movejp_type(pose, speed):
    '''
    函数功能：通过输入机械臂末端的位姿数值，让机械臂以指定速度（0-1，最好小于0.5，否则太快）运动到指定位姿
    输入参数：pose（position.x、position.y、position.z、orientation.x、orientation.y、orientation.z、orientation.w）、speed
    返回值：bool - 发布消息是否成功
    '''
    try:
        moveJ_P_pub = rospy.Publisher("rm_driver/MoveJ_P_Cmd", MoveJ_P, queue_size=1)
        rospy.sleep(0.5)
        move_joint_pose = MoveJ_P()
        move_joint_pose.Pose.position.x = pose[0]
        move_joint_pose.Pose.position.y = pose[1]
        move_joint_pose.Pose.position.z = pose[2]
        move_joint_pose.Pose.orientation.x = pose[3]
        move_joint_pose.Pose.orientation.y = pose[4]
        move_joint_pose.Pose.orientation.z =  pose[5]
        move_joint_pose.Pose.orientation.w =  pose[6]
        move_joint_pose.speed = speed
        moveJ_P_pub.publish(move_joint_pose)
        return True
    except Exception as e:
        rospy.logerr(f"Error publishing MoveJ_P command: {e}")
        return False


def movel_type(pose, speed):
    '''
    函数功能：通过输入机械臂末端的位姿数值，让机械臂以指定速度（0-1，最好小于0.5，否则太快）直线运动到指定位姿
    输入参数：pose（position.x、position.y、position.z、orientation.x、orientation.y、orientation.z、orientation.w）、speed
    返回值：bool - 发布消息是否成功
    '''
    try:
        moveL_pub = rospy.Publisher("rm_driver/MoveL_Cmd", MoveL, queue_size=1)
        rospy.sleep(0.5)
        move_line_pose = MoveL()
        move_line_pose.Pose.position.x = pose[0]
        move_line_pose.Pose.position.y = pose[1]
        move_line_pose.Pose.position.z = pose[2]
        move_line_pose.Pose.orientation.x = pose[3]
        move_line_pose.Pose.orientation.y = pose[4]
        move_line_pose.Pose.orientation.z =  pose[5]
        move_line_pose.Pose.orientation.w =  pose[6]
        move_line_pose.speed = speed
        moveL_pub.publish(move_line_pose)
        return True
    except Exception as e:
        rospy.logerr(f"Error publishing MoveL command: {e}")
        return False

def arm_ready_pose():
    '''
    函数功能：执行整个抓取流程前先运动到一个能够稳定获取物体坐标信息的姿态，让机械臂在此姿态下获取识别物体的三维坐标，机械臂以关节运动的方式到达拍照姿态，
    此关节数值可以根据示教得到，将机械臂通过按住绿色按钮拖动到能够获取较好效果的姿态
    输入参数：无
    返回值：bool - 发布消息是否成功
    '''
    try:
        moveJ_pub = rospy.Publisher("/rm_driver/MoveJ_Cmd", MoveJ, queue_size=1)
        rospy.sleep(1)
        pic_joint = MoveJ()
        pic_joint.joint = [-0.09342730045318604, -0.8248963952064514, 1.5183943510055542, 0.06789795309305191, 0.8130478262901306, 0.015879500657320023]
        pic_joint.speed = 0.3
        moveJ_pub.publish(pic_joint)
        return True
    except Exception as e:
        rospy.logerr(f"Error publishing arm_ready_pose command: {e}")
        return False


def catch_and_place(obj_pose_in_base, arm_orientation_msg, target_place_pose):
    """
    函数功能：执行抓取-移动-放置的完整流程。
    输入参数：
        obj_pose_in_base (np.array): 物体在机械臂基坐标系下的位姿 [x, y, z, rx, ry, rz]
        arm_orientation_msg (ArmState): 机械臂当前的位姿四元数消息
        target_place_pose (list): 目标放置位置 [x, y, z]
    返回值：bool - 操作是否成功
    """
    try:
        print('Starting catch-and-place sequence...')
        
        # --- Step 1: 移动到预抓取位置 ---

        print(f'  Moving to object near: {obj_pose_in_base[:3]}')

        approach_offset = 0.07

        if not movejp_type([
            obj_pose_in_base[0],
            obj_pose_in_base[1],
            obj_pose_in_base[2]+ approach_offset,
            arm_orientation_msg.Pose.orientation.x,
            arm_orientation_msg.Pose.orientation.y,
            arm_orientation_msg.Pose.orientation.z,
            arm_orientation_msg.Pose.orientation.w
        ], 0.3):
            rospy.logerr("Failed to move near object.")
            return False
        rospy.sleep(4) # Wait for movement to complete

        # --- Step 2: 移动到抓取位置 ---

        print(f'  Moving to object: {obj_pose_in_base[:3]}')
        if not movel_type([
            obj_pose_in_base[0],
            obj_pose_in_base[1],
            obj_pose_in_base[2],
            arm_orientation_msg.Pose.orientation.x,
            arm_orientation_msg.Pose.orientation.y,
            arm_orientation_msg.Pose.orientation.z,
            arm_orientation_msg.Pose.orientation.w
        ], 0.3):
            rospy.logerr("Failed to move to object.")
            return False
        rospy.sleep(4)

        # --- Step 3: 关闭夹爪 ---

        print('  Closing gripper...')

        gripper_close()
        rospy.sleep(4) # Allow time for gripping

        # --- Step 4: 移动到安全高度 ---

        print(f'  Moving to safety height: {obj_pose_in_base[:3]}')
        safety_height_offset = 0.1
        if not movel_type([
            obj_pose_in_base[0],
            obj_pose_in_base[1],
            obj_pose_in_base[2] + safety_height_offset,
            arm_orientation_msg.Pose.orientation.x,
            arm_orientation_msg.Pose.orientation.y,
            arm_orientation_msg.Pose.orientation.z,
            arm_orientation_msg.Pose.orientation.w
        ], 0.3):
            rospy.logerr("Failed to move to safety height.")
            return False
        rospy.sleep(4)

        # --- Step 5: 移动到预放置位置 ---
        print(f'  Moving to target place: {target_place_pose}')
      
        place_above_offset = 0.1
        if not movejp_type([
            target_place_pose[0],
            target_place_pose[1],
            target_place_pose[2] + place_above_offset, 
            arm_orientation_msg.Pose.orientation.x,
            arm_orientation_msg.Pose.orientation.y,
            arm_orientation_msg.Pose.orientation.z,
            arm_orientation_msg.Pose.orientation.w
        ], 0.3):
            rospy.logerr("Failed to move above target place.")
            return False
        rospy.sleep(4)

        # --- Step 6: 移动到放置位置 ---
        print(f'  Moving down to place...')

        if not movel_type([
            target_place_pose[0],
            target_place_pose[1],
            target_place_pose[2],
            arm_orientation_msg.Pose.orientation.x,
            arm_orientation_msg.Pose.orientation.y,
            arm_orientation_msg.Pose.orientation.z,
            arm_orientation_msg.Pose.orientation.w
        ], 0.3):
            rospy.logerr("Failed to move down to place.")
            return False
        rospy.sleep(4)

        # --- Step 7: Open gripper to release object ---
        print('  Opening gripper...')
        gripper_open()
        rospy.sleep(4) # Allow time for releasing

        # --- Step 8: 移动到安全位置 ---
        print(f'  Moving to safety position...')

        if not movel_type([
            target_place_pose[0],
            target_place_pose[1],
            target_place_pose[2] + safety_height_offset,
            arm_orientation_msg.Pose.orientation.x,
            arm_orientation_msg.Pose.orientation.y,
            arm_orientation_msg.Pose.orientation.z,
            arm_orientation_msg.Pose.orientation.w
        ], 0.3):
            rospy.logerr("Failed to move down to place.")
            return False
        rospy.sleep(4)
        
        # --- Step 9: Return to ready pose (like original catch step 4) ---
        print('  Returning to ready pose...')

        if not arm_ready_pose():
            rospy.logerr("Failed to return to ready pose.")
            return False
        rospy.sleep(4) # Allow time for return

        print('Catch-and-place sequence completed successfully.')
        return True

    except Exception as e:
        rospy.logerr(f"Error during catch-and-place sequence: {e}")
        # Optionally return to ready pose here too if an error occurred mid-process
        try:
            arm_ready_pose()
        except:
            pass # Ignore errors returning to ready pose after failure
        return False

# Note: The old 'catch' function is replaced by 'catch_and_place'.

#move to point
def navigateToGoal(x, y, orientation_z, orientation_w):
    ac = actionlib.SimpleActionClient('move_base', MoveBaseAction)
    ac.wait_for_server(rospy.Duration(5.0))

    goal = MoveBaseGoal()
    goal.target_pose.header.frame_id = 'map'
    goal.target_pose.header.stamp = rospy.Time.now()
    goal.target_pose.pose.position.x = x
    goal.target_pose.pose.position.y = y
    goal.target_pose.pose.orientation.z = orientation_z
    goal.target_pose.pose.orientation.w = orientation_w
    ac.send_goal(goal)
    ac.wait_for_result()
    state = ac.get_state()
    if state == GoalStatus.SUCCEEDED:
        rospy.loginfo("Successfully reached the goal location")
    else:
        rospy.loginfo("Failed to reach the goal location")

def gripper_open():
    '''
    函数功能：打开4C2夹爪
    输入参数：无
    返回值：无
    '''
    try:
        set_pub = rospy.Publisher("rm_driver/Gripper_Set", Gripper_Set, queue_size=1)
        rospy.sleep(1)
        set = Gripper_Set()
        set.position = 1000
        set_pub.publish(set)
        print("Gripper opened.")
    except Exception as e:
        rospy.logerr(f"Error opening gripper: {e}")


def gripper_close():
    '''
    函数功能：闭合4C2夹爪
    输入参数：无
    返回值：无
    '''
    try:
        pick_pub = rospy.Publisher("rm_driver/Gripper_Pick_On", Gripper_Pick, queue_size=1)
        rospy.sleep(1)
        pick1 = Gripper_Pick()
        pick1.speed = 200
        pick1.force = 1000
        pick_pub.publish(pick1)
        print("Gripper closed.")
    except Exception as e:
        rospy.logerr(f"Error closing gripper: {e}")


if __name__ == '__main__':
    rospy.init_node('object_catch')
    pub_arm_pose = rospy.Publisher("/rm_driver/GetCurrentArmState", Empty, queue_size=1)
    gripper_open()   # 初始化打开夹爪

    arm_ready_pose()
    # navigateToGoal(0.0001, 0.0002, 0.0001736, 1) # 如果需要导航到初始工作区

    # --- 初始化时设置第一个任务 ---
    if task_queue:
        current_task = task_queue.pop(0) # 取出第一个任务
        print(f"Setting first task: Target Class {current_task['target_class']}, Place {current_task['target_place']}")
        # 不再直接设置 object_msg，而是等待匹配
    else:
        print("Task queue is empty!")
        tasks_completed = True # 如果一开始就没有任务，则标记完成

    sub_object_pose = rospy.Subscriber("/object_pose", ObjectInfo, object_pose_callback, queue_size=1)
    rospy.spin()
