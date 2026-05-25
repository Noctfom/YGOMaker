# -*- coding: utf-8 -*-
"""
YGOMaker 后端服务 - FastAPI
提供卡片CDB写入、查询、管理功能，以及前端静态文件服务
"""

import sys
import os
import sqlite3
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, List

from card_writer import card_writer
from config import SERVER_PORT, CORS_ORIGINS, BACKUP_DIR, CDB_PATH, STRINGS_PATH, SCRIPT_DIR
from strings_parser import strings_db
from local_mods_tracker import mods_tracker

app = FastAPI(title="YGOMaker", description="游戏王制卡器", version="2.0.0")

app.add_middleware(CORSMiddleware, allow_origins=CORS_ORIGINS, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# 前端 dist 路径
FRONTEND_DIST = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'yugioh-card-master', 'dist')
HAS_FRONTEND = os.path.exists(os.path.join(FRONTEND_DIST, 'index.html'))

# ============================================================
#  Pydantic 模型
# ============================================================

class CardData(BaseModel):
    password: int = 0
    name: str = ''
    type: str = 'monster'
    cardType: str = 'normal'
    attribute: str = ''
    monsterType: str = ''
    level: int = 0
    rank: int = 0
    pendulumScale: int = 0
    pendulumDescription: str = ''
    atk: int = 0
    def_: int = 0
    arrowList: List[int] = []
    description: str = ''
    image: str = ''
    font: str = ''
    language: str = 'sc'
    color: str = ''
    align: str = 'left'
    gradient: bool = False
    gradientColor1: str = '#999999'
    gradientColor2: str = '#ffffff'
    icon: str = ''
    firstLineCompress: bool = False
    descriptionAlign: bool = False
    descriptionZoom: float = 1.0
    descriptionWeight: int = 0
    package: str = ''
    copyright: str = ''
    laser: str = ''
    rare: str = ''
    twentieth: bool = False
    radius: bool = True
    scale: int = 1
    atkBar: bool = True
    setcode: int = 0
    alias: int = 0
    ot: int = 0x1
    category: int = 0
    abilities: List[str] = []
    model_config = {"populate_by_name": True}

class WriteRequest(BaseModel):
    card: CardData
    overwrite: bool = False

class BatchWriteRequest(BaseModel):
    cards: List[CardData]
    overwrite: bool = False

# ============================================================
#  前端静态文件
# ============================================================

if HAS_FRONTEND:
    assets_path = os.path.join(FRONTEND_DIST, 'assets')
    if os.path.exists(assets_path):
        app.mount("/assets", StaticFiles(directory=assets_path), name="assets")

    @app.get("/", response_class=HTMLResponse)
    async def serve_frontend():
        with open(os.path.join(FRONTEND_DIST, 'index.html'), 'r', encoding='utf-8') as f:
            return f.read()

# ============================================================
#  API 路由
# ============================================================

@app.get("/api/status")
def get_status():
    backup_files = sorted(os.listdir(BACKUP_DIR))[-10:] if os.path.exists(BACKUP_DIR) else []
    return {"status": "running", "backup_count": len(backup_files)}

# --- 卡片 CRUD ---

@app.post("/api/card/write")
def write_card(req: WriteRequest):
    card_dict = req.card.model_dump(by_alias=False)
    if 'def_' in card_dict:
        card_dict['def'] = card_dict.pop('def_')
    result = card_writer.write_card(card_dict, overwrite=req.overwrite)
    if not result['success']:
        raise HTTPException(400, detail=result['message'])
    return result

@app.post("/api/card/batch")
def batch_write(req: BatchWriteRequest):
    cards_list = []
    for card in req.cards:
        cd = card.model_dump(by_alias=False)
        if 'def_' in cd: cd['def'] = cd.pop('def_')
        cards_list.append(cd)
    return card_writer.batch_write(cards_list, overwrite=req.overwrite)

@app.get("/api/card/next-id")
def get_next_id(primary: bool = Query(True)):
    result = card_writer.get_next_id(use_primary=primary)
    if not result['success']: raise HTTPException(500, detail=result['message'])
    return result

@app.get("/api/card/search")
def search_cards(keyword: str = Query(''), limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0)):
    return card_writer.search_cards(keyword=keyword, limit=limit, offset=offset)

@app.get("/api/card/{card_id}")
def get_card(card_id: int):
    result = card_writer.get_card(card_id)
    if result is None: raise HTTPException(404, detail=f'卡片 {card_id} 不存在')
    if 'error' in result: raise HTTPException(500, detail=result['error'])
    return {"success": True, "card": result}

@app.delete("/api/card/{card_id}")
def delete_card(card_id: int):
    result = card_writer.delete_card(card_id)
    if not result['success']: raise HTTPException(400, detail=result['message'])
    mods_tracker.remove_custom_card(card_id)
    return result

# --- strings.conf 查询 ---

@app.get("/api/strings/setnames")
def get_setnames():
    strings_db.load()
    return {'success': True, 'count': len(strings_db.setnames), 'setnames': {f'0x{k:X}': v for k, v in strings_db.setnames.items()}}

@app.get("/api/strings/counters")
def get_counters():
    strings_db.load()
    return {'success': True, 'counters': {f'0x{k:X}': v for k, v in strings_db.counters.items()}}

@app.get("/api/strings/victories")
def get_victories():
    strings_db.load()
    return {'success': True, 'victories': {f'0x{k:X}': v for k, v in strings_db.victories.items()}}

@app.get("/api/strings/next-available")
def get_next_available(field_type: str = Query('setcode')):
    strings_db.load()
    if field_type == 'counter': code = strings_db.get_next_available_counter()
    elif field_type == 'victory': code = strings_db.get_next_available_victory()
    else: code = strings_db.get_next_available_setcode()
    return {'success': True, 'next_code': f'0x{code:X}', 'decimal': code, 'type': field_type}

# --- 本地修改追踪 ---

@app.get("/api/mods/status")
def get_mods_status():
    return {'success': True, 'status': mods_tracker.get_merge_status()}

@app.get("/api/mods/custom-fields")
def get_custom_fields():
    return {'success': True, 'fields': mods_tracker.get_custom_fields()}

@app.post("/api/mods/add-field")
def add_custom_field(field_type: str = Query(...), code: str = Query(...), name: str = Query(...)):
    try:
        int_code = int(code, 16) if code.startswith('0x') else int(code)
    except ValueError:
        raise HTTPException(400, detail=f'无效编码: {code}')
    if field_type == 'setcode': mods_tracker.add_custom_setcode(int_code, name)
    elif field_type == 'counter': mods_tracker.add_custom_counter(int_code, name)
    elif field_type == 'victory': mods_tracker.add_custom_victory(int_code, name)
    else: raise HTTPException(400, detail=f'未知字段类型: {field_type}')
    return {'success': True, 'type': field_type, 'code': code, 'name': name}

@app.delete("/api/mods/remove-field")
def remove_custom_field(field_type: str = Query(...), code: str = Query(...)):
    try:
        int_code = int(code, 16) if code.startswith('0x') else int(code)
    except ValueError:
        raise HTTPException(400, detail=f'无效编码: {code}')
    if field_type == 'setcode': mods_tracker.remove_setcode(int_code)
    elif field_type == 'counter': mods_tracker.remove_counter(int_code)
    elif field_type == 'victory': mods_tracker.remove_victory(int_code)
    else: raise HTTPException(400, detail=f'未知字段类型: {field_type}')
    _cleanup_strings_conf()
    return {'success': True, 'type': field_type, 'code': code}

@app.get("/api/mods/conflicts")
def check_conflicts():
    fields = mods_tracker.get_custom_fields()
    formatted = {'setnames': {}, 'counters': {}, 'victories': {}}
    for k, v in fields['setcodes'].items(): formatted['setnames'][int(k)] = {'name': v}
    for k, v in fields['counters'].items(): formatted['counters'][int(k)] = v
    for k, v in fields['victories'].items(): formatted['victories'][int(k)] = v
    conflicts = strings_db.check_conflicts(formatted)
    return {'success': True, 'conflicts': conflicts, 'has_conflicts': len(conflicts) > 0}

# --- 更新合并 ---

def _cleanup_strings_conf():
    if not os.path.exists(STRINGS_PATH): return
    with open(STRINGS_PATH, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    cleaned = []
    skip = False
    for line in lines:
        if '# YGOMaker ' in line:
            skip = True
            continue
        if skip:
            if line.strip().startswith('!setname') or line.strip().startswith('!counter') or \
               line.strip().startswith('!victory') or line.strip().startswith('# 自定义'):
                continue
            skip = False
        cleaned.append(line)
    while cleaned and cleaned[-1].strip() == '':
        cleaned.pop()
    with open(STRINGS_PATH, 'w', encoding='utf-8') as f:
        f.writelines(cleaned)

@app.post("/api/update/fetch-official")
def fetch_official():
    try:
        import subprocess, urllib.request, tempfile, shutil
        req = urllib.request.Request("https://raw.githubusercontent.com/mycard/ygopro-database/master/locales/zh-CN/cards.cdb", headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as resp:
            with open(CDB_PATH, 'wb') as f: f.write(resp.read())
        req2 = urllib.request.Request("https://raw.githubusercontent.com/mycard/ygopro-database/master/locales/zh-CN/strings.conf", headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req2) as resp:
            with open(STRINGS_PATH, 'wb') as f: f.write(resp.read())
        script_repo = "https://github.com/Fluorohydride/ygopro-scripts.git"
        with tempfile.TemporaryDirectory() as tmp_dir:
            subprocess.run(["git", "clone", "--depth", "1", script_repo, tmp_dir], capture_output=True, text=True, check=True)
            if not os.path.exists(SCRIPT_DIR): os.makedirs(SCRIPT_DIR)
            moved = 0
            for root, _, files in os.walk(tmp_dir):
                if '.git' in root: continue
                for file in files:
                    if file.endswith('.lua'):
                        shutil.copy2(os.path.join(root, file), os.path.join(SCRIPT_DIR, file))
                        moved += 1
        strings_db._loaded = False
        strings_db.load()
        return {'success': True, 'message': '官方数据已拉取', 'scripts_updated': moved}
    except Exception as e:
        raise HTTPException(500, detail=f'拉取失败: {str(e)}')

@app.post("/api/update/merge-custom")
def merge_custom():
    result = {'success': True, 'cards_merged': 0, 'strings_appended': False, 'conflicts': [], 'has_conflicts': False}
    cards_data = mods_tracker.export_custom_cards_data()
    if cards_data:
        result['cards_merged'] = mods_tracker.reimport_custom_cards(cards_data)
    _cleanup_strings_conf()
    custom_strings = mods_tracker.export_custom_strings()
    if custom_strings.strip():
        with open(STRINGS_PATH, 'a', encoding='utf-8') as f:
            f.write('\n' + custom_strings)
        result['strings_appended'] = True
    strings_db._loaded = False
    strings_db.load()
    fields = mods_tracker.get_custom_fields()
    formatted = {'setnames': {}, 'counters': {}, 'victories': {}}
    for k, v in fields['setcodes'].items(): formatted['setnames'][int(k)] = {'name': v}
    for k, v in fields['counters'].items(): formatted['counters'][int(k)] = v
    for k, v in fields['victories'].items(): formatted['victories'][int(k)] = v
    conflicts = strings_db.check_conflicts(formatted)
    result['conflicts'] = conflicts
    result['has_conflicts'] = len(conflicts) > 0
    return result

@app.post("/api/update/update-and-merge")
def update_and_merge():
    import tempfile, urllib.request, shutil
    result = {'success': True, 'official_card_count': 0, 'custom_cards_merged': 0, 'strings_appended': False, 'conflicts': [], 'has_conflicts': False}
    try:
        tmp_dir = tempfile.mkdtemp(prefix='ygomaker_')
        tmp_cdb = os.path.join(tmp_dir, 'cards.cdb')
        tmp_strings = os.path.join(tmp_dir, 'strings.conf')
        req = urllib.request.Request("https://raw.githubusercontent.com/mycard/ygopro-database/master/locales/zh-CN/cards.cdb", headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as resp:
            with open(tmp_cdb, 'wb') as f: f.write(resp.read())
        req2 = urllib.request.Request("https://raw.githubusercontent.com/mycard/ygopro-database/master/locales/zh-CN/strings.conf", headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req2) as resp:
            with open(tmp_strings, 'wb') as f: f.write(resp.read())
        tmp_conn = sqlite3.connect(tmp_cdb)
        result['official_card_count'] = tmp_conn.execute("SELECT COUNT(*) FROM datas").fetchone()[0]
        tmp_conn.close()
        # 替换前先导出自定义卡片
        cards_data = mods_tracker.export_custom_cards_data()
        if os.path.exists(CDB_PATH): shutil.copy2(CDB_PATH, CDB_PATH + '.bak')
        shutil.copy2(tmp_cdb, CDB_PATH)
        if cards_data:
            result['custom_cards_merged'] = mods_tracker.reimport_custom_cards(cards_data)
        if os.path.exists(STRINGS_PATH): shutil.copy2(STRINGS_PATH, STRINGS_PATH + '.bak')
        shutil.copy2(tmp_strings, STRINGS_PATH)
        custom_strings = mods_tracker.export_custom_strings()
        if custom_strings.strip():
            with open(STRINGS_PATH, 'a', encoding='utf-8') as f: f.write('\n' + custom_strings)
            result['strings_appended'] = True
        strings_db._loaded = False
        strings_db.load()
        shutil.rmtree(tmp_dir, ignore_errors=True)
        fields = mods_tracker.get_custom_fields()
        formatted = {'setnames': {}, 'counters': {}, 'victories': {}}
        for k, v in fields['setcodes'].items(): formatted['setnames'][int(k)] = {'name': v}
        for k, v in fields['counters'].items(): formatted['counters'][int(k)] = v
        for k, v in fields['victories'].items(): formatted['victories'][int(k)] = v
        conflicts = strings_db.check_conflicts(formatted)
        result['conflicts'] = conflicts
        result['has_conflicts'] = len(conflicts) > 0
        return result
    except Exception as e:
        raise HTTPException(500, detail=f'增量融合失败: {str(e)}')

@app.get("/api/export/cdb")
def export_cdb():
    if not os.path.exists(CDB_PATH): raise HTTPException(404, detail='cards.cdb 不存在')
    return FileResponse(os.path.abspath(CDB_PATH), media_type='application/octet-stream', filename=f'cards_{datetime.now().strftime("%Y%m%d")}.cdb')

@app.get("/api/export/strings")
def export_strings():
    if not os.path.exists(STRINGS_PATH): raise HTTPException(404, detail='strings.conf 不存在')
    return FileResponse(os.path.abspath(STRINGS_PATH), media_type='text/plain; charset=utf-8', filename=f'strings_{datetime.now().strftime("%Y%m%d")}.conf')

# --- 导入外部自制数据 ---

@app.post("/api/import/foreign-cdb")
def import_foreign_cdb():
    """
    接收上传的外部 cards.cdb 文件，提取其中的自制卡（≥1亿），
    与现有卡密去重后写入当前 CDB。
    """
    import tempfile, shutil
    try:
        # 保存上传的临时文件
        tmp_path = os.path.join(tempfile.gettempdir(), 'ygomaker_import.cdb')
        # Note: FastAPI 需要文件上传，这里先用读取已有文件的方式
        # 实际通过 multipart/form-data 上传
    except Exception as e:
        raise HTTPException(500, detail=str(e))


@app.post("/api/import/foreign-data")
async def import_foreign_data(cdb_file: UploadFile = None, strings_file: UploadFile = None):
    """
    合并外部的自制卡数据和配置文件。

    工作流：
    ① 上传外部 cards.cdb → 提取≥1亿的自制卡 → 去重后写入
    ② 上传外部 strings.conf → 解析自定义字段 → 追加到本地 strings.conf
    ③ 返回合并统计和冲突报告

    卡密去重：相同 ID 的自制卡不重复写入
    strings 字段去重：已在 strings.conf 中或已在 mods_tracker 中的不重复追加
    """
    result = {
        'success': True,
        'cards_imported': 0,
        'cards_skipped': 0,
        'strings_fields_added': 0,
        'strings_fields_skipped': 0,
        'id_conflicts': [],
        'errors': []
    }

    existing_ids = set()
    try:
        conn = sqlite3.connect(CDB_PATH)
        rows = conn.execute("SELECT id FROM datas WHERE id >= 100000000").fetchall()
        existing_ids = set(r[0] for r in rows)
        conn.close()
    except Exception as e:
        result['errors'].append(f'读取本地CDB失败: {e}')

    # 处理外部 CDB
    if cdb_file:
        import tempfile, shutil
        tmp_cdb = tempfile.NamedTemporaryFile(delete=False, suffix='.cdb')
        try:
            content = await cdb_file.read()
            tmp_cdb.write(content)
            tmp_cdb.close()

            ext_conn = sqlite3.connect(tmp_cdb.name)
            cursor = ext_conn.cursor()
            cursor.execute("SELECT id FROM datas WHERE id >= 100000000")
            foreign_ids = [r[0] for r in cursor.fetchall()]

            imported = 0
            skipped = 0
            conflicts = []

            for fid in foreign_ids:
                if fid in existing_ids:
                    skipped += 1
                    conflicts.append({'id': fid, 'reason': '卡密已存在'})
                    continue

                # 读取外部卡片的完整数据
                cursor.execute("SELECT * FROM datas WHERE id = ?", (fid,))
                d_row = cursor.fetchone()
                if not d_row: continue

                # 写入本地 CDB
                conn = sqlite3.connect(CDB_PATH)
                try:
                    conn.execute("""
                        INSERT INTO datas (id, ot, alias, setcode, type, atk, def, level, race, attribute, category)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (fid, d_row[1], d_row[2], d_row[3], d_row[4], d_row[5], d_row[6], d_row[7], d_row[8], d_row[9], d_row[10]))

                    # 读取外部 texts
                    cursor.execute("SELECT * FROM texts WHERE id = ?", (fid,))
                    t_row = cursor.fetchone()
                    if t_row:
                        conn.execute("""
                            INSERT INTO texts (id, name, desc, str1, str2, str3, str4, str5, str6, str7, str8, str9, str10, str11, str12, str13, str14, str15, str16)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (t_row[0], t_row[1], t_row[2], t_row[3], t_row[4], t_row[5], t_row[6], t_row[7], t_row[8], t_row[9], t_row[10], t_row[11], t_row[12], t_row[13], t_row[14], t_row[15], t_row[16]))

                    conn.commit()
                    imported += 1
                    existing_ids.add(fid)
                    # 标记为自定义卡片
                    mods_tracker.mark_card_as_custom(fid)
                except Exception as e:
                    result['errors'].append(f'导入卡片 {fid} 失败: {e}')
                finally:
                    conn.close()

            ext_conn.close()
            os.unlink(tmp_cdb.name)

            result['cards_imported'] = imported
            result['cards_skipped'] = skipped
            result['id_conflicts'] = conflicts
        except Exception as e:
            result['errors'].append(f'处理外部CDB失败: {e}')

    # 处理外部 strings.conf
    if strings_file:
        try:
            content = (await strings_file.read()).decode('utf-8', errors='ignore')
            foreign_fields = {'setnames': {}, 'counters': {}, 'victories': {}}

            # 解析外部 strings.conf 中的自定义条目
            strings_db.load()
            for line in content.split('\n'):
                line = line.strip()
                if not line or line.startswith('#'): continue

                if line.startswith('!setname '):
                    parts = line[9:].split(None, 1)
                    if len(parts) >= 2:
                        try:
                            code = int(parts[0], 16)
                            name = parts[1]
                            # 检查是否已在官方中或已在本地自定义中
                            if code in strings_db.setnames:
                                result['strings_fields_skipped'] += 1
                            elif str(code) in mods_tracker.data.get('custom_setcodes', {}):
                                result['strings_fields_skipped'] += 1
                            else:
                                foreign_fields['setnames'][str(code)] = name
                                result['strings_fields_added'] += 1
                                mods_tracker.add_custom_setcode(code, name)
                        except ValueError:
                            pass

                elif line.startswith('!counter '):
                    parts = line[9:].split(None, 1)
                    if len(parts) >= 2:
                        try:
                            code = int(parts[0], 16)
                            name = parts[1]
                            if code in strings_db.counters:
                                result['strings_fields_skipped'] += 1
                            elif str(code) in mods_tracker.data.get('custom_counters', {}):
                                result['strings_fields_skipped'] += 1
                            else:
                                foreign_fields['counters'][str(code)] = name
                                result['strings_fields_added'] += 1
                                mods_tracker.add_custom_counter(code, name)
                        except ValueError:
                            pass

                elif line.startswith('!victory '):
                    parts = line[9:].split(None, 1)
                    if len(parts) >= 2:
                        try:
                            code = int(parts[0], 16)
                            desc = parts[1]
                            if code in strings_db.victories:
                                result['strings_fields_skipped'] += 1
                            elif str(code) in mods_tracker.data.get('custom_victories', {}):
                                result['strings_fields_skipped'] += 1
                            else:
                                foreign_fields['victories'][str(code)] = desc
                                result['strings_fields_added'] += 1
                                mods_tracker.add_custom_victory(code, desc)
                        except ValueError:
                            pass

            # 重新生成 strings.conf
            if result['strings_fields_added'] > 0:
                _cleanup_strings_conf()
                custom_strings = mods_tracker.export_custom_strings()
                if custom_strings.strip():
                    with open(STRINGS_PATH, 'a', encoding='utf-8') as f:
                        f.write('\n' + custom_strings)

        except Exception as e:
            result['errors'].append(f'处理外部strings.conf失败: {e}')

    return result

if __name__ == '__main__':
    import uvicorn
    print(f"YGOMaker v2.0 - http://localhost:{SERVER_PORT}")
    uvicorn.run(app, host="0.0.0.0", port=SERVER_PORT, log_level="info")
