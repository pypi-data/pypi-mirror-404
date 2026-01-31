#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
任务执行模块 - 执行 AI 自动化测试任务
"""

import asyncio
import sys
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, List, Any, Callable

from loguru import logger

# 添加内置 phone_agent 到 path（支持 pip 安装后使用）
_current_dir = os.path.dirname(os.path.abspath(__file__))
_builtin_phone_agent = os.path.join(_current_dir, "phone_agent")
if os.path.exists(_builtin_phone_agent) and _current_dir not in sys.path:
    sys.path.insert(0, _current_dir)

# 同时兼容旧的目录结构
sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

# 导入 phone_agent 相关模块（优先使用内置版本）
try:
    from .phone_agent.model import ModelClient, ModelConfig
    from .phone_agent.model.client import MessageBuilder
    from .phone_agent.device_factory import (
        DeviceType,
        get_device_factory,
        set_device_type,
    )
    from .phone_agent.actions import ActionHandler
    from .phone_agent.actions.handler import parse_action, finish
    from .phone_agent.agent import AgentConfig, StepResult

    PHONE_AGENT_AVAILABLE = True
except ImportError:
    try:
        from phone_agent.model import ModelClient, ModelConfig
        from phone_agent.model.client import MessageBuilder
        from phone_agent.device_factory import (
            DeviceType,
            get_device_factory,
            set_device_type,
        )
        from phone_agent.actions import ActionHandler
        from phone_agent.actions.handler import parse_action, finish
        from phone_agent.agent import AgentConfig, StepResult

        PHONE_AGENT_AVAILABLE = True
    except ImportError as e:
        PHONE_AGENT_AVAILABLE = False
        logger.warning(f"phone_agent 未完全安装: {e}")

# iOS Agent 支持
try:
    from .phone_agent.agent_ios import IOSPhoneAgent, IOSAgentConfig
    from .phone_agent.actions.handler_ios import IOSActionHandler
    from .phone_agent.xctest import (
        get_screenshot as ios_get_screenshot,
        get_current_app as ios_get_current_app,
    )

    IOS_AGENT_AVAILABLE = True
except ImportError:
    try:
        from phone_agent.agent_ios import IOSPhoneAgent, IOSAgentConfig
        from phone_agent.actions.handler_ios import IOSActionHandler
        from phone_agent.xctest import (
            get_screenshot as ios_get_screenshot,
            get_current_app as ios_get_current_app,
        )

        IOS_AGENT_AVAILABLE = True
    except ImportError as e:
        IOS_AGENT_AVAILABLE = False
        logger.warning(f"iOS Agent 未完全安装: {e}")


@dataclass
class TaskStatus:
    """任务状态"""

    task_id: str
    status: str = "pending"
    current_step: int = 0
    max_steps: int = 0
    logs: list = None
    screenshots: list = None
    result: Optional[str] = None
    error: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    last_success_step: int = 0
    last_fail_step: int = 0

    def __post_init__(self):
        if self.logs is None:
            self.logs = []
        if self.screenshots is None:
            self.screenshots = []

    def to_dict(self) -> Dict:
        return {
            "task_id": self.task_id,
            "status": self.status,
            "current_step": self.current_step,
            "max_steps": self.max_steps,
            "logs": self.logs,
            "screenshots": self.screenshots,
            "result": self.result,
            "error": self.error,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "last_success_step": self.last_success_step,
            "last_fail_step": self.last_fail_step,
        }


@dataclass
class BatchTaskStatus:
    """批量任务状态"""

    batch_id: str
    status: str = "pending"
    total_cases: int = 0
    completed_cases: int = 0
    current_case_index: int = 0
    case_results: list = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    scenario_name: str = ""  # 场景名称

    def __post_init__(self):
        if self.case_results is None:
            self.case_results = []

    def to_dict(self) -> Dict:
        return {
            "batch_id": self.batch_id,
            "status": self.status,
            "total_cases": self.total_cases,
            "completed_cases": self.completed_cases,
            "current_case_index": self.current_case_index,
            "case_results": self.case_results,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "scenario_name": self.scenario_name,  # 包含场景名称
        }


class WebPhoneAgent:
    """支持 Web 日志的 Android Agent"""

    def __init__(
        self,
        model_config,
        agent_config,
        task_id: str,
        task_status: TaskStatus,
        broadcast_func: Callable,
        stop_flags: Dict,
        stop_flag_key: str = None,
        config_manager=None,  # 配置管理器（用于保存截图文件）
        batch_id: str = None,  # 批次 ID
        case_id: str = None,   # 用例 ID
    ):
        self.model_config = model_config
        self.agent_config = agent_config
        self.task_id = task_id
        self.task_status = task_status
        self.broadcast = broadcast_func
        self.stop_flags = stop_flags
        self.stop_flag_key = stop_flag_key or task_id
        self.config_manager = config_manager
        self.batch_id = batch_id or task_id
        self.case_id = case_id or task_id

        self.model_client = ModelClient(self.model_config)
        self.action_handler = ActionHandler(device_id=self.agent_config.device_id)

        self._context: list[dict] = []
        self._step_count = 0

    async def log(self, log_type: str, content: str, **kwargs):
        """记录日志并广播"""
        log_entry = {
            "type": log_type,
            "content": content,
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "step": self._step_count,
            **kwargs,
        }
        self.task_status.logs.append(log_entry)
        try:
            await self.broadcast(self.task_id, log_entry)
        except Exception:
            pass  # 广播失败不影响任务执行

    def should_stop(self) -> bool:
        """检查是否应该停止"""
        return self.stop_flags.get(self.stop_flag_key, False)

    async def run(self, task: str) -> str:
        """执行任务"""
        self._context = []
        self._step_count = 0
        max_steps = (
            self.agent_config.max_steps if self.agent_config.max_steps > 0 else 999
        )

        await self.log("info", "🚀 开始执行任务")

        result = await self._execute_step(task, is_first=True)

        if result.finished or self.should_stop():
            if result.finished:
                self.task_status.last_success_step = self._step_count
            return result.message or "任务完成"

        while self._step_count < max_steps:
            if self.should_stop():
                await self.log("info", "⏹️ 任务已被用户中断")
                return f"任务中断于第 {self._step_count} 步"

            result = await self._execute_step(is_first=False)

            if result.finished:
                self.task_status.last_success_step = self._step_count
                return result.message or "任务完成"

        return "已达到最大步数限制"

    async def _execute_step(
        self, user_prompt: str = None, is_first: bool = False
    ) -> StepResult:
        """执行单步"""
        self._step_count += 1
        self.task_status.current_step = self._step_count

        max_display = (
            self.agent_config.max_steps if self.agent_config.max_steps > 0 else "∞"
        )
        await self.log("step", f"📍 步骤 {self._step_count}/{max_display}")

        device_factory = get_device_factory()
        screenshot = device_factory.get_screenshot(self.agent_config.device_id)
        current_app = device_factory.get_current_app(self.agent_config.device_id)

        # 保存截图到文件（如果有 config_manager）
        image_path = ""
        if self.config_manager and screenshot.base64_data:
            image_path = self.config_manager.save_screenshot(
                self.batch_id, self.case_id, self._step_count, screenshot.base64_data
            )

        self.task_status.screenshots.append(
            {
                "step": self._step_count,
                "image": image_path,  # 存储文件路径而不是 base64
                "width": screenshot.width,
                "height": screenshot.height,
                "timestamp": datetime.now().isoformat(),
                "app": current_app,
            }
        )

        await self.log(
            "screenshot",
            "📷 截图已捕获",
            image=image_path,  # 发送文件路径
            width=screenshot.width,
            height=screenshot.height,
            app=current_app,
        )

        if is_first:
            self._context.append(
                MessageBuilder.create_system_message(self.agent_config.system_prompt)
            )
            screen_info = MessageBuilder.build_screen_info(current_app)
            text_content = f"{user_prompt}\n\n{screen_info}"
            self._context.append(
                MessageBuilder.create_user_message(
                    text=text_content, image_base64=screenshot.base64_data
                )
            )
        else:
            screen_info = MessageBuilder.build_screen_info(current_app)
            text_content = f"** Screen Info **\n\n{screen_info}"
            self._context.append(
                MessageBuilder.create_user_message(
                    text=text_content, image_base64=screenshot.base64_data
                )
            )

        try:
            await self.log("info", "🤖 正在调用 AI 模型...")
            response = await asyncio.to_thread(self.model_client.request, self._context)

            metrics = {
                "ttft": response.time_to_first_token,
                "thinking_time": response.time_to_thinking_end,
                "total_time": response.total_time,
            }
            await self.log("metrics", "⏱️ 性能指标", **metrics)

            if response.thinking:
                await self.log("thinking", f"💭 {response.thinking}")

        except Exception as e:
            await self.log("error", f"❌ 模型调用失败: {e}")
            self.task_status.last_fail_step = self._step_count
            return StepResult(
                success=False,
                finished=True,
                action=None,
                thinking="",
                message=f"模型错误: {e}",
            )

        try:
            action = parse_action(response.action)
        except ValueError:
            action = finish(message=response.action)

        await self.log("action", "🎯 执行动作", action=action)

        self._context[-1] = MessageBuilder.remove_images_from_message(self._context[-1])

        try:
            result = self.action_handler.execute(
                action, screenshot.width, screenshot.height
            )
        except Exception as e:
            await self.log("error", f"❌ 动作执行失败: {e}")
            self.task_status.last_fail_step = self._step_count
            result = self.action_handler.execute(
                finish(message=str(e)), screenshot.width, screenshot.height
            )

        self._context.append(
            MessageBuilder.create_assistant_message(
                f"<think>{response.thinking}</think><answer>{response.action}</answer>"
            )
        )

        finished = action.get("_metadata") == "finish" or result.should_finish

        if finished:
            final_msg = result.message or action.get("message", "完成")
            await self.log("success", f"✅ {final_msg}")

        return StepResult(
            success=result.success,
            finished=finished,
            action=action,
            thinking=response.thinking,
            message=result.message or action.get("message"),
        )


class WebIOSPhoneAgent:
    """支持 Web 日志的 iOS Agent"""

    def __init__(
        self,
        model_config,
        wda_url: str,
        device_id: str,
        max_steps: int,
        lang: str,
        task_id: str,
        task_status: TaskStatus,
        broadcast_func: Callable,
        stop_flags: Dict,
        stop_flag_key: str = None,
    ):
        self.model_config = model_config
        self.wda_url = wda_url
        self.device_id = device_id
        self.max_steps = max_steps
        self.lang = lang
        self.task_id = task_id
        self.task_status = task_status
        self.broadcast = broadcast_func
        self.stop_flags = stop_flags
        self.stop_flag_key = stop_flag_key or task_id

        self.model_client = ModelClient(self.model_config)

        if IOS_AGENT_AVAILABLE:
            self.action_handler = IOSActionHandler(wda_url=wda_url, session_id=None)
        else:
            raise RuntimeError("iOS Agent 不可用，请安装相关依赖")

        self._context: list[dict] = []
        self._step_count = 0

        try:
            from .phone_agent.config import get_system_prompt
        except ImportError:
            from phone_agent.config import get_system_prompt
        self.system_prompt = get_system_prompt(lang)

    async def log(self, log_type: str, content: str, **kwargs):
        """记录日志并广播"""
        log_entry = {
            "type": log_type,
            "content": content,
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "step": self._step_count,
            **kwargs,
        }
        self.task_status.logs.append(log_entry)
        try:
            await self.broadcast(self.task_id, log_entry)
        except Exception:
            pass  # 广播失败不影响任务执行

    def should_stop(self) -> bool:
        return self.stop_flags.get(self.stop_flag_key, False)

    async def run(self, task: str) -> str:
        """执行 iOS 任务"""
        self._context = []
        self._step_count = 0
        max_steps = self.max_steps if self.max_steps > 0 else 999

        await self.log("info", "🚀 开始执行 iOS 任务")

        result = await self._execute_step(task, is_first=True)

        if result.finished or self.should_stop():
            if result.finished:
                self.task_status.last_success_step = self._step_count
            return result.message or "任务完成"

        while self._step_count < max_steps:
            if self.should_stop():
                await self.log("info", "⏹️ 任务已被用户中断")
                return f"任务中断于第 {self._step_count} 步"

            result = await self._execute_step(is_first=False)

            if result.finished:
                self.task_status.last_success_step = self._step_count
                return result.message or "任务完成"

        return "已达到最大步数限制"

    async def _execute_step(
        self, user_prompt: str = None, is_first: bool = False
    ) -> StepResult:
        """执行单步"""
        self._step_count += 1
        self.task_status.current_step = self._step_count

        max_display = self.max_steps if self.max_steps > 0 else "∞"
        await self.log("step", f"📍 步骤 {self._step_count}/{max_display}")

        try:
            screenshot = ios_get_screenshot(
                wda_url=self.wda_url,
                session_id=None,
                device_id=self.device_id,
            )
            current_app = ios_get_current_app(wda_url=self.wda_url, session_id=None)
        except Exception as e:
            await self.log("error", f"❌ iOS 截图失败: {e}")
            return StepResult(
                success=False,
                finished=True,
                action=None,
                thinking="",
                message=f"iOS 截图失败: {e}",
            )

        self.task_status.screenshots.append(
            {
                "step": self._step_count,
                "image": screenshot.base64_data,
                "width": screenshot.width,
                "height": screenshot.height,
                "timestamp": datetime.now().isoformat(),
                "app": current_app,
            }
        )

        await self.log(
            "screenshot",
            "📷 iOS 截图已捕获",
            image=screenshot.base64_data,
            width=screenshot.width,
            height=screenshot.height,
            app=current_app,
        )

        if is_first:
            self._context.append(
                MessageBuilder.create_system_message(self.system_prompt)
            )
            screen_info = MessageBuilder.build_screen_info(current_app)
            text_content = f"{user_prompt}\n\n{screen_info}"
            self._context.append(
                MessageBuilder.create_user_message(
                    text=text_content, image_base64=screenshot.base64_data
                )
            )
        else:
            screen_info = MessageBuilder.build_screen_info(current_app)
            text_content = f"** Screen Info **\n\n{screen_info}"
            self._context.append(
                MessageBuilder.create_user_message(
                    text=text_content, image_base64=screenshot.base64_data
                )
            )

        try:
            await self.log("info", "🤖 正在调用 AI 模型...")
            response = await asyncio.to_thread(self.model_client.request, self._context)

            metrics = {
                "ttft": response.time_to_first_token,
                "thinking_time": response.time_to_thinking_end,
                "total_time": response.total_time,
            }
            await self.log("metrics", "⏱️ 性能指标", **metrics)

            if response.thinking:
                await self.log("thinking", f"💭 {response.thinking}")

        except Exception as e:
            await self.log("error", f"❌ 模型调用失败: {e}")
            self.task_status.last_fail_step = self._step_count
            return StepResult(
                success=False,
                finished=True,
                action=None,
                thinking="",
                message=f"模型错误: {e}",
            )

        try:
            action = parse_action(response.action)
        except ValueError:
            action = finish(message=response.action)

        await self.log("action", "🎯 执行 iOS 动作", action=action)

        self._context[-1] = MessageBuilder.remove_images_from_message(self._context[-1])

        try:
            result = self.action_handler.execute(
                action, screenshot.width, screenshot.height
            )
        except Exception as e:
            await self.log("error", f"❌ iOS 动作执行失败: {e}")
            self.task_status.last_fail_step = self._step_count
            result = self.action_handler.execute(
                finish(message=str(e)), screenshot.width, screenshot.height
            )

        self._context.append(
            MessageBuilder.create_assistant_message(
                f"<think>{response.thinking}</think><answer>{response.action}</answer>"
            )
        )

        finished = action.get("_metadata") == "finish" or result.should_finish

        if finished:
            final_msg = result.message or action.get("message", "完成")
            await self.log("success", f"✅ {final_msg}")

        return StepResult(
            success=result.success,
            finished=finished,
            action=action,
            thinking=response.thinking,
            message=result.message or action.get("message"),
        )


class TaskRunner:
    """任务执行器"""

    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.tasks: Dict[str, TaskStatus] = {}
        self.batch_tasks: Dict[str, BatchTaskStatus] = {}
        self.stop_flags: Dict[str, bool] = {}
        self.active_connections: Dict[str, list] = {}

    def _is_error_result(self, result: str) -> bool:
        """判断结果是否包含错误信息"""
        if not result:
            return False

        result_lower = result.lower()
        error_keywords = [
            "错误",
            "失败",
            "error",
            "fail",
            "exception",
            "异常",
            "超时",
            "timeout",
            "无法",
            "不能",
            "未找到",
            "not found",
            "连接失败",
            "模型错误",
            "调用失败",
            "执行失败",
            "list.remove",
            "keyerror",
            "indexerror",
            "valueerror",
            "typeerror",
            "attributeerror",
            "runtimeerror",
        ]

        for keyword in error_keywords:
            if keyword.lower() in result_lower:
                return True

        return False

    async def broadcast_log(self, task_id: str, log_entry: dict):
        """广播日志到 WebSocket 连接"""
        if task_id in self.active_connections:
            disconnected = []
            for ws in self.active_connections[task_id]:
                try:
                    await ws.send_json(log_entry)
                except:
                    disconnected.append(ws)
            # 安全移除断开的连接
            for ws in disconnected:
                try:
                    if ws in self.active_connections.get(task_id, []):
                        self.active_connections[task_id].remove(ws)
                except (ValueError, KeyError):
                    pass  # 忽略移除错误

    async def run_task(
        self,
        task_id: str,
        device_id: str,
        task: str,
        platform: str,
        base_url: str,
        model: str,
        api_key: str,
        max_steps: int,
        lang: str,
        wda_url: str = None,
        api_config_id: str = None,
    ) -> TaskStatus:
        """执行单个任务"""
        task_status = TaskStatus(task_id=task_id, max_steps=max_steps)
        task_status.status = "running"
        task_status.start_time = datetime.now().isoformat()
        self.tasks[task_id] = task_status
        self.stop_flags[task_id] = False

        try:
            # 获取 API 配置
            if api_config_id:
                api_config = self.config_manager.get_api_config(api_config_id)
                if api_config:
                    base_url = api_config["base_url"]
                    model = api_config["model"]
                    api_key = api_config["api_key"]

            model_config = ModelConfig(
                base_url=base_url,
                api_key=api_key,
                model_name=model,
                lang=lang,
            )

            if platform == "ios":
                if not IOS_AGENT_AVAILABLE:
                    raise RuntimeError("iOS Agent 不可用")

                if not wda_url:
                    wda_url = self.config_manager.get_ios_wda_config(device_id)
                if not wda_url:
                    raise RuntimeError("iOS 设备需要配置 WDA URL")

                agent = WebIOSPhoneAgent(
                    model_config=model_config,
                    wda_url=wda_url,
                    device_id=device_id,
                    max_steps=max_steps,
                    lang=lang,
                    task_id=task_id,
                    task_status=task_status,
                    broadcast_func=self.broadcast_log,
                    stop_flags=self.stop_flags,
                )
            else:
                set_device_type(DeviceType.ADB)

                agent_config = AgentConfig(
                    max_steps=max_steps,
                    device_id=device_id,
                    verbose=True,
                    lang=lang,
                )

                agent = WebPhoneAgent(
                    model_config=model_config,
                    agent_config=agent_config,
                    task_id=task_id,
                    task_status=task_status,
                    broadcast_func=self.broadcast_log,
                    stop_flags=self.stop_flags,
                    config_manager=self.config_manager,
                    batch_id=task_id,
                    case_id=task_id,
                )

            result = await agent.run(task)

            if self.stop_flags.get(task_id, False):
                task_status.status = "stopped"
            else:
                task_status.status = "success"
            task_status.result = result

            await self.broadcast_log(
                task_id,
                {
                    "type": "complete",
                    "status": task_status.status,
                    "result": result,
                    "timestamp": datetime.now().strftime("%H:%M:%S"),
                },
            )

        except Exception as e:
            task_status.status = "failed"
            task_status.error = str(e)
            await self.broadcast_log(
                task_id,
                {
                    "type": "error",
                    "content": str(e),
                    "timestamp": datetime.now().strftime("%H:%M:%S"),
                },
            )

        finally:
            task_status.end_time = datetime.now().isoformat()

            # 保存到历史记录
            single_batch_status = {
                "batch_id": task_id,
                "status": task_status.status,
                "total_cases": 1,
                "completed_cases": 1,
                "start_time": task_status.start_time,
                "end_time": task_status.end_time,
                "case_results": [
                    {
                        "case_id": task_id,
                        "case_name": task[:50] + "..." if len(task) > 50 else task,
                        "status": task_status.status,
                        "result": task_status.result or task_status.error or "",
                        "logs": task_status.logs.copy(),
                        "screenshots": task_status.screenshots.copy(),
                        "start_time": task_status.start_time,
                        "end_time": task_status.end_time,
                        "last_success_step": task_status.last_success_step,
                        "last_fail_step": task_status.last_fail_step,
                    }
                ],
            }
            self.config_manager.add_history_record(task_id, single_batch_status)

            if task_id in self.stop_flags:
                del self.stop_flags[task_id]

        return task_status

    async def run_batch_task(
        self,
        batch_id: str,
        device_id: str,
        test_cases: List[Dict],
        platform: str,
        base_url: str,
        model: str,
        api_key: str,
        max_steps: int,
        lang: str,
        wda_url: str = None,
        api_config_id: str = None,
        scenario_name: str = "",
    ) -> BatchTaskStatus:
        """执行批量任务"""
        batch_status = BatchTaskStatus(
            batch_id=batch_id,
            total_cases=len(test_cases),
        )
        batch_status.status = "running"
        batch_status.start_time = datetime.now().isoformat()
        batch_status.scenario_name = scenario_name  # 保存场景名称
        self.batch_tasks[batch_id] = batch_status
        self.stop_flags[batch_id] = False

        try:
            # 获取 API 配置
            if api_config_id:
                api_config = self.config_manager.get_api_config(api_config_id)
                if api_config:
                    base_url = api_config["base_url"]
                    model = api_config["model"]
                    api_key = api_config["api_key"]

            if platform == "ios":
                if not wda_url:
                    wda_url = self.config_manager.get_ios_wda_config(device_id)
            else:
                set_device_type(DeviceType.ADB)

            for i, test_case in enumerate(test_cases):
                if self.stop_flags.get(batch_id, False):
                    break

                batch_status.current_case_index = i

                task_id = f"{batch_id}_case_{i}"
                task_status = TaskStatus(task_id=task_id, max_steps=max_steps)
                self.tasks[task_id] = task_status

                await self.broadcast_log(
                    batch_id,
                    {
                        "type": "case_start",
                        "case_index": i,
                        "case_name": test_case.get("name", f"用例{i+1}"),
                        "total_cases": len(test_cases),
                        "timestamp": datetime.now().strftime("%H:%M:%S"),
                    },
                )

                model_config = ModelConfig(
                    base_url=base_url,
                    api_key=api_key,
                    model_name=model,
                    lang=lang,
                )

                if platform == "ios":
                    agent = WebIOSPhoneAgent(
                        model_config=model_config,
                        wda_url=wda_url,
                        device_id=device_id,
                        max_steps=max_steps,
                        lang=lang,
                        task_id=batch_id,
                        task_status=task_status,
                        broadcast_func=self.broadcast_log,
                        stop_flags=self.stop_flags,
                        stop_flag_key=batch_id,
                    )
                else:
                    agent_config = AgentConfig(
                        max_steps=max_steps,
                        device_id=device_id,
                        verbose=True,
                        lang=lang,
                    )

                    case_id = test_case.get("id", f"case_{i}")
                    agent = WebPhoneAgent(
                        model_config=model_config,
                        agent_config=agent_config,
                        task_id=batch_id,
                        task_status=task_status,
                        broadcast_func=self.broadcast_log,
                        stop_flags=self.stop_flags,
                        stop_flag_key=batch_id,
                        config_manager=self.config_manager,
                        batch_id=batch_id,
                        case_id=case_id,
                    )

                try:
                    result = await agent.run(test_case.get("description", ""))

                    # 判断用例成功/失败的多重逻辑
                    if self.stop_flags.get(batch_id, False):
                        case_status = "stopped"
                    elif (
                        task_status.last_fail_step is not None
                        and task_status.last_fail_step > 0
                    ):
                        # 如果有失败步骤，标记为失败
                        case_status = "failed"
                    elif self._is_error_result(result):
                        # 如果结果包含错误关键词，标记为失败
                        case_status = "failed"
                    else:
                        case_status = "success"

                except Exception as e:
                    result = str(e)
                    case_status = "failed"

                case_result = {
                    "case_id": test_case.get("id"),
                    "case_name": test_case.get("name", f"用例{i+1}"),
                    "status": case_status,
                    "result": result,
                    "logs": task_status.logs.copy(),
                    "screenshots": task_status.screenshots.copy(),
                    "start_time": task_status.start_time,
                    "end_time": datetime.now().isoformat(),
                    "last_success_step": task_status.last_success_step,
                    "last_fail_step": task_status.last_fail_step,
                }
                batch_status.case_results.append(case_result)
                batch_status.completed_cases = i + 1

                await self.broadcast_log(
                    batch_id,
                    {
                        "type": "case_complete",
                        "case_index": i,
                        "case_name": test_case.get("name", f"用例{i+1}"),
                        "status": case_status,
                        "result": result,
                        "timestamp": datetime.now().strftime("%H:%M:%S"),
                    },
                )

                if self.stop_flags.get(batch_id, False):
                    break

            batch_status.status = (
                "stopped" if self.stop_flags.get(batch_id, False) else "completed"
            )

            await self.broadcast_log(
                batch_id,
                {
                    "type": "batch_complete",
                    "status": batch_status.status,
                    "completed_cases": batch_status.completed_cases,
                    "total_cases": batch_status.total_cases,
                    "timestamp": datetime.now().strftime("%H:%M:%S"),
                },
            )

        except Exception as e:
            batch_status.status = "failed"
            await self.broadcast_log(
                batch_id,
                {
                    "type": "error",
                    "content": str(e),
                    "timestamp": datetime.now().strftime("%H:%M:%S"),
                },
            )

        finally:
            batch_status.end_time = datetime.now().isoformat()
            self.config_manager.add_history_record(
                batch_id,
                batch_status.to_dict(),
                scenario_name=getattr(batch_status, "scenario_name", ""),
            )
            if batch_id in self.stop_flags:
                del self.stop_flags[batch_id]

        return batch_status

    def stop_task(self, task_id: str):
        """停止任务"""
        self.stop_flags[task_id] = True
        if task_id in self.tasks:
            self.tasks[task_id].status = "stopped"
        if task_id in self.batch_tasks:
            self.batch_tasks[task_id].status = "stopped"

    def get_task_status(self, task_id: str) -> Optional[Dict]:
        """获取任务状态"""
        if task_id in self.tasks:
            return self.tasks[task_id].to_dict()
        if task_id in self.batch_tasks:
            return self.batch_tasks[task_id].to_dict()
        return None
