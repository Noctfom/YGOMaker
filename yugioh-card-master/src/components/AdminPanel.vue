<template>
  <div class="admin-panel">
    <div class="panel-header">
      <span class="panel-title">
        <span class="title-icon">⚙️</span>
        数据管理
      </span>
    </div>

    <div class="panel-body">
      <!-- ========== CDB 状态 ========== -->
      <div class="admin-section">
        <div class="section-title">
          <span class="section-icon">📊</span> CDB 状态
        </div>
        <div class="stats-grid" v-if="modsStatus">
          <div class="stat-item">
            <div class="stat-value">{{ modsStatus.total_custom_cards }}</div>
            <div class="stat-label">自定义卡片</div>
          </div>
          <div class="stat-item">
            <div class="stat-value">{{ modsStatus.total_custom_setcodes }}</div>
            <div class="stat-label">自定义系列</div>
          </div>
          <div class="stat-item">
            <div class="stat-value">{{ modsStatus.total_custom_counters }}</div>
            <div class="stat-label">自定义指示物</div>
          </div>
          <div class="stat-item">
            <div class="stat-value">{{ modsStatus.total_custom_victories }}</div>
            <div class="stat-label">自定义胜利条件</div>
          </div>
        </div>
      </div>

      <!-- ========== 更新合并 ========== -->
      <div class="admin-section">
        <div class="section-title">
          <span class="section-icon">🔄</span> 更新合并
        </div>
        <p class="section-desc">
          ① 拉取官方数据库 → ② 合并自制数据 → ③ 导出合并后文件<br/>
          有冲突会自动检测并提示调整。
        </p>
        <div class="merge-actions">
          <el-button size="small" type="danger" @click="handleFetchOfficial" :loading="mergeLoading">
            ⬇️ 覆盖拉取官方数据
          </el-button>
          <el-button size="small" type="primary" @click="handleUpdateAndMerge" :loading="mergeLoading">
            🔀 增量更新融合
          </el-button>
        </div>
        <div class="merge-actions" style="margin-top:8px;">
          <el-button size="small" type="warning" @click="handleCheckConflicts">
            ⚠️ 检查冲突
          </el-button>
        </div>
      </div>

      <!-- ========== 导入外部数据 ========== -->
      <div class="admin-section">
        <div class="section-title">
          <span class="section-icon">📥</span> 导入外部自制数据
        </div>
        <p class="section-desc">
          选择他人的 cards.cdb 和 strings.conf，自动提取其中 ≥1亿 的自制卡和自定义字段。<br/>
          卡密重复自动跳过，官方字段不覆盖。
        </p>
        <div class="merge-actions">
          <el-upload
            :auto-upload="false"
            :show-file-list="false"
            accept=".cdb"
            @change="handleCdbFileChange"
          >
            <el-button size="small" type="primary">
              📂 选择外部 CDB 文件
            </el-button>
          </el-upload>
          <el-upload
            :auto-upload="false"
            :show-file-list="false"
            accept=".conf"
            @change="handleStringsFileChange"
          >
            <el-button size="small" type="success">
              📂 选择外部 strings.conf
            </el-button>
          </el-upload>
        </div>
        <div class="merge-actions" style="margin-top:8px;">
          <el-button size="small" @click="handleImportForeign" :loading="mergeLoading" :disabled="!importFiles.cdb && !importFiles.strings">
            🔀 执行导入合并
          </el-button>
        </div>
        <div v-if="importFiles.cdb" class="field-row" style="margin-top:6px;">
          <span style="font-size:11px;color:#888;">CDB: {{ importFiles.cdb }}</span>
        </div>
        <div v-if="importFiles.strings" class="field-row" style="margin-top:2px;">
          <span style="font-size:11px;color:#888;">strings.conf: {{ importFiles.strings }}</span>
        </div>
        <div class="merge-actions" style="margin-top:8px;">
          <el-button size="small" @click="handleExportCdb">
            📦 导出合并后 CDB
          </el-button>
          <el-button size="small" @click="handleExportStrings">
            📝 导出合并后 strings.conf
          </el-button>
          <el-button size="small" type="warning" @click="handleCheckConflicts">
            ⚠️ 检查冲突
          </el-button>
        </div>
        <div v-if="mergeResult" class="merge-result">
          <div class="result-line" v-if="mergeResult.message">{{ mergeResult.message }}</div>
          <div class="result-line">卡片合并: {{ mergeResult.cards_merged || 0 }} 张</div>
          <div class="result-line">strings追加: {{ mergeResult.strings_appended ? '✅' : '❌' }}</div>
          <div class="result-line" v-if="mergeResult.has_conflicts" style="color:#e06c6c;">
            ⚠️ 发现 {{ mergeResult.conflicts?.length || 0 }} 个冲突
          </div>
        </div>
      </div>

      <!-- ========== 自定义系列名 ========== -->
      <div class="admin-section">
        <div class="section-title">
          <span class="section-icon">🏷️</span> 自定义系列名
        </div>
        <div class="field-list" v-if="customFields.setcodes">
          <div
            v-for="(name, code) in customFields.setcodes"
            :key="code"
            class="field-row"
          >
            <code class="field-code">0x{{ parseInt(code).toString(16).toUpperCase() }}</code>
            <span class="field-name">{{ name }}</span>
            <el-button size="small" type="danger" plain @click="removeField('setcode', code, name)">
              删除
            </el-button>
          </div>
          <div v-if="Object.keys(customFields.setcodes).length === 0" class="field-empty">
            暂无自定义系列
          </div>
        </div>
        <div class="field-add">
          <el-input v-model="newSetcodeCode" placeholder="编码(自动)" size="small" style="width:110px;" />
          <el-input v-model="newSetcodeName" placeholder="系列名称" size="small" style="width:180px;" />
          <el-button size="small" type="primary" @click="addField('setcode')">添加系列</el-button>
          <el-button size="small" @click="getNextCode('setcode')">自动分配编码</el-button>
        </div>
      </div>

      <!-- ========== 自定义指示物 ========== -->
      <div class="admin-section">
        <div class="section-title">
          <span class="section-icon">🔴</span> 自定义指示物
        </div>
        <div class="field-list" v-if="customFields.counters">
          <div
            v-for="(name, code) in customFields.counters"
            :key="code"
            class="field-row"
          >
            <code class="field-code">0x{{ parseInt(code).toString(16).toUpperCase() }}</code>
            <span class="field-name">{{ name }}</span>
            <el-button size="small" type="danger" plain @click="removeField('counter', code, name)">
              删除
            </el-button>
          </div>
          <div v-if="Object.keys(customFields.counters).length === 0" class="field-empty">
            暂无自定义指示物
          </div>
        </div>
        <div class="field-add">
          <el-input v-model="newCounterCode" placeholder="编码(自动)" size="small" style="width:110px;" />
          <el-input v-model="newCounterName" placeholder="指示物名称" size="small" style="width:180px;" />
          <el-button size="small" type="primary" @click="addField('counter')">添加指示物</el-button>
          <el-button size="small" @click="getNextCode('counter')">自动分配编码</el-button>
        </div>
      </div>

      <!-- ========== 自定义胜利条件 ========== -->
      <div class="admin-section">
        <div class="section-title">
          <span class="section-icon">🏆</span> 自定义胜利条件
        </div>
        <div class="field-list" v-if="customFields.victories">
          <div
            v-for="(name, code) in customFields.victories"
            :key="code"
            class="field-row"
          >
            <code class="field-code">0x{{ parseInt(code).toString(16).toUpperCase() }}</code>
            <span class="field-name">{{ name }}</span>
            <el-button size="small" type="danger" plain @click="removeField('victory', code, name)">
              删除
            </el-button>
          </div>
          <div v-if="Object.keys(customFields.victories).length === 0" class="field-empty">
            暂无自定义胜利条件
          </div>
        </div>
        <div class="field-add">
          <el-input v-model="newVictoryCode" placeholder="编码(自动)" size="small" style="width:110px;" />
          <el-input v-model="newVictoryName" placeholder="胜利条件描述" size="small" style="width:180px;" />
          <el-button size="small" type="primary" @click="addField('victory')">添加条件</el-button>
          <el-button size="small" @click="getNextCode('victory')">自动分配编码</el-button>
        </div>
      </div>

      <!-- ========== 官方 strings 浏览 ========== -->
      <div class="admin-section">
        <div class="section-title">
          <span class="section-icon">📖</span> 官方字段参考
        </div>
        <el-tabs v-model="stringsTab" type="card" size="small">
          <el-tab-pane label="系列名" name="setnames">
            <el-input
              v-model="stringsSearch"
              placeholder="搜索系列名..."
              size="small"
              clearable
              style="margin-bottom: 8px;"
            />
            <div class="official-list">
              <div
                v-for="item in filteredSetnames"
                :key="item.code"
                class="official-row"
              >
                <code>0x{{ item.hex }}</code>
                <span>{{ item.name }}</span>
                <span v-if="item.aliases" class="aliases">({{ item.aliases }})</span>
              </div>
            </div>
          </el-tab-pane>
          <el-tab-pane label="指示物" name="counters">
            <div class="official-list">
              <div
                v-for="(name, code) in officialCounters"
                :key="code"
                class="official-row"
              >
                <code>{{ code }}</code>
                <span>{{ name }}</span>
              </div>
            </div>
          </el-tab-pane>
          <el-tab-pane label="胜利条件" name="victories">
            <div class="official-list">
              <div
                v-for="(name, code) in officialVictories"
                :key="code"
                class="official-row"
              >
                <code>{{ code }}</code>
                <span>{{ name }}</span>
              </div>
            </div>
          </el-tab-pane>
        </el-tabs>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { api } from '@/api/index.js';

// 状态
const modsStatus = ref(null);
const customFields = ref({ setcodes: {}, counters: {}, victories: {} });
const mergeLoading = ref(false);
const mergeResult = ref(null);

// 导入文件
const importFiles = reactive({ cdb: null, strings: null, cdbFileName: '', stringsFileName: '' });

function handleCdbFileChange(file) {
  importFiles.cdb = file.raw;
  importFiles.cdbFileName = file.name;
}

function handleStringsFileChange(file) {
  importFiles.strings = file.raw;
  importFiles.stringsFileName = file.name;
}

async function handleImportForeign() {
  if (!importFiles.cdb && !importFiles.strings) {
    ElMessage.warning('请先选择外部数据文件');
    return;
  }
  mergeLoading.value = true;
  mergeResult.value = null;
  try {
    await ElMessageBox.confirm(
      '将提取外部文件中 ≥1亿 的自制卡和自定义字段进行合并且自动去重。继续？',
      '确认导入合并',
      { confirmButtonText: '继续', cancelButtonText: '取消', type: 'info' }
    );
    const result = await api.importForeignData(importFiles.cdb, importFiles.strings);
    mergeResult.value = result;
    ElMessage.success(`导入完成：卡片 ${result.cards_imported} 张，字段 ${result.strings_fields_added} 个`);
    // 清空文件
    importFiles.cdb = null;
    importFiles.strings = null;
    importFiles.cdbFileName = '';
    importFiles.stringsFileName = '';
    await refreshAll();
  } catch (e) {
    if (e !== 'cancel') ElMessage.error(`导入失败: ${e.message}`);
  } finally {
    mergeLoading.value = false;
  }
}

// 添加字段表单
const newSetcodeCode = ref('');
const newSetcodeName = ref('');
const newCounterCode = ref('');
const newCounterName = ref('');
const newVictoryCode = ref('');
const newVictoryName = ref('');

// 官方字段
const stringsTab = ref('setnames');
const stringsSearch = ref('');
const officialSetnames = ref([]);
const officialCounters = ref({});
const officialVictories = ref({});

const filteredSetnames = computed(() => {
  if (!stringsSearch.value) return officialSetnames.value.slice(0, 100);
  const kw = stringsSearch.value.toLowerCase();
  return officialSetnames.value.filter(s =>
    s.name.toLowerCase().includes(kw) || s.hex.toLowerCase().includes(kw)
  ).slice(0, 100);
});

// 加载
onMounted(async () => {
  await refreshAll();
});

async function refreshAll() {
  try {
    const [statusRes, fieldsRes, setnamesRes, countersRes, victoriesRes] = await Promise.all([
      api.getStatus(),
      api.customFields(),
      api.setnames(),
      api.counters(),
      api.victories(),
    ]);
    modsStatus.value = statusRes.status;
    customFields.value = fieldsRes.fields;
    officialSetnames.value = Object.entries(setnamesRes.setnames || {}).map(([k, v]) => ({
      hex: k,
      name: v.name,
      aliases: v.aliases?.join(', ') || ''
    }));
    officialCounters.value = countersRes.counters || {};
    officialVictories.value = victoriesRes.victories || {};
  } catch (e) {
    // API 可能未实现，静默
  }
}

// 更新合并
async function handleFetchOfficial() {
  mergeLoading.value = true;
  mergeResult.value = null;
  try {
    await ElMessageBox.confirm(
      '⚠️ 这将从官方仓库下载最新 cards.cdb 和 strings.conf，覆盖本地文件。\n\n自定义数据将在合并步骤中恢复。是否继续？',
      '确认拉取官方数据',
      { confirmButtonText: '继续', cancelButtonText: '取消', type: 'warning' }
    );
    const result = await api.fetchOfficial();
    ElMessage.success(result.message);
    mergeResult.value = { message: result.message };
    await refreshAll();
  } catch (e) {
    if (e !== 'cancel') ElMessage.error(`拉取失败: ${e.message}`);
  } finally {
    mergeLoading.value = false;
  }
}

async function handleMergeCustom() {
  mergeLoading.value = true;
  try {
    const result = await api.mergeCustom();
    mergeResult.value = result;
    if (result.has_conflicts) {
      ElMessage.warning(`合并完成，发现 ${result.conflicts.length} 个冲突`);
    } else {
      ElMessage.success(`合并完成：${result.cards_merged} 张卡片`);
    }
    await refreshAll();
  } catch (e) {
    ElMessage.error(`合并失败: ${e.message}`);
  } finally {
    mergeLoading.value = false;
  }
}

function handleExportCdb() {
  const a = document.createElement('a');
  a.href = api.getExportCdbUrl();
  a.download = `cards_${new Date().toISOString().slice(0,10)}.cdb`;
  a.click();
  ElMessage.success('CDB 文件下载中...');
}

function handleExportStrings() {
  const a = document.createElement('a');
  a.href = api.getExportStringsUrl();
  a.download = `strings_${new Date().toISOString().slice(0,10)}.conf`;
  a.click();
  ElMessage.success('strings.conf 文件下载中...');
}

async function handlePreMergeBackup() {
  mergeLoading.value = true;
  try {
    const result = await api.preMergeBackup();
    if (result.success) {
      // 下载备份数据
      const blob = new Blob([JSON.stringify(result.cards_data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `ygomaker_backup_${Date.now()}.json`;
      a.click();
      URL.revokeObjectURL(url);

      ElMessage.success(`已备份 ${result.card_count} 张自定义卡片`);

      // 显示 strings 片段
      if (result.strings_content) {
        ElMessageBox.alert(
          `<pre style="max-height:400px;overflow:auto;font-size:12px;">${result.strings_content}</pre>`,
          '自定义 strings 片段（请粘贴到 strings.conf 末尾）',
          { dangerouslyUseHTMLString: true, confirmButtonText: '已复制' }
        );
      }
    }
  } catch (e) {
    ElMessage.error(`备份失败: ${e.message}`);
  } finally {
    mergeLoading.value = false;
  }
}

async function handlePostMergeRestore() {
  mergeLoading.value = true;
  try {
    const result = await api.postMergeRestore();
    if (result.success) {
      ElMessage.success(result.message);
      await refreshAll();
    }
  } catch (e) {
    ElMessage.error(`恢复失败: ${e.message}`);
  } finally {
    mergeLoading.value = false;
  }
}

async function handleExportCustomStrings() {
  try {
    const result = await api.exportCustomStrings();
    if (result.success && result.content) {
      await ElMessageBox.alert(
        `<pre style="max-height:400px;overflow:auto;font-size:12px;">${result.content}</pre>`,
        '自定义 strings 片段',
        { dangerouslyUseHTMLString: true, confirmButtonText: '关闭' }
      );
    } else {
      ElMessage.info('暂无自定义 strings 内容');
    }
  } catch (e) {
    ElMessage.error(`导出失败: ${e.message}`);
  }
}

async function handleCheckConflicts() {
  try {
    const result = await api.checkConflicts();
    if (result.has_conflicts) {
      const msg = result.conflicts.map(c =>
        `[${c.type}] 编码 ${c.code}: 官方=" ${c.existing}"  vs 自定义=" ${c.custom}"`
      ).join('\n');
      ElMessageBox.alert(msg, '发现冲突', { confirmButtonText: '知道了' });
    } else {
      ElMessage.success('无冲突');
    }
  } catch (e) {
    ElMessage.error(`检查失败: ${e.message}`);
  }
}

// 字段管理
async function addField(type) {
  let code, name;
  if (type === 'setcode') { code = newSetcodeCode.value; name = newSetcodeName.value; }
  else if (type === 'counter') { code = newCounterCode.value; name = newCounterName.value; }
  else { code = newVictoryCode.value; name = newVictoryName.value; }

  if (!name.trim()) { ElMessage.warning('请输入名称'); return; }
  if (!code.trim()) {
    const next = await getNextCode(type, true);
    if (!next) return;
    code = next;
  }

  try {
    await api.addCustomField(type, code, name);
    ElMessage.success('添加成功');
    if (type === 'setcode') { newSetcodeCode.value = ''; newSetcodeName.value = ''; }
    else if (type === 'counter') { newCounterCode.value = ''; newCounterName.value = ''; }
    else { newVictoryCode.value = ''; newVictoryName.value = ''; }
    await refreshAll();
  } catch (e) {
    ElMessage.error(`添加失败: ${e.message}`);
  }
}

async function handleUpdateAndMerge() {
  mergeLoading.value = true;
  mergeResult.value = null;
  try {
    await ElMessageBox.confirm(
      '🔀 增量更新融合：\n\n① 从远程拉取官方最新 CDB + strings.conf\n② 自动将本地自定义卡片和字段融合进去\n③ 去重处理，保留自制数据\n\n是否继续？',
      '确认增量更新融合',
      { confirmButtonText: '继续', cancelButtonText: '取消', type: 'info' }
    );
    const result = await api.updateAndMerge();
    mergeResult.value = result;
    ElMessage.success(`融合完成：官方 ${result.official_card_count} 张 + 自定义 ${result.custom_cards_merged} 张`);
    await refreshAll();
  } catch (e) {
    if (e !== 'cancel') ElMessage.error(`融合失败: ${e.message}`);
  } finally {
    mergeLoading.value = false;
  }
}

async function removeField(type, code, name) {
  try {
    await ElMessageBox.confirm(`确定删除 ${type}【${name}】？`, '确认删除', { type: 'warning' });
    await api.removeField(type, code);
    ElMessage.success(`已删除 ${type}【${name}】`);
    await refreshAll();
  } catch (e) {
    if (e !== 'cancel') ElMessage.error(`删除失败: ${e.message}`);
  }
}

async function getNextCode(type, silent = false) {
  try {
    const result = await api.nextAvailableCode(type);
    const codeStr = result.next_code;
    if (!silent) {
      if (type === 'setcode') newSetcodeCode.value = codeStr;
      else if (type === 'counter') newCounterCode.value = codeStr;
      else newVictoryCode.value = codeStr;
    }
    if (!silent) ElMessage.success(`已分配编码: ${codeStr}`);
    return codeStr;
  } catch (e) {
    if (!silent) ElMessage.error(`获取编码失败: ${e.message}`);
    return null;
  }
}
</script>

<style lang="scss" scoped>
.admin-panel {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: linear-gradient(180deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
  overflow: hidden;

  .panel-header {
    padding: 14px 18px;
    background: rgba(0, 0, 0, 0.3);
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    flex-shrink: 0;

    .panel-title {
      font-size: 16px;
      font-weight: 700;
      color: #e8d5a3;
      display: flex;
      align-items: center;
      gap: 8px;

      .title-icon { font-size: 18px; }
    }
  }

  .panel-body {
    flex: 1;
    overflow-y: auto;
    padding: 10px 14px;

    &::-webkit-scrollbar { width: 4px; }
    &::-webkit-scrollbar-thumb { background: rgba(255,255,255,.1); border-radius: 2px; }
  }
}

.admin-section {
  margin-bottom: 16px;
  padding: 12px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 8px;

  .section-title {
    font-size: 13px;
    font-weight: 700;
    color: #c8a84e;
    margin-bottom: 10px;
    display: flex;
    align-items: center;
    gap: 6px;

    .section-icon { font-size: 14px; }
  }

  .section-desc {
    font-size: 11px;
    color: #777;
    margin-bottom: 10px;
    line-height: 1.6;
  }
}

.stats-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;

  .stat-item {
    text-align: center;
    padding: 8px;
    background: rgba(255, 255, 255, 0.04);
    border-radius: 6px;

    .stat-value { font-size: 20px; font-weight: 700; color: #e8d5a3; }
    .stat-label { font-size: 10px; color: #888; margin-top: 2px; }
  }
}

.merge-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.field-list {
  margin-bottom: 8px;

  .field-row {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 6px 8px;
    background: rgba(255,255,255,0.03);
    border-radius: 4px;
    margin-bottom: 4px;

    .field-code { font-size: 11px; color: #c8a84e; min-width: 60px; }
    .field-name { font-size: 12px; color: #ccc; flex: 1; }
  }

  .field-empty {
    font-size: 12px;
    color: #555;
    padding: 8px;
    text-align: center;
  }
}

.field-add {
  display: flex;
  gap: 6px;
  align-items: center;
  flex-wrap: wrap;

  :deep(.el-input__wrapper) {
    background: rgba(255,255,255,0.05);
    border-color: rgba(255,255,255,0.08);
  }
}

.official-list {
  max-height: 300px;
  overflow-y: auto;

  .official-row {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 4px 8px;
    font-size: 11px;
    border-bottom: 1px solid rgba(255,255,255,0.03);

    code { color: #888; min-width: 60px; font-size: 10px; }
    span { color: #ccc; }

    .aliases { color: #666; font-size: 10px; }
  }
}

/* Element Plus tabs 暗色覆盖 */
:deep(.el-tabs) {
  --el-tabs-header-height: 32px;

  .el-tabs__header { margin-bottom: 8px; }
  .el-tabs__item {
    font-size: 11px;
    color: #888;
    height: 30px;
    line-height: 30px;
    &.is-active { color: #e8d5a3; }
  }
  .el-tabs__nav { border-color: rgba(255,255,255,0.06); }
}

:deep(.el-button) { font-size: 11px; }
:deep(.el-input__inner) { color: #ccc; font-size: 11px; }
</style>
