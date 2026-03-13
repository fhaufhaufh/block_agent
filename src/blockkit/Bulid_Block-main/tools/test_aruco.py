import cv2
import numpy as np
import pyrealsense2 as rs
import sys

def get_aruco_detector(aruco_dict_id=cv2.aruco.DICT_4X4_50):
    """
    获取 ArUco 检测器，兼容不同版本的 OpenCV。
    """
    aruco_dict = cv2.aruco.getPredefinedDictionary(aruco_dict_id)
    
    # 尝试获取 DetectorParameters
    try:
        aruco_params = cv2.aruco.DetectorParameters()
    except AttributeError:
        try:
            aruco_params = cv2.aruco.DetectorParameters_create()
        except AttributeError:
            aruco_params = None

    # 尝试使用新的 ArucoDetector 类 (OpenCV 4.7+)
    if hasattr(cv2.aruco, 'ArucoDetector'):
        detector = cv2.aruco.ArucoDetector(aruco_dict, aruco_params)
        return detector, aruco_dict, aruco_params, True # True 表示使用 ArucoDetector 对象
    else:
        return None, aruco_dict, aruco_params, False # False 表示使用旧的函数式 API

def detect_markers_compat(image, detector, aruco_dict, aruco_params, use_obj):
    """
    兼容的检测函数
    """
    if use_obj:
        # 新版 API: detector.detectMarkers
        return detector.detectMarkers(image)
    else:
        # 旧版 API: cv2.aruco.detectMarkers
        if hasattr(cv2.aruco, 'detectMarkers'):
            return cv2.aruco.detectMarkers(image, aruco_dict, parameters=aruco_params)
        else:
            raise AttributeError("当前 OpenCV 版本既没有 ArucoDetector 类，也没有 detectMarkers 函数。请安装 opencv-contrib-python。")

def main():
    # 1. 配置 RealSense
    pipeline = rs.pipeline()
    config = rs.config()
    
    # 配置流：彩色流 640x480, 30fps
    config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
    # 如果需要深度图，可以取消注释下面这行
    # config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)

    print("[INFO] 正在启动 RealSense 相机...")
    try:
        pipeline.start(config)
    except Exception as e:
        print(f"[ERROR] 无法启动相机: {e}")
        return

    # 2. 初始化 ArUco 检测器
    # 修改为 DICT_4X4_1000 以支持 ID 555
    target_dict = cv2.aruco.DICT_ARUCO_ORIGINAL
    print(f"[INFO] 初始化 ArUco 检测器 (Dict ID: {target_dict})...")
    
    detector, aruco_dict, aruco_params, use_obj = get_aruco_detector(target_dict)

    print("[INFO] 开始检测。按 'q' 或 'ESC' 退出。")
    
    try:
        while True:
            # 3. 等待帧
            frames = pipeline.wait_for_frames()
            color_frame = frames.get_color_frame()
            if not color_frame:
                continue

            # 转换为 numpy 数组
            color_image = np.asanyarray(color_frame.get_data())

            # 4. 检测 ArUco 码
            corners, ids, rejected = detect_markers_compat(color_image, detector, aruco_dict, aruco_params, use_obj)

            # 5. 可视化
            if ids is not None and len(ids) > 0:
                # 绘制检测到的标记
                cv2.aruco.drawDetectedMarkers(color_image, corners, ids)
                
                # 打印检测到的 ID
                # print(f"Detected IDs: {ids.flatten()}")

            # 显示图像
            cv2.imshow('RealSense ArUco Detect', color_image)

            # 按键检测
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q') or key == 27:
                break

    except KeyboardInterrupt:
        pass
    finally:
        # 6. 释放资源
        print("[INFO] 停止相机并关闭窗口。")
        pipeline.stop()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
