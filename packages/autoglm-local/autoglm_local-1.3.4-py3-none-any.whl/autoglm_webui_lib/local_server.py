#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
本地端服务 - 运行在本地机器，负责设备操作和任务执行

启动时主动向服务端注册，定期发送心跳
"""

import asyncio
import base64
import os
import subprocess
import sys
import uuid
import socket
import threading
import time
from datetime import datetime
from typing import Optional

import httpx
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
from loguru import logger

# 添加父目录到 path
sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from .device_manager import DeviceManager, ADBUTILS_AVAILABLE, TIDEVICE_AVAILABLE
from .config_manager import ConfigManager
from .task_runner import TaskRunner

# 创建 FastAPI 应用
app = FastAPI(title="AutoGLM 本地端服务", version="1.0.0")

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化管理器
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

device_manager = DeviceManager()
config_manager = ConfigManager(DATA_DIR)
task_runner = TaskRunner(config_manager)

# iOS WDA 配置
ios_wda_configs = config_manager.load_ios_wda_configs()
IOS_SCALE_FACTOR = 3

# 服务端注册配置
SERVER_URL = os.environ.get("SERVER_URL", "http://qa.local:8792")  # 默认服务端地址
LOCAL_PORT = int(os.environ.get("LOCAL_PORT", "8793"))
LOCAL_NAME = os.environ.get("LOCAL_NAME", socket.gethostname())
HEARTBEAT_INTERVAL = 30  # 心跳间隔（秒）

# 全局变量
_server_url = SERVER_URL
_registered = False


def get_local_ip():
    """获取本机局域网 IP（跳过 VPN）"""
    import subprocess
    import re

    # 方法1: 使用 scutil 获取主要网络服务的 IP (macOS)
    try:
        # 获取主要网络服务
        result = subprocess.run(
            ["scutil", "--nwi"], capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            # 查找 IPv4 地址，排除 VPN 接口
            for line in result.stdout.split("\n"):
                if "address" in line.lower() and ":" in line:
                    ip = line.split(":")[-1].strip()
                    # 排除 VPN 常见 IP 段
                    if (
                        ip
                        and not ip.startswith("198.18.")
                        and not ip.startswith("10.8.")
                        and not ip.startswith("100.")
                    ):
                        if (
                            ip.startswith("192.168.")
                            or ip.startswith("10.")
                            or ip.startswith("172.")
                        ):
                            return ip
    except:
        pass

    # 方法2: 使用 ifconfig 查找 en0/en1 (WiFi/以太网) 的 IP
    try:
        result = subprocess.run(["ifconfig"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            # 查找 en0 或 en1 的 IP
            current_interface = None
            for line in result.stdout.split("\n"):
                if line and not line.startswith("\t") and not line.startswith(" "):
                    current_interface = line.split(":")[0]
                if current_interface in ["en0", "en1", "en2"]:
                    match = re.search(r"inet (\d+\.\d+\.\d+\.\d+)", line)
                    if match:
                        ip = match.group(1)
                        if not ip.startswith("127."):
                            return ip
    except:
        pass

    # 方法3: 使用 route 获取默认网关对应的 IP
    try:
        result = subprocess.run(
            ["route", "-n", "get", "default"], capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            for line in result.stdout.split("\n"):
                if "interface:" in line.lower():
                    interface = line.split(":")[-1].strip()
                    # 获取该接口的 IP
                    if_result = subprocess.run(
                        ["ipconfig", "getifaddr", interface],
                        capture_output=True,
                        text=True,
                        timeout=5,
                    )
                    if if_result.returncode == 0:
                        ip = if_result.stdout.strip()
                        if ip and not ip.startswith("198.18."):
                            return ip
    except:
        pass

    # 方法4: 回退到原来的方法（可能返回 VPN IP）
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        pass

    return "127.0.0.1"


async def register_to_server():
    """向服务端注册本地端"""
    global _registered

    if not _server_url:
        logger.info("未配置服务端地址，跳过注册")
        return

    # 判断服务端是否在本地，如果是则使用 localhost
    if "localhost" in _server_url or "127.0.0.1" in _server_url:
        local_ip = "127.0.0.1"
    else:
        local_ip = get_local_ip()

    devices = device_manager.list_all_devices()

    register_data = {
        "name": LOCAL_NAME,
        "ip": local_ip,
        "port": LOCAL_PORT,
        "devices": devices,
        "ios_support": TIDEVICE_AVAILABLE,
        "adb_support": ADBUTILS_AVAILABLE,
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{_server_url}/local/register", json=register_data
            )
            if response.status_code == 200:
                _registered = True
                logger.info(f"✅ 已注册到服务端: {_server_url} (本地端IP: {local_ip})")
            else:
                logger.error(f"❌ 注册失败: {response.status_code}")
    except Exception as e:
        logger.error(f"❌ 无法连接服务端: {e}")


async def heartbeat_loop():
    """心跳循环，定期向服务端报告状态"""
    global _registered

    while True:
        await asyncio.sleep(HEARTBEAT_INTERVAL)

        if not _server_url:
            continue

        # 判断服务端是否在本地，如果是则使用 localhost
        if "localhost" in _server_url or "127.0.0.1" in _server_url:
            local_ip = "127.0.0.1"
        else:
            local_ip = get_local_ip()

        devices = device_manager.list_all_devices()

        heartbeat_data = {
            "name": LOCAL_NAME,
            "ip": local_ip,
            "port": LOCAL_PORT,
            "devices": devices,
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{_server_url}/local/heartbeat", json=heartbeat_data
                )
                if response.status_code == 200:
                    _registered = True
                else:
                    _registered = False
        except Exception as e:
            _registered = False
            logger.warning(f"心跳发送失败: {e}")


@app.on_event("startup")
async def startup_event():
    """启动时注册到服务端"""
    await register_to_server()
    asyncio.create_task(heartbeat_loop())


# ============== 数据模型 ==============


class TaskRequest(BaseModel):
    device_id: str
    task: str
    platform: str = "android"
    wda_url: str = ""
    api_config_id: str = ""
    base_url: str = "https://open.bigmodel.cn/api/paas/v4"
    model: str = "autoglm-phone"
    api_key: str = ""
    max_steps: int = 0
    lang: str = "cn"


class BatchTaskRequest(BaseModel):
    device_id: str
    test_cases: list
    platform: str = "android"
    wda_url: str = ""
    api_config_id: str = ""
    base_url: str = "https://open.bigmodel.cn/api/paas/v4"
    model: str = "autoglm-phone"
    api_key: str = ""
    max_steps: int = 0
    lang: str = "cn"
    scenario_name: str = ""  # 场景名称，用于历史记录命名


class RemoteControlAction(BaseModel):
    action: str
    x: Optional[int] = None
    y: Optional[int] = None
    x2: Optional[int] = None
    y2: Optional[int] = None
    duration: Optional[int] = 300
    keycode: Optional[int] = None
    text: Optional[str] = None


class IOSWDAConfig(BaseModel):
    wda_url: str


# ============== 系统信息 ==============


@app.get("/")
async def root():
    return {
        "message": "AutoGLM 本地端服务运行中",
        "version": "1.0.0",
        "name": LOCAL_NAME,
        "registered": _registered,
        "server_url": _server_url,
    }


@app.get("/system/info")
async def get_system_info():
    return {
        "version": "1.0.0",
        "name": LOCAL_NAME,
        "ip": get_local_ip(),
        "port": LOCAL_PORT,
        "ios_support": TIDEVICE_AVAILABLE,
        "adbutils_support": ADBUTILS_AVAILABLE,
        "scrcpy_support": check_scrcpy_available(),
        "registered": _registered,
        "server_url": _server_url,
    }


@app.get("/system_check")
async def system_check():
    checks = {
        "adb": False,
        "devices": [],
        "ios": TIDEVICE_AVAILABLE,
        "scrcpy": check_scrcpy_available(),
        "name": LOCAL_NAME,
        "ip": get_local_ip(),
    }
    try:
        result = subprocess.run(
            ["adb", "version"], capture_output=True, text=True, timeout=5
        )
        checks["adb"] = result.returncode == 0
    except:
        pass
    checks["devices"] = device_manager.list_all_devices()
    return checks


def check_scrcpy_available():
    try:
        result = subprocess.run(
            ["scrcpy", "--version"], capture_output=True, text=True, timeout=5
        )
        return result.returncode == 0
    except:
        return False


# ============== 设备管理 ==============


@app.get("/devices")
async def get_devices():
    return device_manager.list_all_devices()


@app.get("/devices/android")
async def get_android_devices():
    return device_manager.list_android_devices()


@app.get("/devices/ios")
async def get_ios_devices():
    return device_manager.list_ios_devices()


# ============== 截图 ==============


@app.get("/screenshot/{device_id}")
async def get_screenshot(device_id: str):
    try:
        # 获取设备平台
        platform = device_manager.get_device_platform(device_id)

        if platform == "android":
            screenshot_data = device_manager.get_screenshot_android(device_id)
        elif platform == "ios":
            screenshot_data = device_manager.get_screenshot_ios(device_id)
        else:
            raise HTTPException(status_code=400, detail=f"未知设备: {device_id}")

        if screenshot_data:
            b64_data = base64.b64encode(screenshot_data).decode()
            width, height = device_manager.get_screen_size(device_id)
            return {
                "status": "success",
                "image": b64_data,
                "width": width,
                "height": height,
                "timestamp": datetime.now().isoformat(),
            }
        raise HTTPException(status_code=500, detail="截图失败")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/remote/screen/{device_id}")
async def get_remote_screen(device_id: str):
    try:
        screenshot_data = device_manager.get_screenshot_android(device_id)
        if screenshot_data:
            b64_data = base64.b64encode(screenshot_data).decode()
            width, height = device_manager.get_screen_size(device_id)
            return {
                "status": "success",
                "image": b64_data,
                "width": width,
                "height": height,
            }
        raise HTTPException(status_code=500, detail="截图失败")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============== 截图文件访问 ==============

@app.get("/data/screenshots/{batch_id}/{filename}")
async def get_screenshot_file(batch_id: str, filename: str):
    """获取截图文件"""
    filepath = config_manager.get_screenshot_path(f"screenshots/{batch_id}/{filename}")
    if os.path.exists(filepath):
        return FileResponse(filepath, media_type="image/png")
    raise HTTPException(status_code=404, detail="截图文件不存在")


# ============== 输入法管理 ==============


@app.get("/input_methods/{device_id}")
async def get_device_input_methods(device_id: str):
    try:
        result = device_manager.get_input_methods(device_id)
        return result
    except Exception as e:
        logger.error(f"获取输入法列表失败: {e}")
        return {"imes": [], "current": "", "error": str(e)}


@app.post("/switch_ime/{device_id}")
async def switch_device_ime(device_id: str, ime: str = Form(...)):
    if device_manager.switch_input_method(device_id, ime):
        return {"status": "success"}
    raise HTTPException(status_code=500, detail="切换输入法失败")


# ============== 远程控制 ==============


@app.post("/remote/action/{device_id}")
async def remote_action(device_id: str, action: RemoteControlAction):
    result = device_manager.execute_adb_action(
        device_id,
        action.action,
        x=action.x,
        y=action.y,
        x2=action.x2,
        y2=action.y2,
        duration=action.duration,
        keycode=action.keycode,
        text=action.text,
    )

    if result["status"] == "success":
        return result
    raise HTTPException(status_code=500, detail=result.get("message", "操作失败"))


@app.websocket("/ws/remote/{device_id}")
async def remote_control_ws(websocket: WebSocket, device_id: str):
    await websocket.accept()

    stop_flag = {"stop": False}

    async def screen_stream():
        while not stop_flag["stop"]:
            try:
                screenshot_data = device_manager.get_screenshot_android(device_id)
                if screenshot_data:
                    b64_data = base64.b64encode(screenshot_data).decode()
                    await websocket.send_json(
                        {
                            "type": "screen",
                            "image": b64_data,
                            "timestamp": datetime.now().isoformat(),
                        }
                    )
                await asyncio.sleep(0.1)
            except Exception as e:
                logger.error(f"Screen stream error: {e}")
                await asyncio.sleep(0.5)

    stream_task = asyncio.create_task(screen_stream())

    try:
        while True:
            data = await websocket.receive_json()
            action_type = data.get("action")

            result = device_manager.execute_adb_action(
                device_id,
                action_type,
                x=data.get("x"),
                y=data.get("y"),
                x2=data.get("x2") or data.get("x1"),
                y2=data.get("y2") or data.get("y1"),
                duration=data.get("duration", 300),
                keycode=data.get("keycode"),
                text=data.get("text"),
            )

            await websocket.send_json({"type": "ack", "action": action_type})

    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"Remote control error: {e}")
    finally:
        stop_flag["stop"] = True
        stream_task.cancel()
        try:
            await stream_task
        except asyncio.CancelledError:
            pass


# ============== iOS WDA 配置 ==============


@app.post("/ios/wda/config/{device_id}")
async def set_ios_wda_config(device_id: str, config: IOSWDAConfig):
    config_manager.set_ios_wda_config(device_id, config.wda_url)
    ios_wda_configs[device_id] = config.wda_url.rstrip("/")
    return {"status": "success", "wda_url": config.wda_url}


@app.get("/ios/wda/config/{device_id}")
async def get_ios_wda_config(device_id: str):
    wda_url = config_manager.get_ios_wda_config(device_id)
    return {"wda_url": wda_url}


@app.get("/ios/wda/status/{device_id}")
async def check_ios_wda_status(device_id: str):
    wda_url = ios_wda_configs.get(device_id)
    if not wda_url:
        return {"ready": False, "error": "未配置 WDA URL"}

    try:
        import requests

        response = requests.get(f"{wda_url}/status", timeout=5, verify=False)
        if response.status_code == 200:
            data = response.json()
            return {"ready": True, "status": data}
        return {"ready": False, "error": f"状态码: {response.status_code}"}
    except Exception as e:
        return {"ready": False, "error": str(e)}


@app.get("/ios/remote/screen/{device_id}")
async def get_ios_remote_screen(device_id: str):
    wda_url = ios_wda_configs.get(device_id)
    if not wda_url:
        raise HTTPException(status_code=400, detail="请先配置 WDA URL")

    try:
        import requests

        response = requests.get(f"{wda_url}/screenshot", timeout=30, verify=False)

        if response.status_code == 200:
            data = response.json()
            b64_image = data.get("value", "")

            size_response = requests.get(
                f"{wda_url}/session/0/window/size", timeout=5, verify=False
            )
            width, height = 390, 844
            if size_response.status_code == 200:
                size_data = size_response.json()
                value = size_data.get("value", {})
                width = int(value.get("width", 390) * IOS_SCALE_FACTOR)
                height = int(value.get("height", 844) * IOS_SCALE_FACTOR)

            return {
                "status": "success",
                "image": b64_image,
                "width": width,
                "height": height,
            }
        raise HTTPException(status_code=500, detail=f"截图失败: {response.status_code}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ios/remote/action/{device_id}")
async def ios_remote_action(device_id: str, action: RemoteControlAction):
    wda_url = ios_wda_configs.get(device_id)
    if not wda_url:
        raise HTTPException(status_code=400, detail="请先配置 WDA URL")

    try:
        import requests

        if action.action == "tap":
            url = f"{wda_url}/session/0/actions"
            payload = {
                "actions": [
                    {
                        "type": "pointer",
                        "id": "finger1",
                        "parameters": {"pointerType": "touch"},
                        "actions": [
                            {
                                "type": "pointerMove",
                                "duration": 0,
                                "x": action.x / IOS_SCALE_FACTOR,
                                "y": action.y / IOS_SCALE_FACTOR,
                            },
                            {"type": "pointerDown", "button": 0},
                            {"type": "pause", "duration": 100},
                            {"type": "pointerUp", "button": 0},
                        ],
                    }
                ]
            }
            requests.post(url, json=payload, timeout=10, verify=False)

        elif action.action == "swipe":
            url = f"{wda_url}/session/0/wda/dragfromtoforduration"
            duration = (action.duration or 300) / 1000
            payload = {
                "fromX": action.x / IOS_SCALE_FACTOR,
                "fromY": action.y / IOS_SCALE_FACTOR,
                "toX": action.x2 / IOS_SCALE_FACTOR,
                "toY": action.y2 / IOS_SCALE_FACTOR,
                "duration": duration,
            }
            requests.post(url, json=payload, timeout=10, verify=False)

        elif action.action == "back":
            url = f"{wda_url}/session/0/wda/dragfromtoforduration"
            payload = {
                "fromX": 0,
                "fromY": 400,
                "toX": 200,
                "toY": 400,
                "duration": 0.3,
            }
            requests.post(url, json=payload, timeout=10, verify=False)

        elif action.action == "home":
            requests.post(f"{wda_url}/wda/homescreen", timeout=10, verify=False)

        elif action.action == "text":
            url = f"{wda_url}/session/0/element/0/value"
            payload = {"value": list(action.text or "")}
            requests.post(url, json=payload, timeout=10, verify=False)

        else:
            raise HTTPException(
                status_code=400, detail=f"iOS 不支持的动作: {action.action}"
            )

        return {"status": "success"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============== 任务执行 ==============


@app.post("/run_task")
async def run_task(request: TaskRequest):
    if request.platform != "ios":
        is_adb_keyboard, current_ime = device_manager.check_adb_keyboard(
            request.device_id
        )
        if not is_adb_keyboard:
            raise HTTPException(
                status_code=400,
                detail=f"当前输入法不是 ADB Keyboard！\n当前: {current_ime}\n\n请在「输入法管理」中切换。",
            )
    else:
        wda_url = request.wda_url or config_manager.get_ios_wda_config(
            request.device_id
        )
        if not wda_url:
            raise HTTPException(status_code=400, detail="iOS 设备需要配置 WDA URL！")

    task_id = str(uuid.uuid4())[:8]

    asyncio.create_task(
        task_runner.run_task(
            task_id=task_id,
            device_id=request.device_id,
            task=request.task,
            platform=request.platform,
            base_url=request.base_url,
            model=request.model,
            api_key=request.api_key,
            max_steps=request.max_steps,
            lang=request.lang,
            wda_url=request.wda_url,
            api_config_id=request.api_config_id,
        )
    )

    return {"status": "started", "task_id": task_id}


@app.post("/run_batch")
async def run_batch(request: BatchTaskRequest):
    if request.platform != "ios":
        is_adb_keyboard, current_ime = device_manager.check_adb_keyboard(
            request.device_id
        )
        if not is_adb_keyboard:
            raise HTTPException(
                status_code=400,
                detail=f"当前输入法不是 ADB Keyboard！\n当前: {current_ime}",
            )
    else:
        wda_url = request.wda_url or config_manager.get_ios_wda_config(
            request.device_id
        )
        if not wda_url:
            raise HTTPException(status_code=400, detail="iOS 设备需要配置 WDA URL！")

    batch_id = str(uuid.uuid4())[:8]

    asyncio.create_task(
        task_runner.run_batch_task(
            batch_id=batch_id,
            device_id=request.device_id,
            test_cases=request.test_cases,
            platform=request.platform,
            base_url=request.base_url,
            model=request.model,
            api_key=request.api_key,
            max_steps=request.max_steps,
            lang=request.lang,
            wda_url=request.wda_url,
            api_config_id=request.api_config_id,
            scenario_name=request.scenario_name,
        )
    )

    return {
        "status": "started",
        "batch_id": batch_id,
        "total_cases": len(request.test_cases),
    }


@app.get("/task/{task_id}")
async def get_task_status(task_id: str):
    status = task_runner.get_task_status(task_id)
    if status:
        return status
    raise HTTPException(status_code=404, detail="任务不存在")


@app.post("/stop_task/{task_id}")
async def stop_task(task_id: str):
    task_runner.stop_task(task_id)
    return {"status": "stopping", "task_id": task_id}


@app.websocket("/ws/{task_id}")
async def websocket_endpoint(websocket: WebSocket, task_id: str):
    await websocket.accept()

    if task_id not in task_runner.active_connections:
        task_runner.active_connections[task_id] = []
    task_runner.active_connections[task_id].append(websocket)

    try:
        status = task_runner.get_task_status(task_id)
        if status and "logs" in status:
            for log in status["logs"]:
                try:
                    await websocket.send_json(log)
                except:
                    break

        while True:
            try:
                await websocket.receive_text()
            except (WebSocketDisconnect, Exception):
                break
    except Exception as e:
        logger.debug(f"WebSocket 连接关闭: {e}")
    finally:
        try:
            if (
                task_id in task_runner.active_connections
                and websocket in task_runner.active_connections[task_id]
            ):
                task_runner.active_connections[task_id].remove(websocket)
        except:
            pass


# ============== Scrcpy 支持 ==============

scrcpy_processes = {}


@app.post("/scrcpy/start/{device_id}")
async def start_scrcpy(device_id: str, max_size: int = 720, bit_rate: int = 2000000):
    if not check_scrcpy_available():
        raise HTTPException(status_code=500, detail="scrcpy 未安装")

    if device_id in scrcpy_processes:
        proc = scrcpy_processes[device_id]
        if proc.poll() is None:
            return {"status": "already_running"}

    platform = device_manager.get_device_platform(device_id)
    if platform != "android":
        raise HTTPException(status_code=400, detail="scrcpy 仅支持 Android 设备")

    try:
        cmd = [
            "scrcpy",
            "-s",
            device_id,
            "--max-size",
            str(max_size),
            "--bit-rate",
            str(bit_rate),
            "--window-title",
            f"AutoGLM: {device_id}",
            "--stay-awake",
        ]

        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        scrcpy_processes[device_id] = proc

        return {"status": "started", "pid": proc.pid}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/scrcpy/stop/{device_id}")
async def stop_scrcpy(device_id: str):
    if device_id not in scrcpy_processes:
        return {"status": "not_running"}

    proc = scrcpy_processes[device_id]
    if proc.poll() is None:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()

    del scrcpy_processes[device_id]
    return {"status": "stopped"}


@app.get("/scrcpy/status/{device_id}")
async def scrcpy_status(device_id: str):
    if device_id not in scrcpy_processes:
        return {"running": False}

    proc = scrcpy_processes[device_id]
    running = proc.poll() is None

    if not running:
        del scrcpy_processes[device_id]

    return {"running": running, "pid": proc.pid if running else None}


# ============== 启动函数 ==============


def main():
    """启动本地端服务"""
    global _server_url

    # 配置日志过滤器，隐藏 websockets 库的 AssertionError
    import logging

    class WebSocketErrorFilter(logging.Filter):
        def filter(self, record):
            # 过滤掉 websockets 的 AssertionError 和 data transfer failed 错误
            msg = str(record.getMessage()).lower()
            if "assertionerror" in msg or "data transfer failed" in msg:
                return False
            if "waiter is none or waiter.cancelled" in msg:
                return False
            return True

    # 应用过滤器到相关日志
    for name in ["uvicorn.error", "websockets", "websockets.legacy.protocol"]:
        log = logging.getLogger(name)
        log.addFilter(WebSocketErrorFilter())

    import argparse

    parser = argparse.ArgumentParser(description="AutoGLM 本地端服务")
    parser.add_argument(
        "--server",
        "-s",
        type=str,
        default=SERVER_URL,
        help="服务端地址 (例如: http://192.168.1.100:8792)",
    )
    parser.add_argument(
        "--port", "-p", type=int, default=LOCAL_PORT, help="本地端口 (默认: 8793)"
    )
    parser.add_argument("--name", "-n", type=str, default=LOCAL_NAME, help="本地端名称")
    args = parser.parse_args()

    _server_url = args.server

    # 设置 config_manager 的服务端地址（用于同步历史记录）
    config_manager.server_url = args.server

    print(
        f"""
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║    🤖 AutoGLM 本地端服务                                      ║
║                                                               ║
║    本地地址: http://0.0.0.0:{args.port}                         ║
║    本机名称: {args.name}                                       
║    本机 IP:  {get_local_ip()}                                  
║    服务端:   {args.server if args.server else '未配置（独立运行）'}
║                                                               ║
║    功能:                                                      ║
║    • 设备管理 (Android/iOS)                                   ║
║    • 截图获取                                                 ║
║    • 远程控制                                                 ║
║    • 任务执行                                                 ║
║                                                               ║
║    作者: chenwenkun                                           ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
    """
    )

    uvicorn.run(app, host="0.0.0.0", port=args.port)


if __name__ == "__main__":
    main()
