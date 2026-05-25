<template>
  <div class="card-preview-wrapper" :style="{ transform: `scale(${previewScale})` }">
    <div ref="cardContainer" class="card-container" />
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onBeforeUnmount, shallowRef, computed } from 'vue';
import { YugiohCard as YugiohCardRenderer } from 'yugioh-card';

const props = defineProps({
  cardData: {
    type: Object,
    required: true,
  },
});

const cardContainer = ref(null);
const cardRenderer = shallowRef(null);
const previewScale = ref(0.55);

// 将 cardData 序列化为字符串，确保任何嵌套变化都触发 watch
const cardDataString = computed(() => JSON.stringify(props.cardData));

onMounted(() => {
  initRenderer();
});

onBeforeUnmount(() => {
  if (cardRenderer.value) {
    cardRenderer.value.leafer?.destroy();
    cardRenderer.value = null;
  }
});

// 监听序列化字符串变化 → 确保每次表单修改都立即刷新卡图
watch(cardDataString, () => {
  if (!cardRenderer.value && cardContainer.value) {
    initRenderer();
    return;
  }
  updateRenderer();
});

function initRenderer() {
  if (!cardContainer.value) return;

  // 销毁旧实例
  if (cardRenderer.value) {
    cardRenderer.value.leafer?.destroy();
  }

  // 转换数据格式以匹配渲染器期望
  const renderData = convertToRenderData(props.cardData);

  const resPath = import.meta.env.PROD
    ? 'https://raw.githubusercontent.com/kooriookami/yugioh-card/refs/heads/master/src/assets/yugioh-card'
    : 'src/assets/yugioh-card';

  cardRenderer.value = new YugiohCardRenderer({
    view: cardContainer.value,
    data: renderData,
    resourcePath: resPath,
  });
}

function updateRenderer() {
  if (!cardRenderer.value) {
    initRenderer();
    return;
  }

  const renderData = convertToRenderData(props.cardData);
  cardRenderer.value.setData(renderData);
}

function convertToRenderData(formData) {
  // 将制卡器表单数据转换为 yugioh-card 渲染器期望的数据格式
  const data = {
    language: formData.language || 'sc',
    font: formData.font || '',
    name: formData.name || '(未命名)',
    color: formData.color || '',
    align: formData.align || 'left',
    gradient: formData.gradient || false,
    gradientColor1: formData.gradientColor1 || '#999999',
    gradientColor2: formData.gradientColor2 || '#ffffff',
    type: formData.type || 'monster',
    attribute: formData.attribute || 'dark',
    icon: formData.icon || '',
    image: formData.image || '',
    cardType: formData.cardType || 'normal',
    pendulumType: getPendulumType(formData),
    level: formData.level || 0,
    rank: formData.rank || 0,
    pendulumScale: formData.pendulumScale || 0,
    pendulumDescription: formData.pendulumDescription || '',
    monsterType: getMonsterTypeString(formData),
    atkBar: formData.atkBar !== undefined ? formData.atkBar : true,
    atk: computeAtk(formData),
    def: computeDef(formData),
    arrowList: formData.arrowList || [],
    description: formData.description || '',
    firstLineCompress: formData.firstLineCompress || false,
    descriptionAlign: formData.descriptionAlign || false,
    descriptionZoom: formData.descriptionZoom || 1,
    descriptionWeight: formData.descriptionWeight || 0,
    package: formData.package || '',
    password: formData.password ? String(formData.password) : '',
    copyright: formData.copyright || '',
    laser: formData.laser || '',
    rare: formData.rare || '',
    twentieth: formData.twentieth || false,
    radius: formData.radius !== undefined ? formData.radius : true,
    scale: formData.scale || 1,
  };

  return data;
}

function getPendulumType(formData) {
  if (formData.type !== 'pendulum') return 'normal-pendulum';
  const ct = formData.cardType || 'normal';
  return `${ct}-pendulum`;
}

function getMonsterTypeString(formData) {
  if (formData.type === 'spell' || formData.type === 'trap') {
    return '';
  }

  let race = formData.monsterType || '';
  // 美化种族名称
  const raceNames = {
    'dragon': '龙族',
    'spellcaster': '魔法师族',
    'warrior': '战士族',
    'machine': '机械族',
    'fiend': '恶魔族',
    'fairy': '天使族',
    'zombie': '不死族',
    'reptile': '爬虫类族',
    'dinosaur': '恐龙族',
    'sea-serpent': '海龙族',
    'fish': '鱼族',
    'aqua': '水族',
    'pyro': '炎族',
    'thunder': '雷族',
    'rock': '岩石族',
    'plant': '植物族',
    'insect': '昆虫族',
    'beast': '兽族',
    'beast-warrior': '兽战士族',
    'winged-beast': '鸟兽族',
    'psychic': '念动力族',
    'wyrm': '幻龙族',
    'cyberse': '电子界族',
    'illusion': '幻想魔族',
    'divine-beast': '幻神兽族',
    'creator-god': '创造神族',
  };
  if (race && raceNames[race]) {
    race = raceNames[race];
  }

  // 添加子类型后缀
  const subTypes = [];
  const ct = formData.cardType || 'normal';
  if (ct === 'normal') subTypes.push('通常');
  if (ct === 'effect') subTypes.push('效果');
  if (ct === 'fusion') subTypes.push('融合');
  if (ct === 'ritual') subTypes.push('仪式');
  if (ct === 'synchro') subTypes.push('同调');
  if (ct === 'xyz') subTypes.push('超量');
  if (ct === 'link') subTypes.push('连接');

  // abilities
  const abilities = formData.abilities || [];
  if (abilities.includes('tuner')) subTypes.push('协调');
  if (abilities.includes('spirit')) subTypes.push('灵魂');
  if (abilities.includes('union')) subTypes.push('同盟');
  if (abilities.includes('gemini')) subTypes.push('二重');
  if (abilities.includes('token')) subTypes.push('衍生物');

  if (subTypes.length > 0) {
    return `${race}/${subTypes.join('/')}`;
  }
  return race;
}

function computeAtk(formData) {
  if (formData.type === 'spell' || formData.type === 'trap') return 0;
  if (formData.cardType === 'link') return 0;
  return formData.atk ?? 0;
}

function computeDef(formData) {
  if (formData.type === 'spell' || formData.type === 'trap') return 0;
  if (formData.cardType === 'link') return 0;
  return formData.def ?? 0;
}

function exportImage() {
  if (!cardRenderer.value) return;
  const name = props.cardData.name || '卡片';
  cardRenderer.value.leafer.export(`${name}.png`, {
    screenshot: true,
    pixelRatio: devicePixelRatio,
  });
}

defineExpose({ exportImage });
</script>

<style lang="scss" scoped>
.card-preview-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform 0.3s ease;
  transform-origin: center center;
}

.card-container {
  display: inline-block;
}
</style>
