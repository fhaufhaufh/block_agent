from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from typing import List
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from block_building_agent.config import task_validator_llm


class TaskValidationResult(BaseModel):
    is_valid: bool = Field(description="任务序列是否合理可执行")
    errors: List[str] = Field(description="发现的问题列表；没有问题时为空列表")
    suggestions: List[str] = Field(description="修正建议；没有建议时可为空列表")


def create_task_validator_prompt():
    return ChatPromptTemplate.from_messages([
        ("system", """
你是一名严格的机器人装配任务检查员。
你需要检查 task_advisor 生成的装配级任务序列是否合理、顺序是否正确、依赖是否满足。

你必须严格遵守以下要求：
1. 只输出 JSON，且必须严格符合 format_instructions。
2. 不要输出解释、推理过程或任何额外文本。
3. 输出 JSON 只能包含 is_valid、errors、suggestions 三个字段。

你重点检查：
- task_id 是否从 1 开始且连续递增
- 是否与搭建计划顺序一致
- 高层任务是否排在低层之后
- depends_on 是否合理
- required_class 是否与搭建计划一致
- target_pose 是否与搭建计划的 position + posture 一致
- target_level 是否与搭建计划一致
- selection_rule 是否存在且非空
- 是否遗漏任务或多出任务
"""),
        ("human", """
待检查的任务序列：
{task_sequence}

对应的搭建计划：
{final_plan}

请严格审查，并仅输出指定 JSON。
{format_instructions}
""")
    ])


def _normalize_target_pose(plan_item):
    position = list(plan_item.get("position", [0.0, 0.0, 0.0]))
    posture = list(plan_item.get("posture", [0.0, 0.0, 0.0, 1.0]))
    return position + posture


def _coerce_robot_task_to_assembly(task: dict, fallback_task_id: int) -> dict:
    """兼容 planning_node 的 RobotTask schema：step/class_type/target_position/target_posture -> task_id/required_class/target_pose."""
    if not isinstance(task, dict):
        return {}

    # 优先使用 legacy 字段
    if any(k in task for k in ("task_id", "required_class", "target_pose")):
        return task

    step = task.get("step", fallback_task_id)
    try:
        step = int(step)
    except Exception:
        step = fallback_task_id

    required_class = task.get("class_type", "unknown")
    required_class = str(required_class)

    pos = task.get("target_position") or [0.0, 0.0, 0.0]
    post = task.get("target_posture") or [0.0, 0.0, 0.0, 1.0]
    if not (isinstance(pos, list) and len(pos) >= 3):
        pos = [0.0, 0.0, 0.0]
    if not (isinstance(post, list) and len(post) >= 4):
        post = [0.0, 0.0, 0.0, 1.0]

    # RobotTask 没有 selection_rule，这里给一个默认值避免因缺失直接判错
    selection_rule = task.get("selection_rule")
    if not isinstance(selection_rule, str) or not selection_rule.strip():
        selection_rule = f"choose any reachable block of class {required_class} from tabletop"

    return {
        "task_id": step,
        "required_class": required_class,
        "target_pose": [float(pos[0]), float(pos[1]), float(pos[2]), float(post[0]), float(post[1]), float(post[2]), float(post[3])],
        "target_level": task.get("target_level"),
        "depends_on": task.get("depends_on", []),
        "selection_rule": selection_rule,
    }


def _rule_validate(tasks, plan):
    errors = []
    suggestions = []

    if not isinstance(tasks, list) or len(tasks) == 0:
        return False, ["任务序列为空"], ["请为每个搭建计划项生成一个装配任务"]

    if len(tasks) != len(plan):
        errors.append(f"任务数应为 {len(plan)}，实际为 {len(tasks)}")
        suggestions.append("请确保每个搭建计划项恰好对应一个任务")

    for i, raw_task in enumerate(tasks):
        task = _coerce_robot_task_to_assembly(raw_task, i + 1)
        expected_task_id = i + 1
        if task.get("task_id") != expected_task_id:
            errors.append(
                f"第 {i} 个任务的 task_id 应为 {expected_task_id}，实际为 {task.get('task_id')}"
            )

        if i >= len(plan):
            continue

        plan_item = plan[i]
        expected_pose = _normalize_target_pose(plan_item)

        if task.get("required_class") != plan_item.get("class_type"):
            errors.append(
                f"task_id={task.get('task_id')} 的 required_class 与搭建计划不一致"
            )

        if task.get("target_level") != plan_item.get("level"):
            errors.append(
                f"task_id={task.get('task_id')} 的 target_level 与搭建计划不一致"
            )

        if task.get("target_pose") != expected_pose:
            errors.append(
                f"task_id={task.get('task_id')} 的 target_pose 与搭建计划不一致"
            )

        selection_rule = task.get("selection_rule")
        if not isinstance(selection_rule, str) or not selection_rule.strip():
            errors.append(
                f"task_id={task.get('task_id')} 的 selection_rule 为空或缺失"
            )

        depends_on = task.get("depends_on", [])
        if not isinstance(depends_on, list):
            errors.append(
                f"task_id={task.get('task_id')} 的 depends_on 必须为列表"
            )
        else:
            if i == 0:
                if depends_on not in ([], None):
                    errors.append("第一个任务的 depends_on 应为空列表")
            else:
                if i not in depends_on:
                    errors.append(
                        f"task_id={task.get('task_id')} 应至少依赖前一个任务 task_id={i}"
                    )

    return len(errors) == 0, errors, suggestions


def task_validator_node(state: dict):
    """
    task_validator:
    检查 current_task_sequence 是否合理；
    若通过，则输出 final_task_sequence。
    """
    tasks = state.get("current_task_sequence", [])
    plan = state.get("final_plan", [])
    task_iteration = state.get("task_iteration_count", 0)

    try:
        print(f"[task_validator] invoked: task_iteration={task_iteration} task_len={len(tasks)}")
    except Exception:
        pass

    def format_task_item(i, t):
        if isinstance(t, dict):
            normalized = _coerce_robot_task_to_assembly(t, i + 1)
            return (
                f"Task {normalized.get('task_id', i+1)}: "
                f"required_class={normalized.get('required_class')} "
                f"target_pose={normalized.get('target_pose')} "
                f"target_level={normalized.get('target_level')} "
                f"depends_on={normalized.get('depends_on', [])} "
                f"selection_rule={normalized.get('selection_rule')}"
            )
        return str(t)

    def format_plan_item(i, p):
        if isinstance(p, dict):
            return (
                f"Level {p.get('level', i+1)}: "
                f"class_type={p.get('class_type')} "
                f"position={p.get('position')} "
                f"posture={p.get('posture')}"
            )
        return str(p)

    task_info = "\n".join([format_task_item(i, t) for i, t in enumerate(tasks)])
    plan_info = "\n".join([format_plan_item(i, p) for i, p in enumerate(plan)])

    rule_valid, rule_errors, rule_suggestions = _rule_validate(tasks, plan)

    prompt = create_task_validator_prompt()
    parser = PydanticOutputParser(pydantic_object=TaskValidationResult)
    chain = prompt | task_validator_llm | parser

    try:
        result = chain.invoke({
            "task_sequence": task_info if task_info else "[]",
            "final_plan": plan_info if plan_info else "[]",
            "format_instructions": parser.get_format_instructions(),
        })

        final_errors = list(rule_errors)
        final_suggestions = list(rule_suggestions)

        if not result.is_valid:
            final_errors.extend(result.errors)
            final_suggestions.extend(result.suggestions)

        is_valid = rule_valid and result.is_valid and len(final_errors) == 0

        if final_suggestions:
            feedback_text = "; ".join(final_suggestions)
        else:
            feedback_text = "任务序列验证通过" if is_valid else ("; ".join(final_errors) if final_errors else "任务序列验证失败")

        # 如果 tasks 是 RobotTask schema，也原样返回，供 planning_node/action_planner 使用
        final_task_sequence = tasks if is_valid else None

        return {
            "task_is_valid": is_valid,
            "task_validation_feedback": feedback_text,
            "task_validation_errors": final_errors,
            "final_task_sequence": final_task_sequence,
            "task_iteration_count": task_iteration + 1,
        }

    except Exception as e:
        final_errors = list(rule_errors)
        final_errors.append(str(e))
        return {
            "task_is_valid": rule_valid,
            "task_validation_feedback": (
                "任务序列验证通过（LLM 校验异常，已采用规则校验结果）"
                if rule_valid else f"task_validator 验证过程出错: {str(e)}"
            ),
            "task_validation_errors": final_errors if not rule_valid else [],
            "final_task_sequence": tasks if rule_valid else None,
            "task_iteration_count": task_iteration + 1,
        }