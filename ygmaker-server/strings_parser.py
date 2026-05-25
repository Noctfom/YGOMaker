# -*- coding: utf-8 -*-
"""
strings.conf 解析器
解析 YGOPro 的 strings.conf 文件，提供系统字符串、系列名、指示物、胜利条件的查询
"""

import os
import re
from config import CDB_PATH


class StringsParser:
    """strings.conf 解析器"""

    def __init__(self, strings_path=None):
        if strings_path is None:
            strings_path = os.path.join(os.path.dirname(CDB_PATH), 'strings.conf')
        self.strings_path = strings_path

        # 解析结果
        self.systems = {}        # !system <code> <text>
        self.victories = {}      # !victory <0xXX> <text>
        self.counters = {}       # !counter <0xXX> <text>
        self.setnames = {}       # !setname <0xXX> <name> [|aliases]

        self._loaded = False

    def load(self):
        """解析 strings.conf 文件"""
        if self._loaded:
            return

        if not os.path.exists(self.strings_path):
            print(f"⚠️ strings.conf 未找到: {self.strings_path}")
            self._loaded = True
            return

        with open(self.strings_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue

                # !system <code> <text>
                if line.startswith('!system '):
                    parts = line[8:].split(None, 1)
                    if len(parts) >= 2:
                        try:
                            code = int(parts[0])
                            self.systems[code] = parts[1]
                        except ValueError:
                            pass

                # !victory <0xXX> <text>
                elif line.startswith('!victory '):
                    parts = line[9:].split(None, 1)
                    if len(parts) >= 2:
                        try:
                            code = int(parts[0], 16)
                            self.victories[code] = parts[1]
                        except ValueError:
                            pass

                # !counter <0xXX> <text>
                elif line.startswith('!counter '):
                    parts = line[9:].split(None, 1)
                    if len(parts) >= 2:
                        try:
                            code = int(parts[0], 16)
                            self.counters[code] = parts[1]
                        except ValueError:
                            pass

                # !setname <0xXX> <name> [|aliases]
                elif line.startswith('!setname '):
                    parts = line[9:].split(None, 1)
                    if len(parts) >= 2:
                        try:
                            code = int(parts[0], 16)
                            rest = parts[1]
                            # 处理 | 分隔的别名
                            names = rest.split('|')
                            main_name = names[0].strip()
                            aliases = [n.strip() for n in names[1:]] if len(names) > 1 else []
                            self.setnames[code] = {
                                'name': main_name,
                                'aliases': aliases,
                                'raw': rest
                            }
                        except ValueError:
                            pass

        self._loaded = True
        print(f"✅ strings.conf 加载完成: {len(self.systems)} 系统字符串, "
              f"{len(self.setnames)} 系列名, {len(self.counters)} 指示物, "
              f"{len(self.victories)} 胜利条件")

    # ================================================================
    #  查询接口
    # ================================================================

    def get_system_string(self, code: int) -> str:
        """获取系统字符串"""
        self.load()
        return self.systems.get(code, f'[未知:{code}]')

    def get_victory_reason(self, code: int) -> str:
        """获取胜利条件描述"""
        self.load()
        return self.victories.get(code, f'[未知胜利条件:0x{code:X}]')

    def get_counter_name(self, code: int) -> str:
        """获取指示物名称"""
        self.load()
        return self.counters.get(code, f'[未知指示物:0x{code:X}]')

    def get_setname(self, code: int) -> dict:
        """获取系列名信息"""
        self.load()
        return self.setnames.get(code, {'name': f'[未知系列:0x{code:X}]', 'aliases': [], 'raw': ''})

    def get_all_setnames(self) -> dict:
        """获取所有系列名"""
        self.load()
        return self.setnames

    def get_all_counters(self) -> dict:
        """获取所有指示物"""
        self.load()
        return self.counters

    def get_all_victories(self) -> dict:
        """获取所有胜利条件"""
        self.load()
        return self.victories

    def search_setname(self, keyword: str) -> list:
        """搜索系列名"""
        self.load()
        results = []
        keyword_lower = keyword.lower()
        for code, info in self.setnames.items():
            if keyword_lower in info['name'].lower() or keyword_lower in info['raw'].lower():
                results.append({'code': code, **info})
        return results

    def get_next_available_setcode(self) -> int:
        """
        获取下一个可用的系列编码
        在现有最大系列编码基础上预留 0x10 的间隔（16个位置），方便官方后续更新
        """
        self.load()
        if not self.setnames:
            return 0x200
        max_code = max(self.setnames.keys())
        # 在当前最大值基础上跳 0x10（16个位置）作为新自定义系列的起点
        return ((max_code // 0x10) + 2) * 0x10

    def get_next_available_counter(self) -> int:
        """获取下一个可用的指示物编码"""
        self.load()
        if not self.counters:
            return 0x100
        max_code = max(self.counters.keys())
        return ((max_code // 0x10) + 2) * 0x10

    def get_next_available_victory(self) -> int:
        """获取下一个可用的胜利条件编码"""
        self.load()
        if not self.victories:
            return 0x30
        max_code = max(self.victories.keys())
        return max_code + 1

    def export_custom_additions(self) -> dict:
        """
        导出所有自定义添加的内容
        （需要在本地对照文件中维护的部分）
        """
        self.load()
        return {
            'setnames': self.setnames,
            'counters': self.counters,
            'victories': self.victories,
            'systems': self.systems,
        }

    def check_conflicts(self, existing_data: dict) -> list:
        """
        检查自定义数据与现有 strings.conf 的冲突
        """
        self.load()
        conflicts = []

        for code in existing_data.get('setnames', {}):
            if code in self.setnames:
                conflicts.append({
                    'type': 'setname',
                    'code': f'0x{code:X}',
                    'existing': self.setnames[code]['name'],
                    'custom': existing_data['setnames'][code].get('name', str(code))
                })

        for code in existing_data.get('counters', {}):
            if code in self.counters:
                conflicts.append({
                    'type': 'counter',
                    'code': f'0x{code:X}',
                    'existing': self.counters[code],
                    'custom': existing_data['counters'][code]
                })

        for code in existing_data.get('victories', {}):
            if code in self.victories:
                conflicts.append({
                    'type': 'victory',
                    'code': f'0x{code:X}',
                    'existing': self.victories[code],
                    'custom': existing_data['victories'][code]
                })

        return conflicts


# 单例
strings_db = StringsParser()
