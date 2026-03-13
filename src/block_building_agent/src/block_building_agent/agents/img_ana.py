from __future__ import annotations

import os
import base64
from typing import List, Optional

from pydantic import BaseModel, Field

from block_building_agent.config import llm
from block_building_agent.state import AgentState


DEFAULT_IMAGE_PATH = "/home/ytm/block_agent/src/block_building_agent/test_image/block2.jpg"
class BlockInfoModel(BaseModel):
    class_type: str = Field(..., description="积木类别。按需求：数字就是 class，例如 '1','2','3'...")
    position: List[float] = Field(..., min_length=3, max_length=3, description="位置 [x,y,z]。当前阶段允许输出占位坐标。")
    posture: List[float] = Field(..., min_length=4, max_length=4, description="姿态四元数 [x,y,z,w]。")


class ImgAnaOutput(BaseModel):
    blocks: List[BlockInfoModel]




def img_ana_node(state: AgentState):
    """LangGraph node: 从图片生成 input_blocks，并写回 state。"""

    # 运行时导入：避免不同 langchain 版本/编辑器环境导致的静态解析误报
    # 兼容不同版本的包名：优先尝试项目中已有的 langchain_core，然后回退到 langchain
    try:
        from langchain_core.output_parsers import PydanticOutputParser
        from langchain_core.prompts import ChatPromptTemplate
    except Exception:
        try:
            from langchain.output_parsers import PydanticOutputParser
            from langchain.prompts import ChatPromptTemplate
        except Exception as e:
            raise RuntimeError(
                "无法导入 PydanticOutputParser/ChatPromptTemplate：请在环境中安装 `langchain_core` 或 `langchain`。原始错误: %s" % e
            )

    parser = PydanticOutputParser(pydantic_object=ImgAnaOutput)

    # 注意：这里 image_url 的 url 使用 data:image/...;base64,...
    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            [
                {"type": "text", "text": "You are a helpful assistant."},
            ],
        ),
        (
            "user",
            [
                {"type": "image_url", "image_url": {"url": "{image_url}"}},
                {
                    "type": "text",
                    "text": (
                        "现在这有一张图，我现在告诉你最下面的那个积木块的中心点在机器人坐标系中的位置[X,Y,Z]为[0.5,0.0,0.1]，\n"
                        "图中从右往左是机器人基座坐标系的X轴，从下往上是机器人基座坐标系的Y轴，\n"
                        "请你根据提供的信息推算出其它积木块的位置，并识别每个积木块上的数字。\n\n"
                        "硬性约束：\n"
                        "- 只输出 JSON，必须严格符合 format_instructions，不要输出任何多余文本。\n"
                        "- class_type：积木上印的数字（\"0\"-\"5\"），看不清输出 \"unknown\"。\n"
                        "- position：[x,y,z]，单位米；无法估计输出 [0.0,0.0,0.0]。\n"
                        "- posture：输出四元数 x,y,z,w；无法估计输出单位四元数。\n\n"
                        "format_instructions：\n{format_instructions}"
                    ),
                },
            ],
        ),
    ])

    if not os.path.isfile(DEFAULT_IMAGE_PATH):
        msg = f"img_ana error: DEFAULT_IMAGE_PATH not found: {DEFAULT_IMAGE_PATH}"
        try:
            print(f"[img_ana] {msg}")
            import sys
            sys.stdout.flush()
        except Exception:
            pass
        return {
            "input_blocks": [],
            "build_advisor_feedback": msg,
            "img_ana_debug": msg,
        }

    try:
        with open(DEFAULT_IMAGE_PATH, "rb") as f:
            raw = f.read()
        b64 = base64.b64encode(raw).decode("ascii")
        ext = os.path.splitext(DEFAULT_IMAGE_PATH)[1].lower().lstrip('.')
        if ext in ('jpg', 'jpeg'):
            mime = 'image/jpeg'
        elif ext == 'png':
            mime = 'image/png'
        else:
            mime = 'application/octet-stream'
        image_data_url = f"data:{mime};base64,{b64}"
    except Exception as e:
        msg = f"img_ana error reading image: {e}"
        try:
            print(f"[img_ana] {msg}")
            import sys
            sys.stdout.flush()
        except Exception:
            pass
        return {
            "input_blocks": [],
            "build_advisor_feedback": msg,
            "img_ana_debug": msg,
        }

    chain = prompt | llm | parser
    try:
        out: ImgAnaOutput = chain.invoke({
            "format_instructions": parser.get_format_instructions(),
            "image_url": image_data_url,
        })
    except Exception as e:
        msg = f"img_ana invoke failed: {str(e)}"
        try:
            print(f"[img_ana] {msg}")
            import sys
            sys.stdout.flush()
        except Exception:
            pass
        return {
            "input_blocks": [],
            "build_advisor_feedback": msg,
            "img_ana_debug": msg,
        }

    def _dump(m):
        dump = getattr(m, "model_dump", None)
        if callable(dump):
            return dump()
        return m.dict()

    blocks = [_dump(b) for b in out.blocks]

    # 基本校验与容错：确保每个 block 有必要字段并格式正确
    validated = []
    for b in blocks:
        try:
            cid = str(b.get('class_type', 'unknown'))
            if cid not in [str(i) for i in range(0, 6)]:
                cid = 'unknown'
            pos = b.get('position', [0.0, 0.0, 0.0])
            if not (isinstance(pos, list) and len(pos) >= 3):
                pos = [0.0, 0.0, 0.0]
            posture = b.get('posture', [0.0, 0.0, 0.0, 1.0])
            if not (isinstance(posture, list) and len(posture) >= 4):
                posture = [0.0, 0.0, 0.0, 1.0]
            validated.append({
                'class_type': cid,
                'position': [float(pos[0]), float(pos[1]), float(pos[2])],
                'posture': [float(posture[0]), float(posture[1]), float(posture[2]), float(posture[3])],
            })
        except Exception:
            continue

    if not validated:
        msg = "img_ana: no valid blocks parsed from image"
        try:
            print(f"[img_ana] {msg}")
            import sys
            sys.stdout.flush()
        except Exception:
            pass
        return {
            "input_blocks": [],
            "build_advisor_feedback": msg,
            "img_ana_debug": msg,
        }

    # 写入 state.input_blocks，保持与 planning_node 现有 inputs 结构一致
    return {
        "input_blocks": validated,
        "build_advisor_feedback": "img_ana: blocks extracted",
        "img_ana_debug": f"img_ana: blocks extracted count={len(validated)}",
    }
