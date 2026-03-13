from langgraph.graph import StateGraph, END
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from block_building_agent.state import AgentState
from block_building_agent.agents.img_ana import img_ana_node
from block_building_agent.agents.build_advisor import build_advisor_node
from block_building_agent.agents.build_validator import build_validator_node
from block_building_agent.agents.task_advisor import task_advisor_node
from block_building_agent.agents.task_validator import task_validator_node


def build_construction_graph():
    """
    构建完整的搭建任务流图

    流程：
    img_ana
      -> build_advisor
      -> build_validator
         -> (不通过) 回到 build_advisor
         -> (通过)   进入 task_advisor
      -> task_advisor
      -> task_validator
         -> (不通过) 回到 task_advisor
         -> (通过)   结束，输出 final_task_sequence
    """

    workflow = StateGraph(AgentState)

    # ========== 添加节点 ==========
    workflow.add_node("img_ana", img_ana_node)
    workflow.add_node("build_advisor", build_advisor_node)
    workflow.add_node("build_validator", build_validator_node)
    workflow.add_node("task_advisor", task_advisor_node)
    workflow.add_node("task_validator", task_validator_node)

    # ========== 设置入口 ==========
    workflow.set_entry_point("img_ana")

    # ========== 固定边 ==========
    workflow.add_edge("img_ana", "build_advisor")
    workflow.add_edge("build_advisor", "build_validator")
    workflow.add_edge("task_advisor", "task_validator")

    # ========== build 阶段路由 ==========
    def route_after_build_validator(state: AgentState):
        """
        build_validator 后的路由逻辑：
        - build 通过 -> 进入 task_advisor
        - build 未通过但达到上限 -> 结束
        - build 未通过且未到上限 -> 回到 build_advisor
        """
        if state.get("is_valid", False):
            return "to_task"

        if state.get("iteration_count", 0) >= state.get("max_iterations", 5):
            return "end"

        return "repeat_build"

    workflow.add_conditional_edges(
        "build_validator",
        route_after_build_validator,
        {
            "repeat_build": "build_advisor",
            "to_task": "task_advisor",
            "end": END,
        }
    )

    # ========== task 阶段路由 ==========
    def route_after_task_validator(state: AgentState):
        """
        task_validator 后的路由逻辑：
        - task 通过 -> 结束
        - task 未通过但达到上限 -> 结束
        - task 未通过且未到上限 -> 回到 task_advisor
        """
        if state.get("task_is_valid", False):
            return "end"

        if state.get("task_iteration_count", 0) >= state.get("task_max_iterations", 3):
            return "end"

        return "repeat_task"

    workflow.add_conditional_edges(
        "task_validator",
        route_after_task_validator,
        {
            "repeat_task": "task_advisor",
            "end": END,
        }
    )

    app = workflow.compile()
    return app


# 创建一个全局实例
construction_app = build_construction_graph()
