#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import sys
import time
import subprocess
import importlib.util
import rospy
from std_msgs.msg import String

from block_building_agent.graph.builder import construction_app
from block_building_agent.state import create_initial_state
from block_building_agent.agents.action_planner import action_planner_node

# 尽量兼容你当前环境中 ObjectInfo 的真实包名
try:
    from vi_grab.msg import ObjectInfo
except Exception:
    try:
        from blockkit.msg import ObjectInfo
    except Exception:
        ObjectInfo = None


class PlanningNode:
    def __init__(self):
        rospy.init_node("planning_node", anonymous=False)

        # 参数
        self.max_iterations = rospy.get_param("~max_iterations", 5)
        self.task_max_iterations = rospy.get_param("~task_max_iterations", 3)
        self.action_wait_timeout = rospy.get_param("~action_wait_timeout", 10.0)

        # action_planner 相关参数
        self.generated_action_script_path = rospy.get_param(
            "~generated_action_script_path",
            "//home/ytm/block_agent/src/block_building_agent/tool/action.py"
        )

        # 外部脚本路径：catch.py（提供 arm_ready_pose）
        self.catch_py_path = rospy.get_param(
            "~catch_py_path",
            "/home/ytm/block_agent/src/blockkit/scripts/catch.py"
        )
        self.yolo_script_path = rospy.get_param(
            "~yolo_script_path",
            "/home/ytm/block_agent/src/blockkit/scripts/vi_catch_yolov11.py"
        )

        # 话题
        self.plan_pub = rospy.Publisher("/construction_plan", String, queue_size=10)
        self.task_pub = rospy.Publisher("/task_sequence", String, queue_size=10)
        self.action_script_pub = rospy.Publisher("/generated_action_script_path", String, queue_size=10)

        self.input_sub = rospy.Subscriber(
            "/block_information",
            String,
            self.block_info_callback,
            queue_size=1
        )

        # 订阅真实世界积木信息
        self.latest_world_blocks = []
        self._world_seen_once = False
        if ObjectInfo is not None:
            self.object_sub = rospy.Subscriber(
                "/object_pose",
                ObjectInfo,
                self.object_pose_callback,
                queue_size=50
            )
        else:
            self.object_sub = None
            rospy.logwarn("ObjectInfo message type import failed, action_planner will not receive /object_pose.")

        rospy.loginfo("planning_node started, waiting for /block_information ...")

        # 可选：启动后自动触发一次（不依赖 /block_information），用于走 img_ana
        self.auto_once = rospy.get_param("~auto_once", False)
        self._auto_invoked = False
        self._yolo_process = None
        if self.auto_once:
            rospy.loginfo("auto_once=true: will invoke planning pipeline once at startup (img_ana will generate input_blocks)")
            rospy.Timer(rospy.Duration(0.5), self._auto_invoke_once, oneshot=True)

    def _auto_invoke_once(self, _evt):
        if self._auto_invoked:
            return
        self._auto_invoked = True
        try:
            state = create_initial_state(
                input_blocks=[],
                max_iterations=self.max_iterations,
                task_max_iterations=self.task_max_iterations,
            )
            rospy.loginfo("auto_once: invoking construction_app...")
            result = construction_app.invoke(state)

            final_plan = result.get("final_plan") or result.get("current_plan") or []
            plan_msg = String()
            plan_msg.data = json.dumps(final_plan, ensure_ascii=False)
            self.plan_pub.publish(plan_msg)
            rospy.loginfo("auto_once: published construction plan")
            rospy.loginfo("\n%s", self._format_plan(final_plan))

            self._log_task_interaction_flow(result)

            final_task_sequence = result.get("final_task_sequence") or []
            if final_task_sequence:
                task_msg = String()
                task_msg.data = json.dumps(final_task_sequence, ensure_ascii=False)
                self.task_pub.publish(task_msg)
                rospy.loginfo("auto_once: published final task sequence topic: /task_sequence")
                self._run_action_planner_flow(final_task_sequence)
            else:
                rospy.logwarn("auto_once: No final task sequence published because task stage did not pass validation.")
        except Exception as e:
            rospy.logerr(f"auto_once planning failed: {e}")

    # =========================
    # 数据解析
    # =========================
    def _parse_block_info(self, msg_data):
        try:
            data = json.loads(msg_data)
            if isinstance(data, list):
                return data
            elif isinstance(data, dict) and "input_blocks" in data:
                return data["input_blocks"]
            else:
                rospy.logwarn("Input JSON format not recognized, fallback to empty list.")
                return []
        except Exception as e:
            rospy.logerr(f"Failed to parse block info JSON: {e}")
            return []

    # =========================
    # 真实世界积木信息
    # =========================
    def object_pose_callback(self, msg):
        """
        收集 YOLO 发布的真实世界积木信息。
        当前先做轻量缓存，不做复杂去重。
        """
        try:
            block = {
                "object_class": str(getattr(msg, "object_class", "")),
                "x": float(getattr(msg, "x", 0.0)),
                "y": float(getattr(msg, "y", 0.0)),
                "z": float(getattr(msg, "z", 0.0)),
                "angle": float(getattr(msg, "angle", 0.0)),
                "stamp": time.time(),
            }

            self.latest_world_blocks.append(block)
            # 只保留最近 50 条，避免无限增长
            self.latest_world_blocks = self.latest_world_blocks[-50:]
            self._world_seen_once = True
        except Exception as e:
            rospy.logwarn(f"Failed to cache /object_pose message: {e}")

    def _wait_for_world_blocks(self, timeout_sec, min_blocks: int = 1):
        """
        等待来自 /object_pose 的真实世界积木信息。
        - timeout_sec: 最大等待时间（秒）
        - min_blocks: 最少需要收集的消息数量，达到后返回 True（即使尚未超时）

        返回 True 当收集到至少 min_blocks 条消息，或 False 当超时。
        """
        start = time.time()
        last_log = 0.0
        while not rospy.is_shutdown():
            if len(self.latest_world_blocks) >= min_blocks:
                return True

            now = time.time()
            if now - last_log > 1.0:
                rospy.loginfo("等待接收真实世界的积木信息")
                last_log = now

            if now - start >= timeout_sec:
                return False
            rospy.sleep(0.2)
        return False

    def _start_yolo_if_needed(self):
        """
        启动 YOLO 识别脚本。
        若已经启动且未退出，则不重复启动。
        """
        try:
            if self._yolo_process is not None and self._yolo_process.poll() is None:
                rospy.loginfo("YOLO script is already running")
                return

            if not os.path.exists(self.yolo_script_path):
                rospy.logwarn(f"YOLO script not found: {self.yolo_script_path}")
                return

            self._yolo_process = subprocess.Popen([sys.executable, self.yolo_script_path])
            rospy.loginfo(f"Started YOLO script: {self.yolo_script_path}")
        except Exception as e:
            rospy.logwarn(f"Failed to start YOLO script: {e}")

    def _move_arm_to_ready_pose(self):
        """
        调用 catch.py 中的 arm_ready_pose，让机械臂先到识别姿态。
        """
        try:
            if not self.catch_py_path or not os.path.exists(self.catch_py_path):
                rospy.logwarn(f"catch.py not found: {self.catch_py_path}")
                return False

            spec = importlib.util.spec_from_file_location("blockkit_catch", self.catch_py_path)
            if spec is None or spec.loader is None:
                rospy.logwarn(f"Failed to create import spec for catch.py: {self.catch_py_path}")
                return False

            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            arm_ready_pose = getattr(mod, "arm_ready_pose", None)
            if not callable(arm_ready_pose):
                rospy.logwarn(f"arm_ready_pose not found in catch.py: {self.catch_py_path}")
                return False
        except Exception as e:
            rospy.logwarn(f"Failed to import arm_ready_pose from catch.py ({self.catch_py_path}): {e}")
            return False

        try:
            ok = arm_ready_pose()
            if ok:
                rospy.loginfo("机械臂已到达识别姿态，开始等待真实世界积木信息")
            else:
                rospy.logwarn("arm_ready_pose 调用失败")
            return ok
        except Exception as e:
            rospy.logwarn(f"arm_ready_pose execution failed: {e}")
            return False

    # =========================
    # 格式化输出
    # =========================
    def _format_plan(self, plan):
        if not plan:
            return "[]"

        lines = []
        for i, item in enumerate(plan):
            lines.append(
                f"[{i}] level={item.get('level')}, "
                f"class_type={item.get('class_type')}, "
                f"position={item.get('position')}, "
                f"posture={item.get('posture')}"
            )
        return "\n".join(lines)

    def _format_task_sequence(self, tasks):
        if not tasks:
            return "[]"

        lines = []
        for i, task in enumerate(tasks):
            lines.append(
                f"[{i}] step={task.get('step')}, "
                f"action={task.get('action')}, "
                f"class_type={task.get('class_type')}, "
                f"target_level={task.get('target_level')}, "
                f"target_position={task.get('target_position')}, "
                f"target_posture={task.get('target_posture')}, "
                f"depends_on={task.get('depends_on', [])}"
                + (
                    f", object_index={task.get('object_index')}, "
                    f"stage_in_object={task.get('stage_in_object')}"
                    if "object_index" in task or "stage_in_object" in task
                    else ""
                )
            )
        return "\n".join(lines)

    def _format_world_blocks(self, blocks):
        if not blocks:
            return "[]"

        lines = []
        for i, b in enumerate(blocks):
            lines.append(
                f"[{i}] object_class={b.get('object_class')}, "
                f"x={b.get('x')}, y={b.get('y')}, z={b.get('z')}, angle={b.get('angle', 0.0)}"
            )
        return "\n".join(lines)

    def _format_action_sequence(self, actions):
        if not actions:
            return "[]"

        lines = []
        for i, a in enumerate(actions):
            lines.append(
                f"[{i}] step={a.get('step')}, "
                f"action_type={a.get('action_type')}, "
                f"source_class={a.get('source_class')}, "
                f"source_pose={a.get('source_pose')}, "
                f"target_place={a.get('target_place')}, "
                f"comment={a.get('comment')}"
            )
        return "\n".join(lines)

    def _log_task_interaction_flow(self, result_state):
        final_plan = result_state.get("final_plan") or result_state.get("current_plan") or []
        current_task_sequence = result_state.get("current_task_sequence") or []
        final_task_sequence = result_state.get("final_task_sequence") or []
        task_feedback = result_state.get("task_validation_feedback", "")
        task_is_valid = result_state.get("task_is_valid", False)
        task_iteration_count = result_state.get("task_iteration_count", 0)

        rospy.loginfo("========== task planning stage ==========")

        rospy.loginfo("接收到搭建计划")
        rospy.loginfo("\n%s", self._format_plan(final_plan))

        rospy.loginfo("task_advisor 开始分析")

        rospy.loginfo("将任务计划发给 task_validator")
        rospy.loginfo("\n%s", self._format_task_sequence(current_task_sequence))

        if task_iteration_count > 0:
            rospy.loginfo("task_validator 反馈回 task_advisor")
            rospy.loginfo("%s", task_feedback if task_feedback else "无反馈")
        else:
            rospy.loginfo("task_validator 尚未返回反馈")

        if task_is_valid and final_task_sequence:
            rospy.loginfo("输出最终任务序列")
            rospy.loginfo("\n%s", self._format_task_sequence(final_task_sequence))
        else:
            rospy.logwarn("task 阶段未得到最终通过的任务序列")
            if current_task_sequence:
                rospy.logwarn("当前任务序列如下：")
                rospy.logwarn("\n%s", self._format_task_sequence(current_task_sequence))

        rospy.loginfo("========== end of task planning stage ==========")

    def _run_action_planner_flow(self, final_task_sequence):
        """
        在 task 阶段之后追加 action_planner 流程：
        - 接收任务序列
        - 调用 arm_ready_pose
        - 启动 YOLO
        - 等待真实世界积木信息
        - 调用 action_planner 生成动作序列与脚本文件
        """
        rospy.loginfo("========== action planning stage ==========")

        rospy.loginfo("接收到 task_advisor 输出的任务序列，开始发送给 action_planner")
        rospy.loginfo("\n%s", self._format_task_sequence(final_task_sequence))

        # 先到识别姿态
        self._move_arm_to_ready_pose()

        # 启动 YOLO
        self._start_yolo_if_needed()

        # 清空旧缓存，等待本轮识别
        self.latest_world_blocks = []
        self._world_seen_once = False

        # 等待至少 3 条识别消息，以便 action_planner 有更多世界信息可用
        got_world = self._wait_for_world_blocks(self.action_wait_timeout, min_blocks=3)
        if not got_world:
            rospy.logwarn("等待超时：未接收到来自 YOLO 的真实世界积木信息")
            rospy.loginfo("========== end of action planning stage ==========")
            return

        rospy.loginfo("已经接收到真实世界的积木信息，开始规划动作序列")
        rospy.loginfo("\n%s", self._format_world_blocks(self.latest_world_blocks))

        action_state = {
            "final_task_sequence": final_task_sequence,
            "real_blocks_info": self.latest_world_blocks,
            "generated_action_script_path": self.generated_action_script_path,
        }

        try:
            result = action_planner_node(action_state)
            action_feedback = result.get("action_planner_feedback", "")
            action_sequence = result.get("final_action_sequence") or result.get("current_action_sequence") or []
            script_path = result.get("generated_action_script_path")

            rospy.loginfo("action_planner 反馈：%s", action_feedback if action_feedback else "无反馈")
            rospy.loginfo("输出动作序列")
            rospy.loginfo("\n%s", self._format_action_sequence(action_sequence))

            if script_path:
                rospy.loginfo("已生成可调用脚本文件：%s", script_path)
                msg = String()
                msg.data = script_path
                self.action_script_pub.publish(msg)
        except Exception as e:
            rospy.logerr(f"action_planner failed: {e}")

        rospy.loginfo("========== end of action planning stage ==========")

    # =========================
    # 回调主流程
    # =========================
    def block_info_callback(self, msg):
        rospy.loginfo("Received /block_information")

        input_blocks = self._parse_block_info(msg.data)

        state = create_initial_state(
            input_blocks=input_blocks,
            max_iterations=self.max_iterations,
            task_max_iterations=self.task_max_iterations
        )

        try:
            result = construction_app.invoke(state)

            final_plan = result.get("final_plan") or result.get("current_plan") or []
            plan_msg = String()
            plan_msg.data = json.dumps(final_plan, ensure_ascii=False)
            self.plan_pub.publish(plan_msg)

            rospy.loginfo("published construction plan")
            rospy.loginfo("\n%s", self._format_plan(final_plan))

            # 保留你原来的 task 阶段输出逻辑
            self._log_task_interaction_flow(result)

            final_task_sequence = result.get("final_task_sequence") or []
            if final_task_sequence:
                task_msg = String()
                task_msg.data = json.dumps(final_task_sequence, ensure_ascii=False)
                self.task_pub.publish(task_msg)
                rospy.loginfo("published final task sequence topic: /task_sequence")

                # 新增：task 之后进入 action_planner 阶段
                self._run_action_planner_flow(final_task_sequence)
            else:
                rospy.logwarn("No final task sequence published because task stage did not pass validation.")

        except Exception as e:
            rospy.logerr(f"Planning failed: {e}")


if __name__ == "__main__":
    try:
        PlanningNode()
        rospy.spin()
    except rospy.ROSInterruptException:
        pass