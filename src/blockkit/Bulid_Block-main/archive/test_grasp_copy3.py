import pyrealsense2 as rs
import cv2
import numpy as np
from ultralytics import YOLO
import time
import yaml
import math
from airbot_py.arm import AIRBOTPlay, RobotMode, SpeedProfile


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
        
        # 1. 相机坐标系 -> 机械臂末端坐标系
        # 使用标定的外参矩阵 (假设 extrinsics_matrix 是 T_end_cam)
        cam_point = np.array([cam_x, cam_y, cam_z, 1.0])
        end_point_homogeneous = self.extrinsics_matrix @ cam_point
        end_point = end_point_homogeneous[:3]
        
        # 2. 机械臂末端坐标系 -> 机械臂基座坐标系
        # T_base_end 由机器人当前的位姿决定
        R_base_end = self.quaternion_to_rotation_matrix(robot_quaternion)
        t_base_end = np.array(robot_position)
        
        # P_base = R_base_end * P_end + t_base_end
        base_point = R_base_end @ end_point + t_base_end
        
        return base_point

    def calculate_grasp_quaternion(self, image_angle, robot_quaternion):
        """
        计算基座坐标系下的抓取四元数
        Args:
            image_angle: 图像坐标系下的物体角度 (角度制)
            robot_quaternion: 机械臂当前姿态四元数
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
        # 将角度限制在 [-90, 90] 范围内 (二指夹爪对称性)
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
    
    def process_frame_test(self, color_image, depth_frames, robot_position, robot_quaternion):
        """
        处理单帧图像，检测物体并计算3D位置
        
        Args:
            color_image: 彩色图像 (numpy array)
            depth_frames: 深度帧列表 (list of pyrealsense2 depth frame)
            robot_position: 机器人位置 [x, y, z]
            robot_quaternion: 机器人姿态四元数 [qx, qy, qz, qw]
            
        Returns:
            processed_image: 处理后的图像
            detections: 检测结果列表
        """
        # 运行YOLO检测
        results = self.model(color_image, verbose=False)[0]
        detections = []
        if hasattr(results, 'obb') and results.obb is not None:
            for i in range(len(results.obb.data)):
                cx, cy, w, h, angle_rad, conf, cls = results.obb.data[i].tolist()[:7]
                if conf > self.conf_threshold:
                    # 处理角度
                    angle_degrees = np.degrees(angle_rad)
                    standard_angle = self.obb_angle_to_standard(angle_degrees, w, h)
                    
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
                            grasp_quaternion = self.calculate_grasp_quaternion(standard_angle, robot_quaternion)
                            
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
    
    
    def _capture_and_detect(self, robot_pos, robot_quat):
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
            robot_pos, robot_quat
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
        
        # ================= 第一步：初步检测与对齐 =================
        # 1. 获取当前位姿
        current_pose = self.robot.get_end_pose()
        if current_pose is None:
            print("无法获取机械臂位姿")
            return
        robot_pos, robot_quat = current_pose[0], current_pose[1]

        # 2. 检测
        print("1. 初步检测中...")
        processed_img, detections = self._capture_and_detect(robot_pos, robot_quat)
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
            return

        print(f"锁定目标 (距离中心 {math.sqrt(target['dist_to_center']):.1f} px)")
        
        # 4. 执行对齐 (只平移，不旋转)
        # 计算相机坐标系下的偏移 (X, Y)
        # 我们希望将相机中心移动到物体正上方，即消除 X, Y 偏差
        cam_offset = target['camera_coords'].copy()
        cam_offset[2] = 0 # Z轴(深度)暂时保持，只对齐XY
        
        # 将偏移转换到基座坐标系
        # Delta_Base = R_base_end * R_end_cam * Delta_Cam
        R_end_cam = self.extrinsics_matrix[:3, :3]
        R_base_end = self.quaternion_to_rotation_matrix(robot_quat)
        move_vec_base = R_base_end @ R_end_cam @ cam_offset
        
        # 计算对齐后的目标位置
        align_pos = np.array(robot_pos) + move_vec_base
        
        # 对齐后Z轴稍微下降 (例如 4cm) 以便更近距离观测
        align_pos[2] -= 0.1
        
        print(f"执行视觉对齐平移: {move_vec_base}")
        # 移动机械臂 (保持当前姿态)
        self.robot.move_to_cart_pose([align_pos.tolist(), robot_quat])

        time.sleep(0.8) # 等待稳定

        # ================= 第一步：初步检测与对齐 =================
        # 1. 获取当前位姿
        current_pose = self.robot.get_end_pose()
        if current_pose is None:
            print("无法获取机械臂位姿")
            return
        robot_pos, robot_quat = current_pose[0], current_pose[1]

        # 2. 检测
        print("1. 初步检测中...")
        processed_img, detections = self._capture_and_detect(robot_pos, robot_quat)
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
            return

        print(f"锁定目标 (距离中心 {math.sqrt(target['dist_to_center']):.1f} px)")
        
        # 4. 执行对齐 (只平移，不旋转)
        # 计算相机坐标系下的偏移 (X, Y)
        # 我们希望将相机中心移动到物体正上方，即消除 X, Y 偏差
        cam_offset = target['camera_coords'].copy()
        cam_offset[2] = 0 # Z轴(深度)暂时保持，只对齐XY
        
        # 将偏移转换到基座坐标系
        # Delta_Base = R_base_end * R_end_cam * Delta_Cam
        R_end_cam = self.extrinsics_matrix[:3, :3]
        R_base_end = self.quaternion_to_rotation_matrix(robot_quat)
        move_vec_base = R_base_end @ R_end_cam @ cam_offset
        
        # 计算对齐后的目标位置
        align_pos = np.array(robot_pos) + move_vec_base
        
        print(f"执行视觉对齐平移: {move_vec_base}")
        # 移动机械臂 (保持当前姿态)
        self.robot.move_to_cart_pose([align_pos.tolist(), robot_quat])
        time.sleep(0.8) # 等待稳定


        # ================= 第二步：精确检测与抓取 =================
        # 1. 获取新位姿
        current_pose = self.robot.get_end_pose()
        if current_pose is None: return
        robot_pos, robot_quat = current_pose[0], current_pose[1]

        
        
        # 2. 多次检测取中位数 (5次)
        print("2. 精确检测中 (采样5次)...")
        
        collected_positions = []
        collected_quaternions = []
        last_processed_img = None
        
        for i in range(10):
            processed_img, detections = self._capture_and_detect(robot_pos, robot_quat)
            last_processed_img = processed_img
            
            if detections:
                valid_dets = [d for d in detections if d['class_id'] == class_id]
                if valid_dets:
                    valid_dets.sort(key=lambda x: x['dist_to_center'])
                    best_target = valid_dets[0]
                    collected_positions.append(best_target['grasp_pose']['position'])
                    collected_quaternions.append(best_target['grasp_pose']['quaternion'])
            # print(f"  采样 {i+1}/10")

        if last_processed_img is not None:
            cv2.imwrite('detection_step2.jpg', last_processed_img)
        
        if len(collected_positions) > 0:
            print(f"成功采集 {len(collected_positions)}/10 次数据，计算中位数...")
            
            # 计算位置中位数 (XYZ分别取中位数)
            positions_np = np.array(collected_positions)
            median_x = np.median(positions_np[:, 0])
            median_y = np.median(positions_np[:, 1])
            median_z = np.median(positions_np[:, 2])
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
                grasp_pos[2] = 0.03
            else:
                grasp_pos[2] = 0.015
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
    initial_quaternion = [0.0, 0.5372996083468239, 0.0, 0.8433914458128852] # 机器人姿态四元数 (qx, qy, qz, qw)
    # initial_position = [0.2, 0, 0.1]  # 机器人位置 (x, y, z)
    # grasp_quaternion = detector.euler_to_quaternion(0, 80, -103)
    # print(grasp_quaternion)
    # pose = detector.robot.get_end_pose()
    # print(pose)

    # exit(0)
    place_pose = [[-0.062, -0.32692352748698496, 0.0115], [0, 0.7071068, 0, 0.7071068] ]

    remove_pose_1=[[-0.16288820927393982, -0.3217247688074838, 0.05], [0.5079623881977562, 0.4938207036434973, -0.5001322201433527, 0.4979790027741675]]

    remove_pose_2=[[-0.20288820927393982, -0.3217247688074838, -0.0671829013575066], [0.5079623881977562, 0.4938207036434973, -0.5001322201433527, 0.4979790027741675]]

    remove_pose_3=[[-0.15488820927393982, -0.3217247688074838, -0.0671829013575066], [0.5079623881977562, 0.4938207036434973, -0.5001322201433527, 0.4979790027741675]]
    # [[0.0007813723439017428, -0.33992352748698496, 0.03510353564706023], [0.015433232410532455, 0.6942487587734955, -0.0061318348804662555, 0.7195435197955868]]
    detector.set_robot_pose(initial_position, initial_quaternion)
    # detector.set_robot_pose(initial_position, initial_quaternion)
    # 移动机械臂到初始位置
    
    detector.robot.move_eef_pos([0.07])
    detector.robot.move_to_cart_pose([detector.robot_position, detector.robot_quaternion])
    # detector.robot.move_eef_pos([0.07])
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
        detector.robot.move_to_cart_pose(hover_pose_z)

        detector.robot.move_to_cart_pose([detector.robot_position, detector.robot_quaternion])

    detector.run_detection(class_id=0)  # 抓取第一个1
    execute_place_sequence(place_pose)

    detector.run_detection(class_id=0)  # 抓取第二个1
    place_pose[0][0] += 0.06
    execute_place_sequence(place_pose)

    detector.run_detection(class_id=0)  # 抓取第三个1
    place_pose[0][0] += 0.06
    execute_place_sequence(place_pose)

    detector.run_detection(class_id=0)  # 抓取第四个1
    place_pose[0][0] += 0.06
    execute_place_sequence(place_pose)


    detector.robot.move_to_cart_pose(remove_pose_1)
    detector.robot.move_eef_pos([0.00])
    detector.robot.move_to_cart_pose(remove_pose_2)
    detector.robot.move_to_cart_pose(remove_pose_3)
    detector.robot.move_to_cart_pose(remove_pose_2)
    detector.robot.move_to_cart_pose(remove_pose_1)


    detector.robot.move_to_cart_pose([detector.robot_position, detector.robot_quaternion])
    detector.robot.move_eef_pos([0.07])
    detector.run_detection(class_id=1)  # 抓取第一个2
    place_pose[0][0] -= 0.15
    place_pose[0][2] += 0.032
    execute_place_sequence(place_pose)

    detector.run_detection(class_id=2)  # 抓取第一个3
    place_pose[0][0] += 0.05
    place_pose[0][2] += 0.015
    execute_place_sequence(place_pose)

    detector.run_detection(class_id=2)  # 抓取第二个3
    place_pose[0][0] += 0.035
    execute_place_sequence(place_pose)

    detector.run_detection(class_id=1)  # 抓取第二个2
    place_pose[0][0] += 0.055
    place_pose[0][2] -= 0.015
    execute_place_sequence(place_pose)

    detector.run_detection(class_id=1)  # 抓取第三个2
    place_pose[0][2] += 0.06
    place_pose[0][0] -= 0.06
    execute_place_sequence(place_pose)

    detector.run_detection(class_id=3)  # 抓取第一个4
    place_pose[0][2] += 0.035
    execute_place_sequence(place_pose)

    exit(0)


