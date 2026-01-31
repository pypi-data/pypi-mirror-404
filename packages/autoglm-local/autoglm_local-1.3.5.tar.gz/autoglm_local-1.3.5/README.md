# AI-APPUI 自动化测试平台 v2.0

基于智谱 AI AutoGLM 的移动端 UI 自动化测试平台，支持 **Android** 和 **iOS** 设备。

## 🚀 功能特性

### 设备支持
- ✅ **Android 设备** - 通过 ADB 连接（USB/WiFi/TCP代理）
- ✅ **iOS 设备** - 通过 tidevice 连接（USB）
- ✅ **多设备管理** - 同时管理多台设备
- ✅ **设备状态检测** - 屏幕亮/灭、锁定状态

### AI 自动化
- ✅ **自然语言测试** - 用自然语言描述测试步骤
- ✅ **智能识别** - AI 自动识别 UI 元素并执行操作
- ✅ **实时截图** - 每一步操作自动截图
- ✅ **思考过程日志** - 展示 AI 的思考过程

### 测试管理
- ✅ **多 API 配置** - 支持配置多个 API Key
- ✅ **用例场景** - 将多个用例保存为场景
- ✅ **CSV 导入/导出** - 支持测试用例批量导入导出
- ✅ **Excel 报告** - 导出详细测试报告（含截图）
- ✅ **历史记录** - 查看历史执行记录

### 屏幕投屏（仅 Android）
- ✅ **scrcpy 集成** - 可选的屏幕镜像功能
- ✅ **实时投屏** - 在独立窗口查看设备屏幕

## 📦 安装依赖

### 基础依赖

```bash
# 进入 web_ui 目录
cd Open-AutoGLM/web_ui

# 安装 Python 依赖
pip install -r requirements.txt
```

### Android 支持

```bash
# macOS
brew install android-platform-tools

# Windows
# 下载 Platform Tools: https://developer.android.com/tools/releases/platform-tools
```

### iOS 支持

```bash
# 安装 tidevice
pip install tidevice

# 验证
tidevice list
```

### scrcpy（可选，用于投屏）

```bash
# macOS
brew install scrcpy

# Windows
# 下载: https://github.com/Genymobile/scrcpy/releases
```

## 🚀 启动服务

```bash
cd Open-AutoGLM/web_ui
python3 server.py
```

服务启动后访问: http://localhost:8792

## 📖 使用指南

### 1. 连接设备

**Android:**
```bash
# USB 连接
adb devices

# WiFi 连接
adb tcpip 5555
adb connect <device_ip>:5555
```

**iOS:**
- 用 USB 线连接 iPhone
- 信任此电脑
- 安装 tidevice 后自动识别

### 2. 配置 API

1. 点击 "API 配置" 区域的 "+" 按钮
2. 填写配置信息：
   - 名称：自定义名称
   - Base URL: `https://open.bigmodel.cn/api/paas/v4`
   - 模型: `autoglm-phone`
   - API Key: 你的智谱 API Key
3. 保存后在下拉菜单中选择该配置

### 3. 添加测试用例

可以手动添加或从 CSV 导入：

```csv
name,description,expected
登录测试,1. 打开应用 2. 点击登录 3. 输入账号密码 4. 点击确认,登录成功
搜索测试,1. 点击搜索框 2. 输入关键词 3. 点击搜索,显示搜索结果
```

### 4. 执行测试

1. 选择设备
2. 选择 API 配置
3. 勾选要执行的测试用例
4. 点击 "执行选中用例"

### 5. 查看结果

- **运行日志**: 实时查看执行日志和 AI 思考过程
- **历史记录**: 查看历史执行记录
- **导出 Excel**: 导出详细测试报告

## 📂 项目结构

```
web_ui/
├── server.py          # FastAPI 后端服务
├── requirements.txt   # Python 依赖
├── start_server.py    # 启动脚本
├── static/
│   ├── index.html     # 主界面
│   ├── guide.html     # 环境配置指南
│   ├── style.css      # 样式文件
│   ├── app.js         # 前端逻辑
│   └── favicon.svg    # 网站图标
└── data/
    ├── history.json   # 历史记录
    ├── api_configs.json    # API 配置
    └── scenarios.json      # 用例场景
```

## 🔧 架构说明

本平台采用 **客户端 + 网页端** 架构：

- **客户端（本地服务）**: Python FastAPI 服务，运行在测试人员本地电脑
  - 负责连接和管理设备（通过 ADB/tidevice）
  - 执行 AI 自动化测试
  - 提供 REST API 和 WebSocket

- **网页端**: 静态 HTML/CSS/JS 页面
  - 可部署到任何 Web 服务器
  - 通过 API 与本地服务通信
  - 实时显示测试进度和结果

## 🛠 API 接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/devices` | GET | 获取所有设备 |
| `/devices/android` | GET | 仅获取 Android 设备 |
| `/devices/ios` | GET | 仅获取 iOS 设备 |
| `/system/info` | GET | 获取系统支持信息 |
| `/screenshot/{device_id}` | GET | 获取设备截图 |
| `/ios/screenshot/{device_id}` | GET | 获取 iOS 设备截图 |
| `/run_task` | POST | 执行单个任务 |
| `/run_batch` | POST | 批量执行任务 |
| `/scrcpy/start/{device_id}` | POST | 启动 scrcpy 投屏 |
| `/scrcpy/stop/{device_id}` | POST | 停止 scrcpy 投屏 |

## 📝 注意事项

1. **Android 输入法**: 执行测试前请确保已安装并启用 ADB Keyboard 输入法
2. **iOS 限制**: iOS 设备的 UI 自动化需要额外配置 WebDriverAgent
3. **scrcpy**: scrcpy 投屏功能需要手动安装 scrcpy

## 👨‍💻 作者

陈文坤
