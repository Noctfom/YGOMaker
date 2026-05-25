<template>
  <div class="card-form-panel">
    <div class="panel-header">
      <div class="panel-title">
        <span class="title-icon">🃏</span>
        <span>卡片数据编辑</span>
      </div>
      <div class="panel-actions">
        <el-button size="small" type="primary" :icon="RefreshRight" @click="handleAutoId" :loading="idLoading">
          自动分配卡密
        </el-button>
        <el-button size="small" type="success" :icon="Upload" @click="handleWriteCDB" :loading="writing">
          写入CDB
        </el-button>
        <el-dropdown trigger="click" @command="handleDropdown">
          <el-button size="small" circle>
            <span style="font-size:14px;">⋯</span>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="exportJson">
                <span style="margin-right:4px;">📄</span> 导出JSON
              </el-dropdown-item>
              <el-dropdown-item command="loadOfficialImage">
                <span style="margin-right:4px;">🌐</span> 加载官方卡图
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>

    <div class="panel-body">
      <el-form :model="form" label-position="top" size="default" class="card-form">
        <!-- ========== 基本信息 ========== -->
        <div class="form-section">
          <div class="section-title">
            <span class="section-icon">📋</span> 基本信息
          </div>

          <el-row :gutter="12">
            <el-col :span="14">
              <el-form-item label="卡密 (Password)">
                <el-input
                  v-model="form.password"
                  placeholder="输入卡密或点上方按钮自动分配"
                  :formatter="(v) => v.replace(/\D/g, '')"
                  clearable
                >
                  <template #prefix>
                    <span style="color: #a0a0a0; font-size: 13px;">#</span>
                  </template>
                </el-input>
              </el-form-item>
            </el-col>
            <el-col :span="10">
              <el-form-item label="卡片类型">
                <el-select v-model="form.type" @change="handleTypeChange" style="width: 100%">
                  <el-option label="🟤 怪兽" value="monster" />
                  <el-option label="🟢 魔法" value="spell" />
                  <el-option label="🟣 陷阱" value="trap" />
                  <el-option label="🔷 灵摆" value="pendulum" />
                </el-select>
              </el-form-item>
            </el-col>
          </el-row>

          <el-form-item label="卡片名称">
            <el-input v-model="form.name" placeholder="输入卡片名称" maxlength="60" show-word-limit />
          </el-form-item>

          <el-form-item label="卡包编号">
            <el-input v-model="form.package" placeholder="如: SD25-SC001" maxlength="30" />
          </el-form-item>

          <!-- 卡图管理 -->
          <el-form-item label="卡图">
            <div class="image-upload-area">
              <div class="image-preview" v-if="form.image">
                <img :src="form.image" alt="卡片预览" />
                <el-button
                  size="small"
                  type="danger"
                  circle
                  class="image-remove-btn"
                  @click="form.image = ''"
                >
                  ✕
                </el-button>
              </div>
              <div class="image-actions">
                <el-button size="small" @click="triggerImageUpload">
                  📁 选择本地图片
                </el-button>
                <el-button size="small" @click="loadOfficialCardImage">
                  🌐 加载官方卡图
                </el-button>
              </div>
              <input
                ref="imageInputRef"
                type="file"
                accept="image/*"
                style="display: none"
                @change="handleImageUpload"
              />
            </div>
          </el-form-item>

          <!-- 图片裁剪弹窗 -->
          <el-dialog v-model="cropVisible" title="裁剪卡图（正方形）" width="520px" center>
            <div class="crop-container" v-if="cropVisible">
              <div class="crop-canvas-wrapper">
                <canvas
                  ref="cropCanvasRef"
                  class="crop-canvas"
                  @mousedown="startCropDrag"
                  @mousemove="onCropDrag"
                  @mouseup="stopCropDrag"
                  @wheel.prevent="onCropWheel"
                />
              </div>
              <div class="crop-controls">
                <span style="font-size:11px;color:#888;">裁剪尺寸: </span>
                <el-input-number v-model="cropSize" :min="50" :max="1200" :step="5" size="small" style="width:130px;" />
                <span class="crop-hint" style="margin-left:10px;">滚轮缩放 | 拖拽移动</span>
              </div>
            </div>
            <template #footer>
              <el-button @click="cropVisible = false">取消</el-button>
              <el-button type="primary" @click="applyCrop">确认裁剪</el-button>
            </template>
          </el-dialog>
        </div>

        <!-- ========== 怪兽信息 (怪兽/灵摆时显示) ========== -->
        <div class="form-section" v-if="isMonster">
          <div class="section-title">
            <span class="section-icon">⚔️</span> 怪兽信息
          </div>

          <el-row :gutter="12">
            <el-col :span="12">
              <el-form-item label="怪兽子类型">
                <el-select v-model="form.cardType" @change="handleCardTypeChange" style="width: 100%">
                  <el-option label="通常" value="normal" />
                  <el-option label="效果" value="effect" />
                  <el-option label="融合" value="fusion" />
                  <el-option label="仪式" value="ritual" />
                  <el-option label="同调" value="synchro" />
                  <el-option label="超量" value="xyz" />
                  <el-option label="连接" value="link" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="属性">
                <el-select v-model="form.attribute" style="width: 100%">
                  <el-option label="🌍 地" value="earth" />
                  <el-option label="💧 水" value="water" />
                  <el-option label="🔥 炎" value="fire" />
                  <el-option label="🌪️ 风" value="wind" />
                  <el-option label="✨ 光" value="light" />
                  <el-option label="🌑 暗" value="dark" />
                  <el-option label="👑 神" value="divine" />
                </el-select>
              </el-form-item>
            </el-col>
          </el-row>

          <el-form-item label="种族">
            <el-select v-model="form.monsterType" style="width: 100%" filterable>
              <el-option v-for="race in raceList" :key="race.value" :label="race.label" :value="race.value" />
            </el-select>
          </el-form-item>

          <el-row :gutter="12">
            <!-- 等级 / 阶级 / Link值 -->
            <el-col :span="8">
              <el-form-item v-if="!isXyz && !isLink" label="等级">
                <el-input-number v-model="form.level" :min="0" :max="13" style="width: 100%" />
              </el-form-item>
              <el-form-item v-if="isXyz" label="阶级">
                <el-input-number v-model="form.rank" :min="0" :max="13" style="width: 100%" />
              </el-form-item>
              <el-form-item v-if="isLink" label="Link值">
                <span class="link-value-display">{{ form.arrowList.length || 0 }}</span>
              </el-form-item>
            </el-col>

            <!-- ATK / DEF -->
            <el-col :span="8" v-if="!isLink">
              <el-form-item label="攻击力">
                <el-select
                  v-model="form.atk"
                  style="width: 100%"
                  filterable
                  allow-create
                  clearable
                >
                  <el-option label="0" :value="0" />
                  <el-option label="?" :value="-1" />
                  <el-option label="∞" :value="-2" />
                  <el-option v-for="n in atkPresets" :key="n" :label="String(n)" :value="n" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="8" v-if="isLink">
              <el-form-item label="攻击力">
                <el-input v-model="form.atk" placeholder="0" disabled style="width: 100%" />
              </el-form-item>
            </el-col>

            <el-col :span="8" v-if="!isLink">
              <el-form-item label="守备力">
                <el-select
                  v-model="form.def"
                  style="width: 100%"
                  filterable
                  allow-create
                  clearable
                >
                  <el-option label="0" :value="0" />
                  <el-option label="?" :value="-1" />
                  <el-option label="∞" :value="-2" />
                  <el-option v-for="n in defPresets" :key="n" :label="String(n)" :value="n" />
                </el-select>
              </el-form-item>
            </el-col>

            <!-- Link箭头 (仅Link怪) -->
            <el-col :span="24" v-if="isLink">
              <el-form-item label="Link箭头">
                <div class="link-arrow-selector">
                  <div
                    v-for="arrow in linkArrows"
                    :key="arrow.value"
                    class="arrow-btn"
                    :class="{ active: form.arrowList.includes(arrow.value) }"
                    @click="toggleArrow(arrow.value)"
                    :title="arrow.label"
                  >
                    {{ arrow.icon }}
                  </div>
                </div>
              </el-form-item>
            </el-col>
          </el-row>

          <!-- 灵摆信息 -->
          <template v-if="form.type === 'pendulum'">
            <el-row :gutter="12">
              <el-col :span="8">
                <el-form-item label="灵摆刻度">
                  <el-input-number v-model="form.pendulumScale" :min="0" :max="13" style="width: 100%" />
                </el-form-item>
              </el-col>
              <el-col :span="16">
                <el-form-item label="灵摆效果">
                  <el-input
                    v-model="form.pendulumDescription"
                    type="textarea"
                    :rows="2"
                    placeholder="输入灵摆效果文本"
                  />
                </el-form-item>
              </el-col>
            </el-row>
          </template>

          <!-- 额外能力 -->
          <el-form-item label="额外能力">
            <el-checkbox-group v-model="form.abilities">
              <el-checkbox label="tuner">协调</el-checkbox>
              <el-checkbox label="spirit">灵魂</el-checkbox>
              <el-checkbox label="union">同盟</el-checkbox>
              <el-checkbox label="gemini">二重</el-checkbox>
              <el-checkbox label="token">衍生物</el-checkbox>
            </el-checkbox-group>
          </el-form-item>
        </div>

        <!-- ========== 魔法/陷阱信息 ========== -->
        <div class="form-section" v-if="!isMonster">
          <div class="section-title">
            <span class="section-icon">📜</span> {{ form.type === 'spell' ? '魔法' : '陷阱' }}信息
          </div>

          <el-form-item label="图标类型">
            <el-select v-model="form.icon" style="width: 100%" clearable>
              <el-option label="通常魔法" value="spell" v-if="form.type === 'spell'" />
              <el-option label="永续魔法" value="continuous" v-if="form.type === 'spell'" />
              <el-option label="装备魔法" value="equip" v-if="form.type === 'spell'" />
              <el-option label="场地魔法" value="field" v-if="form.type === 'spell'" />
              <el-option label="速攻魔法" value="quick-play" v-if="form.type === 'spell'" />
              <el-option label="仪式魔法" value="ritual" v-if="form.type === 'spell'" />
              <el-option label="通常陷阱" value="trap" v-if="form.type === 'trap'" />
              <el-option label="永续陷阱" value="continuous" v-if="form.type === 'trap'" />
              <el-option label="反击陷阱" value="counter" v-if="form.type === 'trap'" />
            </el-select>
          </el-form-item>
        </div>

        <!-- ========== 效果文本 ========== -->
        <div class="form-section">
          <div class="section-title">
            <span class="section-icon">📝</span> 效果文本
          </div>
          <el-form-item>
            <el-input
              v-model="form.description"
              type="textarea"
              :rows="5"
              placeholder="输入卡片效果描述文本"
              maxlength="1200"
              show-word-limit
              :style="{ fontSize: (form.descriptionZoom || 1) * 13 + 'px' }"
            />
          </el-form-item>
          <div class="desc-zoom-control">
            <span style="font-size:11px;color:#888;margin-right:8px;">描述字号: {{ (form.descriptionZoom || 1).toFixed(1) }}x</span>
            <el-slider
              v-model="form.descriptionZoom"
              :min="0.5"
              :max="2"
              :step="0.05"
              size="small"
              style="width:200px;"
            />
          </div>
        </div>

        <!-- ========== 显示设定 ========== -->
        <div class="form-section">
          <div class="section-title collapsible" @click="showDisplaySettings = !showDisplaySettings">
            <span class="section-icon">🎨</span> 显示设定
            <span class="collapse-icon">{{ showDisplaySettings ? '▼' : '▶' }}</span>
          </div>

          <el-collapse-transition>
            <div v-show="showDisplaySettings">
              <el-row :gutter="12">
                <el-col :span="12">
                  <el-form-item label="语言">
                    <el-select v-model="form.language" style="width: 100%">
                      <el-option label="简体中文" value="sc" />
                      <el-option label="繁体中文" value="tc" />
                      <el-option label="日本語" value="jp" />
                      <el-option label="English" value="en" />
                      <el-option label="한국어" value="kr" />
                    </el-select>
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="罕贵度">
                    <el-select v-model="form.rare" style="width: 100%" clearable>
                      <el-option label="无" value="" />
                      <el-option label="银碎 SER" value="ser" />
                      <el-option label="全息 HR" value="hr" />
                      <el-option label="红碎 PSER" value="pser" />
                      <el-option label="金碎 GSER" value="gser" />
                    </el-select>
                  </el-form-item>
                </el-col>
              </el-row>

              <el-row :gutter="12">
                <el-col :span="12">
                  <el-form-item label="字体">
                    <el-select v-model="form.font" style="width: 100%" clearable>
                      <el-option label="默认" value="" />
                      <el-option label="自定义1" value="custom1" />
                      <el-option label="自定义2" value="custom2" />
                    </el-select>
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="缩放">
                    <el-input-number v-model="form.scale" :min="1" :max="4" style="width: 100%" />
                  </el-form-item>
                </el-col>
              </el-row>

              <el-form-item label="版权标记">
                <el-select v-model="form.copyright" style="width: 100%" clearable>
                  <el-option label="无" value="" />
                  <el-option label="©高桥和希" value="kazuki" />
                </el-select>
              </el-form-item>

              <el-form-item label="闪膜效果">
                <el-select v-model="form.laser" style="width: 100%" clearable>
                  <el-option label="无" value="" />
                  <el-option label="激光1" value="laser1" />
                  <el-option label="激光2" value="laser2" />
                  <el-option label="激光3" value="laser3" />
                  <el-option label="激光4" value="laser4" />
                </el-select>
              </el-form-item>

              <el-row :gutter="12">
                <el-col :span="8">
                  <el-form-item>
                    <el-checkbox v-model="form.atkBar" label="显示ATK/DEF栏" />
                  </el-form-item>
                </el-col>
                <el-col :span="8">
                  <el-form-item>
                    <el-checkbox v-model="form.radius" label="圆角" />
                  </el-form-item>
                </el-col>
                <el-col :span="8">
                  <el-form-item>
                    <el-checkbox v-model="form.twentieth" label="20th标记" />
                  </el-form-item>
                </el-col>
              </el-row>
            </div>
          </el-collapse-transition>
        </div>

        <!-- ========== 高级设定 ========== -->
        <div class="form-section">
          <div class="section-title collapsible" @click="showAdvancedSettings = !showAdvancedSettings">
            <span class="section-icon">⚙️</span> 高级设定
            <span class="collapse-icon">{{ showAdvancedSettings ? '▼' : '▶' }}</span>
          </div>

          <el-collapse-transition>
            <div v-show="showAdvancedSettings">
              <el-row :gutter="12">
                <el-col :span="12">
                  <el-form-item label="系列编码 (Setcode)">
                    <el-input v-model="form.setcode" placeholder="0x" />
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="别名 (Alias)">
                    <el-input v-model="form.alias" placeholder="异画指向原卡密" />
                  </el-form-item>
                </el-col>
              </el-row>

              <el-row :gutter="12">
                <el-col :span="12">
                  <el-form-item label="OT标识">
                    <el-select v-model="form.ot" style="width: 100%">
                      <el-option label="OCG" :value="0x1" />
                      <el-option label="TCG" :value="0x2" />
                      <el-option label="OCG+TCG" :value="0x3" />
                    </el-select>
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="效果分类 (Category)">
                    <el-input v-model="form.category" placeholder="0" />
                  </el-form-item>
                </el-col>
              </el-row>
            </div>
          </el-collapse-transition>
        </div>
      </el-form>
    </div>

    <!-- 操作结果弹窗 -->
    <el-dialog v-model="dialogVisible" title="操作结果" width="400px" center>
      <div class="result-content" :class="{ success: dialogSuccess, error: !dialogSuccess }">
        <div class="result-icon">{{ dialogSuccess ? '✅' : '❌' }}</div>
        <div class="result-message">{{ dialogMessage }}</div>
      </div>
      <template #footer>
        <el-button @click="dialogVisible = false">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch } from 'vue';
import { Upload, RefreshRight } from '@element-plus/icons-vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { api } from '@/api/index.js';

// ======================== Props & Emits ========================
const props = defineProps({
  modelValue: { type: Object, required: true },
});
const emit = defineEmits(['update:modelValue', 'cardWritten']);

// 直接使用父级的 reactive 对象，无需副本
// 这样表单修改立即反映到父级 → 卡图预览实时刷新
const form = props.modelValue;

// ======================== 状态 ========================
const writing = ref(false);
const idLoading = ref(false);
const dialogVisible = ref(false);
const dialogSuccess = ref(false);
const dialogMessage = ref('');
const showDisplaySettings = ref(false);
const showAdvancedSettings = ref(false);
const imageInputRef = ref(null);

// 图片裁剪状态
const cropVisible = ref(false);
const cropCanvasRef = ref(null);
const cropImage = ref(null);
const cropSize = ref(400);
const cropOffsetX = ref(0);
const cropOffsetY = ref(0);
const cropScale = ref(1);
let cropDragging = false;
let cropDragStartX = 0;
let cropDragStartY = 0;
let cropStartOffsetX = 0;
let cropStartOffsetY = 0;

// 裁剪框大小变化时重绘
watch(cropSize, () => {
  if (cropVisible.value) drawCropCanvas();
});

// ======================== 计算属性 ========================
const isMonster = computed(() => ['monster', 'pendulum'].includes(form.type));
const isXyz = computed(() => form.cardType === 'xyz');
const isLink = computed(() => form.cardType === 'link');

// ======================== 选项列表 ========================
const raceList = [
  { label: '龙族', value: 'dragon' },
  { label: '魔法师族', value: 'spellcaster' },
  { label: '战士族', value: 'warrior' },
  { label: '机械族', value: 'machine' },
  { label: '恶魔族', value: 'fiend' },
  { label: '天使族', value: 'fairy' },
  { label: '不死族', value: 'zombie' },
  { label: '爬虫类族', value: 'reptile' },
  { label: '恐龙族', value: 'dinosaur' },
  { label: '海龙族', value: 'sea-serpent' },
  { label: '鱼族', value: 'fish' },
  { label: '水族', value: 'aqua' },
  { label: '炎族', value: 'pyro' },
  { label: '雷族', value: 'thunder' },
  { label: '岩石族', value: 'rock' },
  { label: '植物族', value: 'plant' },
  { label: '昆虫族', value: 'insect' },
  { label: '兽族', value: 'beast' },
  { label: '兽战士族', value: 'beast-warrior' },
  { label: '鸟兽族', value: 'winged-beast' },
  { label: '念动力族', value: 'psychic' },
  { label: '幻龙族', value: 'wyrm' },
  { label: '电子界族', value: 'cyberse' },
  { label: '幻想魔族', value: 'illusion' },
  { label: '幻神兽族', value: 'divine-beast' },
  { label: '创造神族', value: 'creator-god' },
];

const atkPresets = [100, 200, 300, 400, 500, 600, 700, 800, 900, 1000, 1200, 1300, 1400, 1500, 1600, 1700, 1800, 1900, 2000, 2100, 2200, 2300, 2400, 2500, 2600, 2800, 3000, 3500, 4000, 4500, 5000];
const defPresets = [100, 200, 300, 400, 500, 600, 700, 800, 900, 1000, 1200, 1400, 1500, 1600, 1800, 2000, 2100, 2500, 3000, 3500, 4000];

const linkArrows = [
  { value: 1, label: '↑ 上', icon: '↑' },
  { value: 2, label: '↗ 右上', icon: '↗' },
  { value: 3, label: '→ 右', icon: '→' },
  { value: 4, label: '↘ 右下', icon: '↘' },
  { value: 5, label: '↓ 下', icon: '↓' },
  { value: 6, label: '↙ 左下', icon: '↙' },
  { value: 7, label: '← 左', icon: '←' },
  { value: 8, label: '↖ 左上', icon: '↖' },
];

// ======================== 方法 ========================
function handleTypeChange(val) {
  if (val === 'spell' || val === 'trap') {
    form.cardType = 'normal';
    form.attribute = '';
    form.level = 0;
    form.rank = 0;
    form.atk = 0;
    form.def = 0;
    form.arrowList = [];
    form.pendulumScale = 0;
  } else {
    if (!form.cardType || form.cardType === 'normal') {
      form.cardType = 'effect';
    }
    if (!form.attribute) form.attribute = 'dark';
  }
}

function handleCardTypeChange(val) {
  if (val === 'link') {
    form.def = 0;
  } else if (val === 'xyz') {
    form.level = 0;
  }
}

function toggleArrow(value) {
  const idx = form.arrowList.indexOf(value);
  if (idx > -1) {
    form.arrowList.splice(idx, 1);
  } else {
    form.arrowList.push(value);
  }
}

async function handleAutoId() {
  idLoading.value = true;
  try {
    const result = await api.getNextId(true);
    if (result.success) {
      form.password = result.card_id;
      ElMessage.success(`已分配卡密: ${result.card_id} (${result.range})`);
    } else {
      ElMessage.error(result.message);
    }
  } catch (e) {
    ElMessage.error(`获取卡密失败: ${e.message}`);
  } finally {
    idLoading.value = false;
  }
}

function handleDropdown(command) {
  if (command === 'exportJson') {
    exportJsonFile();
  } else if (command === 'loadOfficialImage') {
    loadOfficialCardImage();
  }
}

function exportJsonFile() {
  const jsonStr = JSON.stringify({ ...form }, null, 2);
  const blob = new Blob([jsonStr], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `${form.name || 'card'}_${form.password || 'data'}.json`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
  ElMessage.success('JSON 文件已下载');
}

function loadOfficialCardImage() {
  if (!form.password) {
    ElMessage.warning('请先输入卡密');
    return;
  }
  const id = String(form.password);
  // 尝试多个官方卡图源
  const sources = [
    `https://cdn02.moecube.com/ygopro/pics/${id}.jpg`,
    `https://images.ygoprodeck.com/images/cards/${id}.jpg`,
    `https://images.ygoprodeck.com/images/cards_cropped/${id}.jpg`,
  ];

  const img = new Image();
  let sourceIndex = 0;

  function tryNext() {
    if (sourceIndex >= sources.length) {
      ElMessage.warning('未找到官方卡图（所有CDN源均失败）');
      return;
    }
    img.src = sources[sourceIndex];
  }

  img.onload = () => {
    form.image = img.src;
    ElMessage.success(`已加载官方卡图 (源${sourceIndex + 1})`);
  };

  img.onerror = () => {
    sourceIndex++;
    tryNext();
  };

  tryNext();
}

function triggerImageUpload() {
  imageInputRef.value?.click();
}

function handleImageUpload(event) {
  const file = event.target.files?.[0];
  if (!file) return;

  if (!file.type.startsWith('image/')) {
    ElMessage.warning('请选择图片文件');
    return;
  }

  const reader = new FileReader();
  reader.onload = (e) => {
    const dataUrl = e.target.result;
    openCropModal(dataUrl);
  };
  reader.readAsDataURL(file);
  // 重置input以便重复选择同一文件
  event.target.value = '';
}

function openCropModal(dataUrl) {
  const img = new Image();
  img.onload = () => {
    cropImage.value = img;
    cropScale.value = Math.min(480 / img.width, 480 / img.height, 1);
    cropSize.value = Math.min(img.width, img.height, 400);
    cropOffsetX.value = (img.width * cropScale.value - cropSize.value) / 2;
    cropOffsetY.value = (img.height * cropScale.value - cropSize.value) / 2;
    cropVisible.value = true;
    // 下一帧渲染canvas
    setTimeout(() => drawCropCanvas(), 50);
  };
  img.src = dataUrl;
}

function drawCropCanvas() {
  const canvas = cropCanvasRef.value;
  if (!canvas || !cropImage.value) return;
  const ctx = canvas.getContext('2d');
  const w = cropImage.value.width * cropScale.value;
  const h = cropImage.value.height * cropScale.value;
  canvas.width = Math.max(w, cropSize.value + 60);
  canvas.height = Math.max(h, cropSize.value + 60);

  ctx.fillStyle = '#333';
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  // 绘制图片
  ctx.drawImage(cropImage.value, cropOffsetX.value, cropOffsetY.value, w, h);

  // 绘制裁剪框
  const cx = (canvas.width - cropSize.value) / 2;
  const cy = (canvas.height - cropSize.value) / 2;
  ctx.strokeStyle = '#c8a84e';
  ctx.lineWidth = 2;
  ctx.strokeRect(cx, cy, cropSize.value, cropSize.value);

  // 半透明遮罩
  ctx.fillStyle = 'rgba(0,0,0,0.5)';
  ctx.fillRect(0, 0, canvas.width, cy);
  ctx.fillRect(0, cy + cropSize.value, canvas.width, canvas.height - cy - cropSize.value);
  ctx.fillRect(0, cy, cx, cropSize.value);
  ctx.fillRect(cx + cropSize.value, cy, canvas.width - cx - cropSize.value, cropSize.value);
}

function applyCrop() {
  const canvas = cropCanvasRef.value;
  if (!canvas || !cropImage.value) return;
  const cx = (canvas.width - cropSize.value) / 2;
  const cy = (canvas.height - cropSize.value) / 2;

  const outCanvas = document.createElement('canvas');
  outCanvas.width = cropSize.value;
  outCanvas.height = cropSize.value;
  const octx = outCanvas.getContext('2d');
  octx.drawImage(
    cropImage.value,
    (cx - cropOffsetX.value) / cropScale.value,
    (cy - cropOffsetY.value) / cropScale.value,
    cropSize.value / cropScale.value,
    cropSize.value / cropScale.value,
    0, 0, cropSize.value, cropSize.value
  );

  form.image = outCanvas.toDataURL('image/jpeg', 0.92);
  cropVisible.value = false;
  ElMessage.success('卡图已裁剪并导入');
}

function startCropDrag(e) {
  cropDragging = true;
  cropDragStartX = e.clientX;
  cropDragStartY = e.clientY;
  cropStartOffsetX = cropOffsetX.value;
  cropStartOffsetY = cropOffsetY.value;
}

function onCropDrag(e) {
  if (!cropDragging) return;
  cropOffsetX.value = cropStartOffsetX + (e.clientX - cropDragStartX);
  cropOffsetY.value = cropStartOffsetY + (e.clientY - cropDragStartY);
  drawCropCanvas();
}

function stopCropDrag() {
  cropDragging = false;
}

function onCropWheel(e) {
  const delta = e.deltaY > 0 ? -0.05 : 0.05;
  cropScale.value = Math.max(0.1, Math.min(5, cropScale.value + delta));
  drawCropCanvas();
}

async function handleWriteCDB() {
  if (!form.password) {
    ElMessage.warning('请先输入或自动分配卡密');
    return;
  }
  if (!form.name.trim()) {
    ElMessage.warning('请输入卡片名称');
    return;
  }

  writing.value = true;
  try {
    const result = await api.writeCard({ ...form, password: Number(form.password) });
    if (result.success) {
      dialogSuccess.value = true;
      dialogMessage.value = result.message;
      dialogVisible.value = true;
      emit('cardWritten', result);
      ElMessage.success(result.message);
    } else {
      // 卡密冲突
      if (result.exists) {
        try {
          await ElMessageBox.confirm(
            `卡密 ${result.card_id} 已存在。是否覆盖？`,
            '卡密冲突',
            { confirmButtonText: '覆盖', cancelButtonText: '取消', type: 'warning' }
          );
          const overwriteResult = await api.writeCard({ ...form, password: Number(form.password) }, true);
          if (overwriteResult.success) {
            dialogSuccess.value = true;
            dialogMessage.value = overwriteResult.message;
            dialogVisible.value = true;
            emit('cardWritten', overwriteResult);
          }
        } catch {
          // 用户取消
        }
      } else {
        dialogSuccess.value = false;
        dialogMessage.value = result.message;
        dialogVisible.value = true;
      }
    }
  } catch (e) {
    dialogSuccess.value = false;
    dialogMessage.value = `写入失败: ${e.message}`;
    dialogVisible.value = true;
  } finally {
    writing.value = false;
  }
}
</script>

<style lang="scss" scoped>
.card-form-panel {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: linear-gradient(180deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
  border-radius: 0;
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

    .panel-actions {
      display: flex;
      gap: 8px;
    }
  }

  .panel-body {
    flex: 1;
    overflow-y: auto;
    padding: 12px 18px;

    &::-webkit-scrollbar {
      width: 5px;
    }
    &::-webkit-scrollbar-track {
      background: transparent;
    }
    &::-webkit-scrollbar-thumb {
      background: rgba(255, 255, 255, 0.15);
      border-radius: 3px;
    }
  }
}

.card-form {
  :deep(.el-form-item) {
    margin-bottom: 14px;
  }

  :deep(.el-form-item__label) {
    color: #a0a0b8;
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 0.5px;
    padding-bottom: 4px;
  }

  :deep(.el-input__wrapper) {
    background: rgba(255, 255, 255, 0.06);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 6px;
    box-shadow: none;
    transition: all 0.2s;

    &:hover {
      border-color: rgba(200, 170, 100, 0.4);
      background: rgba(255, 255, 255, 0.08);
    }

    &.is-focus {
      border-color: #c8a84e;
      box-shadow: 0 0 0 1px rgba(200, 168, 78, 0.2);
    }
  }

  :deep(.el-input__inner) {
    color: #e0d5c0;
    font-size: 13px;

    &::placeholder {
      color: rgba(255, 255, 255, 0.25);
    }
  }

  :deep(.el-textarea__inner) {
    background: rgba(255, 255, 255, 0.06);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 6px;
    color: #e0d5c0;
    font-size: 13px;
    resize: vertical;
    min-height: 80px;

    &:hover {
      border-color: rgba(200, 170, 100, 0.4);
    }

    &:focus {
      border-color: #c8a84e;
      box-shadow: 0 0 0 1px rgba(200, 168, 78, 0.2);
    }

    &::placeholder {
      color: rgba(255, 255, 255, 0.25);
    }
  }

  :deep(.el-select .el-input__wrapper) {
    background: rgba(255, 255, 255, 0.06);
  }

  :deep(.el-select-dropdown) {
    background: #1a1a2e;
    border: 1px solid rgba(255, 255, 255, 0.1);

    .el-select-dropdown__item {
      color: #c0c0d0;
      font-size: 13px;

      &:hover {
        background: rgba(200, 168, 78, 0.15);
      }

      &.selected {
        color: #e8d5a3;
        background: rgba(200, 168, 78, 0.1);
      }
    }
  }

  :deep(.el-input-number) {
    width: 100%;

    .el-input-number__decrease,
    .el-input-number__increase {
      background: rgba(255, 255, 255, 0.04);
      border-color: rgba(255, 255, 255, 0.1);
      color: #a0a0b8;

      &:hover {
        color: #e8d5a3;
      }
    }
  }

  :deep(.el-checkbox) {
    color: #b0b0c0;
    font-size: 12px;
    margin-right: 12px;

    .el-checkbox__inner {
      background: rgba(255, 255, 255, 0.08);
      border-color: rgba(255, 255, 255, 0.2);
    }

    &.is-checked .el-checkbox__inner {
      background: #c8a84e;
      border-color: #c8a84e;
    }
  }

  :deep(.el-button) {
    font-size: 12px;
    letter-spacing: 0.5px;
  }
}

/* 分区样式 */
.form-section {
  margin-bottom: 20px;
  padding: 14px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 8px;

  .section-title {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 13px;
    font-weight: 700;
    color: #c8a84e;
    margin-bottom: 12px;
    letter-spacing: 1px;

    .section-icon {
      font-size: 15px;
    }

    &.collapsible {
      cursor: pointer;
      user-select: none;

      &:hover {
        color: #e8d5a3;
      }
    }

    .collapse-icon {
      margin-left: auto;
      font-size: 10px;
      color: #888;
    }
  }
}

/* Link箭头选择器 */
.link-arrow-selector {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;

  .arrow-btn {
    width: 36px;
    height: 36px;
    display: flex;
    align-items: center;
    justify-content: center;
    border: 1.5px solid rgba(255, 255, 255, 0.15);
    border-radius: 6px;
    font-size: 14px;
    cursor: pointer;
    transition: all 0.2s;
    color: rgba(255, 255, 255, 0.3);
    background: rgba(255, 255, 255, 0.03);

    &:hover {
      border-color: rgba(200, 168, 78, 0.5);
      color: rgba(255, 255, 255, 0.6);
    }

    &.active {
      border-color: #c8a84e;
      background: rgba(200, 168, 78, 0.2);
      color: #e8d5a3;
      box-shadow: 0 0 8px rgba(200, 168, 78, 0.2);
    }
  }
}

.link-value-display {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 32px;
  background: rgba(200, 168, 78, 0.15);
  border: 1px solid rgba(200, 168, 78, 0.3);
  border-radius: 6px;
  color: #e8d5a3;
  font-size: 18px;
  font-weight: 700;
}

/* 结果弹窗 */
.result-content {
  text-align: center;
  padding: 20px 0;

  .result-icon {
    font-size: 48px;
    margin-bottom: 12px;
  }

  .result-message {
    font-size: 14px;
    color: #c0c0d0;
    line-height: 1.6;
  }

  &.success .result-message {
    color: #7ecf8c;
  }

  &.error .result-message {
    color: #e06c6c;
  }
}

:deep(.el-dialog) {
  background: #1a1a2e;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;

  .el-dialog__header {
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    padding: 16px 20px;
  }

  .el-dialog__title {
    color: #e8d5a3;
    font-weight: 700;
  }

  .el-dialog__body {
    padding: 20px;
  }

  .el-dialog__footer {
    border-top: 1px solid rgba(255, 255, 255, 0.08);
    padding: 12px 20px;
  }
}
</style>
