import cv2
import numpy as np
import time
from collections import deque
from test_grasp_copy import DetectionSystem

def nothing(x):
    """ Trackbar 的回调函数，不需要做任何事 """
    pass

def calculate_angle_pca(roi_img, hsv_min, hsv_max):
    """
    对 ROI 区域进行 PCA 角度计算 (HSV 二值化)
    参数:
        hsv_min: np.array([h,s,v])
        hsv_max: np.array([h,s,v])
    返回: 
        角度 (0-360), 成功标志, 二值化掩码(用于调试)
    """
    if roi_img is None or roi_img.size == 0:
        return 0, False, None

    # 1. 预处理 - HSV 二值化
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

    def update(self, angle):
        rad = np.radians(angle)
        self.history_sin.append(np.sin(rad))
        self.history_cos.append(np.cos(rad))
        avg_sin = sum(self.history_sin) / len(self.history_sin)
        avg_cos = sum(self.history_cos) / len(self.history_cos)
        return np.degrees(np.arctan2(avg_sin, avg_cos)) % 360

class PCAMatcher(DetectionSystem):
    def __init__(self):
        super().__init__()
        self.smoother = AngleSmoother(window_size=5)

    def run_matching_visualization(self):
        print("\n=== 开始 PCA 角度计算 (HSV 调试) ===")
        print("操作说明: 在 'Control Panel' 窗口拖动滑块调整 HSV 阈值")
        
        observe_pose = [0.2, 0, 0.2]
        observe_quat = [0.0, 0.537, 0.0, 0.843]
        
        print(f"移动到观测位置: {observe_pose}")
        self.robot.move_to_cart_pose([observe_pose, observe_quat])
        time.sleep(1.0)
        
        # --- 创建窗口和滑动条 ---
        cv2.namedWindow("PCA Result", cv2.WINDOW_NORMAL)
        cv2.namedWindow("ROI Mask", cv2.WINDOW_NORMAL) # 这里看二值化效果
        cv2.namedWindow("Control Panel", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("Control Panel", 400, 300)
        
        # 创建滑动条：HSV Min/Max
        cv2.createTrackbar("H Min", "Control Panel", 0, 179, nothing)
        cv2.createTrackbar("H Max", "Control Panel", 179, 179, nothing)
        cv2.createTrackbar("S Min", "Control Panel", 0, 255, nothing)
        cv2.createTrackbar("S Max", "Control Panel", 255, 255, nothing)
        cv2.createTrackbar("V Min", "Control Panel", 0, 255, nothing)
        cv2.createTrackbar("V Max", "Control Panel", 255, 255, nothing)
        
        while True:
            frames = self.pipeline.wait_for_frames()
            aligned_frames = self.align.process(frames)
            color_frame = aligned_frames.get_color_frame()
            
            if not color_frame: continue
            
            img = np.asanyarray(color_frame.get_data())
            display_img = img.copy()
            # 默认显示全黑，如果没有检测到物体
            roi_debug_img = np.zeros((100, 100), dtype=np.uint8) 
            
            h_img, w_img = img.shape[:2]
            
            # --- 读取滑动条当前的值 ---
            h_min = cv2.getTrackbarPos("H Min", "Control Panel")
            h_max = cv2.getTrackbarPos("H Max", "Control Panel")
            s_min = cv2.getTrackbarPos("S Min", "Control Panel")
            s_max = cv2.getTrackbarPos("S Max", "Control Panel")
            v_min = cv2.getTrackbarPos("V Min", "Control Panel")
            v_max = cv2.getTrackbarPos("V Max", "Control Panel")
            
            hsv_min = np.array([h_min, s_min, v_min])
            hsv_max = np.array([h_max, s_max, v_max])

            # YOLO 推理
            results = self.model(img, verbose=False)[0]
            
            best_conf = 0
            best_detection = None

            if hasattr(results, 'obb') and results.obb is not None:
                obb_data = results.obb.data.cpu().numpy()
                for box in obb_data:
                    cx, cy, w, h, rotation, conf, cls = box[:7]
                    if int(cls) == 2 and conf > 0.5:
                        if conf > best_conf:
                            best_conf = conf
                            best_detection = (cx, cy, w, h)

            if best_detection:
                cx, cy, w, h = best_detection
                side_len = max(w, h) * 1.6
                
                x1 = int(cx - side_len / 2)
                y1 = int(cy - side_len / 2)
                x2 = int(cx + side_len / 2)
                y2 = int(cy + side_len / 2)
                
                x1 = max(0, x1); y1 = max(0, y1)
                x2 = min(w_img, x2); y2 = min(h_img, y2)
                
                if (x2 - x1) > 10 and (y2 - y1) > 10:
                    roi = img[y1:y2, x1:x2]
                    
                    # --- 将滑动条的值传给计算函数 ---
                    raw_angle, success, debug_mask = calculate_angle_pca(roi, hsv_min, hsv_max)
                    
                    if success:
                        if debug_mask is not None:
                            roi_debug_img = debug_mask

                        smoothed_angle = self.smoother.update(raw_angle)
                        
                        # 绘制
                        cv2.rectangle(display_img, (x1, y1), (x2, y2), (255, 200, 0), 2)
                        arrow_len = 80
                        
                        # 将校准后的角度转回图像坐标系用于画图，以验证方向是否正确
                        # Final = (-Original - 90) => Original = -Final - 90
                        draw_angle_deg = -smoothed_angle - 90
                        rad = np.radians(draw_angle_deg)
                        
                        end_x = int(cx + arrow_len * np.cos(rad))
                        end_y = int(cy + arrow_len * np.sin(rad))
                        
                        cv2.arrowedLine(display_img, (int(cx), int(cy)), (end_x, end_y), (0, 0, 255), 4, tipLength=0.2)
                        
                        cv2.putText(display_img, f"Angle: {smoothed_angle:.1f}", (int(cx)-60, int(cy)-50), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                        
            cv2.imshow("PCA Result", display_img)
            cv2.imshow("ROI Mask", roi_debug_img) # 关键：一定要看这个窗口来调参
            
            if cv2.waitKey(1) == ord('q'):
                break
        
        cv2.destroyAllWindows()

if __name__ == "__main__":
    matcher = PCAMatcher()
    matcher.run_matching_visualization()