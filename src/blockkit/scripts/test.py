import cv2
import numpy as np
from ultralytics import YOLO

# ==================== 配置区域 ====================
WEIGHTS_PATH = "/home/ytm/block_space/src/blockkit/model/yolov8-obb.pt"
IMAGE_PATH   = "/home/ytm/block_space/src/blockkit/image/12.jpg"
OUTPUT_PATH  = "/home/ytm/block_space/src/blockkit/image/result.jpg"
CONF_THRESH   = 0.90
DEVICE        = "cpu"
IMGSZ         = 640
# ==================================================

def main():
    # 加载模型
    model = YOLO(WEIGHTS_PATH)
    
    # 执行推理
    results = model(
        source=IMAGE_PATH,
        conf=CONF_THRESH,
        device=DEVICE,
        save=False,
        show=False
    )
    
    # 获取结果
    result = results[0]
    
    # 提取 OBB 信息
    print("=" * 60)
    print("检测结果分析")
    print("=" * 60)
    
    if result.obb is not None:
        obb = result.obb
        # ✅ 使用 xywhr 格式：[x_center, y_center, width, height, angle]
        boxes = obb.xywhr
        
        print(f"检测到 {len(boxes)} 个物体\n")
        
        for i, box in enumerate(boxes):
            # 提取坐标和角度
            x_center, y_center, width, height, angle_rad = box.cpu().numpy()
            
            # 转换角度：弧度转角度
            angle_degrees = float(angle_rad) * 180 / np.pi
            
            # 获取类别和置信度
            cls_id = int(obb.cls[i].cpu().numpy())
            conf = float(obb.conf[i].cpu().numpy())
            class_name = result.names[cls_id]
            
            # 打印详细信息
            print(f"物体 {i+1}:")
            print(f"  类别：{class_name}")
            print(f"  置信度：{conf:.4f}")
            print(f"  中心点：({x_center:.2f}, {y_center:.2f})")
            print(f"  尺寸：{width:.2f} x {height:.2f}")
            print(f"  角度：{angle_degrees:.2f}° ({angle_rad:.4f} 弧度)")
            print("-" * 60)
    else:
        print("未检测到任何物体")
    
    print("=" * 60)
    
    # 保存结果
    annotated_frame = result.plot()
    cv2.imwrite(OUTPUT_PATH, annotated_frame)
    print(f"带标注的结果已保存至：{OUTPUT_PATH}")

if __name__ == "__main__":
    main()