<template>
  <div class="ygomaker-app">
    <!-- ==================== 左侧面板：按模式切换 ==================== -->
    <div class="panel panel-left" :style="{ width: leftPanelWidth + 'px' }">
      <div class="panel-resize-handle" @mousedown="startResize('left', $event)"></div>
      <CardListPanel
        v-if="currentMode === 'card'"
        ref="cardListRef"
        @select-card="handleSelectCard"
        @card-deleted="handleCardDeleted"
      />
      <AdminPanel v-if="currentMode === 'admin'" />
    </div>

    <!-- ==================== 中间面板：卡片预览 ==================== -->
    <div class="panel panel-center" :class="{ 'theme-light': !isDarkMode }">
      <div class="center-toolbar">
        <div class="toolbar-title">
          <span class="toolbar-icon">{{ currentMode === 'card' ? '🃏' : '⚙️' }}</span>
          <span>YGOMaker {{ currentMode === 'card' ? '制卡器' : '管理' }}</span>
        </div>
        <div class="toolbar-actions">
          <el-button-group size="small" style="margin-right: 6px;">
            <el-button :type="currentMode === 'card' ? 'primary' : ''" @click="currentMode = 'card'">
              🃏 制卡
            </el-button>
            <el-button :type="currentMode === 'admin' ? 'primary' : ''" @click="currentMode = 'admin'">
              ⚙️ 管理
            </el-button>
          </el-button-group>
          <template v-if="currentMode === 'card'">
            <el-button size="small" @click="handleNewCard" :icon="Plus">
              新建卡片
            </el-button>
            <el-button size="small" @click="handleExportImage">
              导出图片
            </el-button>
          </template>
          <el-tooltip :content="isDarkMode ? '切换日间模式' : '切换夜间模式'" placement="bottom">
            <el-button size="small" circle @click="toggleTheme">
              {{ isDarkMode ? '☀️' : '🌙' }}
            </el-button>
          </el-tooltip>
          <el-tooltip content="切换JSON编辑器" placement="bottom">
            <el-button size="small" :type="showJsonEditor ? 'primary' : ''" @click="showJsonEditor = !showJsonEditor" circle>
              <span style="font-weight: 700;">{ }</span>
            </el-button>
          </el-tooltip>
        </div>
      </div>

      <div class="preview-area" :class="{ 'theme-light': !isDarkMode }">
        <!-- 制卡模式 -->
        <template v-if="currentMode === 'card'">
          <div class="preview-container" v-if="!showJsonEditor">
            <YugiohCardPreview
              ref="cardPreviewRef"
              :key="previewKey"
              :card-data="currentCardData"
            />
          </div>
          <div class="json-editor-container" v-if="showJsonEditor">
            <json-editor-vue
              v-model="jsonDataStr"
              style="width: 100%; height: 100%"
              mode="text"
              v-bind="jsonOption"
            />
          </div>
        </template>
        <!-- 管理模式 -->
        <div class="preview-container" v-if="currentMode === 'admin'">
          <div class="admin-welcome">
            <div class="welcome-icon">⚙️</div>
            <div class="welcome-title">数据管理</div>
            <div class="welcome-desc">
              在左侧面板管理自定义系列、指示物、胜利条件<br/>
              备份和恢复卡片数据以安全更新官方数据库
            </div>
          </div>
        </div>
      </div>

      <!-- 底部状态栏 -->
      <div class="center-statusbar">
        <span class="status-item" v-if="currentCardData.password">
          卡密: {{ currentCardData.password }}
        </span>
        <span class="status-item" v-if="currentCardData.name">
          {{ currentCardData.name }}
        </span>
        <span class="status-item status-server" :class="{ online: serverOnline }">
          {{ serverOnline ? '🟢 服务已连接' : '🔴 服务离线' }}
        </span>
      </div>
    </div>

    <!-- ==================== 右侧面板：卡片表单（仅制卡模式） ==================== -->
    <div class="panel panel-right" :style="{ width: rightPanelWidth + 'px' }" v-if="currentMode === 'card'">
      <div class="panel-resize-handle left-handle" @mousedown="startResize('right', $event)"></div>
      <CardFormPanel
        v-model="currentCardData"
        @card-written="handleCardWritten"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, watch, onMounted, onBeforeUnmount } from 'vue';
import { Plus } from '@element-plus/icons-vue';
import JsonEditorVue from 'json-editor-vue';
import CardListPanel from '@/components/CardListPanel.vue';
import CardFormPanel from '@/components/CardFormPanel.vue';
import YugiohCardPreview from '@/components/YugiohCardPreview.vue';
import AdminPanel from '@/components/AdminPanel.vue';
import { api } from '@/api/index.js';

// ======================== 引用 ========================
const cardListRef = ref(null);
const cardPreviewRef = ref(null);

// ======================== 面板大小 ========================
const leftPanelWidth = ref(280);
const rightPanelWidth = ref(380);

// ======================== 卡片数据 ========================
const currentCardData = reactive(getDefaultCardData());

// JSON 编辑器
const showJsonEditor = ref(false);
const jsonDataStr = ref('');
const jsonOption = reactive({
  mainMenuBar: false,
  statusBar: false,
});

// 主题与预览刷新
const isDarkMode = ref(true);
const previewKey = ref(0);

// 模式切换
const currentMode = ref('card'); // 'card' | 'admin'

function toggleTheme() {
  isDarkMode.value = !isDarkMode.value;
  document.body.classList.toggle('theme-light', !isDarkMode.value);
}

// 服务器状态
const serverOnline = ref(false);

// 重设面板大小
let resizing = null;
let resizeStartX = 0;
let resizeStartWidth = 0;

function startResize(panel, event) {
  resizing = panel;
  resizeStartX = event.clientX;
  resizeStartWidth = panel === 'left' ? leftPanelWidth.value : rightPanelWidth.value;
  document.addEventListener('mousemove', handleResize);
  document.addEventListener('mouseup', stopResize);
  document.body.style.cursor = 'col-resize';
  document.body.style.userSelect = 'none';
}

function handleResize(event) {
  if (!resizing) return;
  const delta = event.clientX - resizeStartX;
  const newWidth = resizeStartWidth + (resizing === 'right' ? -delta : delta);

  const clamped = Math.max(220, Math.min(500, newWidth));
  if (resizing === 'left') {
    leftPanelWidth.value = clamped;
  } else {
    rightPanelWidth.value = clamped;
  }
}

function stopResize() {
  resizing = null;
  document.removeEventListener('mousemove', handleResize);
  document.removeEventListener('mouseup', stopResize);
  document.body.style.cursor = '';
  document.body.style.userSelect = '';
}

// ======================== 数据同步 ========================
watch(currentCardData, (val) => {
  jsonDataStr.value = JSON.stringify(val, null, 2);
}, { deep: true, immediate: true });

watch(jsonDataStr, (val) => {
  try {
    const parsed = JSON.parse(val);
    Object.assign(currentCardData, parsed);
  } catch {
    // JSON 编辑中，忽略解析错误
  }
});

// ======================== 方法 ========================
function getDefaultCardData() {
  return {
    password: '',
    name: '',
    type: 'monster',
    cardType: 'effect',
    attribute: 'dark',
    monsterType: '',
    level: 4,
    rank: 0,
    pendulumScale: 0,
    pendulumDescription: '',
    atk: 0,
    def: 0,
    arrowList: [],
    description: '',
    image: '',
    font: '',
    language: 'sc',
    color: '',
    align: 'left',
    gradient: false,
    gradientColor1: '#999999',
    gradientColor2: '#ffffff',
    icon: '',
    firstLineCompress: false,
    descriptionAlign: false,
    descriptionZoom: 1,
    descriptionWeight: 0,
    package: '',
    copyright: '',
    laser: '',
    rare: '',
    twentieth: false,
    radius: true,
    scale: 1,
    atkBar: true,
    setcode: 0,
    alias: 0,
    ot: 0x1,
    category: 0,
    abilities: [],
  };
}

function handleSelectCard(cardData) {
  // 将从CDB读取的卡片数据填充到当前编辑数据
  Object.assign(currentCardData, {
    password: cardData.password || cardData.id || '',
    name: cardData.name || '',
    type: cardData.type || 'monster',
    cardType: cardData.cardType || 'normal',
    attribute: cardData.attribute || 'dark',
    monsterType: cardData.monsterType || '',
    level: cardData.level || 0,
    rank: cardData.rank || 0,
    pendulumScale: cardData.pendulumScale || 0,
    pendulumDescription: cardData.pendulumDescription || '',
    atk: cardData.atk || 0,
    def: cardData.def || 0,
    arrowList: cardData.arrowList || [],
    description: cardData.description || '',
    package: cardData.package || '',
    setcode: cardData.setcode || 0,
    alias: cardData.alias || 0,
    ot: cardData.ot || 0x1,
    category: cardData.category || 0,
    abilities: cardData.abilities || [],
    rare: '',
    laser: '',
    copyright: '',
    twentieth: false,
    scale: 1,
  });

  // 切换回预览模式
  showJsonEditor.value = false;
}

function handleCardWritten(result) {
  // 写入成功后刷新列表
  cardListRef.value?.refresh();
}

function handleCardDeleted() {
  // 刷新列表
  cardListRef.value?.refresh();
}

function handleNewCard() {
  Object.assign(currentCardData, getDefaultCardData());
  previewKey.value++;
  showJsonEditor.value = false;
}

function handleExportImage() {
  cardPreviewRef.value?.exportImage();
}

// 检查服务器状态
async function checkServerStatus() {
  try {
    await api.getStatus();
    serverOnline.value = true;
  } catch {
    serverOnline.value = false;
  }
}

onMounted(() => {
  checkServerStatus();
  // 每30秒检查一次
  const interval = setInterval(checkServerStatus, 30000);
  onBeforeUnmount(() => clearInterval(interval));
});
</script>

<style lang="scss">
/* ==================== 全局基础样式 ==================== */
* {
  box-sizing: border-box;
  overflow-wrap: break-word;
  -webkit-tap-highlight-color: transparent;
}

html, body, #app {
  margin: 0;
  padding: 0;
  height: 100%;
  overflow: hidden;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  color: #d0d0d0;
  font-size: 14px;
  background: #0a0a1a;
}

/* Element Plus 全局暗色覆盖 */
:root {
  --el-color-primary: #c8a84e;
  --el-color-primary-light-3: #d4b96a;
  --el-color-primary-light-5: #ddc88a;
  --el-color-primary-light-7: #e9d8a8;
  --el-color-primary-light-9: #f5edd0;
  --el-bg-color: #1a1a2e;
  --el-bg-color-overlay: #1e1e35;
  --el-border-color: rgba(255, 255, 255, 0.08);
  --el-text-color-primary: #d0d0d0;
  --el-text-color-regular: #b0b0c0;
  --el-mask-color: rgba(0, 0, 0, 0.7);
}

.el-message {
  --el-message-bg-color: #1e1e35 !important;
  --el-message-border-color: rgba(255, 255, 255, 0.08) !important;
  --el-message-text-color: #d0d0d0 !important;
}

.el-message-box {
  --el-messagebox-bg-color: #1e1e35 !important;
  --el-messagebox-border-color: rgba(255, 255, 255, 0.08) !important;
  --el-messagebox-title-color: #e8d5a3 !important;
  --el-messagebox-content-color: #c0c0d0 !important;
}
</style>

<style lang="scss" scoped>
.ygomaker-app {
  display: flex;
  height: 100vh;
  width: 100vw;
  background: #0a0a1a;
  overflow: hidden;
}

/* ==================== 面板通用 ==================== */
.panel {
  height: 100%;
  overflow: hidden;
  position: relative;
  flex-shrink: 0;

  .panel-resize-handle {
    position: absolute;
    right: 0;
    top: 0;
    width: 4px;
    height: 100%;
    cursor: col-resize;
    z-index: 100;
    background: transparent;
    transition: background 0.15s;

    &:hover {
      background: rgba(200, 168, 78, 0.3);
    }

    &.left-handle {
      right: auto;
      left: 0;
    }
  }
}

.panel-left {
  border-right: 1px solid rgba(255, 255, 255, 0.06);
  min-width: 220px;
  max-width: 500px;
}

.panel-right {
  border-left: 1px solid rgba(255, 255, 255, 0.06);
  min-width: 220px;
  max-width: 500px;
}

.panel-center {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 400px;
}

/* ==================== 中间工具栏 ==================== */
.center-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 20px;
  background: rgba(255, 255, 255, 0.02);
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  flex-shrink: 0;

  .toolbar-title {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 15px;
    font-weight: 700;
    color: #e8d5a3;
    letter-spacing: 1px;

    .toolbar-icon {
      font-size: 18px;
    }
  }

  .toolbar-actions {
    display: flex;
    gap: 6px;
  }
}

/* ==================== 预览区域 ==================== */
.preview-area {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: auto;
  padding: 20px;
  background:
    radial-gradient(circle at 50% 50%, rgba(200, 168, 78, 0.02) 0%, transparent 70%),
    linear-gradient(180deg, #0d0d22 0%, #0a0a1a 100%);

  .preview-container {
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .json-editor-container {
    width: 100%;
    height: 100%;
    border-radius: 8px;
    overflow: hidden;
    border: 1px solid rgba(255, 255, 255, 0.06);

    :deep(.jsoneditor-vue) {
      height: 100%;
    }

    :deep(.jsoneditor) {
      border: none;
      background: #1a1a2e;

      .jsoneditor-menu {
        background: rgba(0, 0, 0, 0.3);
        border-bottom: 1px solid rgba(255, 255, 255, 0.06);
      }

      .jsoneditor-text {
        color: #d0d0d0;
        background: #1a1a2e;
      }
    }
  }
}

/* ==================== 底部状态栏 ==================== */
.center-statusbar {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 6px 20px;
  background: rgba(0, 0, 0, 0.3);
  border-top: 1px solid rgba(255, 255, 255, 0.06);
  flex-shrink: 0;
  font-size: 11px;

  .status-item {
    color: #666;
    font-family: 'Courier New', monospace;

    &.status-server {
      margin-left: auto;

      &.online {
        color: #7ecf8c;
      }
    }
  }
}

/* ==================== 全局按钮样式 ==================== */
:deep(.el-button) {
  --el-button-bg-color: rgba(255, 255, 255, 0.06);
  --el-button-border-color: rgba(255, 255, 255, 0.1);
  --el-button-text-color: #b0b0c0;
  --el-button-hover-bg-color: rgba(255, 255, 255, 0.1);
  --el-button-hover-border-color: rgba(200, 168, 78, 0.4);
  --el-button-hover-text-color: #e8d5a3;

  &.el-button--primary {
    --el-button-bg-color: #c8a84e;
    --el-button-border-color: #c8a84e;
    --el-button-text-color: #1a1a2e;
    --el-button-hover-bg-color: #d4b96a;
    --el-button-hover-border-color: #d4b96a;
    --el-button-hover-text-color: #1a1a2e;
  }

  &.el-button--danger {
    --el-button-bg-color: rgba(220, 80, 80, 0.15);
    --el-button-border-color: rgba(220, 80, 80, 0.3);
    --el-button-text-color: #e06c6c;
    --el-button-hover-bg-color: rgba(220, 80, 80, 0.25);
    --el-button-hover-border-color: rgba(220, 80, 80, 0.5);
  }

  &.el-button--success {
    --el-button-bg-color: rgba(103, 194, 58, 0.15);
    --el-button-border-color: rgba(103, 194, 58, 0.3);
    --el-button-text-color: #7ecf8c;
    --el-button-hover-bg-color: rgba(103, 194, 58, 0.25);
    --el-button-hover-border-color: rgba(103, 194, 58, 0.5);
  }
}

</style>

<!-- 日间主题样式（必须放在非 scoped 块中才能覆盖子组件） -->
<style lang="scss">
body.theme-light {
  background: #f8f8f8 !important;

  .card-list-panel {
    background: linear-gradient(180deg, #ffffff 0%, #f5f5f5 50%, #eeeeee 100%) !important;

    .panel-header {
      background: rgba(0, 0, 0, 0.03) !important;
      border-bottom-color: rgba(0, 0, 0, 0.08) !important;
      .panel-title { color: #8b6914 !important; }
    }

    .card-item {
      &:hover { background: rgba(0, 0, 0, 0.03) !important; }
      &.active { background: rgba(200, 168, 78, 0.15) !important; }
      .card-item-name { color: #333 !important; }
      .card-item-id { color: #888 !important; }
    }

    .search-bar .el-input__wrapper {
      background: rgba(0, 0, 0, 0.03) !important;
      border-color: rgba(0, 0, 0, 0.1) !important;
    }
  }

  .card-form-panel {
    background: linear-gradient(180deg, #ffffff 0%, #f5f5f5 50%, #eeeeee 100%) !important;

    .panel-header {
      background: rgba(0, 0, 0, 0.03) !important;
      border-bottom-color: rgba(0, 0, 0, 0.08) !important;
      .panel-title { color: #8b6914 !important; }
    }

    .form-section {
      background: rgba(0, 0, 0, 0.02) !important;
      border-color: rgba(0, 0, 0, 0.06) !important;
      .section-title { color: #8b6914 !important; }
    }

    .el-input__wrapper {
      background: white !important;
      border-color: rgba(0, 0, 0, 0.12) !important;
    }
    .el-textarea__inner {
      background: white !important;
      border-color: rgba(0, 0, 0, 0.12) !important;
      color: #333 !important;
    }
    .el-form-item__label { color: #666 !important; }
  }

  .ygomaker-app { background: #fafafa !important; }

  .panel-left, .panel-right { border-color: rgba(0, 0, 0, 0.08) !important; }

  .center-toolbar {
    background: rgba(0, 0, 0, 0.02) !important;
    border-bottom-color: rgba(0, 0, 0, 0.08) !important;
    .toolbar-title { color: #8b6914 !important; }
  }

  .preview-area {
    background:
      radial-gradient(circle at 50% 50%, rgba(200, 168, 78, 0.04) 0%, transparent 70%),
      linear-gradient(180deg, #f8f6f0 0%, #ffffff 100%) !important;
  }

  .center-statusbar {
    background: rgba(0, 0, 0, 0.03) !important;
    border-top-color: rgba(0, 0, 0, 0.08) !important;
    .status-item { color: #888 !important; }
  }

  .admin-panel {
    background: linear-gradient(180deg, #ffffff 0%, #f5f5f5 50%, #eeeeee 100%) !important;

    .panel-header {
      background: rgba(0, 0, 0, 0.03) !important;
      border-bottom-color: rgba(0, 0, 0, 0.08) !important;
      .panel-title { color: #8b6914 !important; }
    }

    .admin-section {
      background: rgba(0, 0, 0, 0.02) !important;
      border-color: rgba(0, 0, 0, 0.06) !important;
      .section-title { color: #8b6914 !important; }
      .section-desc { color: #999 !important; }
    }

    .el-input__wrapper {
      background: white !important;
      border-color: rgba(0, 0, 0, 0.12) !important;
    }
    .el-input__inner { color: #333 !important; }
  }

  .el-button {
    color: #555 !important;
    border-color: rgba(0, 0, 0, 0.12) !important;
    background: rgba(0, 0, 0, 0.04) !important;
    &.el-button--primary { background: #c8a84e !important; color: white !important; }
  }
}
</style>
