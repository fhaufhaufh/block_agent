import pyrealsense2 as rs
import cv2
import numpy as np
from ultralytics import YOLO
import time
import yaml
import math
from airbot_py.arm import AIRBOTPlay, RobotMode, SpeedProfile
from collections import deque

def nothing(x):
    """ Trackbar callback, does nothing """
    pass

def calculate_angle_pca(roi_img, hsv_min, hsv_max):
    """
    Calculate angle using PCA on ROI image with HSV thresholding.
    """
    if roi_img is None or roi_img.size == 0:
        return 0, False, None

    # 1. Preprocessing (HSV)
    hsv = cv2.cvtColor(roi_img, cv2.COLOR_BGR2HSV)
    thresh = cv2.inRange(hsv, hsv_min, hsv_max)

    # Morphological operations (Denoising)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=1)
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel, iterations=1)

    # 2. Find Contours
    contours, _ = cv2.findContours(thresh, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
    if not contours:
        return 0, False, thresh

    # Find the largest suitable contour
    target_cnt = max(contours, key=cv2.contourArea)
    
    # Area filtering
    area = cv2.contourArea(target_cnt)
    h, w = roi_img.shape[:2]
    img_area = h * w
    
    if area < 50 or area > (img_area * 0.95):
        return 0, False, thresh

    # 3. PCA Calculation
    pts = target_cnt.reshape(-1, 2).astype(np.float64)
    mean, eigenvectors = cv2.PCACompute(pts, mean=None)
    
    # Principal axis direction (Eigenvector 0)
    vx, vy = eigenvectors[0, 0], eigenvectors[0, 1]
    
    # Centroid
    cx, cy = mean[0, 0], mean[0, 1]
    
    # --- 4. Eliminate 180-degree ambiguity (Direction Correction) ---
    nx, ny = -vy, vx
    
    # Project all contour points onto the normal vector n
    pts_cnt = target_cnt.reshape(-1, 2)
    projections = (pts_cnt[:, 0] - cx) * nx + (pts_cnt[:, 1] - cy) * ny
    
    # Count pixels on positive and negative sides
    count_pos = np.sum(projections > 0)
    count_neg = np.sum(projections <= 0)
    
    if count_pos < count_neg:
        # Flip principal axis direction
        vx, vy = -vx, -vy
        
    # --- 5. Zero Point Calibration (Coordinate Transformation) ---
    angle_rad = np.arctan2(vy, vx)
    angle_deg = np.degrees(angle_rad)
    
    final_angle = (-angle_deg - 90) % 360
    
    return final_angle, True, thresh

class AngleSmoother:
    """ Angle Smoother using circular mean """
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
        # Load configuration
        self.config_path = config_path
        self.load_config()
        
        # Initialize Model
        self.model = YOLO(self.model_path)

        # Initialize Camera
        self.pipeline = rs.pipeline()
        self.config = rs.config()
        
        self.setup_camera()
        self.start_camera()
        
        # Coordinate transformation parameters
        self.extrinsics_matrix = np.array(self.camera_extrinsics['matrix'])
        # Initialize Robot
        self.robot = AIRBOTPlay(url="localhost", port=50000)
        if not self.robot.connect():
            raise Exception("Connection failed")
        self.robot.switch_mode(RobotMode.PLANNING_POS)
        self.robot.set_speed_profile(SpeedProfile.DEFAULT)
        print("Robot arm connected successfully.")
        # Robot pose parameters
        self.robot_position = None
        self.robot_quaternion = None
        self.smoother = AngleSmoother(window_size=5)
        
        # HSV Thresholds (for Block 3) - Adjust as needed
        self.block3_hsv_min = np.array([0, 0, 0])
        self.block3_hsv_max = np.array([30, 255, 55])
        
        print("Detection system initialized")
    
    def load_config(self):
        """Load configuration file"""
        with open(self.config_path, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)
        
        # Basic parameters
        self.conf_threshold = config_data['detection']['confidence_threshold']
        self.model_path = config_data['detection']['model_path']
        self.window_name = config_data['display']['window_name']
        
        # Camera parameters
        self.camera_extrinsics = config_data['camera_extrinsics']
        self.color_stream = config_data['camera_streams']['color']
        self.depth_stream = config_data['camera_streams']['depth']
        
        # Depth processing parameters
        self.depth_kernel_size = config_data['depth_processing']['kernel_size']
        
        print(f"Loaded config: {self.config_path}")
        print(f"Confidence threshold: {self.conf_threshold}")
        print(f"Model path: {self.model_path}")
    
    def setup_camera(self):
        """Configure camera streams"""
        self.config.enable_stream(
            rs.stream.color,
            self.color_stream['width'],
            self.color_stream['height'],
            getattr(rs.format, self.color_stream['format']),
            self.color_stream['fps']
        )
        
        self.config.enable_stream(
            rs.stream.depth,
            self.depth_stream['width'],
            self.depth_stream['height'],
            getattr(rs.format, self.depth_stream['format']),
            self.depth_stream['fps']
        )
    
    def start_camera(self):
        """Start camera"""
        self.profile = self.pipeline.start(self.config)
        
        # Get depth sensor parameters
        depth_sensor = self.profile.get_device().first_depth_sensor()
        self.depth_scale = depth_sensor.get_depth_scale()
        
        # Set High Accuracy mode
        if depth_sensor.supports(rs.option.visual_preset):
            print("Setting camera to High Accuracy mode")
            depth_sensor.set_option(rs.option.visual_preset, 3)
        
        # Get camera intrinsics
        color_profile = rs.video_stream_profile(self.profile.get_stream(rs.stream.color))
        self.color_intrinsics = color_profile.get_intrinsics()
        
        # Configure aligner (Depth -> Color)
        self.align = rs.align(rs.stream.color)
        # Skip first few frames
        for _ in range(40):
            frames = self.pipeline.wait_for_frames()
            aligned_frames = self.align.process(frames)
        print("Camera started successfully")
    
    def get_frames(self):
        """Get aligned frames"""
        try:
            frames = self.pipeline.wait_for_frames()
            aligned_frames = self.align.process(frames)
            return aligned_frames.get_color_frame(), aligned_frames.get_depth_frame()
        except Exception as e:
            print(f"Failed to get frames: {e}")
            return None, None
    
    def set_robot_pose(self, position, quaternion):
        """Set current robot position and quaternion"""
        self.robot_position = position  # [x, y, z]
        self.robot_quaternion = quaternion  # [qx, qy, qz, qw]
        print(f"Robot position set: {position}")
        print(f"Robot quaternion set: {quaternion}")
    
    def obb_angle_to_standard(self, angle_degrees, w, h):
        """Convert OBB angle to standard angle"""
        if w > h:
            standard_angle = angle_degrees + 90
        else:
            standard_angle = angle_degrees + 180
        return standard_angle % 180
    
    def get_average_depth_center(self, depth_frames, cx, cy, w, h):
        """Get depth at center with multi-frame fusion"""
        if not isinstance(depth_frames, list):
            depth_frames = [depth_frames]

        valid_depths = []
        cx_int, cy_int = int(cx), int(cy)

        for d_frame in depth_frames:
            depth_image = np.asanyarray(d_frame.get_data())
            img_h, img_w = depth_image.shape
            
            val = 0.0
            # 1. Try center point
            if 0 <= cx_int < img_w and 0 <= cy_int < img_h:
                center_depth = depth_image[cy_int, cx_int]
                if center_depth > 0:
                    val = center_depth * self.depth_scale

            # 2. If center invalid, use median of surrounding region
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
            
        # 3. Average of valid depths
        return np.mean(valid_depths)
    
    def pixel2cam(self, pixel_x, pixel_y, depth):
        """Convert pixel coordinates to camera coordinates"""
        x_norm = (pixel_x - self.color_intrinsics.ppx) / self.color_intrinsics.fx
        y_norm = (pixel_y - self.color_intrinsics.ppy) / self.color_intrinsics.fy
        
        X = depth * x_norm
        Y = depth * y_norm
        Z = depth
        
        return np.array([X, Y, Z])
    
    def quaternion_to_rotation_matrix(self, q):
        """Convert quaternion to rotation matrix"""
        qx, qy, qz, qw = q
        R = np.array([
            [1 - 2*qy*qy - 2*qz*qz, 2*qx*qy - 2*qz*qw, 2*qx*qz + 2*qy*qw],
            [2*qx*qy + 2*qz*qw, 1 - 2*qx*qx - 2*qz*qz, 2*qy*qz - 2*qx*qw],
            [2*qx*qz - 2*qy*qw, 2*qy*qz + 2*qx*qw, 1 - 2*qx*qx - 2*qy*qy]
        ])
        return R
    
    def euler_to_quaternion(self, roll, pitch, yaw):
        """Convert Euler angles (degrees) to quaternion [qx, qy, qz, qw] (Z-Y-X)"""
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
        """Camera frame to Base frame conversion (Eye-in-Hand)"""
        if robot_position is None or robot_quaternion is None:
            raise ValueError("Robot position and quaternion not set")
        
        # 1. Camera Frame -> End Effector Frame
        cam_point = np.array([cam_x, cam_y, cam_z, 1.0])
        end_point_homogeneous = self.extrinsics_matrix @ cam_point
        end_point = end_point_homogeneous[:3]
        
        # 2. End Effector Frame -> Base Frame
        R_base_end = self.quaternion_to_rotation_matrix(robot_quaternion)
        t_base_end = np.array(robot_position)
        
        base_point = R_base_end @ end_point + t_base_end
        
        return base_point

    def calculate_grasp_quaternion(self, image_angle, robot_quaternion, class_id=None):
        """Calculate grasp quaternion in base frame"""
        angle_rad = np.radians(image_angle)
        v_cam = np.array([np.cos(angle_rad), np.sin(angle_rad), 0])

        R_end_cam = self.extrinsics_matrix[:3, :3]
        v_end = R_end_cam @ v_cam

        R_base_end = self.quaternion_to_rotation_matrix(robot_quaternion)
        v_base = R_base_end @ v_end

        yaw_base = np.arctan2(v_base[1], v_base[0])
        final_yaw = np.degrees(yaw_base) + 90
        
        # Limit angle for symmetric gripper (except for Block 3)
        if class_id != 2:
            while final_yaw > 90:
                final_yaw -= 180
            while final_yaw < -90:
                final_yaw += 180
            
        return self.euler_to_quaternion(0, 90, final_yaw)

    def draw_detection(self, image, detection):
        """Draw detection results on image"""
        cx, cy = detection['pixel_coords']
        w, h = detection['size']
        angle_degrees = detection['obb_angle']
        standard_angle = detection['image_angle']
        conf = detection['confidence']
        class_name = detection['class_name']
        depth = detection['depth']
        
        rect = ((cx, cy), (w, h), angle_degrees)
        box = cv2.boxPoints(rect).astype(int)
        cv2.drawContours(image, [box], 0, (0, 255, 0), 2)
        
        cv2.circle(image, (int(cx), int(cy)), 5, (0, 0, 255), -1)
        
        arrow_length = min(w, h) / 2
        end_x = int(cx + arrow_length * np.cos(np.radians(standard_angle)))
        end_y = int(cy + arrow_length * np.sin(np.radians(standard_angle)))
        cv2.arrowedLine(image, (int(cx), int(cy)), (end_x, end_y),
                       (255, 0, 0), 3, tipLength=0.3)
        
        label = f"{class_name}: {conf:.2f}"
        cv2.putText(image, label, (int(cx-w/2), int(cy-h/2-10)),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
        
        angle_text = f"Angle: {standard_angle:.1f}"
        cv2.putText(image, angle_text, (int(cx-w/2), int(cy+h/2+20)),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
        
        depth_text = f"Depth: {depth*100:.0f}cm"
        cv2.putText(image, depth_text, (int(cx-w/2), int(cy+h/2+50)),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
    
    def process_frame_test(self, color_image, depth_frames, robot_position, robot_quaternion, use_pca=False, hsv_min=None, hsv_max=None):
        """Process single frame, detect objects and calculate 3D position"""
        results = self.model(color_image, verbose=False)[0]
        detections = []
        if hasattr(results, 'obb') and results.obb is not None:
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
                    if self.class_id == 2 and use_pca and int(cls) == 2:
                        if i != target_index:
                            continue

                    angle_degrees = np.degrees(angle_rad)
                    standard_angle = self.obb_angle_to_standard(angle_degrees, w, h)

                    # --- Special handling for class 2 (Block 3) ---
                    if self.class_id == 2 and use_pca and hsv_min is not None and int(cls) == 2:
                        img_h, img_w = color_image.shape[:2]
                        side_len = max(w, h) * 1.6
                        x1 = int(cx - side_len / 2)
                        y1 = int(cy - side_len / 2)
                        x2 = int(cx + side_len / 2)
                        y2 = int(cy + side_len / 2)
                        
                        x1 = max(0, x1); y1 = max(0, y1)
                        x2 = min(img_w, x2); y2 = min(img_h, y2)
                        
                        if (x2 - x1) > 10 and (y2 - y1) > 10:
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
                            
                            if last_thresh is not None:
                                cv2.imwrite("debug_block3_thresh.jpg", last_thresh)
                            
                            if pca_angles:
                                print(pca_angles)
                                pca_angle = np.median(pca_angles)
                                success = True
                            else:
                                success = False

                            if success:
                                standard_angle = -pca_angle
                                print(f"Class 2 (Block 3). Using PCA Angle: {standard_angle:.1f}")
                    
                    depth_value = self.get_average_depth_center(depth_frames, cx, cy, w, h)
                    
                    if depth_value > 0:
                        try:
                            camera_coords = self.pixel2cam(cx, cy, depth_value)
                            base_coords = self.cam2base(
                                camera_coords[0], camera_coords[1], camera_coords[2],
                                robot_position, robot_quaternion
                            )
                            
                            grasp_quaternion = self.calculate_grasp_quaternion(standard_angle, robot_quaternion, class_id=int(cls))
                            
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
                            self.draw_detection(color_image, detection)
                            
                        except Exception as e:
                            print(f"Error processing detection: {e}")
                            import traceback
                            traceback.print_exc()
        return color_image, detections
    
    def _capture_and_detect(self, robot_pos, robot_quat, use_pca=False, hsv_min=None, hsv_max=None):
        """Helper: Capture and detect (multi-frame depth average)"""
        depth_frames = []
        color_image = None
        
        for _ in range(5):
            colored_frame, d_frame = self.get_frames()
            if colored_frame and d_frame:
                color_image = np.array(colored_frame.get_data())
                depth_frames.append(d_frame)
            
        if color_image is None or not depth_frames:
            return None, []

        processed_image, detections = self.process_frame_test(
            color_image, depth_frames, 
            robot_pos, robot_quat,
            use_pca=use_pca, hsv_min=hsv_min, hsv_max=hsv_max
        )
        
        if detections:
            img_h, img_w = color_image.shape[:2]
            cx_img, cy_img = img_w / 2, img_h / 2
            for det in detections:
                px, py = det['pixel_coords']
                det['dist_to_center'] = (px - cx_img)**2 + (py - cy_img)**2
                
        return processed_image, detections

    def run_detection(self, class_id=0):
        print(f"\n--- Start Detection Flow (Class ID: {class_id}) ---")
        self.class_id = class_id
        # ================= Step 1: Visual Servoing Alignment =================
        align_threshold = 15 # pixel threshold
        max_align_attempts = 5
        
        for attempt in range(max_align_attempts):
            print(f"Alignment attempt {attempt + 1}/{max_align_attempts}...")
            
            current_pose = self.robot.get_end_pose()
            if current_pose is None:
                print("Cannot get robot pose")
                return
            robot_pos, robot_quat = current_pose[0], current_pose[1]

            processed_img, detections = self._capture_and_detect(robot_pos, robot_quat, use_pca=False)
            if attempt == 0:
                cv2.imwrite('detection_step1.jpg', processed_img)

            target = None
            if detections:
                valid_dets = [d for d in detections if d['class_id'] == class_id]
                if valid_dets:
                    valid_dets.sort(key=lambda x: x['dist_to_center'])
                    target = valid_dets[0]
            
            if not target:
                print(f"Target class_id={class_id} not found")
                if attempt == 0: return
                break

            dist_px = math.sqrt(target['dist_to_center'])
            print(f"Target locked (Distance to center {dist_px:.1f} px)")
            
            if dist_px < align_threshold:
                print("Target aligned!")
                break
            
            cam_offset = target['camera_coords'].copy()
            cam_offset[2] = 0 # Keep Z (depth), only align XY
            
            R_end_cam = self.extrinsics_matrix[:3, :3]
            R_base_end = self.quaternion_to_rotation_matrix(robot_quat)
            move_vec_base = R_base_end @ R_end_cam @ cam_offset
            
            align_pos = np.array(robot_pos) + move_vec_base
            
            # Smart height adjustment
            if align_pos[2] > 0.25:
                align_pos[2] = 0.2
            
            print(f"Executing visual alignment translation: {move_vec_base}")
            self.robot.move_to_cart_pose([align_pos.tolist(), robot_quat])
            time.sleep(0.8)


        # ================= Step 2: Precise Detection and Grasping =================
        current_pose = self.robot.get_end_pose()
        if current_pose is None: return
        robot_pos, robot_quat = current_pose[0], current_pose[1]

        print("2. Precise detection (Sampling 10 times)...")
        
        collected_positions = []
        collected_quaternions = []
        last_processed_img = None
        
        use_pca = (class_id == 2)
        range_time = 1
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
                print(f"  Sample {i+1}/10")

        if last_processed_img is not None:
            cv2.imwrite('detection_step2.jpg', last_processed_img)
        
        if len(collected_positions) > 0:
            print(f"Successfully collected {len(collected_positions)}/10 samples, calculating median...")
            
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
            
            quats = np.array(collected_quaternions)
            median_quat = np.median(quats, axis=0)
            norm = np.linalg.norm(median_quat)
            if norm > 0:
                median_quat = median_quat / norm
            else:
                median_quat = quats[0]

            print("Executing grasp sequence...")
            obj_pos = median_pos.copy()
            grasp_quat = median_quat
            
            HOVER_HEIGHT = 0.15
            
            # 1. Hover
            hover_pos = obj_pos.copy()
            hover_pos[2] = HOVER_HEIGHT
            print(f"Move to hover position: {hover_pos}")
            self.robot.move_to_cart_pose([hover_pos.tolist(), grasp_quat.tolist()])
            
            # 2. Descend
            grasp_pos = obj_pos.copy()
            if class_id == 2:
                grasp_pos[2] = 0.03+0.03
            else:
                grasp_pos[2] = 0.02+0.03
            if grasp_pos[2] < 0.005: grasp_pos[2] = 0.005
                
            print(f"Move to grasp position: {grasp_pos}")
            self.robot.move_to_cart_pose([grasp_pos.tolist(), grasp_quat.tolist()])
            
            # 3. Close Gripper
            self.robot.move_eef_pos([0.00]) 
            time.sleep(0.5)
            
            # 4. Lift
            print(f"Lift")
            self.robot.move_to_cart_pose([hover_pos.tolist(), grasp_quat.tolist()])
        else:
            print("Target lost after alignment!")

if __name__ == "__main__":
    detector = DetectionSystem()
    
    initial_position = [0.2, 0, 0.32]
    initial_quaternion = [0.0, 0.5382996083468239, 0.0, 0.8433914458128852]

    place_pose = [[-0.062, -0.32752352748698496, 0.018], [0, 0.7071068, 0, 0.7071068] ]

    remove_pose_1=[[-0.16288820927393982, -0.3217247688074838, 0.05], [0.5079623881977562, 0.4938207036434973, -0.5001322201433527, 0.4979790027741675]]
    remove_pose_2=[[-0.20288820927393982, -0.3217247688074838, -0.0671829013575066], [0.5079623881977562, 0.4938207036434973, -0.5001322201433527, 0.4979790027741675]]
    remove_pose_3=[[-0.15488820927393982, -0.3217247688074838, -0.0671829013575066], [0.5079623881977562, 0.4938207036434973, -0.5001322201433527, 0.4979790027741675]]

    detector.set_robot_pose(initial_position, initial_quaternion)
    
    detector.robot.move_eef_pos([0.07])
    detector.robot.move_to_cart_pose([detector.robot_position, detector.robot_quaternion])
    
    def execute_place_sequence(pose):
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
    
    # Sequence Execution
    detector.run_detection(class_id=0)
    execute_place_sequence(place_pose)
    
    detector.run_detection(class_id=0)  # Grasp second 1
    place_pose[0][0] += 0.06
    execute_place_sequence(place_pose)

    detector.run_detection(class_id=0)  # Grasp third 1
    place_pose[0][0] += 0.06
    place_pose[0][1] -= 0.0015
    execute_place_sequence(place_pose)

    detector.run_detection(class_id=0)  # Grasp fourth 1
    place_pose[0][0] += 0.055
    execute_place_sequence(place_pose)
    place_pose[0][0] += 0.005
    place_pose[0][1] += 0.0015

    # Remove sequence
    detector.robot.move_to_cart_pose(remove_pose_1)
    detector.robot.move_eef_pos([0.00])
    detector.robot.move_to_cart_pose(remove_pose_2)
    detector.robot.move_to_cart_pose(remove_pose_3)
    detector.robot.move_to_cart_pose(remove_pose_2)
    detector.robot.move_to_cart_pose(remove_pose_1)

    detector.robot.move_to_cart_pose([detector.robot_position, detector.robot_quaternion])
    detector.robot.move_eef_pos([0.07])
    
    detector.run_detection(class_id=1)  # Grasp first 2
    place_pose[0][0] -= 0.155
    place_pose[0][2] += 0.032
    execute_place_sequence(place_pose)

    detector.run_detection(class_id=2)  # Grasp first 3
    place_pose[0][0] += 0.05
    place_pose[0][2] += 0.012
    execute_place_sequence(place_pose)

    detector.run_detection(class_id=2)  # Grasp second 3
    place_pose[0][0] += 0.04
    place_pose[0][1] -= 0.001
    execute_place_sequence(place_pose)

    place_pose[0][1] += 0.001
    detector.run_detection(class_id=1)  # Grasp second 2
    place_pose[0][0] += 0.045
    place_pose[0][2] -= 0.013
    execute_place_sequence(place_pose)

    detector.run_detection(class_id=1)  # Grasp third 2
    place_pose[0][2] += 0.056
    place_pose[0][0] -= 0.071
    execute_place_sequence_last(place_pose)

    detector.run_detection(class_id=3)  # Grasp first 4
    place_pose[0][2] += 0.033
    execute_place_sequence_last(place_pose)

    exit(0)


