# -*- coding: utf-8 -*-
"""
本地修改对照文件管理
追踪用户自定义的卡片、系列、指示物、胜利条件
支持与官方数据的更新合并，防止冲突
"""

import os
import json
import sqlite3
from datetime import datetime
from config import CDB_PATH

LOCAL_MODS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'local_modifications.json')


class LocalModsTracker:
    """本地修改追踪器"""

    def __init__(self, mods_file=None):
        self.mods_file = mods_file or LOCAL_MODS_FILE
        self.data = self._load()

    def _load(self) -> dict:
        """加载本地修改记录"""
        if os.path.exists(self.mods_file):
            try:
                with open(self.mods_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                return self._get_default()
        return self._get_default()

    def _get_default(self) -> dict:
        return {
            'version': '1.0',
            'last_updated': '',
            'custom_cards': [],        # 自定义卡密列表
            'custom_setcodes': {},      # {0x1XX: "系列名"}
            'custom_counters': {},      # {0x1XX: "指示物名"}
            'custom_victories': {},     # {0xXX: "胜利条件描述"}
            'custom_systems': {},       # {code: "系统字符串"}
            'merge_history': []         # 合并操作历史
        }

    def save(self):
        """保存修改记录"""
        os.makedirs(os.path.dirname(self.mods_file), exist_ok=True)
        with open(self.mods_file, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)

    # ================================================================
    #  卡片追踪
    # ================================================================

    def mark_card_as_custom(self, card_id: int):
        """标记一张卡片为自定义"""
        if card_id not in self.data['custom_cards']:
            self.data['custom_cards'].append(card_id)
            self.save()

    def is_custom_card(self, card_id: int) -> bool:
        """检查卡片是否为自定义"""
        return card_id in self.data['custom_cards']

    def get_custom_cards(self) -> list:
        """获取所有自定义卡密"""
        return self.data['custom_cards']

    def remove_custom_card(self, card_id: int):
        """移除自定义卡片标记"""
        if card_id in self.data['custom_cards']:
            self.data['custom_cards'].remove(card_id)
            self.save()

    # ================================================================
    #  字段追踪（系列、指示物、胜利条件）
    # ================================================================

    def add_custom_setcode(self, code: int, name: str):
        """添加自定义系列"""
        self.data['custom_setcodes'][str(code)] = name
        self.save()

    def add_custom_counter(self, code: int, name: str):
        """添加自定义指示物"""
        self.data['custom_counters'][str(code)] = name
        self.save()

    def add_custom_victory(self, code: int, description: str):
        """添加自定义胜利条件"""
        self.data['custom_victories'][str(code)] = description
        self.save()

    def get_custom_fields(self) -> dict:
        """获取所有自定义字段"""
        return {
            'setcodes': self.data['custom_setcodes'],
            'counters': self.data['custom_counters'],
            'victories': self.data['custom_victories'],
        }

    # ================================================================
    #  合并与快照
    # ================================================================

    def take_snapshot(self, description: str = '') -> dict:
        """
        拍快照，记录当前 CDB 和 strings.conf 中自定义数据的完整状态
        用于 update 前后的对比
        """
        snapshot = {
            'time': datetime.now().isoformat(),
            'description': description,
            'custom_card_count': len(self.data['custom_cards']),
            'custom_setcodes': dict(self.data['custom_setcodes']),
            'custom_counters': dict(self.data['custom_counters']),
            'custom_victories': dict(self.data['custom_victories']),
        }
        self.data['merge_history'].append(snapshot)
        # 只保留最近20条记录
        if len(self.data['merge_history']) > 20:
            self.data['merge_history'] = self.data['merge_history'][-20:]
        self.save()
        return snapshot

    def export_custom_cards_data(self) -> list:
        """
        导出所有自定义卡片的数据（从 CDB 中读取）
        用于在更新官方 cdb 后重新导入
        """
        if not os.path.exists(CDB_PATH):
            return []

        conn = sqlite3.connect(CDB_PATH)
        cursor = conn.cursor()
        cards_data = []

        for card_id in self.data['custom_cards']:
            cursor.execute("SELECT * FROM datas WHERE id = ?", (card_id,))
            datas_row = cursor.fetchone()
            if datas_row:
                cursor.execute("SELECT * FROM texts WHERE id = ?", (card_id,))
                texts_row = cursor.fetchone()
                if texts_row:
                    cards_data.append({
                        'datas': {
                            'id': datas_row[0], 'ot': datas_row[1], 'alias': datas_row[2],
                            'setcode': datas_row[3], 'type': datas_row[4],
                            'atk': datas_row[5], 'def': datas_row[6], 'level': datas_row[7],
                            'race': datas_row[8], 'attribute': datas_row[9], 'category': datas_row[10]
                        },
                        'texts': {
                            'id': texts_row[0], 'name': texts_row[1], 'desc': texts_row[2],
                            'str1': texts_row[3], 'str2': texts_row[4], 'str3': texts_row[5],
                            'str4': texts_row[6], 'str5': texts_row[7], 'str6': texts_row[8],
                            'str7': texts_row[9], 'str8': texts_row[10], 'str9': texts_row[11],
                            'str10': texts_row[12], 'str11': texts_row[13], 'str12': texts_row[14],
                            'str13': texts_row[15], 'str14': texts_row[16], 'str15': texts_row[17],
                            'str16': texts_row[18]
                        }
                    })

        conn.close()
        return cards_data

    def reimport_custom_cards(self, cards_data: list) -> int:
        """
        将自定义卡片数据重新导入 CDB
        返回成功导入的数量
        """
        if not cards_data:
            return 0

        conn = sqlite3.connect(CDB_PATH)
        cursor = conn.cursor()
        count = 0

        for card in cards_data:
            d = card['datas']
            t = card['texts']
            card_id = d['id']

            # 检查是否已存在
            cursor.execute("SELECT id FROM datas WHERE id = ?", (card_id,))
            exists = cursor.fetchone() is not None

            if exists:
                cursor.execute("""
                    UPDATE datas SET ot=?, alias=?, setcode=?, type=?, atk=?, def=?, level=?, race=?, attribute=?, category=?
                    WHERE id=?
                """, (d['ot'], d['alias'], d['setcode'], d['type'], d['atk'], d['def'], d['level'], d['race'], d['attribute'], d['category'], card_id))
            else:
                cursor.execute("""
                    INSERT INTO datas (id,ot,alias,setcode,type,atk,def,level,race,attribute,category)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?)
                """, (card_id, d['ot'], d['alias'], d['setcode'], d['type'], d['atk'], d['def'], d['level'], d['race'], d['attribute'], d['category']))

            # 删除旧 texts 再插入
            cursor.execute("DELETE FROM texts WHERE id = ?", (card_id,))
            cursor.execute("""
                INSERT INTO texts (id,name,desc,str1,str2,str3,str4,str5,str6,str7,str8,str9,str10,str11,str12,str13,str14,str15,str16)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, (t['id'], t['name'], t['desc'], t['str1'], t['str2'], t['str3'], t['str4'], t['str5'], t['str6'], t['str7'], t['str8'], t['str9'], t['str10'], t['str11'], t['str12'], t['str13'], t['str14'], t['str15'], t['str16']))

            count += 1

        conn.commit()
        conn.close()
        return count

    def export_custom_strings(self) -> str:
        """
        导出自定义 strings.conf 追加内容
        用于附加到官方 strings.conf 末尾
        """
        lines = []
        lines.append('# ============================================================')
        lines.append(f'# YGOMaker 自定义字段 ({datetime.now().strftime("%Y-%m-%d")})')
        lines.append('# 以下为自定义系列/指示物/胜利条件，请勿手动修改')
        lines.append('# ============================================================')

        if self.data['custom_setcodes']:
            lines.append('')
            lines.append('# 自定义系列名')
            for code_str, name in self.data['custom_setcodes'].items():
                code = int(code_str)
                lines.append(f'!setname 0x{code:X} {name}')

        if self.data['custom_counters']:
            lines.append('')
            lines.append('# 自定义指示物')
            for code_str, name in self.data['custom_counters'].items():
                code = int(code_str)
                lines.append(f'!counter 0x{code:X} {name}')

        if self.data['custom_victories']:
            lines.append('')
            lines.append('# 自定义胜利条件')
            for code_str, desc in self.data['custom_victories'].items():
                code = int(code_str)
                lines.append(f'!victory 0x{code:X} {desc}')

        lines.append('')
        return '\n'.join(lines)

    def remove_setcode(self, code: int):
        """删除自定义系列"""
        self.data['custom_setcodes'].pop(str(code), None)
        self.save()

    def remove_counter(self, code: int):
        """删除自定义指示物"""
        self.data['custom_counters'].pop(str(code), None)
        self.save()

    def remove_victory(self, code: int):
        """删除自定义胜利条件"""
        self.data['custom_victories'].pop(str(code), None)
        self.save()

    def get_merge_status(self) -> dict:
        """获取合并状态摘要"""
        return {
            'total_custom_cards': len(self.data['custom_cards']),
            'total_custom_setcodes': len(self.data['custom_setcodes']),
            'total_custom_counters': len(self.data['custom_counters']),
            'total_custom_victories': len(self.data['custom_victories']),
            'last_updated': self.data.get('last_updated', 'N/A'),
            'merge_count': len(self.data.get('merge_history', [])),
        }


# 单例
mods_tracker = LocalModsTracker()
