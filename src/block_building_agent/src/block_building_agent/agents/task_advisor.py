from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from typing import List
import sys
import os

# 添加父目录到路径，以便导入 config 和 state
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from block_building_agent.config import task_advisor_llm


class AssemblyTaskItem(BaseModel):
    task_id: int = Field(description="任务编号，从 1 开始连续递增")
    required_class: str = Field(description="该任务所需积木类别，例如 '0'-'5' 或 'unknown'")
    target_pose: List[float] = Field(
        min_length=7,
        max_length=7,
        description="目标位姿，格式为 [x, y, z, qx, qy, qz, qw]"
    )
    target_level: int = Field(description="该任务对应的目标层级")
    depends_on: List[int] = Field(description="当前任务依赖的前置 task_id 列表；无依赖时为空列表")
    selection_rule: str = Field(description="从桌面候选积木中选择源积木的规则")


class TaskSequenceOutput(BaseModel):
    tasks: List[AssemblyTaskItem] = Field(description="按顺序排列的装配级任务序列")


DEFAULT_SELECTION_RULE = "choose any reachable block of the required class from tabletop"


def create_task_advisor_prompt():
    return ChatPromptTemplate.from_messages([
        ("system", """
你是一个机器人任务规划 Agent。
你的职责是把已经通过 build 阶段审查的“搭建计划”，转换成“装配级任务序列”。

你必须严格遵守以下要求：
1. 只输出 JSON，且必须严格符合 format_instructions。
2. 不要输出解释、注释、推理过程或任何额外文本。
3. 每个搭建计划项必须对应一个任务项，不多不少。
4. task_id 必须从 1 开始连续递增。
5. required_class 必须与搭建计划中的 class_type 一致。
6. target_level 必须与搭建计划中的 level 一致。
7. target_pose 必须由搭建计划中的 position 与 posture 拼接得到：
   [x, y, z, qx, qy, qz, qw]
8. 不允许改变原始搭建顺序。
9. depends_on 规则：
   - 第一个任务输出 []
   - 后续任务通常依赖前一个任务
   - 高层任务至少依赖前一个低层或同层任务，保证先低层后高层
10. selection_rule 必须是可执行的自然语言规则，描述如何从桌面现有积木中选择源积木，
    例如：choose any reachable block of class 2 from tabletop
"""),
        ("human", """
已确认的搭建计划：
{final_plan}

上一次 task_validator 的反馈（如果有）：
{feedback}

请将上述搭建计划转换为装配级任务序列。
要求：
- 每个搭建计划项对应一个任务项
- 只输出 JSON
- 严格符合 format_instructions
- 不要输出额外文本

{format_instructions}
""")
    ])


def _serialize_tasks(tasks):
    serialized_tasks = []
    for t in tasks:
        if hasattr(t, "model_dump"):
            serialized_tasks.append(t.model_dump())
        elif hasattr(t, "dict"):
            serialized_tasks.append(t.dict())
        else:
            serialized_tasks.append(t)
    return serialized_tasks


def _fallback_generate_tasks(plan):
    """
    当 LLM 解析失败时，使用规则回退，直接从搭建计划生成装配级任务。
    """
    tasks = []
    for i, p in enumerate(plan):
        position = p.get("position", [0.0, 0.0, 0.0])
        posture = p.get("posture", [0.0, 0.0, 0.0, 1.0])
        target_pose = list(position) + list(posture)
        task = {
            "task_id": i + 1,
            "required_class": p.get("class_type", "unknown"),
            "target_pose": target_pose,
            "target_level": p.get("level", i + 1),
            "depends_on": [] if i == 0 else [i],
            "selection_rule": (
                f"choose any reachable block of class {p.get('class_type', 'unknown')} from tabletop"
            ),
        }
        tasks.append(task)
    return tasks


def task_advisor_node(state: dict):
    """
    task_advisor:
    接收 build 阶段通过后的 final_plan，
    生成装配级任务序列 current_task_sequence。
    """
    plan = state.get("final_plan") or state.get("current_plan") or []
    previous_feedback = state.get("task_validation_feedback", "")
    task_iteration = state.get("task_iteration_count", 0)

    # 将计划转为文本
    plan_info = "\n".join([
        f"Level {p.get('level', i+1)}: "
        f"class_type={p.get('class_type')} "
        f"position={p.get('position')} "
        f"posture={p.get('posture')}"
        for i, p in enumerate(plan)
    ])

    prompt = create_task_advisor_prompt()
    parser = PydanticOutputParser(pydantic_object=TaskSequenceOutput)
    chain = prompt | task_advisor_llm | parser

    try:
        result = chain.invoke({
            "final_plan": plan_info if plan_info else "[]",
            "feedback": previous_feedback if task_iteration > 0 else "无（首次任务规划）",
            "format_instructions": parser.get_format_instructions(),
        })

        serialized_tasks = _serialize_tasks(result.tasks)

        try:
            print(f"[task_advisor] produced assembly tasks len={len(serialized_tasks)}")
        except Exception:
            pass

        return {
            "current_task_sequence": serialized_tasks,
            "task_advisor_feedback": "",
            "task_is_valid": False,
            "final_task_sequence": None,
        }

    except Exception as e:
        fallback_tasks = _fallback_generate_tasks(plan)
        return {
            "current_task_sequence": fallback_tasks,
            "task_advisor_feedback": f"task_advisor 解析失败，已使用规则回退: {str(e)}",
            "task_is_valid": False,
            "final_task_sequence": None,
        }