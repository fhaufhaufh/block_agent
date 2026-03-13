import random
import os
from ultralytics import YOLO
import rospy
import pyrealsense2 as rs
import math
import yaml
import argparse
import os
import time
import numpy as np
import sys
from std_msgs.msg import String ,Empty
import cv2
from vi_grab.msg import ObjectInfo  #自定义ROS msg

# 配置 RealSense
pipeline = rs.pipeline()
config = rs.config()
config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 15)
config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 15)

# 启动相机流
pipeline.start(config)
align_to = rs.stream.color  # 与color流对齐q
align = rs.align(align_to)
object_info_msg = ObjectInfo()

# 获取相机图像流
def get_aligned_images():
    frames = pipeline.wait_for_frames()  # 等待获取图像帧
    aligned_frames = align.process(frames)  # 获取对齐帧
    aligned_depth_frame = aligned_frames.get_depth_frame()  # 获取对齐帧中的depth帧
    color_frame = aligned_frames.get_color_frame()  # 获取对齐帧中的color帧

    # 相机参数的获取
    intr = color_frame.profile.as_video_stream_profile().intrinsics  # 获取相机内参
    depth_intrin = aligned_depth_frame.profile.as_video_stream_profile(
    ).intrinsics  # 获取深度参数（像素坐标系转相机坐标系会用到）
    '''camera_parameters = {'fx': intr.fx, 'fy': intr.fy,
                         'ppx': intr.ppx, 'ppy': intr.ppy,
                         'height': intr.height, 'width': intr.width,
                         'depth_scale': profile.get_device().first_depth_sensor().get_depth_scale()
                         }'''

    depth_image = np.asanyarray(aligned_depth_frame.get_data())  # 深度图（默认16位）
    color_image = np.asanyarray(color_frame.get_data())  # RGB图

    # 返回相机内参、深度参数、彩色图、深度图、齐帧中的depth帧
    return intr, depth_intrin, color_image, depth_image, aligned_depth_frame

# 获取对应像素点的深度值
def get_3d_camera_coordinate(depth_pixel, aligned_depth_frame, depth_intrin):
    x = depth_pixel[0]
    y = depth_pixel[1]
    dis = aligned_depth_frame.get_distance(x, y)  # 获取该像素点对应的深度
    camera_coordinate = rs.rs2_deproject_pixel_to_point(depth_intrin, depth_pixel, dis)
    return dis, camera_coordinate

if __name__ == '__main__':

    model_path = os.path.join('/home/cn/catkin_rm_nsai/src/vi_grab/model/manipulator_cam_best.pt')
    model = YOLO(model_path)  
    print("[INFO] 完成YoloV11模型加载")
    rospy.init_node("object_detect",anonymous=True)   #建立ROS节点
    object_pub = rospy.Publisher("object_pose",ObjectInfo,queue_size=10)   #定义话题发布器
    # 循环检测图像流
    try:
        while not rospy.is_shutdown():
            # 等待获取一对连续的帧：深度和颜色
            intr, depth_intrin, color_image, depth_image, aligned_depth_frame = get_aligned_images()
            if not depth_image.any() or not color_image.any():
                continue
            # 使用 YOLOv8 OBB 进行目标检测（如果模型输出 obb，即 xywhr）
            results = model.predict(color_image, conf=0.5)
            result = results[0]
            canvas = result.plot()

            # 优先使用 obb 输出（xywhr: x_center, y_center, w, h, angle(rad)）
            if hasattr(result, 'obb') and result.obb is not None:
                obb = result.obb
                boxes = obb.xywhr
                for i, box in enumerate(boxes):
                    x_center, y_center, w, h, angle_rad = box.cpu().numpy()
                    cls_id = int(obb.cls[i].cpu().numpy()) if hasattr(obb, 'cls') else int(result.boxes.data[i][5])
                    name = result.names[cls_id]
                    ux = int(x_center)
                    uy = int(y_center)
                    # 获取深度与相机坐标
                    dis, camera_coordinate = get_3d_camera_coordinate([ux, uy], aligned_depth_frame, depth_intrin)

                    formatted_camera_coordinate = f"({camera_coordinate[0]:.2f}, {camera_coordinate[1]:.2f},{camera_coordinate[2]:.2f})"
                    # 在窗口添加角度显示（角度转为度）
                    angle_deg = float(angle_rad) * 180.0 / math.pi
                    cv2.circle(canvas, (ux, uy), 4, (255, 255, 255), 5)
                    cv2.putText(canvas, f"{formatted_camera_coordinate} {angle_deg:.1f}deg", (ux + 20, uy + 10), 0, 1,
                                [225, 255, 255], thickness=2, lineType=cv2.LINE_AA)

                    # ROS话题发送物体坐标及角度（角度以弧度发送）
                    object_info_msg.object_class = str(name)
                    object_info_msg.x = float(camera_coordinate[0])
                    object_info_msg.y = float(camera_coordinate[1])
                    object_info_msg.z = float(camera_coordinate[2])
                    object_info_msg.angle = float(angle_rad)
                    rospy.loginfo(object_info_msg)
                    object_pub.publish(object_info_msg)
            else:
                # 回退到原始 axis-aligned bbox 输出
                detected_boxes = result.boxes.xyxy
                data = result.boxes.data.cpu().tolist()
                for i, (row, box) in enumerate(zip(data, detected_boxes)):
                    id = int(row[5])
                    name = result.names[id]
                    x1, y1, x2, y2 = map(int, box)
                    ux = int((x1 + x2) / 2)
                    uy = int((y1 + y2) / 2)
                    dis, camera_coordinate = get_3d_camera_coordinate([ux, uy], aligned_depth_frame, depth_intrin)

                    formatted_camera_coordinate = f"({camera_coordinate[0]:.2f}, {camera_coordinate[1]:.2f},{camera_coordinate[2]:.2f})"
                    cv2.circle(canvas, (ux, uy), 4, (255, 255, 255), 5)
                    cv2.putText(canvas, str(formatted_camera_coordinate), (ux + 20, uy + 10), 0, 1,
                                [225, 255, 255], thickness=2, lineType=cv2.LINE_AA)
                    object_info_msg.object_class = str(name)
                    object_info_msg.x = float(camera_coordinate[0])
                    object_info_msg.y = float(camera_coordinate[1])
                    object_info_msg.z = float(camera_coordinate[2])
                    object_info_msg.angle = 0.0
                    rospy.loginfo(object_info_msg)
                    object_pub.publish(object_info_msg)

            cv2.namedWindow('detection', flags=cv2.WINDOW_NORMAL |
                                                   cv2.WINDOW_KEEPRATIO | cv2.WINDOW_GUI_EXPANDED)
            cv2.imshow('detection', canvas)
            key = cv2.waitKey(1)
            # 按下 esc 或者 'q' 退出程序和图像界面
            if key & 0xFF == ord('q') or key == 27:
                cv2.destroyAllWindows()
                break 
    finally:
        # 关闭相机图像流
        pipeline.stop()
