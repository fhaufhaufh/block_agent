import pyrealsense2 as rs
import numpy as np
import cv2
import os
import time
import argparse
import json
from airbot_py.arm import AIRBOTPlay,RobotMode, SpeedProfile

def move_with_cart_waypoints():
    
    input("\x1b[1;35mPress Enter to continue...\x1b[0m")
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-p", "--port", type=int, default=50051, help="Port to connect to the server"
    )
    cart_waypoints = [
        [[0.17, -0.02, 0.21], [0.02, 0.51, -0.05, 0.86]],
    ]
    args = parser.parse_args()
    with AIRBOTPlay(port=args.port) as robot:
        robot.set_speed_profile(SpeedProfile.FAST)
        robot.switch_mode(RobotMode.PLANNING_WAYPOINTS_PATH)
        robot.move_with_cart_waypoints(cart_waypoints)


def create_save_directories(base_path='./collected_data'):
    color_dir = os.path.join(base_path, 'color_images')
    os.makedirs(color_dir, exist_ok=True)
    return color_dir

def main():
    # 创建保存数据的文件夹
    color_save_dir = create_save_directories()
    
    # 初始化RealSense管道和配置
    pipeline = rs.pipeline()
    config = rs.config()
    config.enable_stream(rs.stream.color, 1280,720, rs.format.bgr8, 30)
    
    # 启动管道
    pipeline.start(config)
    
    print("RealSense相机已启动。按以下键操作：")
    print("  's' - 保存当前帧彩色图")
    print("  'q' - 退出程序")
    
    # !!! 修复点1：创建窗口应放在循环之外 !!!
    window_name = 'RealSense采集器'
    cv2.namedWindow(window_name, cv2.WINDOW_AUTOSIZE)
    
    try:
        frame_count = 0
        while True:
            frames = pipeline.wait_for_frames()
            color_frame = frames.get_color_frame()
            
            if not color_frame:
                continue
            
            color_image = np.asanyarray(color_frame.get_data())
            cv2.imshow(window_name, color_image)
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord('s'):
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                color_filename = os.path.join(color_save_dir, f'color_{timestamp}_{frame_count:04d}.png')
                cv2.imwrite(color_filename, color_image)
                print(f"已保存第 {frame_count} 帧: {color_filename}")
                frame_count += 1
            elif key == ord('q'):
                
                print("正在退出程序...")
                break
                
    finally:
        pipeline.stop()
        cv2.destroyAllWindows()
        print(f"采集完成。彩色图像数量: {len(os.listdir(color_save_dir))}")

if __name__ == "__main__":
   move_with_cart_waypoints()
   main()