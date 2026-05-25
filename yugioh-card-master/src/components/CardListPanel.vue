<template>
  <div class="card-list-panel">
    <div class="panel-header">
      <div class="panel-title">
        <span class="title-icon">📚</span>
        <span>卡片列表</span>
      </div>
      <div class="header-badge">{{ totalCount }} 张</div>
    </div>

    <!-- 搜索栏 -->
    <div class="search-bar">
      <el-input
        v-model="keyword"
        placeholder="搜索卡名或卡密..."
        :prefix-icon="Search"
        clearable
        size="small"
        @keyup.enter="handleSearch"
        @clear="handleSearch"
      >
        <template #append>
          <el-button :icon="Search" @click="handleSearch" size="small" />
        </template>
      </el-input>
    </div>

    <!-- 快捷筛选 -->
    <div class="quick-filters">
      <el-button
        size="small"
        :type="filterType === 'all' ? 'primary' : ''"
        @click="setFilter('all')"
      >
        全部
      </el-button>
      <el-button
        size="small"
        :type="filterType === 'custom' ? 'primary' : ''"
        @click="setFilter('custom')"
      >
        自制卡
      </el-button>
      <el-button
        size="small"
        :type="filterType === 'recent' ? 'primary' : ''"
        @click="setFilter('recent')"
      >
        最近
      </el-button>
    </div>

    <!-- 卡片列表 -->
    <div class="card-list" v-loading="loading">
      <div
        v-for="card in cards"
        :key="card.id"
        class="card-item"
        :class="{ active: selectedId === card.id, 'is-custom': card.id >= 100000000 }"
        @click="selectCard(card)"
      >
        <div class="card-item-left">
          <div class="card-item-id">
            <span class="id-badge" :class="{ custom: card.id >= 100000000 }">
              {{ card.id >= 100000000 ? '自制' : '' }}
            </span>
            {{ card.id }}
          </div>
          <div class="card-item-name">{{ card.name || '(未命名)' }}</div>
        </div>
        <div class="card-item-right">
          <div class="card-item-desc">{{ formatType(card) }}</div>
          <div class="card-item-stats" v-if="card.atk !== undefined && card.atk !== 0">
            ATK/{{ formatStat(card.atk) }} DEF/{{ formatStat(card.def) }}
          </div>
        </div>
      </div>

      <div v-if="!loading && cards.length === 0" class="empty-state">
        <div class="empty-icon">🗂️</div>
        <div class="empty-text">{{ keyword ? '没有匹配的卡片' : '暂无卡片数据' }}</div>
      </div>
    </div>

    <!-- 分页 -->
    <div class="pagination" v-if="totalCount > 0">
      <el-pagination
        v-model:current-page="currentPage"
        :page-size="pageSize"
        :total="totalCount"
        layout="prev, next"
        size="small"
        background
        @current-change="handlePageChange"
      />
    </div>

    <!-- 底部操作 -->
    <div class="panel-footer" v-if="selectedId">
      <el-button size="small" type="danger" plain @click="handleDelete" :loading="deleting">
        删除卡片
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import { Search } from '@element-plus/icons-vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { api } from '@/api/index.js';

const emit = defineEmits(['selectCard', 'cardDeleted']);

// 状态
const cards = ref([]);
const keyword = ref('');
const filterType = ref('all');
const selectedId = ref(null);
const loading = ref(false);
const deleting = ref(false);
const currentPage = ref(1);
const pageSize = ref(30);
const totalCount = ref(0);

// 加载卡片
async function loadCards() {
  loading.value = true;
  try {
    let result;
    if (filterType.value === 'custom') {
      // 仅自制卡 (9位数段)
      result = await api.searchCards('', pageSize.value, (currentPage.value - 1) * pageSize.value);
      if (result.success) {
        cards.value = result.cards.filter(c => c.id >= 100000000);
        totalCount.value = cards.value.length; // 简化处理
      }
    } else if (filterType.value === 'recent') {
      result = await api.searchCards('', pageSize.value, 0);
      if (result.success) {
        cards.value = result.cards;
        totalCount.value = result.total;
      }
    } else {
      result = await api.searchCards(keyword.value, pageSize.value, (currentPage.value - 1) * pageSize.value);
      if (result.success) {
        cards.value = result.cards;
        totalCount.value = result.total;
      }
    }
  } catch (e) {
    ElMessage.error(`加载卡片失败: ${e.message}`);
    cards.value = [];
  } finally {
    loading.value = false;
  }
}

function handleSearch() {
  currentPage.value = 1;
  filterType.value = 'all';
  loadCards();
}

function setFilter(type) {
  filterType.value = type;
  keyword.value = '';
  currentPage.value = 1;
  loadCards();
}

function handlePageChange(page) {
  currentPage.value = page;
  loadCards();
}

async function selectCard(card) {
  selectedId.value = card.id;
  loading.value = true;
  try {
    const result = await api.getCard(card.id);
    if (result.success && result.card) {
      emit('selectCard', result.card);
    }
  } catch (e) {
    ElMessage.error(`读取卡片失败: ${e.message}`);
  } finally {
    loading.value = false;
  }
}

async function handleDelete() {
  if (!selectedId.value) return;

  try {
    await ElMessageBox.confirm(
      `确定要删除卡片 ${selectedId.value} 吗？此操作不可恢复。`,
      '确认删除',
      { confirmButtonText: '删除', cancelButtonText: '取消', type: 'warning' }
    );

    deleting.value = true;
    const result = await api.deleteCard(selectedId.value);
    if (result.success) {
      ElMessage.success(result.message);
      selectedId.value = null;
      emit('cardDeleted', selectedId.value);
      loadCards();
    } else {
      ElMessage.error(result.message);
    }
  } catch {
    // 用户取消
  } finally {
    deleting.value = false;
  }
}

// 格式化
function formatType(card) {
  const typeVal = card.type || 0;
  const parts = [];
  if (typeVal & 0x1) parts.push('怪兽');
  if (typeVal & 0x2) parts.push('魔法');
  if (typeVal & 0x4) parts.push('陷阱');
  if (typeVal & 0x1000000) parts.push('灵摆');
  if (typeVal & 0x4000000) parts.push('连接');
  if (typeVal & 0x800000) parts.push('超量');
  if (typeVal & 0x2000) parts.push('同调');
  if (typeVal & 0x40) parts.push('融合');
  return parts.length > 0 ? parts.join('/') : '未知';
}

function formatStat(val) {
  if (val === -1) return '?';
  if (val === undefined || val === null) return '0';
  return String(val);
}

onMounted(() => {
  loadCards();
});

// 暴露方法给父组件
defineExpose({ refresh: loadCards });
</script>

<style lang="scss" scoped>
.card-list-panel {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: linear-gradient(180deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
  overflow: hidden;

  .panel-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 14px 18px;
    background: rgba(0, 0, 0, 0.3);
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    flex-shrink: 0;

    .panel-title {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 16px;
      font-weight: 700;
      color: #e8d5a3;
      letter-spacing: 1px;

      .title-icon {
        font-size: 18px;
      }
    }

    .header-badge {
      font-size: 12px;
      color: #888;
      background: rgba(255, 255, 255, 0.05);
      padding: 3px 10px;
      border-radius: 10px;
    }
  }

  .search-bar {
    padding: 10px 14px;
    flex-shrink: 0;

    :deep(.el-input__wrapper) {
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid rgba(255, 255, 255, 0.08);
      border-radius: 6px;
      box-shadow: none;

      &:hover, &.is-focus {
        border-color: rgba(200, 170, 100, 0.4);
      }
    }

    :deep(.el-input__inner) {
      color: #d0d0d0;
      font-size: 12px;

      &::placeholder {
        color: rgba(255, 255, 255, 0.2);
      }
    }

    :deep(.el-input-group__append) {
      background: transparent;
      border-color: rgba(255, 255, 255, 0.08);

      .el-button {
        background: transparent;
        border: none;
        color: #888;
      }
    }
  }

  .quick-filters {
    display: flex;
    gap: 6px;
    padding: 0 14px 10px;
    flex-shrink: 0;

    .el-button {
      font-size: 11px;
      padding: 4px 12px;
      border-radius: 4px;
    }
  }

  .card-list {
    flex: 1;
    overflow-y: auto;
    padding: 0 6px 10px;

    &::-webkit-scrollbar {
      width: 4px;
    }
    &::-webkit-scrollbar-track {
      background: transparent;
    }
    &::-webkit-scrollbar-thumb {
      background: rgba(255, 255, 255, 0.1);
      border-radius: 2px;
    }
  }

  .card-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 10px 14px;
    margin: 2px 8px;
    border-radius: 6px;
    cursor: pointer;
    transition: all 0.15s;
    border: 1px solid transparent;

    &:hover {
      background: rgba(255, 255, 255, 0.04);
      border-color: rgba(255, 255, 255, 0.06);
    }

    &.active {
      background: rgba(200, 168, 78, 0.12);
      border-color: rgba(200, 168, 78, 0.3);
    }

    &.is-custom {
      .card-item-left {
        position: relative;

        &::before {
          content: '';
          position: absolute;
          left: -10px;
          top: 50%;
          transform: translateY(-50%);
          width: 3px;
          height: 60%;
          background: #c8a84e;
          border-radius: 2px;
        }
      }
    }

    .card-item-left {
      flex: 1;
      min-width: 0;

      .card-item-id {
        font-size: 11px;
        color: #666;
        margin-bottom: 2px;

        .id-badge {
          display: inline-block;
          font-size: 9px;
          padding: 1px 5px;
          border-radius: 3px;
          margin-right: 4px;

          &.custom {
            background: rgba(200, 168, 78, 0.2);
            color: #c8a84e;
          }
        }
      }

      .card-item-name {
        font-size: 13px;
        color: #d0d0d0;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        font-weight: 500;
      }
    }

    .card-item-right {
      flex-shrink: 0;
      text-align: right;
      margin-left: 12px;

      .card-item-desc {
        font-size: 10px;
        color: #666;
        margin-bottom: 1px;
      }

      .card-item-stats {
        font-size: 10px;
        color: #555;
        font-family: 'Courier New', monospace;
      }
    }
  }

  .empty-state {
    text-align: center;
    padding: 40px 20px;
    color: #555;

    .empty-icon {
      font-size: 36px;
      margin-bottom: 10px;
    }

    .empty-text {
      font-size: 13px;
    }
  }

  .pagination {
    display: flex;
    justify-content: center;
    padding: 8px;
    flex-shrink: 0;

    :deep(.el-pagination) {
      .btn-prev, .btn-next {
        background: rgba(255, 255, 255, 0.05) !important;
        color: #888;
        border: 1px solid rgba(255, 255, 255, 0.08);

        &:hover {
          color: #e8d5a3;
        }
      }
    }
  }

  .panel-footer {
    padding: 10px 18px;
    border-top: 1px solid rgba(255, 255, 255, 0.06);
    flex-shrink: 0;
    display: flex;
    justify-content: flex-end;
  }
}

:deep(.el-loading-mask) {
  background: rgba(0, 0, 0, 0.4);
}
</style>
