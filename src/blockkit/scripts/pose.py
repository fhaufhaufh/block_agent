#!/usr/bin/env python3
# -*- coding=UTF-8 -*-
import rospy
from rm_msgs.msg import Arm_Current_State, ArmState
from blockkit.msg import ObjectInfo
import numpy as np
from scipy.spatial.transform import Rotation as R

# 相机坐标系到机械臂末端坐标系的旋转矩阵，通过手眼标定得到
rotation_matrix = np.array([[0, 1, 0],
                            [-1, 0, 0],
                            [0, 0, 1]])
# 相机坐标系到机械臂末端坐标系的平移向量，通过手眼标定得到
translation_vector = np.array([-0.08039019, 0.03225555, -0.09756825])

# 相机坐标系物体到机械臂基坐标系转换函数
def convert(x, y, z, x1, y1, z1, rx, ry, rz):
    """
    函数功能：将相机坐标系下的物体坐标转换为机械臂基坐标系下的坐标
    输入参数：深度相机识别到的物体坐标（x, y, z）和机械臂末端的位姿（x1,y1,z1,rx,ry,rz）
    返回值：物体在机械臂基座坐标系下的位置（x, y, z, rx, ry, rz）
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
    函数功能：每帧图像经过识别后的回调函数，转换物体坐标并输出
    输入参数：data (ObjectInfo) - 检测到的物体信息
    返回值：无
    """
    try:
        # 等待当前的机械臂位姿
        arm_pose_msg = rospy.wait_for_message("/rm_driver/Arm_Current_State", Arm_Current_State, timeout=5.0)
        arm_orientation_msg = rospy.wait_for_message("/rm_driver/ArmCurrentState", ArmState, timeout=5.0)

        # 计算机械臂基坐标系下的物体坐标
        result = convert(data.x, data.y, data.z,
                         arm_pose_msg.Pose[0], arm_pose_msg.Pose[1], arm_pose_msg.Pose[2],
                         arm_pose_msg.Pose[3], arm_pose_msg.Pose[4], arm_pose_msg.Pose[5])
        
        # 输出物体在基坐标系中的位置
        rospy.loginfo(f"检测到物体 '{data.object_class}' 在机器人基坐标系下的位置:")
        rospy.loginfo(f"   X: {result[0]:.4f} 米")
        rospy.loginfo(f"   Y: {result[1]:.4f} 米") 
        rospy.loginfo(f"   Z: {result[2]:.4f} 米")
        rospy.loginfo(f"   RX: {result[3]:.4f} 弧度")
        rospy.loginfo(f"   RY: {result[4]:.4f} 弧度")
        rospy.loginfo(f"   RZ: {result[5]:.4f} 弧度")
        rospy.loginfo("-" * 50)

    except rospy.ROSException as e:
        rospy.logerr(f"等待机械臂位姿时出错: {e}")
    except Exception as e:
        rospy.logerr(f"坐标转换过程中发生错误: {e}")

if __name__ == '__main__':
    rospy.init_node('object_position_publisher')
    rospy.loginfo("物体位置检测节点已启动")
    rospy.loginfo("正在订阅物体位姿话题: /object_pose")
    rospy.loginfo("等待YOLO检测结果，将输出物体在机器人基坐标系下的位置")
    rospy.loginfo("-" * 60)

    # 订阅物体位姿话题
    sub_object_pose = rospy.Subscriber("/object_pose", ObjectInfo, object_pose_callback, queue_size=1)
    
    # 保持节点运行
    rospy.spin()