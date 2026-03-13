#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
angle.py
功能：直接通过修改脚本内的 `ANGLE_DEG` 参数来控制末端执行器绕末端自身 z 轴旋转。

用法：
  1) 编辑文件顶部的 ANGLE_DEG（度），保存。
  2) 在已 source 的 ROS 工作空间中运行脚本：
	   rosrun blockkit angle.py
	 或
	   python3 src/blockkit/scripts/angle.py

说明：脚本会读取当前末端四元数，按给定角度（归一化到 (-180,180]）绕末端局部 z 轴旋转并发布 MoveJ_P。
"""
import math
import rospy
from scipy.spatial.transform import Rotation as R
from rm_msgs.msg import MoveJ_P, ArmState

# --- 在此直接修改角度（度） ---
# 可以写任意值，脚本会把它映射到 (-180,180]，例如 370 -> 10
ANGLE_DEG = 45.0

# 发布速度（0-1）
MOVE_SPEED = 0.25


def normalize_angle_deg(angle_deg):
	a = ((angle_deg + 180.0) % 360.0) - 180.0
	if a == -180.0:
		return 180.0
	return a


def rotate_end_effector_by_deg(delta_deg, speed=0.25, timeout=5.0):
	try:
		arm_state = rospy.wait_for_message('/rm_driver/ArmCurrentState', ArmState, timeout=timeout)
	except rospy.ROSException as e:
		rospy.logerr(f"Failed to get current ArmState: {e}")
		return False

	px = arm_state.Pose.position.x
	py = arm_state.Pose.position.y
	pz = arm_state.Pose.position.z

	qx = arm_state.Pose.orientation.x
	qy = arm_state.Pose.orientation.y
	qz = arm_state.Pose.orientation.z
	qw = arm_state.Pose.orientation.w

	try:
		r_current = R.from_quat([qx, qy, qz, qw])
	except Exception as e:
		rospy.logerr(f"Failed to build rotation from quaternion: {e}")
		return False

	delta_rad = math.radians(delta_deg)
	r_delta = R.from_euler('z', delta_rad, degrees=False)

	# 在末端局部坐标系绕 z 轴旋转：总旋转为 r_current * r_delta
	r_new = r_current * r_delta
	q_new = r_new.as_quat()  # [x,y,z,w]

	pub = rospy.Publisher('rm_driver/MoveJ_P_Cmd', MoveJ_P, queue_size=1)
	rospy.sleep(0.3)

	move_msg = MoveJ_P()
	move_msg.Pose.position.x = float(px)
	move_msg.Pose.position.y = float(py)
	move_msg.Pose.position.z = float(pz)
	move_msg.Pose.orientation.x = float(q_new[0])
	move_msg.Pose.orientation.y = float(q_new[1])
	move_msg.Pose.orientation.z = float(q_new[2])
	move_msg.Pose.orientation.w = float(q_new[3])
	move_msg.speed = float(speed)

	pub.publish(move_msg)
	rospy.loginfo(f"Rotate by {delta_deg:.3f} deg (normalized) and published MoveJ_P. New quat: {q_new}")
	return True


def main():
	rospy.init_node('angle_script_cmd', anonymous=True)

	raw = ANGLE_DEG
	normalized = normalize_angle_deg(raw)
	if abs(normalized) < 1e-6:
		rospy.loginfo(f"ANGLE_DEG is {raw} -> normalized 0 deg. Nothing to do.")
		return

	ok = rotate_end_effector_by_deg(normalized, speed=MOVE_SPEED)
	if not ok:
		rospy.logerr("Rotation command failed.")


if __name__ == '__main__':
	main()

