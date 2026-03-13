import os

# 设置 Qt 插件路径
os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = '/home/dingk/anaconda3/envs/robot/lib/qt/plugins'
# 使用 xcb 平台
os.environ['QT_QPA_PLATFORM'] = 'xcb'
'''
Copyright: qiuzhi.tech
Author: 草木
Date: 2025-05-12 15:20:45
LastEditTime: 2025-05-12 15:30:51
'''
import cv2
import math
import numpy as np
import pyrealsense2 as rs
from scipy.spatial import ConvexHull
from scipy.spatial.transform import Rotation
import time
# from cam_calib import load_camera_params
from airbot_realsense import RealsenseCamera
from airbot_py.arm import AIRBOTPlay, RobotMode , SpeedProfile


def pose_to_SE3(pose):
    """
    将 ((x, y, z), (qx, qy, qz, qw)) 格式转换为 4x4 SE(3) 齐次变换矩阵
    """
    position, orientation = pose

    # 四元数转旋转矩阵
    r = Rotation.from_quat(orientation)
    rot_matrix = r.as_matrix()  # shape (3, 3)

    # 构造 4x4 齐次变换矩阵
    T = np.eye(4)
    T[:3, :3] = rot_matrix
    T[:3, 3] = position

    return T

def SE3_to_pose(T):
    """
    将 4x4 SE(3) 齐次变换矩阵转换为 ((x, y, z), (qx, qy, qz, qw)) 格式
    """
    # 提取位置信息
    position = T[:3, 3]
    
    # 提取旋转矩阵
    rot_matrix = T[:3, :3]
    
    # 旋转矩阵转四元数
    r = Rotation.from_matrix(rot_matrix)
    orientation = r.as_quat()
    
    return (position, orientation)

class ArucoDetector():
    def __init__(self):
        self.detected_objects = []
        self.camera_intrinsic = []
        self.camera_extrinsic = [] 
        # 初始化为4x4单位矩阵
        #self.tmat_cam2tools = np.eye(4)  # 修改这里
#         平移向量 (x, y, z) [米]:
#  [-0.15191629  0.02971404  0.1017569 ]
# 旋转矩阵:
# [[-0.06705755 -0.41176313  0.90882034]
#  [-0.99651049  0.07301251 -0.0404477 ]
#  [-0.04970038 -0.90836132 -0.41522232]]
        self.tmat_cam2tools = np.array([
                        [ 0.01053721, -0.42699052,  0.90419470, -0.13760350],
                        [-0.99881710,  0.03843213,  0.02978883,  0.03339664],
                        [-0.04746968, -0.90343902, -0.42608047,  0.11797660],
                        [ 0.        ,  0.        ,  0.        ,  1.        ]
                    ], dtype=np.float64)
        # 初始化 ArUco 字典和检测器参数
        aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_6X6_250)
        parameters = cv2.aruco.DetectorParameters()
        self.detector = cv2.aruco.ArucoDetector(aruco_dict, parameters)
        # 相机矩阵和畸变系数，实际使用时需替换为真实值
        tmp_cam = RealsenseCamera()
        profile = tmp_cam.pipeline.get_active_profile()
        color_stream = profile.get_stream(rs.stream.color).as_video_stream_profile()
        intr = color_stream.get_intrinsics()
        self.camera_matrix = np.array([
            [intr.fx, 0, intr.ppx],
            [0, intr.fy, intr.ppy],
            [0, 0, 1]
        ])
        self.dist_coeffs = np.array(intr.coeffs)
        tmp_cam.deinit()
        self.marker_size = 0.04  # 标记尺寸，单位：米

    def pcam2tools(self, target):
        tmat_mmk2 = np.eye(4)

        point3d = np.array([target[0], target[1], target[2], 1.0])
        posi_world = self.tmat_cam2tools @ point3d
        posi_local = (np.linalg.inv(tmat_mmk2) @ posi_world.reshape(4, 1))[:3]
        # print(f"pcam2tools 输入: {target}, 输出 posi_world: {posi_world}, posi_local: {posi_local}")  # 添加调试信息
        return posi_world.squeeze(), posi_local.flatten()

    def detect(self, frame, img_depth, camera_intrinsic, min_area=1000, putAxis=True):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        corners, ids, _ = self.detector.detectMarkers(gray)
        # print(f"检测到的 marker 数量: {len(corners)}")  # 添加调试信息
        detected_markers = []
        distance_errors_base = []
        distance_errors_cam = []

        frame_E = frame.copy() #显示外参参数的图像
        frame_I = frame.copy() #显示内参参数的图像

        # 计算预期距离，7.5 的根号 2 倍，转换为毫米
        expected_distance = 7.5 * math.sqrt(2) * 10
        # print(f"预期距离: {expected_distance:.2f}mm")  # 添加调试信息  

        if len(corners) == 5:  # 确保检测到 5 个 marker
            # 假设 self.marker_size 和 self.camera_matrix 等已正确初始化
            rvecs, Rmats, tvecs = self.estimatePoseSingleMarkers(corners, self.marker_size, self.camera_matrix, self.dist_coeffs)
            if putAxis:
                corners_int = np.array(corners).astype(np.int32)
                # self.draw_aruco_axis(frame, corners_int, ids, rvecs, tvecs)

            positions = []
            for i in range(len(corners)):
                corner = corners[i][0]
                # 计算质心
                center_x = int(np.mean(corner[:, 0]))
                center_y = int(np.mean(corner[:, 1]))

                # 获取图像的高度和宽度
                height, width = img_depth.shape

                # 获取深度信息，进行边界检查
                center_y = max(0, min(center_y, height - 1))
                center_x = max(0, min(center_x, width - 1))
                depth_m = img_depth[center_y, center_x] / 1000.0
                # print(f"marker {i} 的深度信息: {depth_m}")  # 添加调试信息

                # 使用相机内参反投影计算三维坐标
                fx = camera_intrinsic[0, 0]
                fy = camera_intrinsic[1, 1]
                cx = camera_intrinsic[0, 2]
                cy = camera_intrinsic[1, 2]

                Z = depth_m
                X = (center_x - cx) * Z / fx
                Y = (center_y - cy) * Z / fy
                
                obj_cam_pose = [X, Y, Z]

                # 扩展到齐次
                homo_cam = np.array([X, Y, Z, 1.0])
                # # 变换到末端系
                homo_eff = self.tmat_cam2tools @ homo_cam
                posi_world= homo_eff[:3]

                # posi_world, _ = self.pcam2tools(obj_cam_pose)
                # print(f"marker {i} 的世界坐标: {posi_world}")  # 添加调试信息

                XW = round(posi_world[0], 4)
                YW = round(posi_world[1], 4)
                ZW = round(posi_world[2], 4)

                positions.append([XW, YW])

            # 计算凸包，确定矩形的 4 个顶点
            positions = np.array(positions)
            if len(positions) >= 2:  # 确保至少有 2 个点
                hull = ConvexHull(positions)
                hull_points = positions[hull.vertices]

                # 计算中心位置
                center = np.mean(positions, axis=0)

                # 找到中心位置的 marker
                center_distances = np.linalg.norm(positions - center, axis=1)
                center_index = np.argmin(center_distances)

                # 排除中心 marker 后，对剩下的 4 个 marker 进行排序
                non_center_indices = np.delete(np.arange(len(positions)), center_index)
                non_center_positions = positions[non_center_indices]

                # 按 y 坐标排序，再按 x 坐标排序
                sorted_indices = non_center_indices[np.lexsort((non_center_positions[:, 0], non_center_positions[:, 1]))]

                # 重新编号
                new_ids = [0] + list(range(1, 5))
                for i, index in enumerate([center_index] + sorted_indices.tolist()):
                    corner = corners[index][0]
                    marker_id = new_ids[i]

                    # 计算质心
                    center_x = int(np.mean(corner[:, 0]))
                    center_y = int(np.mean(corner[:, 1]))

                    # 获取图像的高度和宽度
                    height, width = img_depth.shape

                    # 获取深度信息，进行边界检查
                    center_y = max(0, min(center_y, height - 1))
                    center_x = max(0, min(center_x, width - 1))
                    depth_m = img_depth[center_y, center_x] / 1000.0

                    # 使用相机内参反投影计算三维坐标
                    fx = camera_intrinsic[0, 0]
                    fy = camera_intrinsic[1, 1]
                    cx = camera_intrinsic[0, 2]
                    cy = camera_intrinsic[1, 2]

                    Z = depth_m
                    X = (center_x - cx) * Z / fx
                    Y = (center_y - cy) * Z / fy
                    obj_cam_pose = [X, Y, Z]
                    
                    # 扩展到齐次
                    homo_cam = np.array([X, Y, Z, 1.0])
                    pose_matrix = None
                    pose = airbot.get_end_pose()
                    pose_matrix = np.eye(4)
                    pose_matrix[:3, :3] = Rotation.from_quat(pose[1]).as_matrix()
                    pose_matrix[:3, 3] = pose[0]
                    # print("pose_matrix:", pose_matrix)
                    # 变换到base坐标系
                    homo_base = pose_matrix @ self.tmat_cam2tools @ homo_cam
                    posi_world= homo_base[:3]
                    # posi_world, _ = self.pcam2tools(obj_cam_pose)
                    # print(f"marker {i} 的世界坐标: {posi_world}")  # 添加调试信息

                    XW = round(posi_world[0], 4)
                    YW = round(posi_world[1], 4)
                    ZW = round(posi_world[2], 4)

                    # 计算包围框四个顶点的像素坐标，并进行边界检查
                    x_coords = corner[:, 0]
                    y_coords = corner[:, 1]
                    x_min = int(np.min(x_coords))
                    x_max = int(np.max(x_coords))
                    y_min = int(np.min(y_coords))
                    y_max = int(np.max(y_coords))

                    top_left = (max(0, x_min), max(0, y_min))
                    top_right = (min(x_max, width - 1), max(0, y_min))
                    bottom_left = (max(0, x_min), min(y_max, height - 1))
                    bottom_right = (min(x_max, width - 1), min(y_max, height - 1))

                    # 定义函数将像素坐标和深度转换为三维坐标
                    def pixel_to_3d(pixel, depth, fx, fy, cx, cy):
                        x_pixel, y_pixel = pixel
                        X = (x_pixel - cx) * depth / fx
                        Y = (y_pixel - cy) * depth / fy
                        Z = depth
                        return [X, Y, Z]

                    # 获取四个顶点的深度信息
                    depth_top_left = img_depth[top_left[1], top_left[0]] / 1000.0
                    depth_top_right = img_depth[top_right[1], top_right[0]] / 1000.0
                    depth_bottom_left = img_depth[bottom_left[1], bottom_left[0]] / 1000.0
                    depth_bottom_right = img_depth[bottom_right[1], bottom_right[0]] / 1000.0

                    # 计算四个顶点的三维坐标
                    pos_top_left = pixel_to_3d(top_left, depth_top_left, fx, fy, cx, cy)
                    pos_top_right = pixel_to_3d(top_right, depth_top_right, fx, fy, cx, cy)
                    pos_bottom_left = pixel_to_3d(bottom_left, depth_bottom_left, fx, fy, cx, cy)
                    pos_bottom_right = pixel_to_3d(bottom_right, depth_bottom_right, fx, fy, cx, cy)

                    # 计算长度和宽度
                    length = np.linalg.norm(np.array(pos_top_right) - np.array(pos_top_left))
                    width = np.linalg.norm(np.array(pos_bottom_left) - np.array(pos_top_left))

                    # 假设高度为中心深度与顶点深度的差值，这里简单取平均值
                    height = np.abs(depth_m - (depth_top_left + depth_top_right + depth_bottom_left + depth_bottom_right) / 4)

                    # 转换到世界坐标系
                    length_world = np.linalg.norm(np.array(self.pcam2tools(pos_top_right)[0]) - np.array(self.pcam2tools(pos_top_left)[0]))
                    width_world = np.linalg.norm(np.array(self.pcam2tools(pos_bottom_left)[0]) - np.array(self.pcam2tools(pos_top_left)[0]))
                    height_world = height  # 高度可能需要更精确的计算

                    marker_info = {
                        'class': f"marker_{marker_id}",
                        'confidence': 1.0,
                        'x': center_x,
                        'y': center_y,
                        'w': x_max - x_min,
                        'h': y_max - y_min,
                        'X': X,
                        'Y': Y,
                        'Z': Z,
                        'XW': XW,
                        'YW': YW,
                        'ZW': ZW,
                        'length': length_world,
                        'width': width_world,
                        'height': height_world
                    }
                    # print(f"marker {marker_id} 的信息: {marker_info}")  # 添加调试信息
                    detected_markers.append(marker_info)

                    # 绘制轮廓和中心点
                    cv2.drawContours(frame_I, [corner.astype(np.int32)], -1, (0, 255, 0), 2)
                    cv2.circle(frame_I, (center_x, center_y), 5, (0, 0, 255), -1)
                    cv2.drawContours(frame_E, [corner.astype(np.int32)], -1, (0, 255, 0), 2)
                    cv2.circle(frame_E, (center_x, center_y), 5, (0, 0, 255), -1)
                    cv2.putText(frame_I, f"Marker {marker_id}: ({X:.2f}, {Y:.2f}, {Z:.2f})",
                                (center_x + 20, center_y + 20),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                    cv2.putText(frame_E, f"Marker {marker_id}: ({XW:.2f}, {YW:.2f}, {ZW:.2f})",
                                (center_x - 20, center_y - 20),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)


            # 计算 marker 之间的距离误差
            center_marker = None
            corner_markers = []
            for marker in detected_markers:
                if marker['class'] == 'marker_0':
                    center_marker = marker
                else:
                    corner_markers.append(marker)

            if center_marker and len(corner_markers) == 4:
                center_pos_base = np.array([center_marker['XW'], center_marker['YW'], center_marker['ZW']])
                print(f"中心 marker 的位置 (base): {center_pos_base}")  # 添加调试信息
                center_pose_cam = np.array([center_marker['X'], center_marker['Y'], center_marker['Z']])
                for corner_marker in corner_markers:
                    corner_pos_base = np.array([corner_marker['XW'], corner_marker['YW'], corner_marker['ZW']])
                    print(f"角落 marker 的位置 (base): {corner_pos_base}")  # 添加调试信息
                    actual_distance_base = np.linalg.norm(center_pos_base - corner_pos_base) * 1000  # 转换为毫米
                    print(f"实际距离 (base): {actual_distance_base:.2f}mm")  # 添加调试信息
                    error_base = abs(actual_distance_base - expected_distance)
                    distance_errors_base.append(error_base)

                    corner_pose_cam = np.array([corner_marker['X'], corner_marker['Y'], corner_marker['Z']])
                    actual_distance_cam = np.linalg.norm(center_pose_cam - corner_pose_cam) * 1000  # 转换为毫米
                    error_cam = abs(actual_distance_cam - expected_distance)
                    distance_errors_cam.append(error_cam)

                    # # 在图像上显示距离误差信息
                    # mid_x = (center_marker['x'] + corner_marker['x']) // 2
                    # mid_y = (center_marker['y'] + corner_marker['y']) // 2
                    # text = f"{actual_distance:.1f}mm ({'+' if actual_distance > expected_distance else ''}{error:.1f}mm)"
                    # cv2.putText(frame, text, (mid_x, mid_y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

                # 计算平均误差
                avg_error_base = np.mean(distance_errors_base) if distance_errors_base else 0
                avg_error_cam = np.mean(distance_errors_cam) if distance_errors_cam else 0


                cv2.putText(frame_E, f"Avg Distance Error: {avg_error_base:.2f}mm", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                cv2.putText(frame_I, f"Avg Distance Error: {avg_error_cam:.2f}mm", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

                # 首先建一个字典，方便按 id 索引
                pix = {}
                cam = {}    
                world = {}  
                for m in detected_markers:
                    idx = int(m['class'].split('_')[1])  # 0 到 4
                    pix[idx] = (m['x'], m['y'])  # 像素坐标
                    # cam[idx]   = (m['X'], m['Y'], m['Z'])  # 像素坐标
                    cam[idx] = np.array([m['X'], m['Y'], m['Z']], dtype=np.float64)
                    # world[idx] = np.array([m['XW'], m['YW'], m['ZW']])  # m→mm
                    world[idx] = np.array([m['XW'], m['YW'], m['ZW']], dtype=np.float64)

                pairs = [(1,2), (2,4), (3,4), (3,1)]

                for a, b in pairs:
                    if a in cam and b in cam:
                        # 1) 画线
                        pt1_pix = pix[a]
                        pt2_pix = pix[b]

                        pt1_cam = cam[a]
                        pt2_cam = cam[b]

                        pt1_base = world[a]
                        pt2_base = world[b]

                        cv2.line(frame_I, pt1_pix, pt2_pix, (0,255,0), 2)
                        cv2.line(frame_E, pt1_pix, pt2_pix, (0,255,0), 2)

                        # 2) 计算真实距离（mm） 
                        d_mm_cam = np.linalg.norm(pt1_cam - pt2_cam) * 1000  # 转换为毫米
                        d_mm_base = np.linalg.norm(pt1_base - pt2_base) * 1000 # 已经是毫米

                        # 3) 在线中点写文字
                        mid = ((pt1_pix[0]+pt2_pix[0])//2, (pt1_pix[1]+pt2_pix[1])//2)
                        text_cam = f"{d_mm_cam:.1f}mm"
                        cv2.putText(frame_I, text_cam, mid,
                                    cv2.FONT_HERSHEY_SIMPLEX, 
                                    0.6, (0,255,255), 2, cv2.LINE_AA)
                        
                        text_base = f"{d_mm_base:.1f}mm"
                        cv2.putText(frame_E, text_base, mid,
                                    cv2.FONT_HERSHEY_SIMPLEX, 
                                    0.6, (0,255,255), 2, cv2.LINE_AA)

                
                # cv2.imshow("1 ", frame_I)
                # cv2.imshow("2 ", frame_E)

                cv2.waitKey(0)

            return frame_I, frame_E, Rmats, rvecs, tvecs, ids, corners, detected_markers, avg_error_cam, avg_error_base
        else:
            return frame_I, frame_E, [], [], [], ids, corners, [], avg_error_base, avg_error_cam

    def detect_frame(self,frame, img_depth, camera_intrinsic):
        detected_objects = []
        # 检测积木
        # frame, detected_bricks = self.detect_bricks(frame, img_depth, camera_intrinsic)
        frame, *_, detected_bricks = self.detect(frame, img_depth, camera_intrinsic)
        detected_objects.extend(detected_bricks)

        return frame, detected_objects  # 返回处理后的图像
    
    def extract_brick_info(self, detected_bricks, key_names):
        """
        从检测到的积木信息列表中按名称提取信息
        :param detected_bricks: 存储检测到的积木信息的列表，列表元素为字典
        :param key_names: 要提取的信息的键名列表，例如 ['class', 'XW'] 等
        :return: 包含提取信息的列表，每行为一组积木的信息，每列为对应的 key_name
        """
        # 使用列表推导式生成提取信息的列表
        return [
            [brick.get(key_name) for key_name in key_names]
            for brick in detected_bricks
        ]
    
    def load_camera_params(self,file_path):
        camera_intrinsic = None
        camera_extrinsic = None
        
        with open(file_path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                    
                elif "--Intrinsic--" in line:
                    # 跳过 "list format:" 行
                    f.readline()
                    # 跳过 "[" 行
                    f.readline()
                    matrix = []
                    for _ in range(3):
                        row = f.readline().strip().replace('[', '').replace(']', '').replace(',', '')
                        matrix.append([float(x) for x in row.split()])
                    # 跳过 "]" 行
                    f.readline()
                    camera_intrinsic = np.array(matrix)
                
                elif "--Hand-in-eye-extrinsic--" in line:
                    # 跳过 "list format:" 行
                    f.readline()
                    # 跳过 "[" 行
                    f.readline()
                    matrix = []
                    for _ in range(4):
                        row = f.readline().strip().replace('[', '').replace(']', '').replace(',', '')
                        matrix.append([float(x) for x in row.split()])
                    # 跳过 "]" 行
                    f.readline()
                    camera_extrinsic = np.array(matrix)
                    
        return camera_intrinsic, camera_extrinsic
    
    def aruco_detector(self,caculate_mark=5):
        try:
            calib_txt = "./configs/Calibration_Report.txt"
            _, self.camera_extrinsic = self.load_camera_params(calib_txt)
            # 确保camera_extrinsic是4x4矩阵
            if self.camera_extrinsic is not None and self.camera_extrinsic.shape == (4, 4):
                self.tmat_cam2tools = self.camera_extrinsic
                print("Camera Extrinsic Matrix:\n",self.tmat_cam2tools)
            else:
                print("Warning: Using default transformation matrix")
                # self.tmat_cam2tools = np.eye(4)
                
            # 初始化Realsense相机
            realsense_camera = RealsenseCamera()
            
            # 他给的
            # self.camera_matrix = np.array([ [905.23541975,   0.        , 641.37300301],
            #                             [  0.        , 905.22872074, 367.15461488],
            #                             [  0.        ,   0.        ,   1.        ]])
            # self.dist_coeffs = np.array([0.08921822, 0.01410929, -0.00066497, -0.00398082, -0.60365788])

            # Get intrinsics from SDK
            profile = realsense_camera.pipeline.get_active_profile()
            color_stream = profile.get_stream(rs.stream.color).as_video_stream_profile()
            intr = color_stream.get_intrinsics()
            self.camera_intrinsic = np.array([
                [intr.fx, 0, intr.ppx],
                [0, intr.fy, intr.ppy],
                [0, 0, 1]
            ])
            print("Camera Intrinsic Matrix:\n", self.camera_intrinsic)
            # print("Camera Extrinsic Matrix:\n", self.camera_extrinsic)
            self.camera_matrix = self.camera_intrinsic
            self.dist_coeffs = np.array(intr.coeffs)

            # 定义打印间隔，可根据需要调整
            print_interval = 5
            # 初始化计数器
            frame_counter = 0
            avg_error = 0  # 添加默认值
            avg_error_cam  = 0
            avg_error_base = 0
            while caculate_mark:
                # 从Realsense相机获取彩色图和深度图
                color_image, depth_image = realsense_camera.get_frame(frame_type=["bgr", "depth"], align=True)
                frame_I, frame_E, _, _, _, _, _, detected_markers ,avg_error_cam, avg_error_base = self.detect(color_image, depth_image, self.camera_intrinsic)
                # 计算 marker 之间的距离
                marker_distances = self.calculate_marker_distances(detected_markers)
                # 仅在计数器达到打印间隔时打印距离
                if frame_counter % print_interval == 0:
                    print("Marker 之间的距离:", marker_distances)
                # 计数器加 1
                frame_counter += 1
                cv2.imshow("Intrinsic calibration verification", frame_I)
                cv2.imshow("Extrinsic calibration verification", frame_E)
                # key = cv2.waitKey(1) & 0xFF
                caculate_mark = caculate_mark-1
                # if key == ord('s'):
                #     import time
                #     timestamp = time.strftime("%Y%m%d-%H%M%S")
                #     cv2.imwrite(f"{timestamp}.jpg", detected_image)
                #     print("检测到的物体信息:")
                #     for obj in detected_markers:
                #         print(obj)
                #     print(f"截图已保存: {timestamp}.jpg")

                # if key == ord("q"):
                #     self.detected_objects = detected_markers
                #     break
            return avg_error_cam, avg_error_base
            
        except Exception as e:
            print(f"Error in aruco_detector: {e}")
            return 0  # 发生错误时返回默认值
        finally:
            # 释放相机资源
            realsense_camera.deinit()
            cv2.destroyAllWindows()
            return avg_error_cam, avg_error_base
            

    # 添加 estimatePoseSingleMarkers 方法
    def estimatePoseSingleMarkers(self, corners, marker_size, mtx, distortion):
        marker_points = np.array([[-marker_size / 2,  marker_size / 2, 0],
                                  [ marker_size / 2,  marker_size / 2, 0],
                                  [ marker_size / 2, -marker_size / 2, 0],
                                  [-marker_size / 2, -marker_size / 2, 0]], dtype=np.float32)
        rvecs = []
        Rmats = []
        tvecs = []
        for c in corners:
            _, r, t = cv2.solvePnP(marker_points, c, mtx, distortion, False, cv2.SOLVEPNP_IPPE_SQUARE)
            R, _ = cv2.Rodrigues(r)
            rvecs.append(r)
            Rmats.append(R)
            tvecs.append(t)
        return rvecs, Rmats, tvecs
    
    # 添加 draw_aruco_axis 方法
    def draw_aruco_axis(self, image, corners_int, ids, rvecs, tvecs):
        cv2.drawContours(image, corners_int, -1, (0, 255, 0), 3)
        for i in range(len(rvecs)):
            cv2.drawFrameAxes(image, self.camera_matrix, self.dist_coeffs, rvecs[i], tvecs[i], 0.02)
        return image

    def calculate_marker_distances(self, detected_markers):
        """
        计算识别到的每个 marker 之间的距离。

        :param detected_markers: 包含每个 marker 信息的列表，每个元素是一个字典
        :return: 一个字典，键为 marker ID 对，值为它们之间的距离
        """
        distances = {}
        num_markers = len(detected_markers)
        for i in range(num_markers):
            for j in range(i + 1, num_markers):
                marker1 = detected_markers[i]
                marker2 = detected_markers[j]
                # 提取两个 marker 的世界坐标
                pos1 = np.array([marker1['XW'], marker1['YW'], marker1['ZW']])
                pos2 = np.array([marker2['XW'], marker2['YW'], marker2['ZW']])
                # 计算两个 marker 之间的欧氏距离
                distance = np.linalg.norm(pos1 - pos2)
                # 构建 marker ID 对
                marker_pair = (marker1['class'].split('_')[-1], marker2['class'].split('_')[-1])
                distances[marker_pair] = distance
        return distances

    def AIRBOTPlay_aruco_detector(self):
        avg_errors_cam = []
        avg_errors_base = []
        airbot= AIRBOTPlay(url="localhost", port=50000)
        airbot.connect()
        airbot.switch_mode(RobotMode.PLANNING_POS)
        airbot.set_speed_profile(SpeedProfile.SLOW)
        waypoints = [
            [[0.20947129892648034, 0.015328161474874633, 0.2953903908108203], [-0.26971355225243765, 0.4552062839601087, 0.07996721737387033, 0.8447763508290704]],
            [[0.24553817422482715, -0.0298236570007807, 0.2696489124513268], [-0.06007872878337695, 0.5062845731111876, 0.007339009177617606, 0.8602398597610359]],
            [[0.22152983741147297, -0.1407332821668576, 0.2488084766839721], [0.13062978842079215, 0.51127754115145, -0.11843539734203302, 0.8411326833191665]],
            [[0.12493464691865779, -0.005941169171326185, 0.3284149668042142], [-0.06688373970677693, 0.38724874620182315, 0.002989962786478192, 0.9195412084569606]],
            [[0.32476625782912927, -0.03294480360584416, 0.2503870422889196], [-0.0176142658180435, 0.6454835553501391, 0.027695379605650446, 0.7630685967596453]]
        ]
        for waypoint in waypoints:
            airbot.move_to_cart_pose(waypoint)
            time.sleep(1)
            avg_error_cam, avg_error_base=brickdetector.aruco_detector(caculate_mark=5)
            avg_errors_cam.append(avg_error_cam)
            avg_errors_base.append(avg_error_base)
        error_cam=np.mean(sum(np.array(avg_errors_cam)))
        error_base=np.mean(sum(np.array(avg_errors_base)))
        print(f"内参平均误差: {error_cam:.2f}mm")
        print(f"外参平均误差: {error_base:.2f}mm")
        airbot.disconnect()

if __name__ == "__main__":
    # brickdetector = ArucoDetector()
    # avg_errors = []
    # airbot= AIRBOTPlay(port=50051)
    # airbot.connect()
    # airbot.switch_mode(RobotMode.PLANNING_POS)
    # airbot.set_speed_profile(SpeedProfile.SLOW)
    # waypoints = [
    #     [[0.20947129892648034, 0.015328161474874633, 0.2953903908108203], [-0.26971355225243765, 0.4552062839601087, 0.07996721737387033, 0.8447763508290704]],
    #     [[0.24553817422482715, -0.0298236570007807, 0.2696489124513268], [-0.06007872878337695, 0.5062845731111876, 0.007339009177617606, 0.8602398597610359]],
    #     [[0.22152983741147297, -0.1407332821668576, 0.2488084766839721], [0.13062978842079215, 0.51127754115145, -0.11843539734203302, 0.8411326833191665]],
    #     [[0.12493464691865779, -0.005941169171326185, 0.3284149668042142], [-0.06688373970677693, 0.38724874620182315, 0.002989962786478192, 0.9195412084569606]],
    #     [[0.32476625782912927, -0.03294480360584416, 0.2503870422889196], [-0.0176142658180435, 0.6454835553501391, 0.027695379605650446, 0.7630685967596453]]
    # ]
    # for waypoint in waypoints:
    #     airbot.move_to_cart_pose(waypoint)
    #     time.sleep(1)
    #     avg_error=brickdetector.aruco_detector(caculate_mark=5)
    #     avg_errors.append(avg_error)
    # error=np.mean(sum(np.array(avg_errors)))
    # print(f"平均误差: {error:.2f}mm")
    # airbot.disconnect()
    brickdetector = ArucoDetector()
    avg_errors_cam = []
    avg_errors_base = []
    airbot= AIRBOTPlay(port=50000)
    airbot.connect()
    airbot.switch_mode(RobotMode.PLANNING_POS)
    airbot.set_speed_profile(SpeedProfile.SLOW)
    # print(airbot.get_end_pose())
    waypoints = [
        [[0.25063911454679483, 0.013733683475515823, 0.1634319742901892], [0.017120708225882342, 0.5780019421381718, 0.034138209265947135, 0.8151412263543417]],
        # [[0.20947129892648034, 0.015328161474874633, 0.2953903908108203], [-0.26971355225243765, 0.4552062839601087, 0.07996721737387033, 0.8447763508290704]],
        [[0.24553817422482715, -0.0298236570007807, 0.2696489124513268], [-0.06007872878337695, 0.5062845731111876, 0.007339009177617606, 0.8602398597610359]],
        # [[0.22152983741147297, -0.1407332821668576, 0.2488084766839721], [0.13062978842079215, 0.51127754115145, -0.11843539734203302, 0.8411326833191665]],
        # [[0.12493464691865779, -0.005941169171326185, 0.3284149668042142], [-0.06688373970677693, 0.38724874620182315, 0.002989962786478192, 0.9195412084569606]],
        # [[0.32476625782912927, -0.03294480360584416, 0.2503870422889196], [-0.0176142658180435, 0.6454835553501391, 0.027695379605650446, 0.7630685967596453]]
    ]
    for waypoint in waypoints:
        airbot.move_to_cart_pose(waypoint)
        time.sleep(1)
        avg_error_cam, avg_error_base=brickdetector.aruco_detector(caculate_mark=5)
        avg_errors_cam.append(avg_error_cam)
        avg_errors_base.append(avg_error_base)
        error_cam=np.mean(sum(np.array(avg_errors_cam)))
        error_base=np.mean(sum(np.array(avg_errors_base)))
        print(f"内参平均误差: {error_cam:.2f}mm")
        print(f"外参平均误差: {error_base:.2f}mm")
    airbot.disconnect()
