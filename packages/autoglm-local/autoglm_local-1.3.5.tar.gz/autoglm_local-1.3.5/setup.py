#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AutoGLM WebUI 本地端安装配置

安装方式:
    pip install autoglm-local

使用方式:
    autoglm-local --server http://服务端地址:8792
"""

from setuptools import setup, find_packages
import os

# 读取依赖
requirements_path = os.path.join(os.path.dirname(__file__), "requirements_local.txt")
if os.path.exists(requirements_path):
    with open(requirements_path) as f:
        requirements = [
            line.strip() for line in f if line.strip() and not line.startswith("#")
        ]
else:
    requirements = [
        "fastapi>=0.100.0",
        "uvicorn>=0.22.0",
        "websockets>=11.0",
        "python-multipart>=0.0.6",
        "httpx>=0.24.0",
        "openai>=1.0.0",
        "adbutils>=2.0.0",
        "tidevice>=0.12.0",
        "loguru>=0.7.0",
        "requests>=2.28.0",
        "pydantic>=2.0.0",
        "Pillow>=10.0.0",
    ]

# 读取 README
readme_path = os.path.join(os.path.dirname(__file__), "README_DEPLOY.md")
long_description = ""
if os.path.exists(readme_path):
    with open(readme_path, encoding="utf-8") as f:
        long_description = f.read()

setup(
    name="autoglm-local",
    version="1.3.5",  # 修复截图URL：保存为文件并使用qa.local地址
    description="AutoGLM AI-APPUI 自动化测试平台 - 本地客户端（内置完整依赖）",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="chenwenkun",
    author_email="",
    url="http://qa.local:8787/zsdx/AI_UIauto_app",
    packages=find_packages(include=["autoglm_webui_lib", "autoglm_webui_lib.*"]),
    package_data={
        "autoglm_webui_lib": [
            "static/*",
            "static/**/*",
            "static/downloads/*",
            "phone_agent/**/*",
        ]
    },
    include_package_data=True,
    install_requires=requirements,  # 不再依赖外部 phone-agent
    entry_points={
        "console_scripts": [
            "autoglm-local=autoglm_webui_lib.local_server:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Testing",
        "Topic :: Software Development :: Quality Assurance",
    ],
    python_requires=">=3.8",
    keywords="appium, automation, testing, android, ios, ai",
)
