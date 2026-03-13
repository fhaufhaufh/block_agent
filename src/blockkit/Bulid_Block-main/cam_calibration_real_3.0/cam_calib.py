'''
Copyright: qiuzhi.tech
Author: hanyang
Date: 2025-03-10 16:07:23
LastEditTime: 2025-03-31 15:23:02
'''
import cv2
import numpy as np
import glob
import matplotlib.pyplot as plt
import os
from datetime import datetime

# 棋盘格 配置参数  
calib_config = {
    # "calibration_dir": "./calib/0332",
    # "output_dir": "./calib/0332",
    "calibration_dir": "./yolo_dataset/20250511111940",
    "output_dir": "./yolo_dataset/20250511111940",
    # "pattern_size": (6, 9),       # 内角点数量（列，行）
    "pattern_size": (8, 10),       # 内角点数量（列，行）
    "square_size": 20.0,          # 棋盘格实际尺寸（mm）
    "image_format": "png",
    # "image_size": (1280, 720),
    "image_size": (640, 480),
    "board_type": "chessboard"
}

# 圆点格 配置参数  
# calib_config = {
#     "calibration_dir": "./calib/0328",
#     "output_dir": "./calib/0328",
#     "pattern_size": (11, 9),       # 内角点数量（列，行）
#     "square_size": 30,          # 棋盘格实际尺寸（mm）
#     "image_format": "jpg",
#     "image_size": (1280, 720),
#     "board_type": "circles"
# }

def load_camera_params(file_path):
    camera_intrinsic = None
    camera_extrinsic = None
    
    with open(file_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
                
            elif "--Intrinsic--" in line:
                # 跳过 "list format:" 行
                f.readline()
                # 跳过 "[" 行
                f.readline()
                matrix = []
                for _ in range(3):
                    row = f.readline().strip().replace('[', '').replace(']', '').replace(',', '')
                    matrix.append([float(x) for x in row.split()])
                # 跳过 "]" 行
                f.readline()
                camera_intrinsic = np.array(matrix)
            
            elif "--Extrinsic--" in line:
                # 跳过 "list format:" 行
                f.readline()
                # 跳过 "[" 行
                f.readline()
                matrix = []
                for _ in range(4):
                    row = f.readline().strip().replace('[', '').replace(']', '').replace(',', '')
                    matrix.append([float(x) for x in row.split()])
                # 跳过 "]" 行
                f.readline()
                camera_extrinsic = np.array(matrix)
                
    return camera_intrinsic, camera_extrinsic

def save_camera_params(mtx, dist, mean_error, filepath):
    with open(filepath, 'w') as f:
        f.write(f"# Camera Calibration Results ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})\n\n")
        f.write("[Intrinsic Matrix]\n")
        np.savetxt(f, mtx, fmt='%.8f', header='fx, fy, cx, cy', comments='')
        f.write("\n[Distortion Coefficients]\n")
        np.savetxt(f, dist.ravel(), fmt='%.8f', 
                  header='k1, k2, p1, p2, k3', comments='')
        f.write(f"\n[Mean Reprojection Error]\n{mean_error:.6f} pixels\n")

def calibrate_camera_intrinsic(config):
    os.makedirs(config["output_dir"], exist_ok=True)
    
    # 准备世界坐标点
    objp = np.zeros((config["pattern_size"][0]*config["pattern_size"][1], 3), np.float32)
    objp[:, :2] = np.mgrid[0:config["pattern_size"][0], 
                          0:config["pattern_size"][1]].T.reshape(-1, 2) * config["square_size"]

    objpoints, imgpoints = [], []
    images = glob.glob(os.path.join(config["calibration_dir"], f"*.{config['image_format']}"))
    
    print(f"Processing {len(images)} images...")
    for fname in images:
        img = cv2.imread(fname)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        if config["board_type"] == "chessboard":
            ret, corners = cv2.findChessboardCorners(gray, config["pattern_size"], None)
        elif config["board_type"] == "circles":
            ret, corners = cv2.findCirclesGrid(gray, config["pattern_size"], flags=cv2.CALIB_CB_SYMMETRIC_GRID)
        else:
            raise ValueError("Unsupported board type. Choose 'chessboard' or 'circles'.")
        
        if ret:
            # 亚像素级精确化
            corners_refined = cv2.cornerSubPix(gray, corners, (11,11), (-1,-1), 
                                            (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001))
            objpoints.append(objp)
            imgpoints.append(corners_refined)

            cv2.drawChessboardCorners(img, config["pattern_size"], corners_refined, ret)
            cv2.imshow('Corners Found', img)
            cv2.waitKey(10)
        else:
            print(f"未能在 {fname} 中检测到角点")

    ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(
        objpoints, imgpoints, config["image_size"], None, None)

    total_error = 0
    per_image_errors = []
    for i in range(len(objpoints)):
        imgpoints2, _ = cv2.projectPoints(objpoints[i], rvecs[i], tvecs[i], mtx, dist)
        error = cv2.norm(imgpoints[i], imgpoints2, cv2.NORM_L2)/len(imgpoints2)
        total_error += error
        per_image_errors.append(error)
    mean_error = total_error/len(objpoints)

    param_file = os.path.join(config["output_dir"], "camera_params.txt")
    save_camera_params(mtx, dist, mean_error, param_file)
    print(f"\nCamera parameters saved to: {param_file}")

    # 生成可视化图表
    plt.figure(figsize=(15,5))
    
    # 每张图像误差曲线
    plt.subplot(131)
    plt.plot(per_image_errors, 'b-')
    plt.xlabel('Image Index'), plt.ylabel('Error (pixels)')
    plt.title('Per-image Reprojection Error')
    plt.grid(True)
    
    # 误差直方图
    plt.subplot(132)
    all_errors = np.sqrt(np.sum((np.array(imgpoints)-np.array([cv2.projectPoints(o, r, t, mtx, dist)[0] 
                              for o,r,t in zip(objpoints, rvecs, tvecs)]))**2, axis=2))
    plt.hist(all_errors.ravel(), bins=50, color='g')
    plt.xlabel('Error (pixels)'), plt.ylabel('Count')
    plt.title('Error Histogram')
    plt.grid(True)
    
    # 误差分布箱线图
    plt.subplot(133)
    plt.boxplot(all_errors.ravel(), showfliers=False)
    plt.ylabel('Error (pixels)')
    plt.title('Error Distribution')
    
    # 保存图表
    plot_path = os.path.join(config["output_dir"], "error_analysis.png")
    plt.savefig(plot_path, dpi=300, bbox_inches='tight')
    print(f"Error analysis plot saved to: {plot_path}")
    
    plt.tight_layout()
    plt.show()
    return mtx, dist, mean_error

if __name__ == "__main__":
    np.set_printoptions(precision=6, suppress=True)
    mtx, dist, error = calibrate_camera_intrinsic(calib_config)
    
    print("\n[Calibration Results]")
    print(f"Camera Matrix:\n{mtx}")
    print(f"Distortion Coefficients: {dist.ravel()}")
    print(f"Mean Reprojection Error: {error:.4f} pixels")