import pyrealsense2 as rs
import cv2
import numpy as np
from ultralytics import YOLO
import time
import yaml
import math

class DetectionSystem:
    def __init__(self, config_path="../config/camera.yaml"):
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
        
        # 获取相机内参
        color_profile = rs.video_stream_profile(self.profile.get_stream(rs.stream.color))
        self.color_intrinsics = color_profile.get_intrinsics()
        
        # 配置对齐器
        self.align = rs.align(rs.stream.color)
        
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
    
    def cam2base(self, cam_x, cam_y, cam_z, robot_position, robot_quaternion):
        """相机坐标系到基座坐标系的转换"""
        if robot_position is None or robot_quaternion is None:
            raise ValueError("机器人位置和姿态未设置")
        
        # 相机坐标系下的点
        cam_point = np.array([cam_x, cam_y, cam_z])
        
        # 使用外部标定矩阵转换到机器人基座坐标系
        cam_point_homogeneous = np.append(cam_point, 1.0)
        base_point_homogeneous = self.extrinsics_matrix @ cam_point_homogeneous
        base_point = base_point_homogeneous[:3]
        
        # 获取机器人旋转矩阵
        R_robot = self.quaternion_to_rotation_matrix(robot_quaternion)
        
        # 考虑机器人姿态的变换
        transformed_point = R_robot @ base_point + np.array(robot_position)
        
        return transformed_point
    
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
                            
                            # 保存检测结果
                            detection = {
                                'class_id': int(cls),
                                'class_name': results.names[int(cls)],
                                'pixel_coords': (cx, cy),
                                'camera_coords': camera_coords,
                                'base_coords': base_coords,
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
        
        return color_image, detections
    
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
    
    initial_position = [0.1096244807434647, -0.0005740185108923657, 0.29688057655132444]  # 机器人位置 (x, y, z)
    initial_quaternion = [  -0.007666483683098752,
            0.39861216852740355,
            0.00030740498063957036,
            0.9170874928991211,]  # 机器人姿态四元数 (qx, qy, qz, qw)
    
    detector.set_robot_pose(initial_position, initial_quaternion)
    
    # 运行检测循环
    detector.run_detection_loop()