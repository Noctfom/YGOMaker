# -*- coding: utf-8 -*-
"""
YGOMaker 后端配置
"""

import os

# 项目根目录
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# cards.cdb 路径 (项目根目录)
CDB_PATH = os.path.join(BASE_DIR, 'cards.cdb')

# strings.conf 路径 (项目根目录)
STRINGS_PATH = os.path.join(BASE_DIR, 'strings.conf')

# 脚本目录路径 (共享 script 目录)
SCRIPT_DIR = os.path.join(BASE_DIR, 'script')

# CDB 自动备份目录
BACKUP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backup')

# 服务端口
SERVER_PORT = 8848

# 自定义卡密范围
# 策略1（首选）: 9位数段（1亿~2亿），完全避开官方卡密，YGOPro uint32 兼容
# 策略2（备选）: 智能扫描脚本库，找到 8 位数空白段
CUSTOM_ID_RANGE = {
    'primary_start': 100000000,   # 1亿（9位数首选区间）
    'primary_end':   200000000,   # 2亿
    'fallback_start': 20000000,   # 2千万（备选，需额外去重检查）
    'fallback_end':   99999999,   # 1亿-1
}

# CORS 允许的来源
CORS_ORIGINS = [
    'http://localhost:5173',
    'http://localhost:8848',
    'http://127.0.0.1:5173',
    'http://127.0.0.1:8848',
]
