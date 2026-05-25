/**
 * YGOMaker API 接口层
 * 与后端 FastAPI 服务通信
 */

const API_BASE = import.meta.env.PROD ? '' : 'http://localhost:8848';

/**
 * 通用请求封装
 */
async function request(url, options = {}) {
  const config = {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  };

  const response = await fetch(`${API_BASE}${url}`, config);
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: '网络请求失败' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }
  return response.json();
}

export const api = {
  // ======================== 卡片 CRUD ========================

  /**
   * 写入/更新一张卡片到 CDB
   * @param {Object} card - 卡片完整数据
   * @param {boolean} overwrite - 是否覆盖已有卡片
   */
  async writeCard(card, overwrite = false) {
    return request('/api/card/write', {
      method: 'POST',
      body: JSON.stringify({ card, overwrite }),
    });
  },

  /**
   * 批量写入卡片
   */
  async batchWrite(cards, overwrite = false) {
    return request('/api/card/batch', {
      method: 'POST',
      body: JSON.stringify({ cards, overwrite }),
    });
  },

  /**
   * 读取一张卡片
   * @param {number} cardId
   */
  async getCard(cardId) {
    return request(`/api/card/${cardId}`);
  },

  /**
   * 删除一张卡片
   * @param {number} cardId
   */
  async deleteCard(cardId) {
    return request(`/api/card/${cardId}`, { method: 'DELETE' });
  },

  /**
   * 获取下一个可用卡密
   * @param {boolean} usePrimary - 是否优先使用9位数段
   */
  async getNextId(usePrimary = true) {
    return request(`/api/card/next-id?primary=${usePrimary}`);
  },

  /**
   * 搜索卡片
   * @param {string} keyword - 搜索关键词
   * @param {number} limit - 每页条数
   * @param {number} offset - 偏移量
   */
  async searchCards(keyword = '', limit = 50, offset = 0) {
    return request(`/api/card/search?keyword=${encodeURIComponent(keyword)}&limit=${limit}&offset=${offset}`);
  },

  // ======================== 服务状态 ========================

  /**
   * 获取服务状态
   */
  async getStatus() {
    return request('/api/status');
  },

  // ======================== strings.conf ========================

  async setnames() {
    return request('/api/strings/setnames');
  },
  async searchSetnames(keyword) {
    return request(`/api/strings/setnames/search?keyword=${encodeURIComponent(keyword)}`);
  },
  async counters() {
    return request('/api/strings/counters');
  },
  async victories() {
    return request('/api/strings/victories');
  },
  async nextAvailableCode(type = 'setcode') {
    return request(`/api/strings/next-available?field_type=${type}`);
  },

  // ======================== 本地修改追踪 ========================

  async modsStatus() {
    return request('/api/mods/status');
  },
  async customFields() {
    return request('/api/mods/custom-fields');
  },
  async addCustomField(type, code, name) {
    return request(`/api/mods/add-field?field_type=${type}&code=${code}&name=${encodeURIComponent(name)}`, {
      method: 'POST',
    });
  },
  async preMergeBackup() {
    return request('/api/mods/pre-merge-backup', { method: 'POST' });
  },
  async postMergeRestore() {
    return request('/api/mods/post-merge-restore', { method: 'POST' });
  },
  async exportCustomStrings() {
    return request('/api/mods/export-custom-strings', { method: 'POST' });
  },
  async checkConflicts() {
    return request('/api/mods/conflicts');
  },

  // ======================== 更新流程 ========================

  async fetchOfficial() {
    return request('/api/update/fetch-official', { method: 'POST' });
  },
  async mergeCustom() {
    return request('/api/update/merge-custom', { method: 'POST' });
  },
  async updateAndMerge() {
    return request('/api/update/update-and-merge', { method: 'POST' });
  },
  async removeField(type, code) {
    return request(`/api/mods/remove-field?field_type=${type}&code=${code}`, { method: 'DELETE' });
  },
  getExportCdbUrl() {
    return `${API_BASE}/api/export/cdb`;
  },
  getExportStringsUrl() {
    return `${API_BASE}/api/export/strings`;
  },

  // ======================== 导入外部数据 ========================

  async importForeignData(cdbFile, stringsFile) {
    const formData = new FormData();
    if (cdbFile) formData.append('cdb_file', cdbFile);
    if (stringsFile) formData.append('strings_file', stringsFile);
    const response = await fetch(`${API_BASE}/api/import/foreign-data`, {
      method: 'POST',
      body: formData,
    });
    if (!response.ok) throw new Error((await response.json()).detail || '导入失败');
    return response.json();
  },
};
