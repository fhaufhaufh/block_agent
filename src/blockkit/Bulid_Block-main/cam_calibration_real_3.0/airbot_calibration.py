import argparse
import sys
import os
import datetime
import numpy as np
import cv2
import time

import matplotlib.pyplot as plt
from scipy.spatial.transform import Rotation as R
from scipy.spatial.transform import Slerp

try:
    from airbot_py.arm import AIRBOTPlay, RobotMode ,SpeedProfile
except ImportError as e:
    print(f"ImportError: Failed to import airbot_py.arm: {e}")
    sys.exit(1)
except Exception as e:
    print(f"An unexpected error occurred during import: {e}")
    sys.exit(1)

parser = argparse.ArgumentParser(description="Airbot Calibration Tool")
parser.add_argument(
    "-t", "--type", type=str, default="hand_in_eye", choices=["hand_to_eye","hand_in_eye", "intrinsic","hand_in_eye_auto"], 
    help="Calibartion type, available calibration type: [hand_to_eye,hand_in_eye, intrinsic, hand_in_eye_auto]"
)
parser.add_argument(
    "-c", "--camera-type", type=str, default="realsense", choices=["usbcam", "realsense"], 
    help="Camera type, available camera type: [usbcam, realsense]"    
)
parser.add_argument(
    "-r", "--resolution", type=str, default="480p", choices=["480p", "720p", "1080p"], 
    help="Camera resolution, available resolution: [480p, 720p, 1080p]",
)
parser.add_argument(
    "-o", "--output-path", type=str, default="calib/", 
    help="Directory to save the generated calibration data.",
)
parser.add_argument(
    "-p", "--port", type=int, default=50051, 
    help="Robot port number.",
)
parser.add_argument(
    "-d", "--device-id", type=int, default=0, 
    help="Device ID for USB camera (default: 0).",
)

args = parser.parse_args()
space_len = 6

class ChessBoard:
    def __init__(self):
        self.rows = 10
        self.cols = 8
        self.square_size = 0.02 # m
        self.number_of_image_needed =40


class AirbotCalibration:
    def __init__(self):
        self.type = args.type
        self.camera = None
        # self.cam_intrinsic = None
        # self.cam_distortion = None
        self.cam_intrinsic  = np.array([[910.17253503, 0., 648.03673935],
                                        [0., 910.82653109, 355.56878168],
                                        [0., 0., 1.]], dtype=np.float64)

        self.cam_distortion = np.array([0.14665168, -0.47511030,
                                        -0.00384002, 0.00044003,
                                         0.45689670], dtype=np.float64)
        self.cam2end = None
        self.project_error = None
        
        self.images = []
        self.end_pose_matrixes = []
        
        if args.camera_type == "realsense":
            from airbot_realsense import RealsenseCamera
            self.camera = RealsenseCamera()
            print("here")
        elif args.camera_type == "usbcam":
            self.usb_camera_id = 0 if not hasattr(args, 'usb_camera_id') else args.usb_camera_id
            self.camera = USBCamera(device_id=self.usb_camera_id)
        else:
            raise ValueError("Unsupported sensor type")
        self.chessboard = ChessBoard()
        self.time_str = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        self.save_path = os.path.join(args.output_path, f"{self.type}_{self.camera.WIDTH}x{self.camera.HEIGHT}", self.time_str)
        os.makedirs(self.save_path, exist_ok=True)
        
    def choose_image(self, name="Image"):
        while True:
            image = self.camera.get_frame(frame_type="bgr",align=True)
            print("image shape:", image.shape)
            cv2.imshow(name, image)
            key = cv2.waitKey(1)
            if key == 27:
                return image

    def load_waypoints(self, file_path: str = None):
        """
        加载轨迹点数据
        
        Args:
            file_path: 轨迹文件路径（None则使用默认轨迹）
        """
        if file_path and os.path.exists(file_path):
            # 从文件加载轨迹
            pass  # 实现文件加载逻辑
        else:
            # 默认轨迹（原AIROBOT轨迹点）
            self.waypoints = [
[-0.3912031650543213, -0.8642328381538391, 1.4360647201538086, 1.6924163103103638, -1.8255512714385986, 1.3601510524749756],
[-0.25425344705581665, -0.8497368097305298, 1.437972068786621, 1.7011902332305908, -1.8060959577560425, 1.4505608081817627],
[0.0078202486038208, -0.8321889042854309, 1.437972068786621, 1.6546502113342285, -1.7729076147079468, 1.645494818687439],
[0.24090181291103363, -0.8321889042854309, 1.437972068786621, 1.5730143785476685, -1.7462043762207031, 1.7828259468078613],
[0.404936283826828, -0.8321889042854309, 1.437972068786621, 1.5424963235855103, -1.7492561340332031, 1.8732357025146484],
[0.8218890428543091, -1.0297932624816895, 1.5363928079605103, 1.2209124565124512, -1.8491210842132568, 2.259289026260376],
[1.0458152294158936, -1.110666036605835, 1.4814603328704834, 1.0709925889968872, -1.8459876585006714, 2.4092087745666504],
[1.0690852403640747, -1.3200961351394653, 1.5367742776870728, 1.047722578048706, -1.8494208860397339, 2.5133516788482666],
[1.1308842897415161, -1.507400631904602, 1.659609317779541, 0.9988937377929688, -1.8498023557662964, 2.564469337463379],
[-0.404936283826828, -1.0393301248550415, 1.6248950958251953, 1.594377040863037, -1.7534523010253906, -1.9594491720199585],
[-0.08068207651376724, -1.0687037706375122, 1.6241321563720703, 1.4070725440979004, -1.7824444770812988, -1.7034790515899658],
[0.020027466118335724, -1.0866330862045288, 1.6241321563720703, 1.3952468633651733, -1.7996108531951904, -1.581406831741333],
[0.17833982408046722, -1.0870145559310913, 1.6241321563720703, 1.3471808433532715, -1.8068588972091675, -1.4070725440979004],
[0.2939268946647644, -1.1190584897994995, 1.6241321563720703, 1.3315403461456299, -1.7988479137420654, -1.264782190322876],
[0.44308385252952576, -1.1549172401428223, 1.6248950958251953, 1.346036434173584, -1.7462043762207031, -1.1377508640289307],
[0.1184481605887413, -1.3738842010498047, 2.016288995742798, 1.1820019483566284, -1.7740520238876343, -1.7027161121368408],
[0.1802472025156021, -1.3738842010498047, 2.016288995742798, 1.1686503887176514, -1.7656595706939697, -1.6168841123580933],
[0.2817196846008301, -1.3738842010498047, 2.016288995742798, 1.183146357536316, -1.840755262374878, -1.5333409309387207],
[0.4552910625934601, -1.3075073957443237, 2.016288995742798, 1.339932918548584, -1.8175402879714966, -1.2430380582809448],
[0.3580147922039032, -1.3078888654708862, 2.016288995742798, 1.3281071186065674, -1.8460959577560425, -1.3891432285308838],
[-0.6155108213424683, -0.23594263195991516, 1.3181887865066528, 1.957541823387146, -1.8417913722991943, -0.6845578551292419],
[-0.6101701259613037, -0.41256579756736755, 1.5859845876693726, 1.8636988401412964, -1.8414099025726318, -0.6815060377120972],
[-0.404936283826828, -1.1476691961288452, 1.745059847831726, 1.5413519144058228, -1.8491210842132568, -1.4673457145690918],
[-0.17910276353359222, -1.1408026218414307, 1.7500190734863281, 1.6020065546035767, -1.7793927192687988, -2.193293571472168],
[0.06923781335353851, -1.1408026218414307, 1.7500190734863281, 1.4368276596069336, -1.728274941444397, -2.382887125015259],
[1.0763332843780518, -1.2205309867858887, 1.5409704446792603, 0.8611810207366943, -1.84724036693573, -1.4150835275650024],
[1.0763332843780518, -1.2903410196304321, 1.5409704446792603, 0.8615625500679016, -1.8402654933929443, -1.6355763673782349],
[1.0767147541046143, -1.3662546873092651, 1.5421148538589478, 0.7623788714408875, -1.8255512714385986, -1.646257758140564],
[1.0786221027374268, -1.4475089311599731, 1.5421148538589478, 0.6578545570373535, -1.8255512714385986, -1.647020697593689],
[-0.1989395022392273, -0.2637903392314911, 1.5989547967910767, 1.7286564111709595, -1.8411101007461548, -1.0942625999450684],
[-0.15468832850456238, -1.182383418083191, 1.9979782104492188, 1.6737239360809326, -1.8251698017120361, -2.0098040103912354],
[0.13752193748950958, -1.120965838432312, 1.7755779027938843, 1.2525749206542969, -1.799229383468628, -1.9048981666564941],
[0.13752193748950958, -1.1232547760009766, 1.7755779027938843, 1.1633096933364868, -1.6969939470291138, -1.6233692169189453],
[-0.07038223743438721, -1.429198145866394, 1.8488212823867798, 1.5157930850982666, -1.84724036693573, -0.9462500810623169],
[0.2817196846008301, -1.4288166761398315, 1.8488212823867798, 1.2876707315444946, -1.7549782991409302, -2.0670251846313477],
[0.2817196846008301, -1.5318150520324707, 1.8480583429336548, 1.332684874534607, -1.8255512714385986, -1.9113832712173462],
[0.2817196846008301, -1.6924163103103638, 1.8492027521133423, 1.1972609758377075, -1.8468588972091675, -1.3586251735687256],
[-0.012779430486261845, -1.4803158044815063, 2.016288995742798, 1.4639123678207397, -1.8410284328460693, -0.9557870030403137],
[-0.011635004542768002, -1.2926298379898071, 2.012474298477173, 1.3323034048080444, -1.8453062677383423, -1.4707789421081543]
    ]

    def interpolate_points(self, points, num_interp):
        """
        在给定的关节角度之间进行线性插值。

        Args:
            points (list): 原始关节角度列表，每个元素是一个6维关节角度列表。
            num_interp (int): 每个相邻点对之间要插入的点的个数。

        Returns:
            list: 包含原始点和插值点的新关节角度列表。
        """
        new_points = []
        for i in range(len(points) - 1):
            # 获取相邻两个关节角度
            joint1 = np.array(points[i])
            joint2 = np.array(points[i + 1])
            
            # 生成插值点的时间参数
            t_values = np.linspace(0, 1, num_interp + 2)[1:-1]
            
            # 对6个关节角度进行线性插值
            for t in t_values:
                interp_joint = (1 - t) * joint1 + t * joint2
                new_points.append(interp_joint.tolist())
                
            new_points.append(points[i])
        
        new_points.append(points[-1])
        return new_points
    
    def auto_choose_image(self, name="Image"):
        cv2.namedWindow(name, cv2.WINDOW_AUTOSIZE)
        image = self.camera.get_frame(frame_type="bgr", align=True)
        print("image shape:", image.shape)
        cv2.imshow(name, image)
        return image
    

    def data_collect(self):
        with AIRBOTPlay(port=args.port) as robot:
            robot.switch_mode(RobotMode.GRAVITY_COMP)
        for i in range(self.chessboard.number_of_image_needed):
            image = self.choose_image(f"Collect data{i}")
            self.images.append(image)
            image_name = os.path.join(self.save_path, f"image{i}.png")
            cv2.imwrite(image_name, image)
            if self.type == "hand_in_eye" or self.type == "hand_to_eye":
                pose_matrix = None
                with AIRBOTPlay(port=args.port) as robot:
                    pose = robot.get_end_pose()
                    q=robot.get_joint_pos()
                    print(f"{q},")
                    # print(f"Pose: {pose}")
                    pose_matrix = np.eye(4) 
                    pose_matrix[:3, :3] = R.from_quat(pose[1]).as_matrix()
                    pose_matrix[:3, 3] = pose[0]
                    # 将位姿矩阵转换为位置+四元数格式
                    position = pose_matrix[:3, 3]
                    quaternion = R.from_matrix(pose_matrix[:3, :3]).as_quat()
                self.end_pose_matrixes.append(pose_matrix)
                # print(f"--Data{i} Saved--\n  Image: {image_name}")
                # print(f"[[{position[0]:.6f}, {position[1]:.6f}, {position[2]:.6f}],"
                    #   f"[{quaternion[0]:.6f}, {quaternion[1]:.6f}, {quaternion[2]:.6f}, {quaternion[3]:.6f}]],")
            elif self.type == "intrinsic":
                print(f"--Data{i} Saved--\n  Image: {image_name}")
            else:
                raise ValueError("Unsupported calibration type")

            cv2.destroyAllWindows()

    def auto_data_collect(self):
        self.load_waypoints()
        #线性插值更密集的点
        # self.waypoints = self.interpolate_points(self.waypoints, 5)
        
        with AIRBOTPlay(port=args.port) as robot:
            robot.switch_mode(RobotMode.PLANNING_POS)
            robot.set_speed_profile(SpeedProfile.SLOW)
            robot.move_to_cart_pose([[0.227385, 0.000541, 0.278720],[-0.010554, 0.479376, -0.006724, 0.877520]])   
        for i , point in enumerate(self.waypoints):
            print(f"Moving to the {i+1} point")
            with AIRBOTPlay(port=args.port) as robot:
                print(point)
                robot.move_to_joint_pos(point)
                # robot.move_to_cart_pose(point)
                time.sleep(1)
                image = self.auto_choose_image(f"Auot Collect data {i+1}/{self.chessboard.number_of_image_needed}")
                self.images.append(image)
                image_name = os.path.join(self.save_path, f"image{i}.png")
                cv2.imwrite(image_name, image)
                if self.type == "hand_in_eye_auto":
                    pose_matrix = None
                    pose = robot.get_end_pose()
                    pose_matrix = np.eye(4)
                    pose_matrix[:3, :3] = R.from_quat(pose[1]).as_matrix()
                    pose_matrix[:3, 3] = pose[0]
                    self.end_pose_matrixes.append(pose_matrix)
                    print(f"--Data{i} Saved--")
                elif self.type == "intrinsic":
                    print(f"--Data{i} Saved--")
                else:
                    raise ValueError("Unsupported calibration type")

            cv2.destroyAllWindows()
    
    def plot_calibration_result(self, project_errors, image_points, object_points, rvecs, tvecs, mtx, dist):
        plt.figure(figsize=(15,5))
        # 每张图像误差曲线
        plt.subplot(131)
        plt.plot(project_errors, 'b-')
        plt.xlabel('Image Index'), plt.ylabel('Error (pixels)')
        plt.title('Per-image Reprojection Error')
        plt.grid(True)
        # 误差直方图
        plt.subplot(132)
        all_errors = np.sqrt(np.sum((np.array(image_points)-np.array([cv2.projectPoints(o, r, t, mtx, dist)[0] 
                                for o,r,t in zip(object_points, rvecs, tvecs)]))**2, axis=2))
        plt.hist(all_errors.ravel(), bins=50, color='g')
        plt.xlabel('Error (pixels)'), plt.ylabel('Count')
        plt.title('Error Histogram')
        plt.grid(True)
        # 误差分布箱线图
        plt.subplot(133)
        plt.boxplot(all_errors.ravel(), showfliers=False)
        plt.ylabel('Error (pixels)')
        plt.title('Error Distribution')

        plt.tight_layout()
        # 保存图表
        save_dir = os.path.join(self.save_path, "error_analysis.jpg")
        plt.savefig(save_dir, dpi=300, bbox_inches='tight')
        print(f"Error analysis plot saved to: {save_dir}\n\n")
        
    def calibrate_camera(self):
        # 3D object points of the chessboard
        object_point = np.zeros((self.chessboard.rows * self.chessboard.cols, 3), np.float32)
        object_point[:, :2] = np.mgrid[0:self.chessboard.cols, 0:self.chessboard.rows].T.reshape(-1, 2)
        object_point *= self.chessboard.square_size
        
        object_points = []
        image_points = []
        for image in self.images:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            ret, corners = cv2.findChessboardCorners(gray, (self.chessboard.cols, self.chessboard.rows), None)
            if ret:
                # optimize the corner positions
                criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
                corners2 = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)
                
                object_points.append(object_point)
                image_points.append(corners2)
                
                img_show = image.copy()
                cv2.drawChessboardCorners(img_show, (self.chessboard.cols, self.chessboard.rows), corners2, ret)
                cv2.imshow('Corners', img_show)
                cv2.waitKey(50)
            else:
                print("Chessboard pattern not found in image")
        
        cv2.destroyAllWindows()
        
        ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(object_points, image_points, (self.camera.WIDTH, self.camera.HEIGHT), None, None)
        
        self.cam_intrinsic = mtx
        self.cam_distortion = dist
        print("cam_intrinsic:")
        print("  python type  :", type(self.cam_intrinsic))   # 应为 <class 'numpy.ndarray'>
        print("  shape        :", self.cam_intrinsic.shape)  # (3, 3)
        print("  dtype        :", self.cam_intrinsic.dtype)  # float64

        print("cam_distortion:")
        print("  python type  :", type(self.cam_distortion)) # <class 'numpy.ndarray'>
        print("  shape        :", self.cam_distortion.shape) # (5, 1) 或 (1, 5) 或 (5,)
        print("  dtype        :", self.cam_distortion.dtype) # float64
        
        project_errors = []
        for i in range(len(object_points)):
            imgpoints2, _ = cv2.projectPoints(object_points[i], rvecs[i], tvecs[i], mtx, dist)
            error = cv2.norm(image_points[i], imgpoints2, cv2.NORM_L2)/len(imgpoints2)
            project_errors.append(error)
        self.project_error = np.mean(np.array(project_errors))
        
        self.plot_calibration_result(project_errors, image_points, object_points, rvecs, tvecs, mtx, dist)
        
        
    def calibrate_hand_in_eye(self, intrinsic, distortion):
        # 3D object points of the chessboard
        object_point = np.zeros((self.chessboard.rows * self.chessboard.cols, 3), np.float32)
        object_point[:, :2] = np.mgrid[0:self.chessboard.cols, 0:self.chessboard.rows].T.reshape(-1, 2)
        object_point *= self.chessboard.square_size
        
        R_checkerboard_to_camera_poses = []
        T_checkerboard_to_camera_poses = []
        R_end_to_base_poses = []
        T_end_to_base_poses = []
        
        for i in range(len(self.images)):
            gray = cv2.cvtColor(self.images[i], cv2.COLOR_BGR2GRAY)
            ret, corners = cv2.findChessboardCorners(gray, (self.chessboard.cols, self.chessboard.rows), None)
            if not ret:
                print("Chessboard pattern not found in image")
                continue
            else:
                criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
                corners2 = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)
                ret, rvec, tvec = cv2.solvePnP(object_point, corners2, intrinsic, distortion)
                R_cam_pose, _ = cv2.Rodrigues(rvec)
                R_checkerboard_to_camera_poses.append(R_cam_pose)
                T_checkerboard_to_camera_poses.append(tvec.flatten())
                # print(f"T_checkerboard_to_camera_poses: {T_checkerboard_to_camera_poses}")
                
                R_end_to_base_poses.append(self.end_pose_matrixes[i][:3, :3])
                T_end_to_base_poses.append(self.end_pose_matrixes[i][:3, 3])
                # print(f"T_end_to_base_poses: {T_end_to_base_poses}")

                print("111")
            
        R_cam2end, T_cam2end = cv2.calibrateHandEye(
            R_end_to_base_poses, T_end_to_base_poses, 
            R_checkerboard_to_camera_poses, T_checkerboard_to_camera_poses,
            method=cv2.CALIB_HAND_EYE_TSAI
        )
        
        self.cam2end = np.eye(4)
        self.cam2end[:3, :3] = R_cam2end
        self.cam2end[:3, 3] = T_cam2end.flatten()
        
        return self.cam2end
    
    def calibrate_hand_to_eye(self, intrinsic, distortion):
        """
        Calibrate eye-to-hand transformation using the calibration data
        Args:
            intrinsic: Camera intrinsic matrix
            distortion: Camera distortion coefficients
        Returns:
            cam2base: The transformation from camera to robot base
        """
        # 3D object points of the chessboard
        object_point = np.zeros((self.chessboard.rows * self.chessboard.cols, 3), np.float32)
        object_point[:, :2] = np.mgrid[0:self.chessboard.cols, 0:self.chessboard.rows].T.reshape(-1, 2)
        object_point *= self.chessboard.square_size
        
        R_checkerboard2cam_list = []  # 标定板到相机的旋转矩阵列表
        t_checkerboard2cam_list = []  # 标定板到相机的平移向量列表
        R_end2base_list = []         # 末端到基座的旋转矩阵列表  
        t_end2base_list = []         # 末端到基座的平移向量列表

        # 处理每组图像和位姿数据
        for i in range(len(self.images)):
            gray = cv2.cvtColor(self.images[i], cv2.COLOR_BGR2GRAY)
            ret, corners = cv2.findChessboardCorners(gray, (self.chessboard.cols, self.chessboard.rows), None)
            
            if not ret:
                print(f"Failed to find chessboard corners in image {i}")
                continue
                
            # 优化角点位置
            criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
            corners2 = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)
            
            # 求解PnP获取标定板到相机的变换
            ret, rvec, tvec = cv2.solvePnP(object_point, corners2, intrinsic, distortion)
            R_checkerboard2cam, _ = cv2.Rodrigues(rvec)
            
            # 存储当前帧的变换矩阵
            R_checkerboard2cam_list.append(R_checkerboard2cam)
            t_checkerboard2cam_list.append(tvec.flatten())
            
            # 从末端位姿矩阵中提取旋转和平移
            R_end2base_list.append(self.end_pose_matrixes[i][:3, :3])
            t_end2base_list.append(self.end_pose_matrixes[i][:3, 3])

        # 使用cv2.calibrateHandEye进行眼在手外标定
        # 注意:对于眼在手外标定,我们需要将末端到基座的变换作为第一组参数
        R_cam2base, t_cam2base = cv2.calibrateHandEye(
            R_end2base_list, t_end2base_list,
            R_checkerboard2cam_list, t_checkerboard2cam_list,
            method=cv2.CALIB_HAND_EYE_TSAI
        )
        
        # 构建相机到基座的4x4变换矩阵
        cam2base = np.eye(4)
        cam2base[:3, :3] = R_cam2base
        cam2base[:3, 3] = t_cam2base.flatten()
        
        self.cam2base = cam2base
        
        # 计算重投影误差
        total_error = 0
        point_count = 0
        
        for i in range(len(R_checkerboard2cam_list)):
            # 计算通过标定得到的相机位置重投影的角点
            projected_points, _ = cv2.projectPoints(
                object_point,
                cv2.Rodrigues(R_checkerboard2cam_list[i])[0],
                t_checkerboard2cam_list[i],
                intrinsic,
                distortion
            )
            
            # 计算与实际检测到的角点的误差
            error = cv2.norm(corners2, projected_points, cv2.NORM_L2)
            total_error += error
            point_count += len(object_point)
        
        avg_error = total_error/point_count if point_count > 0 else float('inf')
        print(f"Average reprojection error: {avg_error} pixels")
        
        return cam2base
    
    def report_calibration(self):
        reporter_head = f"""---Calibration Report---
Camera Type: {args.camera_type}
Resolution: {self.camera.WIDTH}x{self.camera.HEIGHT}
Chessboard: {self.chessboard.rows}x{self.chessboard.cols}-{self.chessboard.square_size}m
Project Error: {self.project_error}
"""
        print(reporter_head)
        print("--Intrinsic--")
        MatrixPrinter.print_matrix(self.cam_intrinsic)
        print("\n--Distortion--")
        MatrixPrinter.print_matrix(self.cam_distortion)
        # MatrixPrinter.print_matrix(self.cam_distortion.reshape(-1, 1))
        if args.type == "hand_in_eye" or args.type == "hand_in_eye_auto":
            print("\n--Hand-in-eye--extrinsic--")
            MatrixPrinter.print_matrix(self.cam2end)
        elif args.type == "hand_to_eye":
            print("\n--Hand-to-eye--extrinsic--")
            MatrixPrinter.print_matrix(self.cam2base)    
        print("\n--Calibration Report Saved--")
        
        file_name = os.path.join(self.save_path, "Calibration_Report.txt")

        with open(file_name, "w") as f:
            f.write(reporter_head)
        MatrixPrinter.save_matrix(self.cam_intrinsic, "Intrinsic", file_name)
        MatrixPrinter.save_matrix(self.cam_distortion, "Distortion", file_name)

        if args.type == "hand_in_eye" or args.type == "hand_in_eye_auto":
            MatrixPrinter.save_matrix(self.cam2end, "Hand-in-eye-extrinsic", file_name)
        elif args.type == "hand_to_eye":
            MatrixPrinter.save_matrix(self.cam2base, "Hand-to-eye-extrinsic", file_name)
                   
class MatrixPrinter:
    """Utilities for formatted printing of matrices"""
    
    @staticmethod
    def format_number(v: float) -> str:
        """Format a number for display with consistent spacing"""
        if abs(v - 0) < 1e-12:
            return "0.        "
        elif abs(v - 1) < 1e-12:
            return "1.        "
        else:
            return f"{v:.8f}"
    
    @staticmethod
    def print_matrix(matrix: np.ndarray) -> None:
        """Print a matrix in two different formats for readability"""
        if not isinstance(matrix, np.ndarray):
            raise TypeError("Input must be a numpy ndarray.")

        # Format all values
        str_matrix = [[MatrixPrinter.format_number(val) for val in row] for row in matrix]
        
        # Calculate max width per column for alignment
        col_widths = [max(len(row[i]) for row in str_matrix) for i in range(matrix.shape[1])]

        # Create formatted row strings
        def format_row(row):
            return ", ".join(f"{val:>{col_widths[i]}}" for i, val in enumerate(row))

        print("\nlist format:")
        if matrix.shape[0] == 1:
            print(f"[{format_row(str_matrix[0])}]")
        else:
            print("[")
            for i, row in enumerate(str_matrix):
                comma = "," if i < len(str_matrix) - 1 else ""
                print(f" [{format_row(row)}]{comma}")
            print("]")

        print("\nyaml format:")
        for row in str_matrix:
            print(" " * space_len + f"- [{format_row(row)}]")
    
    def save_matrix(matrix: np.ndarray, segment_name, file_path: str) -> None:
        with open(file_path, "a") as f:
            """Print a matrix in two different formats for readability"""
            if not isinstance(matrix, np.ndarray):
                raise TypeError("Input must be a numpy ndarray.")

            # Format all values
            str_matrix = [[MatrixPrinter.format_number(val) for val in row] for row in matrix]
            
            # Calculate max width per column for alignment
            col_widths = [max(len(row[i]) for row in str_matrix) for i in range(matrix.shape[1])]

            # Create formatted row strings
            def format_row(row):
                return ", ".join(f"{val:>{col_widths[i]}}" for i, val in enumerate(row))

            f.write(f"\n--{segment_name}--\n")
            f.write("list format:\n")
            if matrix.shape[0] == 1:
                f.write(f"[{format_row(str_matrix[0])}]\n")
            else:
                f.write("[\n")
                for i, row in enumerate(str_matrix):
                    comma = "," if i < len(str_matrix) - 1 else ""
                    f.write(f" [{format_row(row)}]{comma}\n")
                f.write("]\n")

            f.write("yaml format:\n")
            for row in str_matrix:
                f.write(f"    - [{format_row(row)}]\n")

class USBCamera:
    WIDTH = 640
    HEIGHT = 480

    def __init__(self, device_id=0):
        self.cap = cv2.VideoCapture(device_id)
        if not self.cap.isOpened():
            raise ValueError(f"无法打开 USB 相机 (设备号: {device_id})")

        # 设置分辨率
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.WIDTH)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.HEIGHT)

    def get_frame(self, frame_type="bgr", align=None):
        """
        模拟 Realsense 的 get_frame 接口
        :param frame_type: 支持 "bgr" 或 "rgb"
        :param align: 兼容参数（realsense 中用于对齐深度图，这里忽略）
        :return: 返回 BGR 或 RGB 图像
        """
        ret, frame = self.cap.read()
        if not ret:
            return None

        if frame_type == "rgb":
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        elif frame_type != "bgr":
            raise ValueError(f"Unsupported frame_type: {frame_type}")

        return frame

    def release(self):
        self.cap.release()

def draw_frame(T, ax=None, name='frame'):
    length=0.1
    linewidth=1.0
    if ax is None:
        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')

    origin = T[:3, 3]
    x_axis = T[:3, 0] * length
    y_axis = T[:3, 1] * length
    z_axis = T[:3, 2] * length

    ax.quiver(*origin, *x_axis, color='r', linewidth=linewidth)
    ax.quiver(*origin, *y_axis, color='g', linewidth=linewidth)
    ax.quiver(*origin, *z_axis, color='b', linewidth=linewidth)

    if origin[0] == 0 and origin[1] == 0 and origin[2] == 0:
        coord_str = f'{name} (0,0,0)'
    else:
        coord_str = f'{name} ({origin[0]:.3f},{origin[1]:.3f},{origin[2]:.3f})'
    ax.text(*origin, coord_str, fontsize=10)


    ax.set_xlim([-0.25, 0.25])
    ax.set_ylim([-0.25, 0.25])
    ax.set_zlim([-0.25, 0.25])
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')
    ax.set_box_aspect([0.5,0.5,0.5])

    return ax


if __name__ == "__main__":
    print(f"\n{'='*60}")
    print(f"Airbot Calibration Tool")
    print(f"{'='*60}")
    print(f"Calibration type: {args.type}")
    print(f"Camera type: {args.camera_type}")
    print(f"Resolution: {args.resolution}")
    print(f"Output path: {args.output_path}")
    print(f"Robot port: {args.port}")
    if args.camera_type == "usbcam":
        print(f"USB camera device ID: {args.device_id}")
    print(f"{'='*60}\n")
    try:
        calibrator = AirbotCalibration()
        if args.type == "intrinsic":
            calibrator.data_collect()
            print("Collecting data for intrinsic calibration...")
            calibrator.calibrate_camera()
        elif args.type == "hand_in_eye":
            calibrator.data_collect()
            print("Collecting data for hand-in-eye calibration...")
            calibrator.calibrate_camera()
            print("Data collection completed.")
            calibrator.calibrate_hand_in_eye(calibrator.cam_intrinsic, calibrator.cam_distortion)
        elif args.type == "hand_in_eye_auto":
            print("Collecting data for hand-in-eye auto calibration...")
            calibrator.auto_data_collect()
            print("Data collection completed.")
            # calibrator.calibrate_camera()
            print("Calibrating hand-in-eye transformation...")
            print("starting calibration ssssssssssssssssssssssssssssssssssssss")
            calibrator.calibrate_hand_in_eye(calibrator.cam_intrinsic, calibrator.cam_distortion)
        elif args.type == "hand_to_eye":
            calibrator.data_collect()
            calibrator.calibrate_camera()
            calibrator.calibrate_hand_to_eye(calibrator.cam_intrinsic, calibrator.cam_distortion)
        print("Calibration completed, generating report...")
        calibrator.report_calibration()
        ax = draw_frame(np.eye(4), name='eef')
        draw_frame(calibrator.cam2end, ax=ax, name='cam')
        ax.view_init(elev=20, azim=70)
        plt.show()
        print("Calibration completed successfully!")        
    except Exception as e:
        print(f"\nError during calibration: {e}")