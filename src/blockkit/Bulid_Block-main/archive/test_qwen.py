#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基于 Qwen2.5-VL API 的图像目标检测脚本
从 spatial_understanding.ipynb 中学习 API 调用方式
"""

import os
import base64
import json
import cv2
import numpy as np
from openai import OpenAI
#from PIL import Image, ImageDraw, ImageFont
import xml.etree.ElementTree as ET

# 清理代理设置
# os.environ["http_proxy"] = ""
# os.environ["https_proxy"] = ""
# os.environ["HTTP_PROXY"] = ""
# os.environ["HTTPS_PROXY"] = ""
# os.environ["all_proxy"] = ""
# os.environ["ALL_PROXY"] = ""

# API 配置
API_KEY = "sk-1657d8957354498cb2f0cca7b08032d9"
BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
IMAGE_PATH = "test_image.jpg"

# def encode_image(image_path):
#     """将图像编码为 base64 格式"""
#     with open(image_path, "rb") as image_file:
#         return base64.b64encode(image_file.read()).decode("utf-8")

def encode_image(image_path):
    """将图像使用cv2.imread读取并编码为base64格式"""
    # 使用OpenCV读取图像
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError(f"无法读取图像: {image_path}")
    
    # 将numpy数组转换为JPEG格式的二进制数据
    success, encoded_img = cv2.imencode('.jpg', image)
    if not success:
        raise ValueError("无法编码图像为JPEG格式")
    
    # 将二进制数据编码为base64字符串
    return base64.b64encode(encoded_img.tobytes()).decode("utf-8")

def inference_with_api(image_path, prompt, sys_prompt="You are a helpful assistant.", 
                      model_id="qwen3-vl-plus", min_pixels=512*28*28, max_pixels=2048*28*28):
    """使用 API 进行推理"""
    base64_image = encode_image(image_path)
    
    client = OpenAI(
        api_key=API_KEY,
        base_url=BASE_URL,
    )

    messages = [
        {
            "role": "system",
            "content": [{"type": "text", "text": sys_prompt}]
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "min_pixels": min_pixels,
                    "max_pixels": max_pixels,
                    "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                },
                {"type": "text", "text": prompt},
            ],
        }
    ]
    
    completion = client.chat.completions.create(
        model=model_id,
        messages=messages,
    )
    
    return completion.choices[0].message.content

def parse_json_response(json_output):
    """解析 JSON 输出（从 notebook 中学习）"""
    lines = json_output.splitlines()
    for i, line in enumerate(lines):
        if line == "```json":
            json_output = "\n".join(lines[i+1:])
            json_output = json_output.split("```")[0]
            break
    return json_output

def draw_bboxes_with_opencv(image_path, detection_result):
    """使用 OpenCV 绘制边界框（增加坐标反归一化处理）"""
    image = cv2.imread(image_path)
    if image is None:
        print(f"无法读取图像: {image_path}")
        return None
    
    # 获取原始图像的宽高
    height, width = image.shape[:2]
    
    try:
        # 解析 JSON 结果
        parsed_result = parse_json_response(detection_result)
        detections = json.loads(parsed_result)
    except json.JSONDecodeError as e:
        print(f"JSON 解析错误: {e}")
        print(f"原始结果: {detection_result}")
        return None
    
    # 绘制边界框
    for i, detection in enumerate(detections):
        bbox = detection["bbox_2d"]
        label = detection.get("label", f"Object {i+1}")
        
        # --- 核心修改开始 ---
        # Qwen-VL 返回的坐标通常是基于 1000x1000 的归一化坐标
        # 需要将其映射回原始图像的尺寸
        # 格式通常为 [ymin, xmin, ymax, xmax] 或 [xmin, ymin, xmax, ymax]
        # Qwen 默认通常是 [x1, y1, x2, y2]
        
        x1_norm, y1_norm, x2_norm, y2_norm = bbox
        # print(f"归一化坐标 {bbox}")
        
        # 进行坐标转换： (数值 / 1000) * 实际边长
        x1 = int((x1_norm / 1000.0) * width)
        y1 = int((y1_norm / 1000.0) * height)
        x2 = int((x2_norm / 1000.0) * width)
        y2 = int((y2_norm / 1000.0) * height)
        
        # 边界保护，防止画出图外
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(width, x2), min(height, y2)
        # --- 核心修改结束 ---
        print(f"绘制框: ({x1}, {y1}), ({x2}, {y2}) 标签: {label}")
        print(f"中心点: ({(x1+x2)//2}, {(y1+y2)//2})")
        
        # 绘制矩形框
        cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)
        
        # 绘制标签背景
        label_text = f"{i+1}: {label}"
        label_size = cv2.getTextSize(label_text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)[0]
        # 确保标签不画出图外
        label_y = max(y1, label_size[1] + 10) 
        
        cv2.rectangle(image, (x1, label_y - 25), (x1 + label_size[0] + 10, label_y), (0, 255, 0), -1)
        
        # 绘制标签文本
        cv2.putText(image, label_text, (x1 + 5, label_y - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)
    
    return image

def decode_xml_points(text):
    """解析 XML 点坐标（从 notebook 中学习）"""
    try:
        root = ET.fromstring(text)
        num_points = (len(root.attrib) - 1) // 2
        points = []
        for i in range(num_points):
            x = root.attrib.get(f'x{i+1}')
            y = root.attrib.get(f'y{i+1}')
            points.append([x, y])
        alt = root.attrib.get('alt')
        phrase = root.text.strip() if root.text else None
        return {
            "points": points,
            "alt": alt,
            "phrase": phrase
        }
    except Exception as e:
        print(f"XML 解析错误: {e}")
        return None

def draw_points_with_opencv(image_path, xml_response):
    """使用 OpenCV 绘制点标记"""
    image = cv2.imread(image_path)
    if image is None:
        print(f"无法读取图像: {image_path}")
        return None
    
    height, width = image.shape[:2]
    
    # 解析 XML 响应
    xml_text = xml_response.replace('```xml', '').replace('```', '')
    data = decode_xml_points(xml_text)
    
    if data is None:
        print("无法解析 XML 点数据")
        return image
    
    points = data['points']
    description = data['phrase']
    
    # 绘制点
    for i, point in enumerate(points):
        x, y = int(point[0]), int(point[1])
        
        # 绘制圆点
        cv2.circle(image, (x, y), 5, (0, 255, 0), -1)
        
        # 绘制描述文本
        if description:
            cv2.putText(image, description, (x + 10, y - 10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
    
    return image

def main():
    """主函数"""
    print("=== Qwen2.5-VL API 图像检测测试 ===")
    
    # 检查图像文件是否存在
    if not os.path.exists(IMAGE_PATH):
        print(f"图像文件不存在: {IMAGE_PATH}")
        return
    
    print(f"处理图像: {IMAGE_PATH}")
    
    # 测试 1: 检测所有
    print("\n1. 检测所有积木...")
    prompt1 = "检测图中每一个木头积木的位置。请输出基于1000x1000坐标系的归一化坐标，以json格式输出：[{\"bbox_2d\": [x1, y1, x2, y2], \"label\": \"block\"}, ..."
    try:
        response1 = inference_with_api(IMAGE_PATH, prompt1)
        print("API 响应:")
        print(response1)
        
        # 绘制结果
        result_image1 = draw_bboxes_with_opencv(IMAGE_PATH, response1)
        if result_image1 is not None:
            cv2.imshow('Detection Result', result_image1)
            cv2.waitKey(0)
            cv2.imwrite('detection_all_cakes.png', result_image1)
            print("结果已保存为 detection_all_cakes.png")
    except Exception as e:
        print(f"检测失败: {e}")
    
    # # 测试 2: 检测特定蛋糕
    # print("\n2. 检测特定蛋糕...")
    # prompt2 = "定位最右上角的棕色蛋糕，以JSON格式输出其bbox坐标"
    # try:
    #     response2 = inference_with_api(IMAGE_PATH, prompt2)
    #     print("API 响应:")
    #     print(response2)
        
    #     # 绘制结果
    #     result_image2 = draw_bboxes_with_opencv(IMAGE_PATH, response2)
    #     if result_image2 is not None:
    #         cv2.imwrite('detection_specific_cake.png', result_image2)
    #         print("结果已保存为 detection_specific_cake.png")
    # except Exception as e:
    #     print(f"检测失败: {e}")
    
    # # 测试 3: 点定位
    # print("\n3. 点定位测试...")
    # prompt3 = "以点的形式定位图中桌子远处的擀面杖，以XML格式输出其坐标 <points x y>object</points>"
    # try:
    #     response3 = inference_with_api(IMAGE_PATH, prompt3)
    #     print("API 响应:")
    #     print(response3)
        
    #     # 绘制结果
    #     result_image3 = draw_points_with_opencv(IMAGE_PATH, response3)
    #     if result_image3 is not None:
    #         cv2.imwrite('detection_points.png', result_image3)
    #         print("结果已保存为 detection_points.png")
    # except Exception as e:
    #     print(f"点定位失败: {e}")
    
    # # 测试 4: 计数功能
    # print("\n4. 计数功能测试...")
    # prompt4 = "请以JSON格式输出图中所有物体bbox的坐标以及它们的名字，然后基于检测结果回答以下问题：图中物体的数目是多少？"
    # try:
    #     response4 = inference_with_api(IMAGE_PATH, prompt4)
    #     print("API 响应:")
    #     print(response4)
        
    #     # 绘制结果
    #     result_image4 = draw_bboxes_with_opencv(IMAGE_PATH, response4)
    #     if result_image4 is not None:
    #         cv2.imwrite('detection_counting.png', result_image4)
    #         print("结果已保存为 detection_counting.png")
    # except Exception as e:
    #     print(f"计数功能失败: {e}")
    
    # # 测试 5: 使用自定义系统提示
    # print("\n5. 自定义系统提示测试...")
    # system_prompt = "As an AI assistant, you specialize in accurate image object detection, delivering coordinates in plain text format 'x1,y1,x2,y2 object'."
    # prompt5 = "find all cakes"
    # try:
    #     response5 = inference_with_api(IMAGE_PATH, prompt5, sys_prompt=system_prompt)
    #     print("API 响应:")
    #     print(response5)
    # except Exception as e:
    #     print(f"自定义系统提示测试失败: {e}")
    
    # print("\n=== 测试完成 ===")

if __name__ == "__main__":
    main()