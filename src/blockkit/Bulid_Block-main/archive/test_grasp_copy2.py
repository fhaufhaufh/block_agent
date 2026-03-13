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
        
        # # 获取相机内参
        color_profile = rs.video_stream_profile(self.profile.get_stream(rs.stream.color))
        self.color_intrinsics = color_profile.get_intrinsics()
        
        # 配置对齐器
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
    
    def get_average_depth_center(self, depth_frame, cx, cy, w, h):
        """获取检测框中心点附近的深度值 (使用中值滤波优化)"""
        # 将深度帧转换为numpy数组
        depth_image = np.asanyarray(depth_frame.get_data())
        
        # 获取中心点周围区域 (上下左右各2个像素)
        margin = 2
        img_h, img_w = depth_image.shape
        
        cx_int, cy_int = int(cx), int(cy)
        
        x_start = max(0, cx_int - margin)
        x_end = min(img_w, cx_int + margin + 1)
        y_start = max(0, cy_int - margin)
        y_end = min(img_h, cy_int + margin + 1)
        
        # 获取区域内的深度值
        depth_region = depth_image[y_start:y_end, x_start:x_end]
        
        # 剔除深度值为0的点
        valid_depths = depth_region[depth_region > 0]
        
        if len(valid_depths) == 0:
            return 0.0
            
        # [优化] 使用中值 (Median) 代替平均值 (Mean) 以抵抗噪声
        return np.median(valid_depths) * self.depth_scale
    def get_average_depth(self, depth_frame, cx, cy, w, h):
        """获取检测框区域的平均深度值"""
        # 将深度帧转换为numpy数组
        depth_image = np.asanyarray(depth_frame.get_data())
        
        # 计算检测框区域
        x_start = int(max(0, cx - w/2))
        x_end = int(min(depth_image.shape[1], cx + w/2))
        y_start = int(max(0, cy - h/2))
        y_end = int(min(depth_image.shape[0], cy + h/2))
        
        # 获取区域内的深度值
        depth_region = depth_image[y_start:y_end, x_start:x_end]
        valid_depths = depth_region[depth_region > 0]
        
        if len(valid_depths) > 0:
            # 计算平均深度并转换为米
            avg_depth_raw = np.mean(valid_depths)
            return avg_depth_raw * self.depth_scale
        else:
            return 0.0
    
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
    
    def process_frame_test(self, color_image, depth_frame, robot_position, robot_quaternion):
        """
        处理单帧图像，检测物体并计算3D位置
        
        Args:
            color_image: 彩色图像 (numpy array)
            depth_frame: 深度帧 (pyrealsense2 depth frame)
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
                    
                    # 获取深度
                    depth_value = self.get_average_depth_center(depth_frame, cx, cy, w, h)
                    
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
    
    def process_frame(self, color_image, depth_frame, robot_position, robot_quaternion):
        """
        处理单帧图像，检测物体并计算3D位置
        
        Args:
            color_image: 彩色图像 (numpy array)
            depth_frame: 深度帧 (pyrealsense2 depth frame)
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
                    
                    # 获取深度
                    depth_value = self.get_average_depth(depth_frame, cx, cy, w, h)
                    
                    if depth_value > 0:
                        try:
                            # 1. 像素坐标 → 相机坐标
                            camera_coords = self.pixel2cam(cx, cy, depth_value)
                            
                            # 2. 相机坐标 → 基坐标
                            base_coords = self.cam2base(
                                camera_coords[0], camera_coords[1], camera_coords[2],
                                robot_position, robot_quaternion
                            )
                            # 3. 计算抓取姿态(四元数)
                            grasp_quaternion = self.euler_to_quaternion(0, 90, standard_angle)
                            
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
                            # self.draw_detection(color_image, detection)
                            
                        except Exception as e:
                            print(f"处理检测时出错: {e}")
        
        return color_image, detections
    def run_detection(self, class_id=0):
        # [优化] 1. 实时获取机械臂位姿，确保坐标转换准确
        current_pose = self.robot.get_end_pose()
        if current_pose is None:
            print("无法获取机械臂位姿，使用缓存值")
            robot_pos = self.robot_position
            robot_quat = self.robot_quaternion
        else:
            robot_pos = current_pose[0]
            robot_quat = current_pose[1]
            print(f"实时位姿获取成功: {robot_pos}")

        # [优化] 2. 多帧融合获取稳定图像 (丢弃前几帧，取最后一帧，或者做平均)
        # 这里简单做：连续读 5 次，取最后一次的 Color，但深度可以做融合（这里简化为取最后一次，配合 get_average_depth_center 的中值滤波）
        for _ in range(5):
            colored_frame, depth_frame = self.get_frames()
            time.sleep(0.05) # 稍微间隔一下
            
        color_image = np.array(colored_frame.get_data())
        
        processed_image, detections = self.process_frame_test(
            color_image, depth_frame, 
            robot_pos, robot_quat  # 传入实时位姿
        )
        cv2.imwrite('detection_result.jpg', processed_image)
        
        # 根据置信度排序并尝试移动到第一个 class_id == 0 的目标
        if detections:
            # 按 confidence 降序排序
            detections_sorted = sorted(detections, key=lambda d: d.get('confidence', 0.0), reverse=True)
            target = None
            for det in detections_sorted:
                if det.get('class_id') == class_id:
                    target = det
                    break
            
            if target is not None:
                print("原始角度", target['obb_angle'])
                print("计算后的角度", target['image_angle'])
                
                # 获取物体实际位置
                obj_pos = target['grasp_pose']['position'].copy()
                grasp_quat = target['grasp_pose']['quaternion']
                
                # 定义高度偏移量 (米)
                HOVER_HEIGHT = 0.15   # 悬停高度 (相对于物体)
                GRASP_HEIGHT = 0.005  # 抓取高度 (相对于物体，可能需要微调，如果是中心点可能为0或负值)
                
                # 1. 移动到物体正上方 (悬停)
                hover_pos = obj_pos.copy()
                hover_pos[2] = HOVER_HEIGHT
                print(f"移动到悬停位置: {hover_pos}")
                self.robot.move_to_cart_pose([hover_pos.tolist(), grasp_quat.tolist()])
                
                # 2. 下降抓取
                grasp_pos = obj_pos.copy()
                grasp_pos[2] =0.02 
                # 增加一个最低高度保护，防止撞桌面 (假设桌面在 z=0)
                if grasp_pos[2] < 0.005: 
                    grasp_pos[2] = 0.005
                    
                print(f"移动到抓取位置: {grasp_pos}")
                self.robot.move_to_cart_pose([grasp_pos.tolist(), grasp_quat.tolist()])
                
                # 3. 闭合夹爪
                self.robot.move_eef_pos([0.00]) 
                time.sleep(0.5)
                
                # 4. 抬起
                print(f"抬起回到悬停位置")
                self.robot.move_to_cart_pose([hover_pos.tolist(), grasp_quat.tolist()])
            else:
                print(f"未找到 class_id={class_id} 的目标")



    def run_detection_loop(self):
        """运行检测循环"""
        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
        
        print("按 'q' 退出检测循环")
        
        try:
            while True:
                # 获取帧
                color_frame, depth_frame = self.get_frames()
                if not color_frame or not depth_frame:
                    continue
                
                # 转换为numpy数组
                color_image = np.asanyarray(color_frame.get_data())
                
                # 处理帧
                processed_image, detections = self.process_frame(
                    color_image, depth_frame, 
                    self.robot_position, self.robot_quaternion
                )
                
                # 显示结果信息
                if detections:
                    print(f"\n检测到 {len(detections)} 个物体:")
                    for i, det in enumerate(detections):
                        print(f"  目标 #{i+1}: {det['class_name']}")
                        print(f"    像素坐标: ({det['pixel_coords'][0]:.1f}, {det['pixel_coords'][1]:.1f})")
                        print(f"    相机坐标: ({det['camera_coords'][0]:.3f}, {det['camera_coords'][1]:.3f}, {det['camera_coords'][2]:.3f}) m")
                        print(f"    基座坐标: ({det['base_coords'][0]:.3f}, {det['base_coords'][1]:.3f}, {det['base_coords'][2]:.3f}) m")
                        print(f"    角度: {det['image_angle']:.1f}°, 深度: {det['depth']*100:.0f}cm")
                        print("  " + "-" * 40)
                
                # 显示图像
                cv2.imshow(self.window_name, processed_image)
                
                # 键盘控制
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    break
        
        except KeyboardInterrupt:
            print("\n检测被用户中断")
        except Exception as e:
            print(f"检测运行出错: {e}")
        finally:
            # 清理资源
            self.pipeline.stop()
            cv2.destroyAllWindows()
            print("检测已结束")

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
    place_pose = [[0.0007813723439017428, -0.33992352748698496, 0.01710353564706023], [0.015433232410532455, 0.6942487587734955, -0.0061318348804662555, 0.7195435197955868]]
    # [[0.0007813723439017428, -0.33992352748698496, 0.03510353564706023], [0.015433232410532455, 0.6942487587734955, -0.0061318348804662555, 0.7195435197955868]]
    detector.set_robot_pose(initial_position, initial_quaternion)
    # detector.set_robot_pose(initial_position, initial_quaternion)
    # 移动机械臂到初始位置
    
    detector.robot.move_eef_pos([0.07])
    detector.robot.move_to_cart_pose([detector.robot_position, detector.robot_quaternion])
    detector.robot.move_eef_pos([0.07])
    # 运行检测循环
    detector.run_detection(class_id=0)  # 抓取第一个1
    detector.robot.move_to_cart_pose(place_pose)    # 放置第一个1
    detector.robot.move_eef_pos([0.07])
    detector.robot.move_to_cart_pose([detector.robot_position, detector.robot_quaternion])  # 回到初始位置

    detector.run_detection(class_id=0)  # 抓取第二个1
    place_pose[0][0] += 0.06
    detector.robot.move_to_cart_pose(place_pose)    # 放置第二个1
    detector.robot.move_eef_pos([0.07])
    detector.robot.move_to_cart_pose([detector.robot_position, detector.robot_quaternion])  # 回到初始位置

    detector.run_detection(class_id=0)  # 抓取第二个1
    place_pose[0][0] += 0.06
    detector.robot.move_to_cart_pose(place_pose)    # 放置第二个1
    detector.robot.move_eef_pos([0.07])
    detector.robot.move_to_cart_pose([detector.robot_position, detector.robot_quaternion])  # 回到初始位置

    detector.run_detection(class_id=0)  # 抓取第二个1
    place_pose[0][0] += 0.06
    detector.robot.move_to_cart_pose(place_pose)    # 放置第二个1
    detector.robot.move_eef_pos([0.07])
    detector.robot.move_to_cart_pose([detector.robot_position, detector.robot_quaternion])  # 回到初始位置

    detector.run_detection(class_id=1)  # 抓取第二个1
    place_pose[0][0] -= 0.15
    place_pose[0][2] += 0.04
    detector.robot.move_to_cart_pose(place_pose)    # 放置第二个1
    detector.robot.move_eef_pos([0.07])
    detector.robot.move_to_cart_pose([detector.robot_position, detector.robot_quaternion])  # 回到初始位置



