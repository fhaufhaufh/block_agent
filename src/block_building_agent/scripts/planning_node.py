#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Block Planning ROS Node
订阅：/vision/blocks_info
发布：/planning/construction_plan
"""
import rospy
import json
import time
import traceback
from pprint import pformat
from std_msgs.msg import String
from block_building_agent.graph.builder import construction_app
import sys


def _red(text: str) -> str:
    """Wrap text with ANSI red color for terminal output."""
    return f"\x1b[31m{text}\x1b[0m"


def log_error_red(msg: str, *args, **kwargs):
    """
    同时通过 rospy.logerr 记录错误（写入日志文件/rosout），
    并以红色字体将错误信息打印到 stderr，方便终端查看。
    """
    rospy.logerr(msg, *args, **kwargs)
    # 尝试将 msg 格式化后输出红色
    try:
        formatted = msg % args if args else msg
    except Exception:
        formatted = msg
    print(_red(formatted), file=sys.stderr)


class BlockPlanningNode:
    def __init__(self):
        """Initialize ROS node, subscriber and publishers."""
        rospy.init_node('block_planning_node', anonymous=True)
        rospy.loginfo("Block Planning Node Started")

        # 如果没有外部视觉节点发布 /vision/blocks_info，也可以在启动后自动跑一次（走 img_ana）
        # 默认 false，避免影响原有逻辑
        self.auto_once = rospy.get_param('~auto_once', False)
        self._auto_invoked = False
        self.task_max_iterations = rospy.get_param('~task_max_iterations', 3)

        # Subscriber for vision blocks info
        rospy.Subscriber('/vision/blocks_info', String, self.vision_callback)

        # Publisher for final construction plan
        self.plan_pub = rospy.Publisher('/planning/construction_plan', String, queue_size=10)

        # 保留原有功能：debug publisher
        self.debug_pub = rospy.Publisher('/planning/debug', String, queue_size=1)

        # 新增：发布最终任务序列，不影响原有计划发布逻辑
        self.task_pub = rospy.Publisher('/planning/task_sequence', String, queue_size=10)

        rospy.loginfo("Waiting for blocks info...")
        if self.auto_once:
            rospy.loginfo("auto_once=true: will run img_ana once at startup using IMG_PATH from .env")

        # 可选：自动触发一次（不依赖 /vision/blocks_info）
        if self.auto_once:
            rospy.Timer(rospy.Duration(0.5), self._auto_invoke_once, oneshot=True)

    def _auto_invoke_once(self, _evt):
        if self._auto_invoked:
            return
        self._auto_invoked = True
        rospy.loginfo("auto_once enabled: invoking planning pipeline without /vision/blocks_info (img_ana will generate input_blocks)")
        self._invoke_pipeline(blocks_info=[])

    def vision_callback(self, msg):
        try:
            rospy.loginfo("Received blocks info")
            try:
                blocks_info = json.loads(msg.data) if msg and msg.data else []
                if not isinstance(blocks_info, list):
                    rospy.logwarn("/vision/blocks_info is not a JSON list; fallback to empty list to trigger img_ana")
                    blocks_info = []
            except Exception:
                rospy.logwarn("Failed to parse /vision/blocks_info JSON; fallback to empty list to trigger img_ana")
                blocks_info = []

            self._invoke_pipeline(blocks_info=blocks_info)
        except Exception as e:
            log_error_red(f"Error during vision_callback: {e}")
            tb = traceback.format_exc()
            # 使用 log_error_red 将 traceback 也输出为红色（但 rospy.logerr 可能不支持多行，分开处理）
            for line in tb.splitlines():
                if line.strip():
                    log_error_red(line)
            # 也将错误发送到调试 topic 以便远程查看
            try:
                err = String()
                payload = json.dumps({
                    'error': str(e),
                    'traceback': tb
                }, ensure_ascii=False)
                if len(payload) > 15000:
                    payload = payload[:15000] + '...TRUNCATED...'
                err.data = payload
                self.debug_pub.publish(err)
            except Exception:
                rospy.logdebug("Failed to publish error payload to /planning/debug")

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
        """
        兼容新旧两种 task 结构：
        - 旧结构：step/action/class_type/target_position/target_posture
        - 新结构：task_id/required_class/target_pose/selection_rule
        """
        if not tasks:
            return "[]"

        lines = []
        for i, task in enumerate(tasks):
            if not isinstance(task, dict):
                lines.append(str(task))
                continue

            if 'task_id' in task or 'required_class' in task or 'target_pose' in task:
                lines.append(
                    f"[{i}] task_id={task.get('task_id')}, "
                    f"required_class={task.get('required_class')}, "
                    f"target_pose={task.get('target_pose')}, "
                    f"target_level={task.get('target_level')}, "
                    f"depends_on={task.get('depends_on', [])}, "
                    f"selection_rule={task.get('selection_rule')}"
                )
            else:
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
                        if 'object_index' in task or 'stage_in_object' in task
                        else ""
                    )
                )
        return "\n".join(lines)

    def _log_task_interaction_flow(self, result_state):
        """
        保留之前新增的输出逻辑，在 Published construction plan 后面继续输出 task 流程。
        """
        final_plan = result_state.get('final_plan') or result_state.get('current_plan') or []
        current_task_sequence = result_state.get('current_task_sequence') or []
        final_task_sequence = result_state.get('final_task_sequence') or []
        task_feedback = result_state.get('task_validation_feedback', '')
        task_is_valid = result_state.get('task_is_valid', False)
        task_iteration_count = result_state.get('task_iteration_count', 0)
        task_errors = result_state.get('task_validation_errors', []) or []

        rospy.loginfo("========== task planning stage ==========")
        rospy.loginfo("接收到搭建计划")
        rospy.loginfo("\n%s", self._format_plan(final_plan))
        rospy.loginfo("task_advisor 开始分析")
        rospy.loginfo("将任务计划发给 task_validator")
        rospy.loginfo("\n%s", self._format_task_sequence(current_task_sequence))

        if task_iteration_count > 0:
            rospy.loginfo("task_validator 反馈回 task_advisor")
            rospy.loginfo("%s", task_feedback if task_feedback else "无反馈")
            if task_errors:
                rospy.loginfo("task_validator errors: %s", task_errors)
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

    def _invoke_pipeline(self, blocks_info):
        """Invoke LangGraph pipeline and publish plan/debug."""
        rospy.loginfo("Starting LangGraph invocation...")

        inputs = {
            "input_blocks": blocks_info,
            "iteration_count": 0,
            "max_iterations": 3,
            # 新增 task 阶段初始字段；不影响原有 build 逻辑
            "task_iteration_count": 0,
            "task_max_iterations": self.task_max_iterations,
            "current_task_sequence": [],
            "final_task_sequence": None,
            "task_is_valid": False,
            "task_validation_feedback": "",
            "task_validation_errors": [],
        }
        rospy.logdebug(f"Invocation inputs: {pformat(inputs)}")

        start = time.time()
        result = construction_app.invoke(inputs)
        duration = time.time() - start
        rospy.loginfo(f"LangGraph invocation finished in {duration:.3f}s")

        # 尝试把返回值序列化为 JSON 友好格式用于日志与发布
        def safe_serialize(obj):
            try:
                return json.loads(json.dumps(obj, default=str, ensure_ascii=False))
            except Exception:
                try:
                    return str(obj)
                except Exception:
                    return repr(obj)

        try:
            serial_result = safe_serialize(result)
        except Exception:
            serial_result = str(result)

        # DEBUG: log the full serialized result to help trace missing fields
        try:
            full_json = json.dumps(serial_result, ensure_ascii=False)
            rospy.logdebug(f"Raw result: {pformat(serial_result)}")
            print(f"[planning_node] full_result={full_json}")
            try:
                sys.stdout.flush()
            except Exception:
                pass
        except Exception:
            rospy.logdebug(f"Raw result (non-serializable): {pformat(serial_result)}")

        plan_data = None
        try:
            if isinstance(result, dict):
                plan_data = result.get('final_plan') or result.get('current_plan') or []
                messages = result.get('messages')
                is_valid = result.get('is_valid')
                validation_feedback = result.get('build_validation_feedback') or result.get('validation_feedback') or result.get('build_advisor_feedback')
                validation_errors = result.get('build_validation_errors') or result.get('validation_errors')
            else:
                get = getattr(result, 'get', None)
                if callable(get):
                    plan_data = result.get('final_plan') or result.get('current_plan') or []
                    messages = result.get('messages')
                    is_valid = result.get('is_valid')
                    validation_feedback = result.get('build_validation_feedback') or result.get('validation_feedback') or result.get('build_advisor_feedback')
                    validation_errors = result.get('build_validation_errors') or result.get('validation_errors')
                else:
                    plan_data = getattr(result, 'final_plan', None) or getattr(result, 'current_plan', None) or []
                    messages = getattr(result, 'messages', None)
                    is_valid = getattr(result, 'is_valid', None)
                    validation_feedback = getattr(result, 'build_validation_feedback', None) or getattr(result, 'validation_feedback', None) or getattr(result, 'build_advisor_feedback', None)
                    validation_errors = getattr(result, 'build_validation_errors', None) or getattr(result, 'validation_errors', None)
        except Exception as e:
            rospy.logwarn(f"Failed to extract standard fields from result: {e}")
            plan_data = []
            messages = None
            is_valid = None
            validation_feedback = None
            validation_errors = None

        if messages:
            try:
                rospy.loginfo(f"Result contains {len(messages)} message(s)")
                for i, m in enumerate(messages):
                    try:
                        if isinstance(m, dict):
                            role = m.get('role')
                            status = m.get('status')
                        else:
                            role = getattr(m, 'role', None)
                            status = getattr(m, 'status', None)
                        rospy.loginfo(f"Message[{i}] role={role} status={status}")
                    except Exception:
                        rospy.logdebug(f"Cannot parse message[{i}]")
            except Exception:
                rospy.logdebug("Failed to iterate messages for summarized logging")

        rospy.loginfo(f"Validation: is_valid={is_valid} feedback={validation_feedback}")

        try:
            # 尝试提取 input_blocks（若 img_ana 生成）以便调试与发布
            input_blocks = []
            try:
                if isinstance(serial_result, dict):
                    input_blocks = serial_result.get('input_blocks', []) or []
                else:
                    get = getattr(result, 'get', None)
                    if callable(get):
                        input_blocks = result.get('input_blocks', []) or []
                    else:
                        input_blocks = getattr(result, 'input_blocks', None) or []
            except Exception:
                input_blocks = []

            # 准备调试结构，包含 input_blocks 的精简序列化（避免超长）
            dbg_blocks = None
            try:
                dbg_blocks = json.loads(json.dumps(input_blocks, default=str, ensure_ascii=False))
            except Exception:
                try:
                    dbg_blocks = str(input_blocks)
                except Exception:
                    dbg_blocks = None

            debug_msg = String()
            debug_struct = {
                'is_valid': is_valid,
                'validation_feedback': validation_feedback,
                'messages_count': len(messages) if messages else 0,
                'input_blocks_count': len(dbg_blocks) if isinstance(dbg_blocks, list) else (0 if dbg_blocks is None else 1),
            }
            # 将较小的 input_blocks 直接嵌入调试负载（长度受限）
            try:
                debug_struct['input_blocks'] = dbg_blocks
            except Exception:
                pass

            debug_payload = json.dumps(debug_struct, ensure_ascii=False)
            if len(debug_payload) > 20000:
                debug_payload = debug_payload[:20000] + '...TRUNCATED...'
            debug_msg.data = debug_payload
            self.debug_pub.publish(debug_msg)

            # 也把 input_blocks 输出到 stdout，便于直接在终端查看
            try:
                print(f"[planning_node] input_blocks={json.dumps(dbg_blocks, ensure_ascii=False)}")
                try:
                    sys.stdout.flush()
                except Exception:
                    pass
            except Exception:
                try:
                    print(f"[planning_node] input_blocks={dbg_blocks}")
                    try:
                        sys.stdout.flush()
                    except Exception:
                        pass
                except Exception:
                    pass

        except Exception:
            rospy.logdebug("Failed to publish debug payload")

        plan_data = plan_data or []
        rospy.loginfo(f"Plan data (len={len(plan_data)}): {pformat(plan_data)}")

        # 保留原有功能：发布 construction plan
        plan_msg = String()
        plan_msg.data = json.dumps(plan_data, ensure_ascii=False)
        self.plan_pub.publish(plan_msg)
        rospy.loginfo("Published construction plan")

        # 在原有输出后追加 task 阶段日志与发布，不删除原逻辑
        try:
            task_sequence = []
            if isinstance(result, dict):
                task_sequence = result.get('final_task_sequence') or result.get('current_task_sequence') or []
            else:
                get = getattr(result, 'get', None)
                if callable(get):
                    task_sequence = result.get('final_task_sequence') or result.get('current_task_sequence') or []
                else:
                    task_sequence = getattr(result, 'final_task_sequence', None) or getattr(result, 'current_task_sequence', None) or []

            self._log_task_interaction_flow(result if isinstance(result, dict) else serial_result if isinstance(serial_result, dict) else {})

            if task_sequence:
                task_msg = String()
                task_msg.data = json.dumps(task_sequence, ensure_ascii=False)
                self.task_pub.publish(task_msg)
                rospy.loginfo("Published task sequence")
        except Exception as e:
            rospy.logwarn(f"Failed to log/publish task sequence: {e}")

    def run(self):
        rospy.spin()


if __name__ == '__main__':
    try:
        node = BlockPlanningNode()
        node.run()
    except rospy.ROSInterruptException:
        pass
    except Exception as e:
        log_error_red(f"Fatal: {e}")
        # print fatal error in red to stderr
        try:
            print(_red(f"Fatal: {e}"), file=sys.stderr)
        except Exception:
            pass
        import sys
        sys.exit(1)