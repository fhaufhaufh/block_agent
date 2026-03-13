import pyrealsense2 as rs
import cv2
import numpy as np
from ultralytics import YOLO
import time
import yaml
import math
from airbot_py.arm import AIRBOTPlay, RobotMode, SpeedProfile
from collections import deque


from collections import deque

def nothing(x):
    """ Trackbar 的回调函数，不需要做任何事 """
    pass

def calculate_angle_pca(roi_img, hsv_min, hsv_max):
    """
    对 ROI 区域进行 PCA 角度计算 (HSV)
    """
    if roi_img is None or roi_img.size == 0:
        return 0, False, None

    # 1. 预处理 (HSV)
    hsv = cv2.cvtColor(roi_img, cv2.COLOR_BGR2HSV)
    thresh = cv2.inRange(hsv, hsv_min, hsv_max)

    # 形态学操作 (去噪点)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=1)
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel, iterations=1)

    # 2. 找轮廓
    contours, _ = cv2.findContours(thresh, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
    if not contours:
        return 0, False, thresh

    # 找到最大的合适轮廓
    target_cnt = max(contours, key=cv2.contourArea)
    
    # 面积过滤
    area = cv2.contourArea(target_cnt)
    h, w = roi_img.shape[:2]
    img_area = h * w
    
    if area < 50 or area > (img_area * 0.95):
        return 0, False, thresh

    # 3. PCA 计算
    pts = target_cnt.reshape(-1, 2).astype(np.float64)
    mean, eigenvectors = cv2.PCACompute(pts, mean=None)
    
    # 主轴方向 (Eigenvector 0)
    vx, vy = eigenvectors[0, 0], eigenvectors[0, 1]
    
    # 重心
    cx, cy = mean[0, 0], mean[0, 1]
    
    # --- 4. 消除 180 度歧义 (方向校正) ---
    nx, ny = -vy, vx
    
    # 将所有轮廓点投影到法向量 n 上
    pts_cnt = target_cnt.reshape(-1, 2)
    projections = (pts_cnt[:, 0] - cx) * nx + (pts_cnt[:, 1] - cy) * ny
    
    # 统计正侧（n方向）和负侧的像素数量
    count_pos = np.sum(projections > 0)
    count_neg = np.sum(projections <= 0)
    
    if count_pos < count_neg:
        # 翻转主轴方向
        vx, vy = -vx, -vy
        
    # --- 5. 零点校准 (坐标系转换) ---
    angle_rad = np.arctan2(vy, vx)
    angle_deg = np.degrees(angle_rad)
    
    final_angle = (-angle_deg - 90) % 360
    
    return final_angle, True, thresh

class AngleSmoother:
    """ 角度平滑器 """
    def __init__(self, window_size=5):
        self.window_size = window_size
        self.history_sin = deque(maxlen=window_size)
        self.history_cos = deque(maxlen=window_size)
        self.class_id = None

    def update(self, angle):
        rad = np.radians(angle)
        self.history_sin.append(np.sin(rad))
        self.history_cos.append(np.cos(rad))
        avg_sin = sum(self.history_sin) / len(self.history_sin)
        avg_cos = sum(self.history_cos) / len(self.history_cos)
        return np.degrees(np.arctan2(avg_sin, avg_cos)) % 360

class DetectionSystem:
    def __init__(self, config_path="config/camera.yaml"):
        # 加载配置
        self.config_path = config_path
        self.load_config()
        
        # 初始化模型
        self.model = YOLO(self.model_path)

        # 初始化相机
        self.pipeline = rs.pipeline()
        self.config = rs.config()
        
        self.setup_camera()
        self.start_camera()
        
        # 坐标变换参数
        self.extrinsics_matrix = np.array(self.camera_extrinsics['matrix'])
        # 初始化机器人
        self.robot = AIRBOTPlay(url="localhost", port=50000)
        if not self.robot.connect():
            raise Exception("连接失败")
        self.robot.switch_mode(RobotMode.PLANNING_POS)
        self.robot.set_speed_profile(SpeedProfile.DEFAULT)
        print("机械臂连接成功。")
        # 机器人位姿参数
        self.robot_position = None
        self.robot_quaternion = None
        self.smoother = AngleSmoother(window_size=5)
        
        # HSV 阈值 (针对积木3) - 需要根据实际情况调整
        # 默认设置为比较宽的范围，或者针对黄色/橙色
        self.block3_hsv_min = np.array([0, 0, 0])
        self.block3_hsv_max = np.array([30, 255, 55])
        
        print("检测系统初始化完成")
    
    def load_config(self):
        """加载配置文件"""
        with open(self.config_path, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)
        
        # 基本参数
        self.conf_threshold = config_data['detection']['confidence_threshold']
        self.model_path = config_data['detection']['model_path']
        self.window_name = config_data['display']['window_name']
        
        # 相机参数
        self.camera_extrinsics = config_data['camera_extrinsics']
        #self.color_intrinsics = config_data['camera_intrinsics']
        self.color_stream = config_data['camera_streams']['color']
        self.depth_stream = config_data['camera_streams']['depth']
        
        # 深度处理参数
        self.depth_kernel_size = config_data['depth_processing']['kernel_size']
        
        print(f"加载配置文件: {self.config_path}")
        print(f"置信度阈值: {self.conf_threshold}")
        print(f"模型路径: {self.model_path}")
    
    def setup_camera(self):
        """配置相机流"""
        # 配置彩色流
        self.config.enable_stream(
            rs.stream.color,
            self.color_stream['width'],
            self.color_stream['height'],
            getattr(rs.format, self.color_stream['format']),
            self.color_stream['fps']
        )
        
        # 配置深度流
        self.config.enable_stream(
            rs.stream.depth,
            self.depth_stream['width'],
            self.depth_stream['height'],
            getattr(rs.format, self.depth_stream['format']),
            self.depth_stream['fps']
        )
    
    def start_camera(self):
        """启动相机"""
        self.profile = self.pipeline.start(self.config)
        
        # 获取深度传感器参数
        depth_sensor = self.profile.get_device().first_depth_sensor()
        self.depth_scale = depth_sensor.get_depth_scale()
        
        # 设置高精度模式 (High Accuracy)
        if depth_sensor.supports(rs.option.visual_preset):
            print("设置相机为高精度模式 (High Accuracy)")
            depth_sensor.set_option(rs.option.visual_preset, 3)
        
        # 获取相机内参 (使用彩色相机内参，深度对齐到彩色)
        color_profile = rs.video_stream_profile(self.profile.get_stream(rs.stream.color))
        self.color_intrinsics = color_profile.get_intrinsics()
        
        # 配置对齐器 (Depth -> Color)
        self.align = rs.align(rs.stream.color)
        # 放掉前面几帧
        for _ in range(40):
            frames = self.pipeline.wait_for_frames()
            aligned_frames = self.align.process(frames)
            color_frame = aligned_frames.get_color_frame()
            depth_frame = aligned_frames.get_depth_frame()
        print("相机启动成功")
    
    def get_frames(self):
        """获取对齐后的帧"""
        try:
            frames = self.pipeline.wait_for_frames()
            aligned_frames = self.align.process(frames)
            return aligned_frames.get_color_frame(), aligned_frames.get_depth_frame()
        except Exception as e:
            print(f"获取帧失败: {e}")
            return None, None
    
    def set_robot_pose(self, position, quaternion):
        """设置机器人当前位置和姿态（四元数）"""
        self.robot_position = position  # [x, y, z]
        self.robot_quaternion = quaternion  # [qx, qy, qz, qw]
        print(f"机器人位置设置: {position}")
        print(f"机器人姿态设置: {quaternion}")
    
    def obb_angle_to_standard(self, angle_degrees, w, h):
        """将OBB角度转换为标准角度"""
        if w > h:
            standard_angle = angle_degrees + 90
        else:
            standard_angle = angle_degrees + 180
        return standard_angle % 180
    
    def get_average_depth_center(self, depth_frames, cx, cy, w, h):
        """获取检测框中心点附近的深度值 (多帧融合: 优先中心点，失败则区域中值，最后取多帧平均)"""
        # 兼容单个帧输入
        if not isinstance(depth_frames, list):
            depth_frames = [depth_frames]

        valid_depths = []
        cx_int, cy_int = int(cx), int(cy)

        for d_frame in depth_frames:
            depth_image = np.asanyarray(d_frame.get_data())
            img_h, img_w = depth_image.shape
            
            val = 0.0
            # 1. 尝试直接获取中心点深度
            if 0 <= cx_int < img_w and 0 <= cy_int < img_h:
                center_depth = depth_image[cy_int, cx_int]
                if center_depth > 0:
                    val = center_depth * self.depth_scale

            # 2. 如果中心点无效，使用周围区域中值
            if val == 0.0:
                margin = 2
                x_start = max(0, cx_int - margin)
                x_end = min(img_w, cx_int + margin + 1)
                y_start = max(0, cy_int - margin)
                y_end = min(img_h, cy_int + margin + 1)
                
                depth_region = depth_image[y_start:y_end, x_start:x_end]
                region_valid = depth_region[depth_region > 0]
                
                if len(region_valid) > 0:
                    val = np.median(region_valid) * self.depth_scale
            
            if val > 0:
                valid_depths.append(val)
            
        if not valid_depths:
            return 0.0
            
        # 3. 多帧取平均
        return np.mean(valid_depths)
    
    
    def pixel2cam(self, pixel_x, pixel_y, depth):
        """像素坐标转换为相机坐标系"""
        # 归一化像素坐标
        x_norm = (pixel_x - self.color_intrinsics.ppx) / self.color_intrinsics.fx
        y_norm = (pixel_y - self.color_intrinsics.ppy) / self.color_intrinsics.fy
        # x_norm = (pixel_x - self.color_intrinsics['matrix'][0][2]) / self.color_intrinsics['matrix'][0][0]
        # y_norm = (pixel_y - self.color_intrinsics['matrix'][1][2]) / self.color_intrinsics['matrix'][1][1]
        
        # 计算相机坐标系下的坐标
        X = depth * x_norm
        Y = depth * y_norm
        Z = depth
        
        return np.array([X, Y, Z])
    
    def quaternion_to_rotation_matrix(self, q):
        """四元数转换为旋转矩阵"""
        qx, qy, qz, qw = q
        
        # 计算旋转矩阵
        R = np.array([
            [1 - 2*qy*qy - 2*qz*qz, 2*qx*qy - 2*qz*qw, 2*qx*qz + 2*qy*qw],
            [2*qx*qy + 2*qz*qw, 1 - 2*qx*qx - 2*qz*qz, 2*qy*qz - 2*qx*qw],
            [2*qx*qz - 2*qy*qw, 2*qy*qz + 2*qx*qw, 1 - 2*qx*qx - 2*qy*qy]
        ])
        
        return R
    
    def euler_to_quaternion(self, roll, pitch, yaw):
        """
        将欧拉角(角度制)转换为四元数 [qx, qy, qz, qw]
        顺序: Z-Y-X (Yaw-Pitch-Roll)
        """
        # 转换为弧度
        roll = np.radians(roll)
        pitch = np.radians(pitch)
        yaw = np.radians(yaw)

        cy = np.cos(yaw * 0.5)
        sy = np.sin(yaw * 0.5)
        cp = np.cos(pitch * 0.5)
        sp = np.sin(pitch * 0.5)
        cr = np.cos(roll * 0.5)
        sr = np.sin(roll * 0.5)

        qw = cr * cp * cy + sr * sp * sy
        qx = sr * cp * cy - cr * sp * sy
        qy = cr * sp * cy + sr * cp * sy
        qz = cr * cp * sy - sr * sp * cy

        return np.array([qx, qy, qz, qw])
    def cam2base(self, cam_x, cam_y, cam_z, robot_position, robot_quaternion):
        """相机坐标系到基座坐标系的转换 (Eye-in-Hand)"""
        if robot_position is None or robot_quaternion is None:
            raise ValueError("机器人位置和姿态未设置")
        
        # 1. 相机坐标系 -> 机械臂末端坐标系neixt(0
        #ww)
        # 使用标定的外参矩阵 (假设 extrinsics_matrix 是 T_end_cam)
        cam_point = np.array([cam_x, cam_y, cam_z, 1.0])
        end_point_homogeneous = self.extrinsics_matrix @ cam_point
        end_point = end_point_homogeneous[:3]
        
        # 2. 机械臂末端坐标系 -> 机械臂基座坐标系
        # T_base_end 由机器人当前的位姿决定
        R_base_end = self.quaternion_to_rotation_matrix(robot_quaternion)
        t_base_end = np.array(robot_position)
        #wwwwdn
        # P_base = R_base_end * P_end + t_base_end
        base_point = R_base_end @ end_point + t_base_end
        
        return base_point

    def calculate_grasp_quaternion(self, image_angle, robot_quaternion, class_id=None):
        """
        计算基座坐标系下的抓取四元数
        Args:
            image_angle: 图像坐标系下的物体角度 (角度制)
            robot_quaternion: 机械臂当前姿态四元数
            class_id: 物体类别ID，用于特殊处理
        """
        # 1. 计算物体在图像/相机坐标系下的方向向量
        # 图像坐标系: X右, Y下. 角度通常是相对于X轴
        # 相机坐标系: X右, Y下, Z前 (RealSense默认)
        angle_rad = np.radians(image_angle)
        v_cam = np.array([np.cos(angle_rad), np.sin(angle_rad), 0])

        # 2. 将方向向量转换到末端坐标系
        # 只旋转向量，不平移，所以只用外参的旋转部分
        R_end_cam = self.extrinsics_matrix[:3, :3]
        v_end = R_end_cam @ v_cam

        # 3. 将方向向量转换到基座坐标系
        R_base_end = self.quaternion_to_rotation_matrix(robot_quaternion)
        v_base = R_base_end @ v_end

        # 4. 计算基座坐标系下的 Yaw 角
        # 我们希望抓手垂直向下 (Pitch=90)，且在水平面内的旋转与物体对齐
        yaw_base = np.arctan2(v_base[1], v_base[0])
        
        # 5. 构造最终抓取姿态 (Roll=0, Pitch=90, Yaw=calculated)
        # 注意：这里的 90 度取决于机械臂末端定义，通常 Pitch=90 是垂直向下
        final_yaw = np.degrees(yaw_base) + 90
        
        # 如果不是积木3 (class_id != 2)，则将角度限制在 [-90, 90] 范围内 (二指夹爪对称性)
        if class_id != 2:
            while final_yaw > 90:
                final_yaw -= 180
            while final_yaw < -90:
                final_yaw += 180
            
        return self.euler_to_quaternion(0, 90, final_yaw)

    
    def draw_detection(self, image, detection):
        """在图像上绘制检测结果"""
        cx, cy = detection['pixel_coords']
        w, h = detection['size']
        angle_degrees = detection['obb_angle']
        standard_angle = detection['image_angle']
        conf = detection['confidence']
        class_name = detection['class_name']
        depth = detection['depth']
        
        # 绘制OBB框
        rect = ((cx, cy), (w, h), angle_degrees)
        box = cv2.boxPoints(rect).astype(int)
        cv2.drawContours(image, [box], 0, (0, 255, 0), 2)
        
        # 绘制中心点
        cv2.circle(image, (int(cx), int(cy)), 5, (0, 0, 255), -1)
        
        # 绘制方向箭头
        arrow_length = min(w, h) / 2
        end_x = int(cx + arrow_length * np.cos(np.radians(standard_angle)))
        end_y = int(cy + arrow_length * np.sin(np.radians(standard_angle)))
        cv2.arrowedLine(image, (int(cx), int(cy)), (end_x, end_y),
                       (255, 0, 0), 3, tipLength=0.3)
        
        # 添加标签
        label = f"{class_name}: {conf:.2f}"
        cv2.putText(image, label, (int(cx-w/2), int(cy-h/2-10)),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
        
        angle_text = f"Angle: {standard_angle:.1f}"
        cv2.putText(image, angle_text, (int(cx-w/2), int(cy+h/2+20)),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
        
        depth_text = f"Depth: {depth*100:.0f}cm"
        cv2.putText(image, depth_text, (int(cx-w/2), int(cy+h/2+50)),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        # cv2.imwrite("detection_result.jpg", image)
    
    def process_frame_test(self, color_image, depth_frames, robot_position, robot_quaternion, use_pca=False, hsv_min=None, hsv_max=None):
        """
        处理单帧图像，检测物体并计算3D位置
        
        Args:
            color_image: 彩色图像 (numpy array)
            depth_frames: 深度帧列表 (list of pyrealsense2 depth frame)
            robot_position: 机器人位置 [x, y, z]
            robot_quaternion: 机器人姿态四元数 [qx, qy, qz, qw]
            use_pca: 是否使用 PCA 计算角度 (针对 Block 3)
            hsv_min: HSV 阈值下限
            hsv_max: HSV 阈值上限
            
        Returns:
            processed_image: 处理后的图像
            detections: 检测结果列表
        """
        # 运行YOLO检测
        results = self.model(color_image, verbose=False)[0]
        detections = []
        if hasattr(results, 'obb') and results.obb is not None:
            # 预处理：如果是精确检测模式(use_pca=True)，找出距离中心最近的 class_id=2
            target_index = -1
            if self.class_id == 2 and use_pca:
                min_dist = float('inf')
                img_h, img_w = color_image.shape[:2]
                cx_img, cy_img = img_w / 2, img_h / 2
                
                for i in range(len(results.obb.data)):
                    _cx, _cy, _w, _h, _angle, _conf, _cls = results.obb.data[i].tolist()[:7]
                    if int(_cls) == 2 and _conf > self.conf_threshold:
                        dist = (_cx - cx_img)**2 + (_cy - cy_img)**2
                        if dist < min_dist:
                            min_dist = dist
                            target_index = i

            for i in range(len(results.obb.data)):
                cx, cy, w, h, angle_rad, conf, cls = results.obb.data[i].tolist()[:7]
                if conf > self.conf_threshold:
                    # 如果是精确检测模式，忽略非目标(非最近)的 class 2
                    if self.class_id == 2 and use_pca and int(cls) == 2:
                        if i != target_index:
                            continue

                    # 处理角度
                    angle_degrees = np.degrees(angle_rad)
                    standard_angle = self.obb_angle_to_standard(angle_degrees, w, h)

                    # --- Special handling for class 2 (Block 3) ---
                    if self.class_id == 2 and use_pca and hsv_min is not None and int(cls) == 2:
                        # Extract ROI
                        img_h, img_w = color_image.shape[:2]
                        side_len = max(w, h) * 1.6
                        x1 = int(cx - side_len / 2)
                        y1 = int(cy - side_len / 2)
                        x2 = int(cx + side_len / 2)
                        y2 = int(cy + side_len / 2)
                        
                        x1 = max(0, x1); y1 = max(0, y1)
                        x2 = min(img_w, x2); y2 = min(img_h, y2)
                        
                        if (x2 - x1) > 10 and (y2 - y1) > 10:
                            # --- Internal 60-frame loop for PCA stability ---
                            pca_angles = []
                            last_thresh = None
                            
                            # 1. Process current frame
                            roi = color_image[y1:y2, x1:x2]
                            ang, succ, th = calculate_angle_pca(roi, hsv_min, hsv_max)
                            if succ: 
                                pca_angles.append(ang)
                                last_thresh = th
                            
                            # 2. Capture and process additional frames
                            print("  [Internal] Collecting 60 PCA samples for closest Block 3...")
                            for _ in range(10):
                                c_frame, _ = self.get_frames()
                                if c_frame:
                                    c_img = np.asanyarray(c_frame.get_data())
                                    roi_new = c_img[y1:y2, x1:x2]
                                    ang, succ, th = calculate_angle_pca(roi_new, hsv_min, hsv_max)
                                    if succ: 
                                        pca_angles.append(ang)
                                        last_thresh = th
                            
                            # 保存二值化图像以便调试
                            if last_thresh is not None:
                                cv2.imwrite("debug_block3_thresh.jpg", last_thresh)
                            
                            if pca_angles:
                                print(pca_angles)
                                pca_angle = np.median(pca_angles)
                                success = True
                            else:
                                success = False

                            if success:
                                # 直接使用 PCA 角度
                                standard_angle = -pca_angle
                                print(f"Class 2 (Block 3). Using PCA Angle: {standard_angle:.1f}")
                    
                    # 获取深度 (传入多帧)
                    depth_value = self.get_average_depth_center(depth_frames, cx, cy, w, h)
                    
                    if depth_value > 0:
                        try:
                            # 1. 像素坐标 → 相机坐标
                            camera_coords = self.pixel2cam(cx, cy, depth_value)
                            
                            # 2. 相机坐标 → 基坐标
                            base_coords = self.cam2base(
                                camera_coords[0], camera_coords[1], camera_coords[2],
                                robot_position, robot_quaternion
                            )
                            
                            # 3. 计算抓取姿态(四元数) - 使用修正后的逻辑
                            grasp_quaternion = self.calculate_grasp_quaternion(standard_angle, robot_quaternion, class_id=int(cls))
                            
                            # 保存检测结果
                            detection = {
                                'class_id': int(cls),
                                'class_name': results.names[int(cls)],
                                'pixel_coords': (cx, cy),
                                'camera_coords': camera_coords,
                                'base_coords': base_coords,
                                'grasp_pose':{
                                    'position': base_coords,
                                    'quaternion': grasp_quaternion,
                                    # 这里的 euler 仅作参考显示
                                    'euler_angles': (0, 90, standard_angle) 
                                },
                                'image_angle': standard_angle,
                                'depth': depth_value,
                                'confidence': conf,
                                'size': (w, h),
                                'obb_angle': angle_degrees
                            }
                            detections.append(detection)
                            
                            # 绘制到图像上
                            self.draw_detection(color_image, detection)
                            
                        except Exception as e:
                            print(f"处理检测时出错: {e}")
                            import traceback
                            traceback.print_exc()
        return color_image, detections
    
    
    def _capture_and_detect(self, robot_pos, robot_quat, use_pca=False, hsv_min=None, hsv_max=None):
        """辅助函数：采集图像并进行检测 (多帧深度平均)"""
        # 采集5帧深度数据
        depth_frames = []
        color_image = None
        
        for _ in range(5):
            colored_frame, d_frame = self.get_frames()
            if colored_frame and d_frame:
                color_image = np.array(colored_frame.get_data())
                depth_frames.append(d_frame)
            
        if color_image is None or not depth_frames:
            return None, []

        # 使用最后一帧的图像和所有深度帧进行检测
        processed_image, detections = self.process_frame_test(
            color_image, depth_frames, 
            robot_pos, robot_quat,
            use_pca=use_pca, hsv_min=hsv_min, hsv_max=hsv_max
        )
        
        # 计算距离图像中心的距离
        if detections:
            img_h, img_w = color_image.shape[:2]
            cx_img, cy_img = img_w / 2, img_h / 2
            for det in detections:
                px, py = det['pixel_coords']
                det['dist_to_center'] = (px - cx_img)**2 + (py - cy_img)**2
                
        return processed_image, detections

    def run_detection(self, class_id=0):
        print(f"\n--- 开始检测流程 (Class ID: {class_id}) ---")
        self.class_id = class_id
        # ================= 第一步：闭环视觉伺服对齐 =================
        align_threshold = 15 # 像素阈值
        max_align_attempts = 5 # 最大尝试次数
        
        for attempt in range(max_align_attempts):
            print(f"对齐尝试 {attempt + 1}/{max_align_attempts}...")
            
            # 1. 获取当前位姿
            current_pose = self.robot.get_end_pose()
            if current_pose is None:
                print("无法获取机械臂位姿")
                return
            robot_pos, robot_quat = current_pose[0], current_pose[1]

            # 2. 检测 (对齐阶段不使用 PCA)
            processed_img, detections = self._capture_and_detect(robot_pos, robot_quat, use_pca=False)
            if attempt == 0:
                cv2.imwrite('detection_step1.jpg', processed_img)

            # 3. 筛选目标 (距离中心最近)
            target = None
            if detections:
                # 筛选 class_id 并按距离中心排序
                valid_dets = [d for d in detections if d['class_id'] == class_id]
                if valid_dets:
                    valid_dets.sort(key=lambda x: x['dist_to_center'])
                    target = valid_dets[0]
            
            if not target:
                print(f"未找到 class_id={class_id} 的目标")
                if attempt == 0: return
                break # 之前找到过，现在丢了，停止对齐

            dist_px = math.sqrt(target['dist_to_center'])
            print(f"锁定目标 (距离中心 {dist_px:.1f} px)")
            
            if dist_px < align_threshold:
                print("目标已对齐！")
                break
            
            # 4. 执行对齐 (只平移，不旋转)
            cam_offset = target['camera_coords'].copy()
            cam_offset[2] = 0 # Z轴(深度)暂时保持，只对齐XY
            
            R_end_cam = self.extrinsics_matrix[:3, :3]
            R_base_end = self.quaternion_to_rotation_matrix(robot_quat)
            move_vec_base = R_base_end @ R_end_cam @ cam_offset
            
            # 计算对齐后的目标位置
            align_pos = np.array(robot_pos) + move_vec_base
            
            # 智能高度调整：如果太高就下降以便观测，否则保持
            if align_pos[2] > 0.25:
                align_pos[2] = 0.2
            
            print(f"执行视觉对齐平移: {move_vec_base}")
            self.robot.move_to_cart_pose([align_pos.tolist(), robot_quat])
            time.sleep(0.8) # 等待稳定


        # ================= 第二步：精确检测与抓取 =================
        # 1. 获取新位姿
        current_pose = self.robot.get_end_pose()
        if current_pose is None: return
        robot_pos, robot_quat = current_pose[0], current_pose[1]

        
        # 2. 多次检测取中位数 (10次)
        print("2. 精确检测中 (采样10次)...")
        
        collected_positions = []
        collected_quaternions = []
        last_processed_img = None
        
        # Determine if we use PCA and HSV settings
        use_pca = (class_id == 2)
        if class_id == 2:
            range_time=1
        else:
            range_time=1
        hsv_min = self.block3_hsv_min if class_id == 2 else None
        hsv_max = self.block3_hsv_max if class_id == 2 else None
        
        for i in range(range_time):
            processed_img, detections = self._capture_and_detect(
                robot_pos, robot_quat, 
                use_pca=use_pca, hsv_min=hsv_min, hsv_max=hsv_max
            )
            last_processed_img = processed_img
            
            if detections:
                valid_dets = [d for d in detections if d['class_id'] == class_id]
                if valid_dets:
                    valid_dets.sort(key=lambda x: x['dist_to_center'])
                    best_target = valid_dets[0]
                    collected_positions.append(best_target['grasp_pose']['position'])
                    collected_quaternions.append(best_target['grasp_pose']['quaternion'])
            if i % 2 == 0:
                print(f"  采样 {i+1}/10")

        if last_processed_img is not None:
            cv2.imwrite('detection_step2.jpg', last_processed_img)
        
        if len(collected_positions) > 0:
            print(f"成功采集 {len(collected_positions)}/10 次数据，计算中位数...")
            
            # 计算位置中位数 (引入 IQR 过滤)
            positions_np = np.array(collected_positions)
            
            def get_iqr_median(data):
                if len(data) < 4: return np.median(data)
                q1 = np.percentile(data, 25)
                q3 = np.percentile(data, 75)
                iqr = q3 - q1
                lower_bound = q1 - 1.5 * iqr
                upper_bound = q3 + 1.5 * iqr
                clean_data = data[(data >= lower_bound) & (data <= upper_bound)]
                if len(clean_data) == 0: return np.median(data)
                return np.median(clean_data)

            median_x = get_iqr_median(positions_np[:, 0])
            median_y = get_iqr_median(positions_np[:, 1])
            median_z = get_iqr_median(positions_np[:, 2])
            median_pos = np.array([median_x, median_y, median_z])
            
            # 计算四元数中位数 (对各分量取中位数并归一化)
            quats = np.array(collected_quaternions)
            median_quat = np.median(quats, axis=0)
            norm = np.linalg.norm(median_quat)
            if norm > 0:
                median_quat = median_quat / norm
            else:
                median_quat = quats[0]

            print("执行抓取序列...")
            # 使用中位数结果
            obj_pos = median_pos.copy()
            grasp_quat = median_quat
            
            # 定义高度偏移量 (米)
            HOVER_HEIGHT = 0.15   # 悬停高度
            
            # 1. 移动到物体正上方 (悬停) - 这次带上抓取角度
            hover_pos = obj_pos.copy()
            hover_pos[2] = HOVER_HEIGHT
            print(f"移动到悬停位置: {hover_pos}")
            self.robot.move_to_cart_pose([hover_pos.tolist(), grasp_quat.tolist()])
            
            # 2. 下降抓取
            grasp_pos = obj_pos.copy()
            if class_id == 2:
                grasp_pos[2] = 0.03+0.03
            else:
                grasp_pos[2] = 0.02+0.03
            if grasp_pos[2] < 0.005: grasp_pos[2] = 0.005
                
            print(f"移动到抓取位置: {grasp_pos}")
            self.robot.move_to_cart_pose([grasp_pos.tolist(), grasp_quat.tolist()])
            
            # 3. 闭合夹爪
            self.robot.move_eef_pos([0.00]) 
            time.sleep(0.5)
            
            # 4. 抬起
            print(f"抬起")
            self.robot.move_to_cart_pose([hover_pos.tolist(), grasp_quat.tolist()])
        else:
            print("对齐后丢失目标！")




# 主函数
if __name__ == "__main__":
    detector = DetectionSystem()
    
    initial_position = [0.2, 0, 0.32]  # 机器人位置 (x, y, z)
    initial_quaternion = [0.0, 0.5382996083468239, 0.0, 0.8433914458128852] # 机器人姿态四元数 (qx, qy, qz, qw)

    # exit(0)
    place_pose = [[-0.062, -0.32752352748698496, 0.018], [0, 0.7071068, 0, 0.7071068] ]

    remove_pose_1=[[-0.16288820927393982, -0.3217247688074838, 0.05], [0.5079623881977562, 0.4938207036434973, -0.5001322201433527, 0.4979790027741675]]

    remove_pose_2=[[-0.20288820927393982, -0.3217247688074838, -0.0671829013575066], [0.5079623881977562, 0.4938207036434973, -0.5001322201433527, 0.4979790027741675]]

    remove_pose_3=[[-0.15488820927393982, -0.3217247688074838, -0.0671829013575066], [0.5079623881977562, 0.4938207036434973, -0.5001322201433527, 0.4979790027741675]]
    # [[0.0007813723439017428, -0.33992352748698496, 0.03510353564706023], [0.015433232410532455, 0.6942487587734955, -0.0061318348804662555, 0.7195435197955868]]
    detector.set_robot_pose(initial_position, initial_quaternion)
    # detector.set_robot_pose(initial_position, initial_quaternion)
    # 移动机械臂到初始位置
    
    detector.robot.move_eef_pos([0.07])
    detector.robot.move_to_cart_pose([detector.robot_position, detector.robot_quaternion])
    # 运行检测循环
    
    def execute_place_sequence(pose):
        # 计算悬停位置 (Z+3cm)
        hover_pose_x = [list(pose[0]), list(pose[1])]
        hover_pose_x[0][0] += 0.03
        
        hover_pose_x_z = [list(pose[0]), list(pose[1])]
        hover_pose_x_z[0][0] += 0.03
        hover_pose_x_z[0][2] += 0.1

        hover_pose_z = [list(pose[0]), list(pose[1])]
        hover_pose_z[0][2] += 0.03
        
        detector.robot.move_to_cart_pose(hover_pose_x_z)
        detector.robot.move_to_cart_pose(hover_pose_x)
        detector.robot.move_to_cart_pose(pose)
        detector.robot.move_eef_pos([0.07])
        time.sleep(0.5)
        detector.robot.move_eef_pos([0.])
        time.sleep(0.5)
        detector.robot.move_eef_pos([0.07])
        time.sleep(0.5)
        detector.robot.move_to_cart_pose(hover_pose_z)

        detector.robot.move_to_cart_pose([detector.robot_position, detector.robot_quaternion])

    def execute_place_sequence_last(pose):
        # 计算悬停位置 (Z+3cm)
        hover_pose_x_z = [list(pose[0]), list(pose[1])]
        hover_pose_x_z[0][0] += 0.03
        hover_pose_x_z[0][2] += 0.1

        hover_pose_z = [list(pose[0]), list(pose[1])]
        hover_pose_z[0][2] += 0.03
        
        detector.robot.move_to_cart_pose(hover_pose_z)
        detector.robot.move_to_cart_pose(pose)
        detector.robot.move_eef_pos([0.07])
        time.sleep(0.5)
        detector.robot.move_eef_pos([0.])
        time.sleep(0.5)
        detector.robot.move_eef_pos([0.07])
        time.sleep(0.5)
        time.sleep(0.5)
        detector.robot.move_to_cart_pose(hover_pose_z)

        detector.robot.move_to_cart_pose([detector.robot_position, detector.robot_quaternion])
    
    # place_pose[0][2] +=0.05  # 抓取第一个1
    # for _ in range(10):
    #     detector.run_detection(class_id=2)
    #     execute_place_sequence(place_pose)
    # exit(0)

    

    detector.run_detection(class_id=0)
    #place_pose[0][2] +=0.05  # 抓取第一个1
    execute_place_sequence(place_pose)
    #exit(0)
    detector.run_detection(class_id=0)  # 抓取第二个1
    place_pose[0][0] += 0.06
    execute_place_sequence(place_pose)

    detector.run_detection(class_id=0)  # 抓取第三个1
    place_pose[0][0] += 0.06
    place_pose[0][1] -= 0.0015
    execute_place_sequence(place_pose)

    detector.run_detection(class_id=0)  # 抓取第四个1
    place_pose[0][0] += 0.055
    execute_place_sequence(place_pose)
    place_pose[0][0] += 0.005
    place_pose[0][1] += 0.0015


    detector.robot.move_to_cart_pose(remove_pose_1)
    detector.robot.move_eef_pos([0.00])
    detector.robot.move_to_cart_pose(remove_pose_2)
    detector.robot.move_to_cart_pose(remove_pose_3)
    detector.robot.move_to_cart_pose(remove_pose_2)
    detector.robot.move_to_cart_pose(remove_pose_1)


    detector.robot.move_to_cart_pose([detector.robot_position, detector.robot_quaternion])
    detector.robot.move_eef_pos([0.07])
    detector.run_detection(class_id=1)  # 抓取第一个2
    place_pose[0][0] -= 0.155
    place_pose[0][2] += 0.032
    execute_place_sequence(place_pose)

    detector.run_detection(class_id=2)  # 抓取第一个3
    place_pose[0][0] += 0.05
    place_pose[0][2] += 0.012
    execute_place_sequence(place_pose)

    detector.run_detection(class_id=2)  # 抓取第二个3
    place_pose[0][0] += 0.04
    place_pose[0][1] -= 0.001
    execute_place_sequence(place_pose)

    place_pose[0][1] += 0.001
    detector.run_detection(class_id=1)  # 抓取第二个2
    place_pose[0][0] += 0.045
    place_pose[0][2] -= 0.013
    execute_place_sequence(place_pose)

    detector.run_detection(class_id=1)  # 抓取第三个2
    place_pose[0][2] += 0.056
    place_pose[0][0] -= 0.071
    execute_place_sequence_last(place_pose)

    detector.run_detection(class_id=3)  # 抓取第一个4
    place_pose[0][2] += 0.033
    execute_place_sequence_last(place_pose)

    exit(0)


