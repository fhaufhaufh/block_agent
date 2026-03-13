import cv2
import numpy as np
import pyrealsense2 as rs
import time
from scipy.spatial.transform import Rotation as R
from airbot_py.arm import AIRBOTPlay, RobotMode, SpeedProfile

class HighPrecisionCalibrator:
    def __init__(self, robot_ip="192.168.1.135"):
        # ================= [高精度配置] =================
        self.marker_length = 0.10       # [重要] 标定板实际边长 (米)
        self.robot_ip = robot_ip
        
        # 自动采样参数
        self.sample_counts = 17          # 这里的数字仅作记录，实际点数由生成策略决定
        self.angle_span = 20             # 全角度范围 (度) - 建议 30 度
        self.trans_span = 0.1         # 平移范围 (米) - 建议 5 厘米
        
        # [自定义初始位置] 
        # 如果为 None，则以程序启动时机械臂的位置为准
        # 如果填入关节角列表 (弧度)，则自动移动到该位置开始
        # 示例: [0, -0.5, 1.0, 0, 1.57, 0]
        self.init_joint_pose = [0, -0.8,0.9545891523361206, -1.57, 1.339719271659851, 1.5444037914276123] 
        # ===============================================

        # --- 1. RealSense 初始化 (高分辨率模式) ---
        self.pipeline = rs.pipeline()
        config = rs.config()
        # 提升分辨率到 1280x720 以获得更高检测精度
        config.enable_stream(rs.stream.color, 1920, 1080, rs.format.bgr8, 30)
        
        print(f"正在启动 RealSense (High Res) ...")
        cfg = self.pipeline.start(config)
        time.sleep(2.0)  # 等待相机稳定
        # 获取内参
        profile = cfg.get_stream(rs.stream.color)
        intr = profile.as_video_stream_profile().get_intrinsics()
        self.camera_matrix = np.array([
            [intr.fx, 0, intr.ppx],
            [0, intr.fy, intr.ppy],
            [0, 0, 1]
        ])
        self.dist_coeffs = np.array(intr.coeffs)

        # --- 2. Aruco 初始化 (亚像素优化) ---
        # 修改为 DICT_4X4_1000 以支持 ID 555
        # 如果使用的是 "Original ArUco" (5x5)，请改为 cv2.aruco.DICT_ARUCO_ORIGINAL
        self.aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_ARUCO_ORIGINAL)
        self.aruco_params = cv2.aruco.DetectorParameters()
        # 开启亚像素角点细化
        self.aruco_params.cornerRefinementMethod = cv2.aruco.CORNER_REFINE_SUBPIX
        self.aruco_params.cornerRefinementWinSize = 5
        self.aruco_params.cornerRefinementMaxIterations = 30
        self.aruco_params.cornerRefinementMinAccuracy = 0.01

        # --- 3. AIRBOT 初始化 ---
        print(f"正在连接 AIRBOT ({self.robot_ip})...")
        self.robot = AIRBOTPlay(url="localhost", port=50000)
        if not self.robot.connect():
            raise Exception("连接失败")
        
        self.robot.switch_mode(RobotMode.PLANNING_POS)
        self.robot.set_speed_profile(SpeedProfile.DEFAULT)
        print("机械臂连接成功。")

        # 数据容器
        self.R_base_end = []
        self.t_base_end = []
        self.R_cam_marker = []
        self.t_cam_marker = []

    def get_robot_pose(self):
        """获取机械臂末端位姿 (RotationMatrix, Translation)"""
        end_pose = self.robot.get_end_pose()
        if end_pose is None: return None, None
        
        pos = np.array(end_pose[0])
        quat = end_pose[1] # [x, y, z, w]
        rot_mat = R.from_quat(quat).as_matrix()
        return rot_mat, pos

    def get_high_precision_marker_pose(self, sample_frames=30):
        """
        [高精度采集] 连续采集多帧，去除异常值后取平均
        """
        rvecs_list = []
        tvecs_list = []
        
        print(f"    正在进行高精度视觉采样 ({sample_frames}帧)...", end="", flush=True)
        for i in range(30):
            frames = self.pipeline.wait_for_frames()
            color_frame = frames.get_color_frame()
            if not color_frame: continue


        for i in range(sample_frames):
            frames = self.pipeline.wait_for_frames()
            color_frame = frames.get_color_frame()
            if not color_frame: continue
            
            image = np.asanyarray(color_frame.get_data())
            corners, ids, _ = cv2.aruco.detectMarkers(image, self.aruco_dict, parameters=self.aruco_params)
            
            if ids is not None and len(ids) > 0:
                # 姿态估计
                rvec, tvec, _ = cv2.aruco.estimatePoseSingleMarkers(
                    corners[0], self.marker_length, self.camera_matrix, self.dist_coeffs
                )
                rvecs_list.append(rvec[0][0])
                tvecs_list.append(tvec[0][0])
            
            # 简单的可视化（只显示最后一帧）
            if i == sample_frames - 1:
                if ids is not None and len(ids) > 0:
                    cv2.drawFrameAxes(image, self.camera_matrix, self.dist_coeffs, rvec, tvec, 0.03)
                cv2.imshow("High Precision View", image)
                cv2.waitKey(1)

        print(" 完成")
        
        if len(tvecs_list) < sample_frames * 0.5:
            print("    [失败] 有效帧数不足，视野不稳定")
            return None, None

        # --- 数据滤波与平均 ---
        # 1. 转换为 numpy 数组
        t_data = np.array(tvecs_list)
        r_data = np.array(rvecs_list)
        
        # 2. 简单的均值滤波 (也可以用中值 np.median)
        t_avg = np.mean(t_data, axis=0)
        r_vec_avg = np.mean(r_data, axis=0) # 旋转向量在小范围内平均是可行的
        
        # 3. 转回旋转矩阵
        rot_mat, _ = cv2.Rodrigues(r_vec_avg)
        return rot_mat, t_avg

    def generate_spherical_waypoints(self, center_pose):
        """
        生成 17 个采样点 (参考 ROS easy_handeye 策略):
        1. Roll/Pitch/Yaw 全角度旋转 (6个)
        2. Roll/Pitch/Yaw 半角度旋转 (6个)
        3. X/Y 正负平移, Z 上升 (5个)
        注意：每次只动一个轴
        """
        center_pos = np.array(center_pose[0])
        center_quat = center_pose[1]
        center_rot = R.from_quat(center_quat)
        
        waypoints = [center_pose] # 包含原点 (第0个)

        # 参数
        angle_full = self.angle_span
        angle_half = self.angle_span / 2.0
        trans_step = self.trans_span

        # --- 1. 旋转采样 (12个) ---
        # 旋转是在当前末端坐标系下进行的 (Intrinsic rotation), 保持位置不变
        # 顺序: X(Roll), Y(Pitch), Z(Yaw)
        
        # 定义旋转轴
        axes = {
            'x': [1, 0, 0],
            'y': [0, 1, 0],
            'z': [0, 0, 1]
        }
        
        # 生成旋转点函数
        def add_rot_points(angle):
            for axis_name in ['x', 'y', 'z']:
                axis = axes[axis_name]
                # 正向
                delta_rot_p = R.from_rotvec(np.array(axis) * np.radians(angle))
                new_rot_p = center_rot * delta_rot_p
                waypoints.append([center_pos.tolist(), new_rot_p.as_quat().tolist()])
                
                # 负向
                delta_rot_n = R.from_rotvec(np.array(axis) * np.radians(-angle))
                new_rot_n = center_rot * delta_rot_n
                waypoints.append([center_pos.tolist(), new_rot_n.as_quat().tolist()])

        # 添加全角度 (6个)
        add_rot_points(angle_full)
        
        # 添加半角度 (6个)
        add_rot_points(angle_half)

        # --- 2. 平移采样 (5个) ---
        # 平移是在基座坐标系下进行的 (Base frame translation), 保持姿态不变
        # X正负, Y正负, Z上升
        
        # X+
        pos_x_p = center_pos + np.array([trans_step/2, 0, 0])
        waypoints.append([pos_x_p.tolist(), center_quat])
        
        # X-
        pos_x_n = center_pos + np.array([-trans_step/2, 0, 0])
        waypoints.append([pos_x_n.tolist(), center_quat])
        
        # Y+
        pos_y_p = center_pos + np.array([0, trans_step, 0])
        waypoints.append([pos_y_p.tolist(), center_quat])
        
        # Y-
        pos_y_n = center_pos + np.array([0, -trans_step, 0])
        waypoints.append([pos_y_n.tolist(), center_quat])
        
        # Z+ (上升)
        pos_z_p = center_pos + np.array([0, 0, trans_step/3])
        waypoints.append([pos_z_p.tolist(), center_quat])

        return waypoints

    def run(self):
        print("\n================ 高精度自动标定 ================")
        
        # 1. 移动到初始位置
        if self.init_joint_pose is not None:
            print(f"移动到自定义初始关节角: {self.init_joint_pose}")
            self.robot.move_to_joint_pos(self.init_joint_pose, blocking=True)
            time.sleep(1.0)
        else:
            print("使用当前机械臂位置作为初始中心点。")

        start_pose = self.robot.get_end_pose()
        if not start_pose:
            print("无法获取机械臂状态！")
            return
        # 2. 生成轨迹
        targets = self.generate_spherical_waypoints(start_pose)
        print(f"计划采集 {len(targets)} 个高精度样本...")

        # 3. 执行
        valid_samples = 0
        for i, target in enumerate(targets):
            print(f"--> 点位 {i+1}/{len(targets)}")
            
            # 移动
            if not self.robot.move_to_cart_pose(target, blocking=True):
                print("    运动不可达，跳过")
                continue
            
            # 必须等待机械臂完全静止，避免残余抖动影响精度
            time.sleep(3.0) 
            
            # 采集
            R_rob, t_rob = self.get_robot_pose()
            R_cam, t_cam = self.get_high_precision_marker_pose(sample_frames=60) # 采集45帧取平均
            
            if R_rob is not None and R_cam is not None:
                self.R_base_end.append(R_rob)
                self.t_base_end.append(t_rob)
                self.R_cam_marker.append(R_cam)
                self.t_cam_marker.append(t_cam)
                valid_samples += 1
                print(f"    [成功] 累计有效样本: {valid_samples}")
            else:
                print("    [丢弃] 视觉识别失败")

        # 4. 复位
        self.robot.move_to_cart_pose(start_pose, blocking=True)

        # 5. 计算
        if valid_samples >= 5:
            self.compute_calibration()
        else:
            print("有效样本不足，无法计算。")

    def compute_calibration(self):
        print("\n正在使用 Daniilidis 算法进行高精度求解...")
        
        # 使用 Daniilidis 算法，通常比 Tsai 更鲁棒
        # 注意: Daniilidis 求解结果有时会有多解或符号问题，OpenCV 内部已处理，
        # 但如果结果异常，可以回退到 cv2.CALIB_HAND_EYE_TSAI
        try:
            R_cam2end, t_cam2end = cv2.calibrateHandEye(
                self.R_base_end, self.t_base_end,
                self.R_cam_marker, self.t_cam_marker,
                method=cv2.CALIB_HAND_EYE_DANIILIDIS
            )
        except cv2.error:
            print("Daniilidis 求解失败，回退到 Tsai 算法...")
            R_cam2end, t_cam2end = cv2.calibrateHandEye(
                self.R_base_end, self.t_base_end,
                self.R_cam_marker, self.t_cam_marker,
                method=cv2.CALIB_HAND_EYE_TSAI
            )

        print("\n========== [高精度标定结果] Eye-in-Hand ==========")
        print(f"平移向量 (x, y, z) [米]:\n {t_cam2end.ravel()}")
        print(f"旋转矩阵:\n{R_cam2end}")
        
        quat = R.from_matrix(R_cam2end).as_quat()
        print(f"四元数 [x, y, z, w]: {quat}")
        print("==================================================")

    def close(self):
        self.pipeline.stop()

if __name__ == "__main__":
    calib = HighPrecisionCalibrator(robot_ip="192.168.1.135")
    
    # [设置] 如果您想指定初始位置，请取消下面的注释并填入关节角
    # calib.init_joint_pose = [0.0, -0.5, 1.0, 0.0, 1.57, 0.0] 
    
    try:
        calib.run()
    finally:
        calib.close()