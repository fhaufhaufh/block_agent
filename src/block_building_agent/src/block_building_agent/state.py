from typing import List, Annotated, Optional
from typing_extensions import TypedDict
import operator


class BlockInfo(TypedDict):
    """单个积木的信息"""
    class_type: str        # 积木上的数字类别（字符串，例如 "0"-"5" 或 "unknown"）
    position: List[float]  # 位置: [X, Y, Z]
    posture: List[float]   # 姿态四元数: [x, y, z, w]


class ConstructionPlan(TypedDict):
    """搭建计划的结构"""
    level: int
    class_type: str
    position: List[float]
    posture: List[float]


class RobotTask(TypedDict):
    """机器人任务序列中的单步任务（保持你当前版本不变）"""
    step: int
    action: str                   # 例如 "pick_and_place"
    class_type: str
    target_level: int
    target_position: List[float]
    target_posture: List[float]
    depends_on: List[int]         # 当前任务依赖的前置 step 编号


class RealBlockInfo(TypedDict, total=False):
    """YOLO 识别到的真实世界积木信息"""
    object_class: str
    x: float
    y: float
    z: float
    angle: float
    stamp: float


class ActionStep(TypedDict, total=False):
    """action_planner 输出的动作步骤"""
    step: int
    action_type: str              # 当前先固定为 catch_and_place
    source_class: str
    source_pose: List[float]      # [x, y, z, angle]
    target_place: List[float]     # [x, y, z]
    comment: str


class AgentState(TypedDict):
    """
    多智能体系统的全局状态
    所有 Agent 共享这个状态
    """

    # ========== 输入数据 ==========
    input_blocks: List[BlockInfo]

    # ========== build 阶段 ==========
    current_plan: List[ConstructionPlan]
    final_plan: Optional[List[ConstructionPlan]]

    build_advisor_feedback: str
    build_validation_feedback: str
    is_valid: bool
    build_validation_errors: List[str]

    iteration_count: int
    max_iterations: int

    # ========== task 阶段 ==========
    current_task_sequence: List[RobotTask]
    final_task_sequence: Optional[List[RobotTask]]

    task_advisor_feedback: str
    task_validation_feedback: str
    task_is_valid: bool
    task_validation_errors: List[str]

    task_iteration_count: int
    task_max_iterations: int

    # ========== action 阶段 ==========
    real_blocks_info: List[RealBlockInfo]
    current_action_sequence: List[ActionStep]
    final_action_sequence: Optional[List[ActionStep]]
    action_planner_feedback: str
    generated_action_script_path: Optional[str]
    action_waiting_for_world: bool

    # ========== 调试 / 历史 ==========
    messages: Annotated[List[dict], operator.add]


def create_initial_state(
    input_blocks: Optional[List[BlockInfo]] = None,
    max_iterations: int = 5,
    task_max_iterations: int = 3,
) -> AgentState:
    """
    方便外部调用 construction_app.invoke(...) 时初始化状态。
    """
    return {
        "input_blocks": input_blocks or [],

        # build
        "current_plan": [],
        "final_plan": None,
        "build_advisor_feedback": "",
        "build_validation_feedback": "",
        "is_valid": False,
        "build_validation_errors": [],
        "iteration_count": 0,
        "max_iterations": max_iterations,

        # task
        "current_task_sequence": [],
        "final_task_sequence": None,
        "task_advisor_feedback": "",
        "task_validation_feedback": "",
        "task_is_valid": False,
        "task_validation_errors": [],
        "task_iteration_count": 0,
        "task_max_iterations": task_max_iterations,

        # action
        "real_blocks_info": [],
        "current_action_sequence": [],
        "final_action_sequence": None,
        "action_planner_feedback": "",
        "generated_action_script_path": None,
        "action_waiting_for_world": False,

        # messages
        "messages": [],
    }