from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from typing import List
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from block_building_agent.config import build_validator_llm

# 定义验证结果格式：只包含 is_valid, errors, suggestions（无需长文本推理）
class BuildValidationResult(BaseModel):
    """验证结果的输出格式（仅结构化字段）"""
    is_valid: bool = Field(description="计划是否可行")
    errors: List[str] = Field(description="发现的错误列表，如果没有错误则为空列表")
    suggestions: List[str] = Field(description="改进建议，简洁条目")


def create_build_validator_prompt():
    """创建Validator的Prompt模板（强制仅输出 JSON）"""
    return ChatPromptTemplate.from_messages([
        ("system", """
你是一名严格的结构工程师和质量检查员。
在验证一个方案时，你必须仅输出一个与所提供格式说明完全匹配的 JSON 结构，不得包含任何其他内容。
不要包含链式思考、逐步推理或任何解释性文字。
输出的 JSON 必须只包含 is_valid, errors, suggestions 三个字段。
"""),
        ("human", """
待验证的搭建计划：
{current_plan}

原始积木信息：
{blocks_info}

请严格审查这个计划并仅返回指定的 JSON。
{format_instructions}
""")
    ])


def build_validator_node(state: dict):
    """
    Validator节点函数
    输入：state（包含当前计划）
    输出：更新后的state（包含验证结果）
    """
    from block_building_agent.state import BlockInfo

    # 从state中提取信息
    plan = state.get('current_plan', [])
    blocks = state.get('input_blocks', [])
    iteration = state.get('iteration_count', 0)

    # 简单入口日志，便于调试（图内部运行时会捕获 stdout）
    try:
        print(f"[build_validator] invoked: iteration={iteration} plan_len={len(plan)}")
    except Exception:
        pass

    # 格式化计划信息（为LLM提供简洁文本表示）
    def format_plan_item(i, p):
        # 支持不同结构：如果是层级计划，使用 layer_number/blocks/description
        if isinstance(p, dict):
            # 新格式：build_advisor_json -> {level,class_type,position,posture}
            if 'level' in p and 'class_type' in p and 'position' in p:
                lv = p.get('level', i + 1)
                ct = p.get('class_type', 'unknown')
                pos = p.get('position')
                post = p.get('posture')
                return f"Level {lv}: class_type={ct} position={pos} posture={post}"

            if 'layer_number' in p or 'blocks' in p:
                ln = p.get('layer_number', i+1)
                desc = p.get('description', '')
                blocks_list = p.get('blocks', [])
                return f"Layer {ln}: {desc}\n  Blocks: {', '.join(blocks_list)}"
            # 支持行动序列项，例如 {'action':'place','block_id':...,'position':[...]} -> 把每个当作一层描述
            if 'action' in p and 'block_id' in p:
                return f"Step {i+1}: action={p.get('action')} block={p.get('block_id')} position={p.get('position')}"
        # 其他可打印表示
        try:
            return str(p)
        except Exception:
            return repr(p)

    plan_info = "\n".join([format_plan_item(i, p) for i, p in enumerate(plan)])

    # 格式化积木信息
    blocks_info = "\n".join([
        f"Block {i+1}: Type={b['class_type']}, Position={b['position']}, ID={b.get('block_id', f'block_{i}') }"
        for i, b in enumerate(blocks)
    ])

    # 创建Prompt
    prompt = create_build_validator_prompt()

    # 创建解析器
    parser = PydanticOutputParser(pydantic_object=BuildValidationResult)

    # 构建链
    chain = prompt | build_validator_llm | parser

    # 调用LLM
    try:
        result = chain.invoke({
            "current_plan": plan_info,
            "blocks_info": blocks_info,
            "format_instructions": parser.get_format_instructions()
        })

        # 更新状态：只包含结构化验证结果，避免长文本消息
        # 如果没有 suggestions 且 is_valid 为 False，应返回明确的失败提示
        if result.suggestions:
            feedback_text = "; ".join(result.suggestions)
        else:
            feedback_text = "验证通过" if result.is_valid else "验证失败"

        # 如果验证通过，将 current_plan 视作 final_plan 返回
        final_plan = plan if result.is_valid else None

        return {
            "is_valid": result.is_valid,
            "build_validation_feedback": feedback_text,
            "build_validation_errors": result.errors,
            "final_plan": final_plan,
            "iteration_count": iteration + 1,
        }

    except Exception as e:
        # 如果解析失败，保守起见返回失败并简要错误
        return {
            "is_valid": False,
            "build_validation_feedback": f"验证过程出错: {str(e)}",
            "build_validation_errors": [str(e)],
            "final_plan": None,
            "iteration_count": iteration + 1,
        }