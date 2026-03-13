from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from typing import List
import sys
import os

# 添加父目录到路径，以便导入config和state
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


from block_building_agent.config import build_advisor_llm

# 输出格式：严格匹配 src/block_building_agent/build_advisor_json
class PlanItem(BaseModel):
    level: int = Field(description="层级/步骤编号，从 1 开始")
    class_type: str = Field(description="积木类别（字符串，例如 '0'-'5' 或 'unknown'）")
    position: List[float] = Field(min_length=3, max_length=3, description="位置 [x,y,z]，单位米")
    posture: List[float] = Field(min_length=4, max_length=4, description="姿态四元数 [x,y,z,w]")


class BuildPlanOutput(BaseModel):
    plans: List[PlanItem] = Field(description="按顺序的搭建计划列表（每项为 PlanItem）")


def create_build_advisor_prompt():
    """创建Advisor的Prompt模板（明确要求仅输出 JSON）"""
    return ChatPromptTemplate.from_messages([
        ("system", """
你是一个积木块搭建计划编制者。
当被要求生成搭建计划时，你必须仅输出与所提供的格式说明完全匹配的 JSON 结构，不得包含任何其他内容。
不要包含链式思考、推理过程或任何解释性文字。

输出语言可以为中文或英文，但输出必须严格符合 format_instructions 中给出的 JSON 格式说明。
"""),
    ("human", """
积木信息（来自 img_ana，字段严格为 class_type / position / posture）：
{blocks_info}

之前的反馈（如果有）：
{feedback}

任务：请给出搭建/放置顺序（level 从 1 开始），并为每个 level 输出：class_type、position、posture。
层数判定规则（非常重要）：
1) level 只能由 Z 高度决定（使用 position[2]）。严禁用 X/Y 的变化来决定层数。
2) 如果所有积木的 Z 相同（或差值在 0.03 米以内视作相同），那么所有积木都属于同一层：level 全部为 1。
3) 只有当存在明显不同的 Z 高度（差值 > 0.03 米）时，才增加新的层：最低 Z 的那一组为 level=1，次低为 level=2，以此类推。

示例：
- Z=[0.10,0.10,0.10] -> level 全为 1
- Z=[0.10,0.15,0.20] -> level 分别为 1,2,3


请先根据上述规则计算每个积木的 level，再输出 JSON。
要求：只输出 JSON，严格符合 format_instructions，不要输出额外文本。

{format_instructions}
""")
    ])


def build_advisor_node(state: dict):
    """
    Advisor节点函数
    输入：state（包含积木信息）
    输出：更新后的state（包含生成的计划）
    """
    from block_building_agent.state import BlockInfo

    # 从state中提取信息
    blocks = state.get('input_blocks', [])
    previous_feedback = state.get('build_validation_feedback', '')
    iteration = state.get('iteration_count', 0)

    # 格式化积木信息
    blocks_info = "\n".join([
        f"Block {i+1}: class_type={b.get('class_type')}, position={b.get('position')}, posture={b.get('posture')}"
        for i, b in enumerate(blocks)
    ])

    # 创建Prompt
    prompt = create_build_advisor_prompt()

    # 创建解析器（仅期待 plans 字段的 JSON）
    parser = PydanticOutputParser(pydantic_object=BuildPlanOutput)

    # 构建链
    chain = prompt | build_advisor_llm | parser

    # 调用LLM
    try:
        result = chain.invoke({
            "blocks_info": blocks_info,
            "feedback": previous_feedback if iteration > 0 else "无（首次规划）",
            "format_instructions": parser.get_format_instructions()
        })

        # 只将解析后的 plans 写回 state，避免包含自由文本 messages
        # 将可能的 Pydantic 对象序列化为可 JSON 化的 dict
        try:
            serialized_plans = []
            for p in result.plans:
                if hasattr(p, 'model_dump'):
                    serialized_plans.append(p.model_dump())
                elif hasattr(p, 'dict'):
                    serialized_plans.append(p.dict())
                else:
                    serialized_plans.append(p)
        except Exception:
            serialized_plans = result.plans

        try:
            print(f"[build_advisor] produced plans len={len(serialized_plans)}")
        except Exception:
            pass

        return {
            "current_plan": serialized_plans,
            "build_advisor_feedback": "",
            "iteration_count": iteration + 1,
        }
    except Exception as e:
        # 解析失败时返回错误字段，外层流程会处理
        return {
            "build_advisor_feedback": f"build_advisor 解析失败: {str(e)}",
            "is_valid": False,
            "iteration_count": iteration + 1,
        }