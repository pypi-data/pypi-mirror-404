#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
设备管理模块 - 管理 Android 和 iOS 设备
"""

import subprocess
from typing import List, Dict, Optional
from loguru import logger

# 可选依赖 - adbutils
try:
    import adbutils
    ADBUTILS_AVAILABLE = True
except ImportError:
    adbutils = None
    ADBUTILS_AVAILABLE = False
    print("⚠️ adbutils 未安装，使用基本 ADB 命令。安装: pip install adbutils")

# 可选依赖 - tidevice (iOS)
try:
    import tidevice
    TIDEVICE_AVAILABLE = True
except ImportError:
    tidevice = None
    TIDEVICE_AVAILABLE = False
    print("⚠️ tidevice 未安装，iOS 设备支持已禁用。安装: pip install tidevice")


class DeviceManager:
    """设备管理器 - 统一管理 Android 和 iOS 设备"""
    
    def __init__(self):
        self.adbutils_available = ADBUTILS_AVAILABLE
        self.tidevice_available = TIDEVICE_AVAILABLE
    
    def list_all_devices(self) -> List[Dict]:
        """列出所有设备（Android + iOS）"""
        devices = []
        devices.extend(self.list_android_devices())
        devices.extend(self.list_ios_devices())
        return devices
    
    def list_android_devices(self) -> List[Dict]:
        """列出所有 Android 设备"""
        devices = []
        
        if self.adbutils_available:
            try:
                for d in adbutils.adb.device_list():
                    try:
                        model = d.prop.get("ro.product.model", "Unknown")
                        screen_on = self._is_android_screen_on(d)
                        unlocked = self._is_android_unlocked(d)
                        
                        devices.append({
                            "serial": d.serial,
                            "state": d.get_state(),
                            "model": model,
                            "platform": "android",
                            "screen_on": screen_on,
                            "unlocked": unlocked,
                        })
                    except Exception as e:
                        logger.error(f"Error getting device info for {d.serial}: {e}")
            except Exception as e:
                logger.error(f"Error listing Android devices with adbutils: {e}")
        else:
            # 回退到基本 ADB 命令
            try:
                result = subprocess.run(
                    ["adb", "devices", "-l"],
                    capture_output=True, text=True, timeout=10
                )
                lines = result.stdout.strip().split("\n")[1:]
                
                for line in lines:
                    if not line.strip() or "offline" in line:
                        continue
                    
                    parts = line.split()
                    if len(parts) < 2 or parts[1] != "device":
                        continue
                    
                    serial = parts[0]
                    model = "Unknown"
                    
                    for part in parts[2:]:
                        if part.startswith("model:"):
                            model = part.replace("model:", "")
                    
                    try:
                        model_result = subprocess.run(
                            ["adb", "-s", serial, "shell", "getprop", "ro.product.model"],
                            capture_output=True, text=True, timeout=5
                        )
                        if model_result.returncode == 0 and model_result.stdout.strip():
                            model = model_result.stdout.strip()
                    except:
                        pass
                    
                    screen_on = True
                    unlocked = True
                    
                    try:
                        power_result = subprocess.run(
                            ["adb", "-s", serial, "shell", "dumpsys", "power"],
                            capture_output=True, text=True, timeout=5
                        )
                        if power_result.returncode == 0:
                            output = power_result.stdout
                            if "mWakefulness=Asleep" in output:
                                screen_on = False
                        
                        keyguard_result = subprocess.run(
                            ["adb", "-s", serial, "shell", "dumpsys", "window"],
                            capture_output=True, text=True, timeout=5
                        )
                        if keyguard_result.returncode == 0:
                            output = keyguard_result.stdout
                            if "mShowingLockscreen=true" in output or "mDreamingLockscreen=true" in output:
                                unlocked = False
                    except:
                        pass
                    
                    devices.append({
                        "serial": serial,
                        "state": "device",
                        "model": model,
                        "platform": "android",
                        "screen_on": screen_on,
                        "unlocked": unlocked,
                    })
            except Exception as e:
                logger.error(f"Error listing Android devices: {e}")
        
        return devices
    
    def list_ios_devices(self) -> List[Dict]:
        """列出所有 iOS 设备"""
        devices = []
        
        if not self.tidevice_available:
            return devices
        
        try:
            t = tidevice.Usbmux()
            for d in t.device_list():
                try:
                    dev = tidevice.Device(d.udid)
                    name = dev.name
                    model = dev.get_value(key="ProductType") or "iPhone"
                except:
                    name = "iOS Device"
                    model = "Unknown"
                
                devices.append({
                    "serial": d.udid,
                    "state": "device",
                    "model": name,
                    "product": model,
                    "platform": "ios",
                    "screen_on": True,
                    "unlocked": True,
                })
        except Exception as e:
            logger.error(f"Error listing iOS devices: {e}")
        
        return devices
    
    def get_device_platform(self, serial: str) -> str:
        """获取设备平台类型"""
        android_devices = self.list_android_devices()
        for d in android_devices:
            if d["serial"] == serial:
                return "android"
        
        ios_devices = self.list_ios_devices()
        for d in ios_devices:
            if d["serial"] == serial:
                return "ios"
        
        return "unknown"
    
    def _is_android_screen_on(self, device) -> bool:
        """检查 Android 设备屏幕是否亮起（参考 appinstalltest）"""
        try:
            # Method 1: dumpsys power (mWakefulness=Awake)
            output = device.shell("dumpsys power")
            if "mWakefulness=Awake" in output:
                return True
            # 如果明确是 Asleep 或 Dozing，才返回 False
            if "mWakefulness=Asleep" in output or "mWakefulness=Dozing" in output:
                return False
            
            # Method 2: dumpsys deviceidle (mScreenOn=true)
            output2 = device.shell("dumpsys deviceidle")
            if "mScreenOn=true" in output2:
                return True
            if "mScreenOn=false" in output2:
                return False
            
            # Method 3: dumpsys display (state=ON)
            output3 = device.shell("dumpsys display")
            if "state=ON" in output3:
                return True
            if "state=OFF" in output3:
                return False
            
            # 默认返回 True（宁可误判为亮屏）
            return True
        except Exception as e:
            logger.error(f"Error checking screen state: {e}")
            return True
    
    def _is_android_unlocked(self, device) -> bool:
        """检查 Android 设备是否已解锁（参考 appinstalltest）"""
        try:
            output = device.shell("dumpsys window policy")
            
            # 如果明确显示锁屏，返回 False
            if "mShowingLockscreen=true" in output:
                return False
            if "mDreamingLockscreen=true" in output:
                return False
            
            # 如果明确显示没有锁屏，返回 True  
            if "mShowingLockscreen=false" in output:
                return True
            if "mDreamingLockscreen=false" in output:
                return True
            
            # Method 2: dumpsys trust
            output_trust = device.shell("dumpsys trust")
            if "mDeviceLocked=true" in output_trust:
                return False
            if "mDeviceLocked=false" in output_trust:
                return True
            
            # Method 3: Check keyguard
            output_activity = device.shell("dumpsys activity activities")
            if "mKeyguardShowing=true" in output_activity:
                return False
            if "mKeyguardShowing=false" in output_activity:
                return True
            
            # 默认返回 True（宁可误判为解锁）
            return True
        except Exception as e:
            logger.error(f"Error checking lock state: {e}")
            return True
    
    def get_input_methods(self, device_id: str) -> Dict:
        """获取 Android 设备输入法列表"""
        try:
            result = subprocess.run(
                ["adb", "-s", device_id, "shell", "ime", "list", "-s"],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                imes = [line.strip() for line in result.stdout.strip().split("\n") if line.strip()]
                current_result = subprocess.run(
                    ["adb", "-s", device_id, "shell", "settings", "get", "secure", "default_input_method"],
                    capture_output=True, text=True, timeout=5
                )
                current_ime = current_result.stdout.strip() if current_result.returncode == 0 else ""
                return {"imes": imes, "current": current_ime}
        except Exception as e:
            logger.error(f"Error getting input methods: {e}")
        return {"imes": [], "current": ""}
    
    def switch_input_method(self, device_id: str, ime: str) -> bool:
        """切换 Android 输入法"""
        try:
            result = subprocess.run(
                ["adb", "-s", device_id, "shell", "ime", "set", ime],
                capture_output=True, text=True, timeout=10
            )
            return result.returncode == 0
        except:
            return False
    
    def check_adb_keyboard(self, device_id: str) -> tuple:
        """检查是否使用 ADB Keyboard"""
        try:
            result = subprocess.run(
                ["adb", "-s", device_id, "shell", "settings", "get", "secure", "default_input_method"],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                current_ime = result.stdout.strip().lower()
                if "adbkeyboard" in current_ime or "adb" in current_ime:
                    return True, current_ime
                return False, current_ime
        except Exception as e:
            return False, str(e)
        return False, "unknown"
    
    def install_apk(self, device_id: str, apk_path: str) -> tuple:
        """安装 APK 到 Android 设备"""
        try:
            result = subprocess.run(
                ["adb", "-s", device_id, "install", "-r", apk_path],
                capture_output=True, text=True, timeout=120
            )
            return result.returncode == 0, result.stdout + result.stderr
        except Exception as e:
            return False, str(e)
    
    def get_screenshot_android(self, device_id: str) -> Optional[bytes]:
        """获取 Android 设备截图"""
        try:
            result = subprocess.run(
                ["adb", "-s", device_id, "exec-out", "screencap", "-p"],
                capture_output=True, timeout=10
            )
            if result.returncode == 0 and result.stdout:
                return result.stdout
        except Exception as e:
            logger.error(f"Screenshot error: {e}")
        return None
    
    def get_screenshot_ios(self, device_id: str) -> Optional[bytes]:
        """获取 iOS 设备截图（使用 tidevice）"""
        if not self.tidevice_available:
            return None
        
        try:
            result = subprocess.run(
                ["tidevice", "-u", device_id, "screenshot", "-"],
                capture_output=True, timeout=30
            )
            if result.returncode == 0:
                return result.stdout
        except Exception as e:
            logger.error(f"iOS screenshot error: {e}")
        return None
    
    def get_screen_size(self, device_id: str) -> tuple:
        """获取 Android 屏幕尺寸"""
        try:
            import re
            size_result = subprocess.run(
                ["adb", "-s", device_id, "shell", "wm", "size"],
                capture_output=True, text=True, timeout=5
            )
            if size_result.returncode == 0:
                match = re.search(r"(\d+)x(\d+)", size_result.stdout)
                if match:
                    return int(match.group(1)), int(match.group(2))
        except:
            pass
        return 1080, 1920  # 默认尺寸
    
    def execute_adb_action(self, device_id: str, action: str, **kwargs) -> Dict:
        """执行 ADB 操作"""
        try:
            if action == "tap":
                cmd = ["adb", "-s", device_id, "shell", "input", "tap", str(kwargs.get("x")), str(kwargs.get("y"))]
            elif action == "swipe":
                cmd = ["adb", "-s", device_id, "shell", "input", "swipe",
                       str(kwargs.get("x")), str(kwargs.get("y")),
                       str(kwargs.get("x2")), str(kwargs.get("y2")),
                       str(kwargs.get("duration", 300))]
            elif action == "key":
                cmd = ["adb", "-s", device_id, "shell", "input", "keyevent", str(kwargs.get("keycode"))]
            elif action == "text":
                cmd = ["adb", "-s", device_id, "shell", "am", "broadcast", "-a", "ADB_INPUT_TEXT", "--es", "msg", kwargs.get("text", "")]
            elif action == "back":
                cmd = ["adb", "-s", device_id, "shell", "input", "keyevent", "4"]
            elif action == "home":
                cmd = ["adb", "-s", device_id, "shell", "input", "keyevent", "3"]
            elif action == "recent":
                cmd = ["adb", "-s", device_id, "shell", "input", "keyevent", "187"]
            else:
                return {"status": "error", "message": f"未知动作: {action}"}
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                return {"status": "success"}
            else:
                return {"status": "error", "message": result.stderr}
        except subprocess.TimeoutExpired:
            return {"status": "error", "message": "命令执行超时"}
        except Exception as e:
            return {"status": "error", "message": str(e)}


# 全局设备管理器实例
device_manager = DeviceManager()
