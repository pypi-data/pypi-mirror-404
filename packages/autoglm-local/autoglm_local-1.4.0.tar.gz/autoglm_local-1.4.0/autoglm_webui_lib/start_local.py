#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
启动本地端服务
"""

import os
import sys

# 确保可以导入 phone_agent
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

if __name__ == "__main__":
    from autoglm_webui_lib.local_server import main
    main()
