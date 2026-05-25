# -*- coding: utf-8 -*-
"""
CardWriter 模块
负责将卡片数据写入 cards.cdb（datas 表 + texts 表）
"""

import os
import shutil
import sqlite3
from datetime import datetime
from config import CDB_PATH, BACKUP_DIR, CUSTOM_ID_RANGE, SCRIPT_DIR
from local_mods_tracker import mods_tracker

# ============================================================
# 卡片类型/属性/种族映射表（与 YGOPro constants 对齐）
# ============================================================

# 卡片大类 → TYPE 标志位
CARD_TYPE_MAP = {
    'monster':  0x1,       # TYPE_MONSTER
    'spell':    0x2,       # TYPE_SPELL
    'trap':     0x4,       # TYPE_TRAP
}

# 怪兽子类型 → TYPE 标志位
MONSTER_CARD_TYPE_MAP = {
    'normal':   0x10,       # TYPE_NORMAL
    'effect':   0x20,       # TYPE_EFFECT
    'fusion':   0x40,       # TYPE_FUSION
    'ritual':   0x80,       # TYPE_RITUAL
    'spirit':   0x200,      # TYPE_SPIRIT
    'union':    0x400,      # TYPE_UNION
    'gemini':   0x800,      # TYPE_DUAL (二重)
    'tuner':    0x1000,     # TYPE_TUNER
    'synchro':  0x2000,     # TYPE_SYNCHRO
    'token':    0x4000,     # TYPE_TOKEN
    'xyz':      0x800000,   # TYPE_XYZ
    'pendulum': 0x1000000,  # TYPE_PENDULUM
    'link':     0x4000000,  # TYPE_LINK
}

# 属性 → 数值
ATTRIBUTE_MAP = {
    'earth':    0x01,       # ATTRIBUTE_EARTH
    'water':    0x02,       # ATTRIBUTE_WATER
    'fire':     0x04,       # ATTRIBUTE_FIRE
    'wind':     0x08,       # ATTRIBUTE_WIND
    'light':    0x10,       # ATTRIBUTE_LIGHT
    'dark':     0x20,       # ATTRIBUTE_DARK
    'divine':   0x40,       # ATTRIBUTE_DIVINE
}

# 种族 → 数值
RACE_MAP = {
    'warrior':        0x1,
    'spellcaster':    0x2,
    'fairy':          0x4,
    'fiend':          0x8,
    'zombie':         0x10,
    'machine':        0x20,
    'aqua':           0x40,
    'pyro':           0x80,
    'rock':           0x100,
    'winged-beast':   0x200,
    'winged beast':   0x200,
    'plant':          0x400,
    'insect':         0x800,
    'thunder':        0x1000,
    'dragon':         0x2000,
    'beast':          0x4000,
    'beast-warrior':  0x8000,
    'beast warrior':  0x8000,
    'dinosaur':       0x10000,
    'fish':           0x20000,
    'sea-serpent':    0x40000,
    'sea serpent':    0x40000,
    'reptile':        0x80000,
    'psychic':        0x100000,
    'divine-beast':   0x200000,
    'divine beast':   0x200000,
    'creator-god':    0x400000,
    'creator god':    0x400000,
    'wyrm':           0x800000,
    'cyberse':        0x1000000,
    'illusion':       0x2000000,
}


class CardWriter:
    """游戏王卡片数据写入器"""

    def __init__(self, db_path=None):
        self.db_path = db_path or CDB_PATH
        self.backup_dir = BACKUP_DIR
        self._ensure_backup_dir()

    def _ensure_backup_dir(self):
        """确保备份目录存在"""
        os.makedirs(self.backup_dir, exist_ok=True)

    def _backup_cdb(self):
        """写入前自动备份 cards.cdb"""
        if not os.path.exists(self.db_path):
            return
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = os.path.join(self.backup_dir, f'cards_{timestamp}.cdb')
        shutil.copy2(self.db_path, backup_path)
        return backup_path

    def _connect(self):
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    # ================================================================
    #  卡片类型转换（前端数据 → CDB 字段值）
    # ================================================================

    def _compute_type(self, data: dict) -> int:
        """根据前端数据计算 datas.type 字段值"""
        type_val = 0

        card_type = data.get('type', 'monster')  # monster / spell / trap
        monster_card_type = data.get('cardType', 'normal')  # normal / effect / fusion ...

        if card_type == 'spell':
            type_val = 0x2  # TYPE_SPELL
        elif card_type == 'trap':
            type_val = 0x4  # TYPE_TRAP
        else:
            type_val = 0x1  # TYPE_MONSTER

        # 如果是怪兽，叠加子类型
        if card_type == 'monster' or card_type == 'pendulum':
            if monster_card_type in MONSTER_CARD_TYPE_MAP:
                type_val |= MONSTER_CARD_TYPE_MAP[monster_card_type]
            # effect 类型的基础判定
            if monster_card_type in ('effect', 'fusion', 'ritual', 'synchro', 'xyz', 'link'):
                type_val |= 0x20  # TYPE_EFFECT

        # pendulum 叠加
        if card_type == 'pendulum':
            type_val |= 0x1000000  # TYPE_PENDULUM

        # 如果数据中有额外的 abilities（如 tuner, spirit 等）
        abilities = data.get('abilities', [])
        for ab in abilities:
            if ab in MONSTER_CARD_TYPE_MAP:
                type_val |= MONSTER_CARD_TYPE_MAP[ab]

        return type_val

    def _compute_attribute(self, data: dict) -> int:
        """计算属性值"""
        attr = data.get('attribute', '').lower().strip()
        if attr in ATTRIBUTE_MAP:
            return ATTRIBUTE_MAP[attr]
        return 0

    def _compute_race(self, data: dict) -> int:
        """计算种族值"""
        race_raw = data.get('monsterType', '')  # 如 "龙族/效果" 或 "魔法师族"
        # 提取种族部分（斜杠前）
        race_name = race_raw.split('/')[0].strip()
        # 移除常见后缀
        race_name = race_name.replace('族', '').strip().lower()
        if race_name in RACE_MAP:
            return RACE_MAP[race_name]
        return 0

    def _compute_level(self, data: dict) -> int:
        """计算 level 字段（包含等级/阶级/Link值/灵摆刻度）"""
        card_type = data.get('type', 'monster')
        monster_card_type = data.get('cardType', 'normal')

        level = data.get('level', 0)
        rank = data.get('rank', 0)
        pendulum_scale = data.get('pendulumScale', 0)
        arrow_count = len(data.get('arrowList', []))

        raw_level = 0

        if monster_card_type == 'xyz':
            raw_level = rank & 0xFFFF
        elif monster_card_type == 'link':
            raw_level = arrow_count & 0xFFFF
        else:
            raw_level = level & 0xFFFF

        # 灵摆刻度存储在高位
        if card_type == 'pendulum' or (card_type == 'monster' and pendulum_scale > 0):
            lscale = pendulum_scale
            rscale = pendulum_scale
            raw_level |= (lscale & 0xFF) << 24
            raw_level |= (rscale & 0xFF) << 16

        return raw_level

    def _compute_atk(self, data: dict) -> int:
        """计算攻击力（-2 → ∞, -1 → ?，显示为 -2/-1，实际存储值）"""
        atk = data.get('atk', 0)
        if atk is None or atk == '':
            return 0
        try:
            atk = int(atk)
            if atk == -2:  # ∞ 的攻击力，YGOPro 通常存储为 -1 或特殊值
                return -1
            return max(atk, 0)
        except (ValueError, TypeError):
            return 0

    def _compute_def(self, data: dict) -> int:
        """计算守备力（link 怪时存储 link_marker）"""
        card_type = data.get('cardType', 'normal')

        if card_type == 'link':
            # link 怪的 def 字段存储 link_marker
            arrow_list = data.get('arrowList', [])
            marker = 0
            for arrow in arrow_list:
                try:
                    marker |= (1 << (int(arrow) - 1))
                except (ValueError, TypeError):
                    pass
            return marker

        defense = data.get('def', 0)
        if defense is None or defense == '':
            return 0
        try:
            defense = int(defense)
            if defense == -2:
                return -1
            return max(defense, 0)
        except (ValueError, TypeError):
            return 0

    def _compute_setcode(self, data: dict) -> int:
        """计算系列字段"""
        setcode = data.get('setcode', 0)
        try:
            if isinstance(setcode, str) and setcode.startswith('0x'):
                return int(setcode, 16)
            return int(setcode) if setcode else 0
        except (ValueError, TypeError):
            return 0

    # ================================================================
    #  核心写入方法
    # ================================================================

    def write_card(self, data: dict, overwrite: bool = False) -> dict:
        """
        写入一张卡片到 cards.cdb

        参数:
            data: 前端传入的卡片数据字典
            overwrite: 是否覆盖已有卡片

        返回:
            dict: {success: bool, message: str, card_id: int}
        """
        card_id = data.get('password')
        if not card_id:
            return {'success': False, 'message': '卡密（password）不能为空'}

        try:
            card_id = int(card_id)
        except (ValueError, TypeError):
            return {'success': False, 'message': f'卡密格式错误: {card_id}'}

        # 备份
        backup_path = self._backup_cdb()

        conn = self._connect()
        try:
            cursor = conn.cursor()

            # 检查是否存在
            cursor.execute("SELECT id FROM datas WHERE id = ?", (card_id,))
            exists = cursor.fetchone() is not None

            if exists and not overwrite:
                conn.close()
                return {
                    'success': False,
                    'message': f'卡密 {card_id} 已存在。如需覆盖请勾选"覆盖已有卡片"',
                    'card_id': card_id,
                    'exists': True
                }

            # 计算各字段值
            type_val = self._compute_type(data)
            attribute = self._compute_attribute(data)
            race = self._compute_race(data)
            level = self._compute_level(data)
            atk = self._compute_atk(data)
            defense = self._compute_def(data)
            setcode = self._compute_setcode(data)
            category = data.get('category', 0)
            ot = data.get('ot', 0x1)  # 默认OCG
            alias = data.get('alias', 0)

            # 写入 datas 表
            if exists:
                cursor.execute("""
                    UPDATE datas SET
                        ot = ?, alias = ?, setcode = ?, type = ?,
                        atk = ?, def = ?, level = ?, race = ?,
                        attribute = ?, category = ?
                    WHERE id = ?
                """, (ot, alias, setcode, type_val, atk, defense, level, race, attribute, category, card_id))
            else:
                cursor.execute("""
                    INSERT INTO datas (id, ot, alias, setcode, type, atk, def, level, race, attribute, category)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (card_id, ot, alias, setcode, type_val, atk, defense, level, race, attribute, category))

            # 写入 texts 表
            name = data.get('name', '')
            desc = data.get('description', '')
            pendulum_desc = data.get('pendulumDescription', '')

            # texts 表结构: id, name, desc, str1~str16
            str_fields = [pendulum_desc] + [''] * 15  # str1 放灵摆描述

            if exists:
                cursor.execute("DELETE FROM texts WHERE id = ?", (card_id,))

            cursor.execute("""
                INSERT INTO texts (id, name, desc, str1, str2, str3, str4, str5, str6, str7, str8,
                                   str9, str10, str11, str12, str13, str14, str15, str16)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (card_id, name, desc, *str_fields))

            conn.commit()
            conn.close()

            # 自动标记为自定义卡片（9位数段）
            if card_id >= 100000000:
                mods_tracker.mark_card_as_custom(card_id)

            return {
                'success': True,
                'message': f'卡片 {card_id} ({name}) {"更新" if exists else "创建"}成功',
                'card_id': card_id,
                'name': name,
                'is_new': not exists,
                'backup': backup_path
            }

        except Exception as e:
            conn.rollback()
            conn.close()
            # 恢复备份
            if backup_path and os.path.exists(backup_path):
                shutil.copy2(backup_path, self.db_path)
            return {'success': False, 'message': f'写入失败: {str(e)}', 'card_id': card_id}

    def batch_write(self, cards: list, overwrite: bool = False) -> dict:
        """批量写入卡片"""
        results = []
        for card in cards:
            result = self.write_card(card, overwrite=overwrite)
            results.append(result)

        success_count = sum(1 for r in results if r.get('success'))
        fail_count = len(results) - success_count

        return {
            'total': len(results),
            'success': success_count,
            'fail': fail_count,
            'details': results
        }

    def delete_card(self, card_id: int) -> dict:
        """删除一张卡片"""
        self._backup_cdb()
        conn = self._connect()
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM datas WHERE id = ?", (card_id,))
            cursor.execute("DELETE FROM texts WHERE id = ?", (card_id,))
            conn.commit()
            conn.close()

            # 同步删除脚本文件
            script_path = os.path.join(SCRIPT_DIR, f'c{card_id}.lua')
            script_deleted = False
            if os.path.exists(script_path):
                os.remove(script_path)
                script_deleted = True

            return {
                'success': True,
                'message': f'卡片 {card_id} 已删除',
                'script_deleted': script_deleted
            }
        except Exception as e:
            conn.rollback()
            conn.close()
            return {'success': False, 'message': f'删除失败: {str(e)}'}

    def get_card(self, card_id: int) -> dict:
        """读取一张卡片的完整数据"""
        conn = self._connect()
        try:
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM datas WHERE id = ?", (card_id,))
            datas_row = cursor.fetchone()
            if not datas_row:
                conn.close()
                return None

            cursor.execute("SELECT * FROM texts WHERE id = ?", (card_id,))
            texts_row = cursor.fetchone()

            conn.close()

            # 解析 datas 字段
            columns = ['id', 'ot', 'alias', 'setcode', 'type', 'atk', 'def',
                       'level', 'race', 'attribute', 'category']
            datas_dict = dict(zip(columns, datas_row))

            # 解析 texts 字段
            texts_cols = ['id', 'name', 'desc'] + [f'str{i}' for i in range(1, 17)]
            texts_dict = dict(zip(texts_cols, texts_row)) if texts_row else {}

            # 合并并转为前端友好格式
            return self._db_to_frontend(datas_dict, texts_dict)

        except Exception as e:
            conn.close()
            return {'error': str(e)}

    def get_next_id(self, use_primary: bool = True) -> dict:
        """
        获取下一个可用卡密

        策略：
        1. 首选 9 位数段（1亿起），从已用最大ID+1开始
        2. 备选 8 位数段（2千万起），查找空白位
        """
        conn = self._connect()
        try:
            cursor = conn.cursor()

            primary_start = CUSTOM_ID_RANGE['primary_start']
            primary_end = CUSTOM_ID_RANGE['primary_end']

            # 查找 9 位数段中最大的已用 ID
            cursor.execute(
                "SELECT MAX(id) FROM datas WHERE id >= ? AND id < ?",
                (primary_start, primary_end)
            )
            row = cursor.fetchone()
            max_id = row[0] if row[0] else primary_start - 1

            if max_id < primary_end - 1:
                next_id = max_id + 1 if max_id >= primary_start else primary_start
                conn.close()
                return {
                    'success': True,
                    'card_id': next_id,
                    'range': 'primary (9位数段)',
                    'strategy': '安全递增'
                }

            # 9位数段已满（极不可能），降级到 8 位数扫描
            fallback_start = CUSTOM_ID_RANGE['fallback_start']
            fallback_end = CUSTOM_ID_RANGE['fallback_end']

            cursor.execute(
                "SELECT id FROM datas WHERE id >= ? AND id <= ? ORDER BY id",
                (fallback_start, fallback_end)
            )
            used_ids = set(row[0] for row in cursor.fetchall())

            for candidate in range(fallback_start, fallback_end + 1):
                if candidate not in used_ids:
                    conn.close()
                    return {
                        'success': True,
                        'card_id': candidate,
                        'range': 'fallback (8位数段)',
                        'strategy': '空白扫描'
                    }

            conn.close()
            return {'success': False, 'message': '卡密空间已耗尽，请联系管理员'}

        except Exception as e:
            conn.close()
            return {'success': False, 'message': f'获取卡密失败: {str(e)}'}

    def search_cards(self, keyword: str = '', limit: int = 50, offset: int = 0) -> dict:
        """搜索卡片"""
        conn = self._connect()
        try:
            cursor = conn.cursor()

            if keyword:
                cursor.execute("""
                    SELECT d.*, t.name, t.desc
                    FROM datas d
                    LEFT JOIN texts t ON d.id = t.id
                    WHERE t.name LIKE ? OR CAST(d.id AS TEXT) LIKE ?
                    ORDER BY d.id DESC
                    LIMIT ? OFFSET ?
                """, (f'%{keyword}%', f'%{keyword}%', limit, offset))
            else:
                cursor.execute("""
                    SELECT d.*, t.name, t.desc
                    FROM datas d
                    LEFT JOIN texts t ON d.id = t.id
                    ORDER BY d.id DESC
                    LIMIT ? OFFSET ?
                """, (limit, offset))

            rows = cursor.fetchall()

            # 获取总数
            if keyword:
                cursor.execute("""
                    SELECT COUNT(*) FROM texts WHERE name LIKE ? OR CAST(id AS TEXT) LIKE ?
                """, (f'%{keyword}%', f'%{keyword}%'))
            else:
                cursor.execute("SELECT COUNT(*) FROM datas")
            total = cursor.fetchone()[0]

            conn.close()

            cards = []
            for row in rows:
                card = {
                    'id': row[0],
                    'ot': row[1],
                    'alias': row[2],
                    'setcode': row[3],
                    'type': row[4],
                    'atk': row[5],
                    'def': row[6],
                    'level': row[7],
                    'race': row[8],
                    'attribute': row[9],
                    'category': row[10],
                    'name': row[11] if len(row) > 11 else '',
                    'desc': row[12] if len(row) > 12 else '',
                }
                cards.append(card)

            return {
                'success': True,
                'total': total,
                'limit': limit,
                'offset': offset,
                'cards': cards
            }

        except Exception as e:
            conn.close()
            return {'success': False, 'message': f'搜索失败: {str(e)}', 'cards': []}

    def _db_to_frontend(self, datas: dict, texts: dict) -> dict:
        """将数据库字段反向映射为前端数据格式"""
        type_val = datas['type']

        # 判断卡片大类
        if type_val & 0x2:
            card_type = 'spell'
        elif type_val & 0x4:
            card_type = 'trap'
        else:
            card_type = 'monster'

        # 判断怪兽子类型
        monster_card_type = 'normal'
        if type_val & 0x4000000:
            monster_card_type = 'link'
        elif type_val & 0x800000:
            monster_card_type = 'xyz'
        elif type_val & 0x2000:
            monster_card_type = 'synchro'
        elif type_val & 0x40:
            monster_card_type = 'fusion'
        elif type_val & 0x80:
            monster_card_type = 'ritual'
        elif type_val & 0x20:
            monster_card_type = 'effect'

        if type_val & 0x1000000:
            card_type = 'pendulum'

        # 属性
        attr_reverse = {v: k for k, v in ATTRIBUTE_MAP.items()}
        attribute = attr_reverse.get(datas['attribute'], '')

        # 种族
        race_reverse = {v: k for k, v in RACE_MAP.items()}
        race = race_reverse.get(datas['race'], '')

        # 等级 / 阶级
        level = datas['level'] & 0xFFFF
        rank = level if monster_card_type == 'xyz' else 0
        if monster_card_type not in ('xyz', 'link'):
            pass  # level 保持

        # 灵摆刻度
        lscale = (datas['level'] >> 24) & 0xFF
        pendulum_scale = lscale if lscale > 0 else 0

        # Link 箭头
        arrow_list = []
        if monster_card_type == 'link':
            marker = datas['def']
            for i in range(8):
                if marker & (1 << i):
                    arrow_list.append(i + 1)

        result = {
            'password': datas['id'],
            'name': texts.get('name', ''),
            'description': texts.get('desc', ''),
            'pendulumDescription': texts.get('str1', ''),
            'type': card_type,
            'cardType': monster_card_type,
            'attribute': attribute,
            'monsterType': race,
            'level': level if monster_card_type not in ('xyz', 'link') else 0,
            'rank': rank,
            'pendulumScale': pendulum_scale,
            'atk': datas['atk'] if monster_card_type != 'link' else 0,
            'def': datas['def'] if monster_card_type != 'link' else 0,
            'arrowList': arrow_list,
            'setcode': datas['setcode'],
            'alias': datas['alias'],
            'ot': datas['ot'],
            'category': datas['category'],
        }

        # 处理负数（∞ 和 ?）
        if datas['atk'] < 0:
            result['atk'] = datas['atk']  # -1 前端自行处理显示
        if datas['def'] < 0 and monster_card_type != 'link':
            result['def'] = datas['def']

        return result


# 单例实例
card_writer = CardWriter()
