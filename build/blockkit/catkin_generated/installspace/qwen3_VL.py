from openai import OpenAI
import os
import base64
import json
import re
from datetime import datetime


# base64 编码格式
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")



base64_image = encode_image("/home/ytm/block_agent/src/block_building_agent/test_image/block2.jpg")

client = OpenAI(

    api_key="sk-085136cf9d09461faa70028e1704146c",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)


prompt_text = """
现在这有一张图，我现在告诉你最下面的那个积木块的中心点在机器人坐标系中的位置[X,Y,Z]为[0.5,0.0,0.1]，
图中从右往左是机器人基座坐标系的X轴，从下往上是机器人基座坐标系的Y轴，
请你根据提供的信息推算出其它两个积木块的位置，并以json格式输出，只输出结果即可。

要求以JSON格式输出，格式如下：
{
  "blocks": [
    {"id": 1, "position": [x1, y1, z1], "class": "积木块上的数字"},
    {"id": 2, "position": [x2, y2, z2], "class": "积木块上的数字"},
    {"id": 3, "position": [x3, y3, z3], "class": "积木块上的数字"}
  ]
}
其中：
1. position数组的三个值分别对应X、Y、Z坐标（单位：米）
2. class字段表示积木块上的数字（如"2"、"3"、"4"等）
3. id为1的积木块是已知的（最下面的积木块），请使用我提供的位置[0.5,0.0,0.1]
4. 请同时识别出每个积木块上的数字作为class
"""
# prompt_text = """
# 你知道图中有些什么东西吗
# """
completion = client.chat.completions.create(
    model="qwen3-vl-plus",
    messages=[
        {
            "role": "system",
            "content": [{"type": "text", "text": "You are a helpful assistant."}]
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                },
                {
                    "type": "text",
                    "text": prompt_text
                },
            ],
        }
    ],
)

# 解析响应并保存到文件
response_text = completion.choices[0].message.content
print("模型原始响应:")
print(response_text)

# 提取JSON部分（模型可能返回带解释的文本）
json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
if json_match:
    json_str = json_match.group()
    try:
        block_data = json.loads(json_str)
        
        # 验证数据结构
        if "blocks" not in block_data:
            print("警告: JSON中没有'blocks'字段")
            # 尝试重构数据格式
            if isinstance(block_data, list):
                block_data = {"blocks": block_data}
            else:
                # 如果是其他格式，尝试提取必要信息
                blocks = []
                for key, value in block_data.items():
                    if isinstance(value, list) and len(value) >= 3:
                        blocks.append({
                            "id": len(blocks) + 1,
                            "position": value[:3],
                            "class": str(key) if not key.startswith("block") else "unknown"
                        })
                if blocks:
                    block_data = {"blocks": blocks}
        
        # 确保每个block都有id、position和class字段
        for i, block in enumerate(block_data.get("blocks", [])):
            if "id" not in block:
                block["id"] = i + 1
            if "class" not in block:
                block["class"] = "unknown"
            # 确保position是列表且长度为3
            if "position" in block and isinstance(block["position"], list) and len(block["position"]) == 3:
                # 将位置坐标转换为浮点数
                block["position"] = [float(coord) for coord in block["position"]]
        
        # 保存到文件
        filename = f"block_positions.json"

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(block_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n积木位置已保存到: {filename}")
        print(f"数据内容:")
        print(json.dumps(block_data, indent=2, ensure_ascii=False))
        
        # 打印用于机械臂控制的信息
        print("\n用于机械臂控制的信息:")
        print("=" * 60)
        for block in block_data.get("blocks", []):
            class_num = block.get("class", "unknown")
            position = block.get("position", [0, 0, 0])
            print(f"积木块 {block['id']} (数字: {class_num}): 位置 = [{position[0]:.3f}, {position[1]:.3f}, {position[2]:.3f}]")
        print("=" * 60)
        
    except json.JSONDecodeError as e:
        print(f"JSON解析错误: {e}")
        print(f"原始JSON字符串: {json_str}")
        # 尝试清理JSON字符串
        json_str_clean = json_str.replace("'", "\"").replace("True", "true").replace("False", "false")
        try:
            block_data = json.loads(json_str_clean)
            print("清理后成功解析JSON")
        except:
            print("清理后仍然无法解析JSON")
    except Exception as e:
        print(f"处理JSON时发生错误: {e}")
        print(f"原始响应: {response_text}")
else:
    print("未找到JSON格式数据")
    print(f"模型响应: {response_text}")