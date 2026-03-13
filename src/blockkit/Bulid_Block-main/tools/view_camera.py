import pyrealsense2 as rs
import numpy as np
import cv2
import os
import time

def main():
    # 1. 创建保存图像的文件夹
    save_folder = "dataset_images"
    if not os.path.exists(save_folder):
        os.makedirs(save_folder)
        print(f"新建文件夹: {save_folder}")
    else:
        print(f"文件夹已存在: {save_folder}")

    # 2. 配置 RealSense 管道
    pipeline = rs.pipeline()
    config = rs.config()

    # 启用彩色流，分辨率 1280x720，帧率 30fps，格式 BGR8 (OpenCV 默认格式)
    config.enable_stream(rs.stream.color, 1280, 720, rs.format.bgr8, 30)

    # 3. 开始流传输
    print("正在启动 RealSense 相机...")
    try:
        pipeline.start(config)
        print("相机已启动。")
        print("按 '空格键' 保存图像")
        print("按 'q' 或 'ESC' 退出程序")
    except Exception as e:
        print(f"无法启动相机: {e}")
        return

    # 图片计数器，用于生成唯一文件名
    # 自动检测文件夹中已有的图片数量，避免覆盖
    existing_files = [f for f in os.listdir(save_folder) if f.endswith('.jpg') or f.endswith('.png')]
    img_counter = len(existing_files)

    try:
        while True:
            # 等待一帧数据
            frames = pipeline.wait_for_frames()
            color_frame = frames.get_color_frame()

            if not color_frame:
                continue

            # 将图像转换为 numpy 数组
            color_image = np.asanyarray(color_frame.get_data())

            # 显示图像
            cv2.imshow('RealSense Color Stream (640x480)', color_image)

            # 等待按键输入
            key = cv2.waitKey(1)

            # 按下 ESC (27) 或 'q' 退出
            if key == 27 or key == ord('q'):
                break
            
            # 按下空格键 (32) 保存图像
            elif key == 32:
                img_name = os.path.join(save_folder, f"img_{img_counter:04d}.jpg")
                cv2.imwrite(img_name, color_image)
                print(f"已保存: {img_name}")
                img_counter += 1

    except Exception as e:
        print(f"发生错误: {e}")

    finally:
        # 停止管道并关闭窗口
        pipeline.stop()
        cv2.destroyAllWindows()
        print("程序已结束")

if __name__ == "__main__":
    main()