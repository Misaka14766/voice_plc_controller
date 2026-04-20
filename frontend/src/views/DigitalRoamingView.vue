<template>
  <div class="digital-roaming">
    <div class="roaming-bg">
      <div class="grid-lines"></div>
      <div class="floating-particles">
        <div v-for="i in 20" :key="i" class="particle" :style="getParticleStyle(i)"></div>
      </div>
    </div>

    <div class="roaming-header">
      <div class="header-left">
        <div class="cyber-corner top-left"></div>
        <h1 class="roaming-title">
          <span class="title-text">数字漫游模式</span>
          <span class="title-glow"></span>
        </h1>
        <div class="roaming-mode-switch" @click="handleExit">
          <div class="roaming-switch-track" :class="{ active: true }">
            <div class="roaming-switch-thumb">
              <el-icon><Monitor /></el-icon>
            </div>
          </div>
          <span class="roaming-switch-label">退出漫游</span>
        </div>
        <div class="status-indicators">
          <div class="status-item">
            <span class="status-dot pulse"></span>
            <span class="status-label">系统正常</span>
          </div>
          <div class="status-item">
            <span class="status-dot online"></span>
            <span class="status-label">PLC已连接</span>
          </div>
        </div>
      </div>
      <div class="header-right">
        <div class="time-display">
          <div class="time-value">{{ currentTime }}</div>
          <div class="time-date">{{ currentDate }}</div>
        </div>
      </div>
    </div>

    <div class="roaming-content">
      <div class="carousel-container">
        <Transition :name="carouselDirection === 'left' ? 'carousel-left' : 'carousel-right'" mode="out-in">
          <div :key="currentIndex" class="carousel-item">
            <component :is="currentComponent" />
          </div>
        </Transition>
      </div>

      <div class="carousel-indicators">
        <div
          v-for="(item, index) in carouselItems"
          :key="index"
          class="indicator"
          :class="{ active: index === currentIndex }"
          @click="goToSlide(index)"
        >
          <span class="indicator-dot"></span>
          <span class="indicator-label">{{ item.title }}</span>
        </div>
      </div>
    </div>

    <div class="roaming-footer">
      <div class="footer-left">
        <span class="footer-text">PLC科创实验室 v1.0</span>
      </div>
      <div class="footer-center">
        <div class="auto-play-controls">
          <el-button :icon="isPlaying ? VideoPause : VideoPlay" circle @click="toggleAutoPlay" />
          <span class="play-label">{{ isPlaying ? '自动播放中' : '已暂停' }}</span>
        </div>
      </div>
      <div class="footer-right">
        <span class="scan-line"></span>
      </div>
    </div>

    <div class="corner-decoration top-right">
      <svg viewBox="0 0 100 100" class="corner-svg">
        <path d="M100 0 L0 0 L0 10 L90 10 L90 100 L100 100 Z" fill="none" stroke="currentColor" stroke-width="2"/>
      </svg>
    </div>
    <div class="corner-decoration bottom-left">
      <svg viewBox="0 0 100 100" class="corner-svg">
        <path d="M0 100 L0 0 L10 0 L10 90 L100 90 L100 100 Z" fill="none" stroke="currentColor" stroke-width="2"/>
      </svg>
    </div>
    <div class="corner-decoration bottom-right">
      <svg viewBox="0 0 100 100" class="corner-svg">
        <path d="M100 100 L0 100 L0 90 L90 90 L90 0 L100 0 Z" fill="none" stroke="currentColor" stroke-width="2"/>
      </svg>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, h } from 'vue'
import { VideoPlay, VideoPause } from '@element-plus/icons-vue'
import * as THREE from 'three'
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js'

const emit = defineEmits<{
  exit: []
}>()

const currentIndex = ref(0)
const carouselDirection = ref('right')
const isPlaying = ref(true)
const currentTime = ref('')
const currentDate = ref('')

const ModelPanel = {
  setup() {
    const containerRef = ref<HTMLElement | null>(null)
    let scene: THREE.Scene
    let camera: THREE.PerspectiveCamera
    let renderer: THREE.WebGLRenderer
    let model: THREE.Object3D
    let animationId: number

    onMounted(() => {
      if (containerRef.value) {
        initThree()
      }
    })

    onUnmounted(() => {
      if (animationId) cancelAnimationFrame(animationId)
      if (renderer) renderer.dispose()
    })

    const initThree = () => {
      if (!containerRef.value) return

      const width = containerRef.value.clientWidth
      const height = containerRef.value.clientHeight

      scene = new THREE.Scene()
      scene.background = new THREE.Color(0x0a0a1a)

      camera = new THREE.PerspectiveCamera(60, width / height, 0.1, 1000)
      camera.position.set(0, 2, 5)

      renderer = new THREE.WebGLRenderer({ antialias: true })
      renderer.setSize(width, height)
      renderer.setPixelRatio(window.devicePixelRatio)
      renderer.toneMapping = THREE.ACESFilmicToneMapping
      containerRef.value.appendChild(renderer.domElement)

      const ambientLight = new THREE.AmbientLight(0x4040ff, 0.5)
      scene.add(ambientLight)

      const pointLight1 = new THREE.PointLight(0x00ffff, 2, 20)
      pointLight1.position.set(5, 5, 5)
      scene.add(pointLight1)

      const pointLight2 = new THREE.PointLight(0xff00ff, 2, 20)
      pointLight2.position.set(-5, 3, -5)
      scene.add(pointLight2)

      const gridHelper = new THREE.GridHelper(20, 40, 0x00ffff, 0x004444)
      scene.add(gridHelper)

      const loader = new GLTFLoader()
      loader.load(
        '/models/tank.glb',
        (gltf) => {
          model = gltf.scene
          model.scale.set(0.5, 0.5, 0.5)
          scene.add(model)
        },
        undefined,
        () => {}
      )

      const torusGeo = new THREE.TorusGeometry(2, 0.05, 16, 100)
      const torusMat = new THREE.MeshBasicMaterial({ color: 0x00ffff })
      const torus = new THREE.Mesh(torusGeo, torusMat)
      torus.rotation.x = Math.PI / 2
      torus.position.y = -1
      scene.add(torus)

      animate()
    }

    const animate = () => {
      animationId = requestAnimationFrame(animate)
      if (model) {
        model.rotation.y += 0.005
      }
      renderer.render(scene, camera)
    }

    return () => h('div', { class: 'panel-content model-panel' }, [
      h('div', { ref: containerRef, class: 'model-container' })
    ])
  }
}

const DataPanel = {
  setup() {
    const dataItems = ref([
      { name: '温度传感器', value: 45.2, unit: '°C', min: 0, max: 100 },
      { name: '压力传感器', value: 2.5, unit: 'MPa', min: 0, max: 5 },
      { name: '流量计', value: 120.5, unit: 'L/min', min: 0, max: 200 },
      { name: '液位传感器', value: 75.0, unit: '%', min: 0, max: 100 },
      { name: '电机转速', value: 1450, unit: 'RPM', min: 0, max: 3000 },
      { name: '功率', value: 45.8, unit: 'kW', min: 0, max: 100 }
    ])

    const formatValue = (val: number) => val.toFixed(1)

    return () => h('div', { class: 'panel-content data-panel' }, [
      h('h3', { class: 'panel-title' }, '实时数据监控'),
      h('div', { class: 'data-grid' },
        dataItems.value.map(item =>
          h('div', { class: 'data-card', key: item.name }, [
            h('div', { class: 'data-name' }, item.name),
            h('div', { class: 'data-value' }, [
              h('span', { class: 'value' }, formatValue(item.value)),
              h('span', { class: 'unit' }, item.unit)
            ]),
            h('div', { class: 'data-bar' }, [
              h('div', {
                class: 'bar-fill',
                style: { width: `${(item.value / item.max) * 100}%` }
              })
            ])
          ])
        )
      )
    ])
  }
}

const ProcessPanel = {
  setup() {
    const steps = ref([
      { id: 1, name: '原料投入', status: 'completed', progress: 100 },
      { id: 2, name: '混合搅拌', status: 'active', progress: 65 },
      { id: 3, name: '加热反应', status: 'pending', progress: 0 },
      { id: 4, name: '冷却分离', status: 'pending', progress: 0 },
      { id: 5, name: '成品输出', status: 'pending', progress: 0 }
    ])

    return () => h('div', { class: 'panel-content process-panel' }, [
      h('h3', { class: 'panel-title' }, '工艺流程监控'),
      h('div', { class: 'process-flow' },
        steps.value.map((step, idx) =>
          h('div', { class: `process-step ${step.status}`, key: step.id }, [
            h('div', { class: 'step-indicator' }, [
              h('div', { class: 'step-dot' }),
              idx < steps.value.length - 1 ? h('div', { class: 'step-line' }) : null
            ]),
            h('div', { class: 'step-content' }, [
              h('div', { class: 'step-name' }, step.name),
              h('div', { class: 'step-progress' }, `${step.progress}%`)
            ])
          ])
        )
      )
    ])
  }
}

const StatusPanel = {
  setup() {
    const systemStatus = ref({
      cpu: 35,
      memory: 62,
      network: 128.5,
      uptime: '72:34:15'
    })

    return () => h('div', { class: 'panel-content status-panel' }, [
      h('h3', { class: 'panel-title' }, '系统状态'),
      h('div', { class: 'status-grid' }, [
        h('div', { class: 'status-card' }, [
          h('div', { class: 'status-icon cpu' }),
          h('div', { class: 'status-info' }, [
            h('span', { class: 'label' }, 'CPU使用率'),
            h('span', { class: 'value' }, `${systemStatus.value.cpu}%`)
          ]),
          h('div', { class: 'progress-bar' }, [
            h('div', { class: 'progress-fill', style: { width: `${systemStatus.value.cpu}%` } })
          ])
        ]),
        h('div', { class: 'status-card' }, [
          h('div', { class: 'status-icon memory' }),
          h('div', { class: 'status-info' }, [
            h('span', { class: 'label' }, '内存使用率'),
            h('span', { class: 'value' }, `${systemStatus.value.memory}%`)
          ]),
          h('div', { class: 'progress-bar' }, [
            h('div', { class: 'progress-fill', style: { width: `${systemStatus.value.memory}%` } })
          ])
        ]),
        h('div', { class: 'status-card' }, [
          h('div', { class: 'status-icon network' }),
          h('div', { class: 'status-info' }, [
            h('span', { class: 'label' }, '网络带宽'),
            h('span', { class: 'value' }, `${systemStatus.value.network} Mbps`)
          ])
        ]),
        h('div', { class: 'status-card' }, [
          h('div', { class: 'status-icon uptime' }),
          h('div', { class: 'status-info' }, [
            h('span', { class: 'label' }, '运行时间'),
            h('span', { class: 'value' }, systemStatus.value.uptime)
          ])
        ])
      ])
    ])
  }
}

const MentorPanel = {
  setup() {
    return () => h('div', { class: 'panel-content mentor-panel' }, [
      h('h3', { class: 'panel-title' }, '导师介绍'),
      h('div', { class: 'mentor-content' }, [
        h('div', { class: 'mentor-image-container' }, [
          h('div', { class: 'mentor-image' }),
          h('div', { class: 'image-glow' })
        ]),
        h('div', { class: 'mentor-info' }, [
          h('h4', { class: 'mentor-name' }, '张教授'),
          h('p', { class: 'mentor-title' }, '自动化控制专家'),
          h('div', { class: 'mentor-description' }, [
            h('p', null, '张教授拥有20年自动化控制领域经验，专注于PLC编程与工业自动化系统设计。'),
            h('p', null, '曾主持多个大型工业自动化项目，发表学术论文30余篇，培养研究生50余人。'),
            h('p', null, '现任PLC科创实验室主任，致力于推动工业4.0技术在实际生产中的应用。')
          ]),
          h('div', { class: 'mentor-skills' }, [
            h('span', { class: 'skill-tag' }, 'PLC编程'),
            h('span', { class: 'skill-tag' }, '工业自动化'),
            h('span', { class: 'skill-tag' }, '控制系统设计'),
            h('span', { class: 'skill-tag' }, '工业4.0')
          ])
        ])
      ])
    ])
  }
}

const carouselItems = [
  { title: '3D模型', component: ModelPanel },
  { title: '数据监控', component: DataPanel },
  { title: '工艺流程', component: ProcessPanel },
  { title: '系统状态', component: StatusPanel },
  { title: '导师介绍', component: MentorPanel }
]

let autoPlayInterval: number

const currentComponent = computed(() => {
  return carouselItems[currentIndex.value]?.component
})

const updateTime = () => {
  const now = new Date()
  currentTime.value = now.toLocaleTimeString('zh-CN', { hour12: false })
  currentDate.value = now.toLocaleDateString('zh-CN', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })
}

const nextSlide = () => {
  carouselDirection.value = 'left'
  currentIndex.value = (currentIndex.value + 1) % carouselItems.length
}

const prevSlide = () => {
  carouselDirection.value = 'right'
  currentIndex.value = (currentIndex.value - 1 + carouselItems.length) % carouselItems.length
}

const goToSlide = (index: number) => {
  carouselDirection.value = index > currentIndex.value ? 'left' : 'right'
  currentIndex.value = index
}

const toggleAutoPlay = () => {
  isPlaying.value = !isPlaying.value
}

const handleExit = () => {
  emit('exit')
}

const getParticleStyle = (i: number) => {
  const size = Math.random() * 4 + 1
  const duration = Math.random() * 20 + 10
  const delay = Math.random() * 10
  return {
    width: `${size}px`,
    height: `${size}px`,
    left: `${Math.random() * 100}%`,
    top: `${Math.random() * 100}%`,
    animationDuration: `${duration}s`,
    animationDelay: `${delay}s`
  }
}

onMounted(() => {
  updateTime()
  setInterval(updateTime, 1000)

  autoPlayInterval = setInterval(() => {
    if (isPlaying.value) {
      nextSlide()
    }
  }, 8000)
})

onUnmounted(() => {
  if (autoPlayInterval) clearInterval(autoPlayInterval)
})
</script>

<style scoped>
.digital-roaming {
  width: 100%;
  height: 100vh;
  background: linear-gradient(135deg, #0a0a1a 0%, #1a0a2e 50%, #0a1a2e 100%);
  position: relative;
  overflow: hidden;
  font-family: 'Orbitron', 'Rajdhani', 'Microsoft YaHei', sans-serif;
}

.roaming-bg {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
}

.grid-lines {
  position: absolute;
  width: 100%;
  height: 100%;
  background-image:
    linear-gradient(rgba(0, 255, 255, 0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(0, 255, 255, 0.03) 1px, transparent 1px);
  background-size: 50px 50px;
  animation: gridMove 20s linear infinite;
}

@keyframes gridMove {
  0% { transform: perspective(500px) rotateX(60deg) translateY(0); }
  100% { transform: perspective(500px) rotateX(60deg) translateY(50px); }
}

.floating-particles {
  position: absolute;
  width: 100%;
  height: 100%;
}

.particle {
  position: absolute;
  background: radial-gradient(circle, rgba(0, 255, 255, 0.8), transparent);
  border-radius: 50%;
  animation: float 15s ease-in-out infinite;
}

@keyframes float {
  0%, 100% { transform: translateY(0) translateX(0); opacity: 0.3; }
  25% { transform: translateY(-100px) translateX(50px); opacity: 0.8; }
  50% { transform: translateY(-50px) translateX(-30px); opacity: 0.5; }
  75% { transform: translateY(-150px) translateX(20px); opacity: 0.7; }
}

.roaming-header {
  position: relative;
  z-index: 10;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 30px 40px;
}

.header-left {
  position: relative;
  display: flex;
  align-items: center;
  gap: 20px;
}

.cyber-corner {
  position: absolute;
  width: 20px;
  height: 20px;
}

.cyber-corner.top-left {
  top: -10px;
  left: -10px;
  border-top: 2px solid #00ffff;
  border-left: 2px solid #00ffff;
}

.roaming-title {
  position: relative;
  margin: 0;
}

.title-text {
  font-size: 32px;
  font-weight: 700;
  color: #00ffff;
  text-shadow: 0 0 20px rgba(0, 255, 255, 0.5);
  letter-spacing: 4px;
}

.title-glow {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(0, 255, 255, 0.4), transparent);
  animation: titleGlow 3s ease-in-out infinite;
}

@keyframes titleGlow {
  0%, 100% { transform: translateX(-100%); }
  50% { transform: translateX(100%); }
}

.roaming-mode-switch {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 6px 14px;
  background: rgba(0, 255, 255, 0.1);
  border: 1px solid rgba(0, 255, 255, 0.3);
  border-radius: 24px;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  backdrop-filter: blur(10px);
  box-shadow: 0 4px 20px rgba(0, 255, 255, 0.2);
  flex-shrink: 0;
}

.roaming-mode-switch:hover {
  background: rgba(0, 255, 255, 0.15);
  box-shadow: 0 6px 30px rgba(0, 255, 255, 0.3);
  transform: translateY(-2px);
}

.roaming-switch-track {
  width: 48px;
  height: 26px;
  background: linear-gradient(135deg, rgba(0, 255, 255, 0.3), rgba(0, 150, 255, 0.3));
  border: 1px solid rgba(0, 255, 255, 0.5);
  border-radius: 13px;
  position: relative;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: inset 0 0 10px rgba(0, 255, 255, 0.2);
}

.roaming-switch-track.active {
  background: linear-gradient(135deg, rgba(255, 100, 150, 0.4), rgba(255, 50, 100, 0.4));
  border-color: rgba(255, 100, 150, 0.6);
  box-shadow: inset 0 0 15px rgba(255, 100, 150, 0.3);
}

.roaming-switch-thumb {
  width: 22px;
  height: 22px;
  background: linear-gradient(135deg, #00ffff, #00aaff);
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 50%;
  position: absolute;
  top: 1px;
  left: 1px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 2px 8px rgba(0, 255, 255, 0.4);
  animation: thumbGlow 2s ease-in-out infinite alternate;
}

@keyframes thumbGlow {
  0% {
    box-shadow: 0 2px 8px rgba(0, 255, 255, 0.4);
  }
  100% {
    box-shadow: 0 4px 16px rgba(0, 255, 255, 0.8), 0 0 20px rgba(0, 255, 255, 0.5);
  }
}

.roaming-switch-track.active .roaming-switch-thumb {
  left: 24px;
  background: linear-gradient(135deg, #ff6699, #ff3366);
  box-shadow: 0 2px 8px rgba(255, 100, 150, 0.6);
  animation: activeThumbGlow 2s ease-in-out infinite alternate;
}

@keyframes activeThumbGlow {
  0% {
    box-shadow: 0 2px 8px rgba(255, 100, 150, 0.6);
  }
  100% {
    box-shadow: 0 4px 16px rgba(255, 100, 150, 0.9), 0 0 20px rgba(255, 100, 150, 0.6);
  }
}

.roaming-switch-thumb .el-icon {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.9);
  text-shadow: 0 0 4px rgba(255, 255, 255, 0.5);
}

.roaming-switch-label {
  font-size: 14px;
  font-weight: 600;
  color: #00ffff;
  text-shadow: 0 0 8px rgba(0, 255, 255, 0.5);
  letter-spacing: 1px;
  transition: all 0.3s ease;
}

.roaming-mode-switch:hover .roaming-switch-label {
  color: #ffffff;
  text-shadow: 0 0 12px rgba(255, 255, 255, 0.8);
}

.status-indicators {
  display: flex;
  gap: 20px;
  margin-top: 15px;
}

.status-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #00ff00;
}

.status-dot.pulse {
  animation: pulse 2s ease-in-out infinite;
}

.status-dot.online {
  background: #00ffff;
  box-shadow: 0 0 10px #00ffff;
}

@keyframes pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.5; transform: scale(1.2); }
}

.status-label {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.7);
  letter-spacing: 1px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 30px;
}

.time-display {
  text-align: right;
}

.time-value {
  font-size: 28px;
  font-weight: 700;
  color: #00ffff;
  text-shadow: 0 0 15px rgba(0, 255, 255, 0.5);
  letter-spacing: 2px;
}

.time-date {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.6);
  margin-top: 5px;
}

.exit-btn {
  width: 50px;
  height: 50px;
  background: linear-gradient(135deg, #ff0055 0%, #ff5500 100%) !important;
  border: none !important;
  box-shadow: 0 0 20px rgba(255, 0, 85, 0.5);
  transition: all 0.3s ease;
}

.exit-btn:hover {
  transform: scale(1.1);
  box-shadow: 0 0 30px rgba(255, 0, 85, 0.8);
}

.roaming-content {
  position: relative;
  z-index: 10;
  height: calc(100vh - 200px);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 0 40px;
}

.carousel-container {
  width: 100%;
  max-width: 1200px;
  height: 500px;
  perspective: 1000px;
}

.carousel-item {
  width: 100%;
  height: 100%;
  background: rgba(0, 20, 40, 0.6);
  border: 1px solid rgba(0, 255, 255, 0.3);
  border-radius: 10px;
  backdrop-filter: blur(10px);
  box-shadow:
    0 0 30px rgba(0, 255, 255, 0.1),
    inset 0 0 60px rgba(0, 255, 255, 0.05);
  overflow: hidden;
}

.carousel-left-enter-active,
.carousel-left-leave-active,
.carousel-right-enter-active,
.carousel-right-leave-active {
  transition: all 0.6s cubic-bezier(0.4, 0, 0.2, 1);
}

.carousel-left-enter-from {
  opacity: 0;
  transform: translateX(100px) scale(0.9);
}

.carousel-left-leave-to {
  opacity: 0;
  transform: translateX(-100px) scale(0.9);
}

.carousel-right-enter-from {
  opacity: 0;
  transform: translateX(-100px) scale(0.9);
}

.carousel-right-leave-to {
  opacity: 0;
  transform: translateX(100px) scale(0.9);
}

.carousel-indicators {
  display: flex;
  gap: 30px;
  margin-top: 30px;
}

.indicator {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.indicator-dot {
  width: 12px;
  height: 12px;
  border: 2px solid rgba(0, 255, 255, 0.5);
  border-radius: 50%;
  transition: all 0.3s ease;
}

.indicator.active .indicator-dot {
  background: #00ffff;
  border-color: #00ffff;
  box-shadow: 0 0 15px #00ffff;
}

.indicator:hover .indicator-dot {
  border-color: #00ffff;
}

.indicator-label {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
  letter-spacing: 1px;
  transition: all 0.3s ease;
}

.indicator.active .indicator-label {
  color: #00ffff;
  text-shadow: 0 0 10px rgba(0, 255, 255, 0.5);
}

.roaming-footer {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  z-index: 10;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 40px;
}

.footer-text {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.4);
  letter-spacing: 2px;
}

.footer-center {
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 20px;
}

.auto-play-controls {
  display: flex;
  align-items: center;
  gap: 10px;
}

.auto-play-controls .el-button {
  background: rgba(0, 255, 255, 0.1) !important;
  border: 1px solid rgba(0, 255, 255, 0.3) !important;
  color: #00ffff !important;
}

.auto-play-controls .el-button:hover {
  background: rgba(0, 255, 255, 0.2) !important;
}

.play-label {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.8);
  letter-spacing: 1px;
  text-shadow: 0 0 8px rgba(255, 255, 255, 0.5);
}

.scan-line {
  position: absolute;
  bottom: 0;
  left: 0;
  width: 100%;
  height: 2px;
  background: linear-gradient(90deg, transparent, #00ffff, transparent);
  animation: scan 4s ease-in-out infinite;
}

@keyframes scan {
  0%, 100% { transform: translateX(-100%); opacity: 0; }
  50% { transform: translateX(100%); opacity: 1; }
}

.corner-decoration {
  position: absolute;
  width: 100px;
  height: 100px;
  color: rgba(0, 255, 255, 0.3);
}

.corner-decoration.top-right {
  top: 20px;
  right: 20px;
}

.corner-decoration.bottom-left {
  bottom: 20px;
  left: 20px;
}

.corner-decoration.bottom-right {
  bottom: 20px;
  right: 20px;
}

.corner-svg {
  width: 100%;
  height: 100%;
}

.panel-content {
  width: 100%;
  height: 100%;
  padding: 30px;
}

.panel-title {
  font-size: 20px;
  color: #00ffff;
  margin: 0 0 30px 0;
  letter-spacing: 3px;
  text-shadow: 0 0 10px rgba(0, 255, 255, 0.5);
}

.model-panel {
  padding: 0;
}

.model-container {
  width: 100%;
  height: 100%;
}

.data-panel {
  overflow-y: auto;
}

.data-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
}

.data-card {
  background: rgba(0, 20, 40, 0.8);
  border: 1px solid rgba(0, 255, 255, 0.2);
  border-radius: 8px;
  padding: 20px;
  transition: all 0.3s ease;
}

.data-card:hover {
  border-color: rgba(0, 255, 255, 0.5);
  box-shadow: 0 0 20px rgba(0, 255, 255, 0.2);
}

.data-name {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.6);
  margin-bottom: 10px;
  letter-spacing: 1px;
}

.data-value {
  display: flex;
  align-items: baseline;
  gap: 5px;
}

.data-value .value {
  font-size: 28px;
  font-weight: 700;
  color: #00ffff;
  text-shadow: 0 0 10px rgba(0, 255, 255, 0.5);
}

.data-value .unit {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.5);
}

.data-bar {
  height: 4px;
  background: rgba(0, 255, 255, 0.1);
  border-radius: 2px;
  margin-top: 15px;
  overflow: hidden;
}

.bar-fill {
  height: 100%;
  background: linear-gradient(90deg, #00ffff, #00ff88);
  border-radius: 2px;
  transition: width 1s ease;
}

.process-panel {
  overflow-y: auto;
}

.process-flow {
  display: flex;
  flex-direction: column;
}

.mentor-panel {
  padding: 40px;
  display: flex;
  flex-direction: column;
  align-items: center;
  overflow-y: auto;
}

.mentor-content {
  display: flex;
  gap: 40px;
  align-items: center;
  width: 100%;
  max-width: 900px;
  animation: slideIn 1s ease-out;
}

.mentor-image-container {
  position: relative;
  width: 200px;
  height: 200px;
  animation: pulse 2s ease-in-out infinite alternate;
}

.mentor-image {
  width: 100%;
  height: 100%;
  background: linear-gradient(135deg, #00ffff, #00ff88), url('/Illustration_Vedal.png');
  background-size: cover;
  background-position: center;
  background-blend-mode: overlay;
  border-radius: 50%;
  box-shadow: 0 0 30px rgba(0, 255, 255, 0.5);
  position: relative;
  overflow: hidden;
}

.mentor-image::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.3);
  border-radius: 50%;
}

.image-glow {
  position: absolute;
  top: -10px;
  left: -10px;
  right: -10px;
  bottom: -10px;
  background: linear-gradient(45deg, #00ffff, #00ff88, #00ffff);
  border-radius: 50%;
  z-index: -1;
  animation: rotate 3s linear infinite;
  opacity: 0.6;
}

.mentor-info {
  flex: 1;
  animation: fadeIn 1.5s ease-out;
}

.mentor-name {
  font-size: 24px;
  font-weight: 700;
  color: #00ffff;
  text-shadow: 0 0 15px rgba(0, 255, 255, 0.8);
  margin: 0 0 10px 0;
  letter-spacing: 2px;
}

.mentor-title {
  font-size: 16px;
  color: rgba(255, 255, 255, 0.9);
  text-shadow: 0 0 10px rgba(255, 255, 255, 0.5);
  margin: 0 0 20px 0;
  letter-spacing: 1px;
}

.mentor-description {
  margin: 0 0 20px 0;
  line-height: 1.6;
}

.mentor-description p {
  color: rgba(255, 255, 255, 0.95);
  text-shadow: 0 0 8px rgba(255, 255, 255, 0.3);
  margin: 0 0 10px 0;
  font-size: 14px;
}

.mentor-skills {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.skill-tag {
  background: rgba(0, 255, 255, 0.1);
  border: 1px solid rgba(0, 255, 255, 0.3);
  border-radius: 16px;
  padding: 6px 12px;
  font-size: 12px;
  color: #00ffff;
  letter-spacing: 1px;
  transition: all 0.3s ease;
  animation: slideInUp 0.5s ease-out forwards;
}

.skill-tag:hover {
  background: rgba(0, 255, 255, 0.2);
  box-shadow: 0 0 15px rgba(0, 255, 255, 0.4);
  transform: translateY(-2px);
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateX(-50px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

@keyframes slideInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes rotate {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

@media (max-width: 768px) {
  .mentor-content {
    flex-direction: column;
    text-align: center;
  }
  
  .mentor-image-container {
    width: 150px;
    height: 150px;
  }
}

.process-step {
  display: flex;
  align-items: flex-start;
  gap: 20px;
}

.step-indicator {
  display: flex;
  align-items: center;
}

.step-dot {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  border: 2px solid rgba(255, 255, 255, 0.3);
  background: rgba(0, 20, 40, 0.8);
  transition: all 0.3s ease;
}

.process-step.completed .step-dot {
  background: #00ff00;
  border-color: #00ff00;
  box-shadow: 0 0 15px rgba(0, 255, 0, 0.5);
}

.process-step.active .step-dot {
  background: #00ffff;
  border-color: #00ffff;
  box-shadow: 0 0 15px rgba(0, 255, 255, 0.5);
  animation: pulse 2s ease-in-out infinite;
}

.step-line {
  width: 2px;
  height: 40px;
  background: rgba(255, 255, 255, 0.2);
  margin-left: 9px;
}

.process-step.completed .step-line {
  background: linear-gradient(to bottom, #00ff00, rgba(0, 255, 0, 0.3));
}

.step-content {
  flex: 1;
  padding-top: 2px;
}

.step-name {
  font-size: 16px;
  color: rgba(255, 255, 255, 0.8);
  margin-bottom: 5px;
}

.process-step.active .step-name {
  color: #00ffff;
  text-shadow: 0 0 10px rgba(0, 255, 255, 0.5);
}

.step-progress {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.4);
}

.status-panel {
  overflow-y: auto;
}

.status-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
}

.status-card {
  display: flex;
  align-items: center;
  gap: 15px;
  background: rgba(0, 20, 40, 0.8);
  border: 1px solid rgba(0, 255, 255, 0.2);
  border-radius: 8px;
  padding: 20px;
}

.status-icon {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  background: linear-gradient(135deg, rgba(0, 255, 255, 0.2), rgba(0, 255, 255, 0.1));
}

.status-icon.cpu { background: linear-gradient(135deg, rgba(255, 100, 0, 0.3), rgba(255, 100, 0, 0.1)); }
.status-icon.memory { background: linear-gradient(135deg, rgba(100, 0, 255, 0.3), rgba(100, 0, 255, 0.1)); }
.status-icon.network { background: linear-gradient(135deg, rgba(0, 255, 100, 0.3), rgba(0, 255, 100, 0.1)); }
.status-icon.uptime { background: linear-gradient(135deg, rgba(255, 255, 0, 0.3), rgba(255, 255, 0, 0.1)); }

.status-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.status-info .label {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
}

.status-info .value {
  font-size: 18px;
  font-weight: 600;
  color: #00ffff;
}

.progress-bar {
  width: 100%;
  height: 4px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 2px;
  margin-top: 8px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #00ffff, #00ff88);
  border-radius: 2px;
}

@media (max-width: 768px) {
  .roaming-header {
    padding: 20px;
    flex-direction: column;
    gap: 20px;
  }

  .title-text {
    font-size: 24px;
  }

  .carousel-container {
    height: 350px;
  }

  .data-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .status-grid {
    grid-template-columns: 1fr;
  }

  .carousel-indicators {
    gap: 15px;
  }

  .indicator-label {
    font-size: 10px;
  }
}
</style>
