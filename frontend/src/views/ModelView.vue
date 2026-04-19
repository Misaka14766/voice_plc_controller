<template>
  <div class="model-view">
    <el-row :gutter="20">
      <el-col :span="24">
        <el-card class="model-card">
          <template #header>
            <div class="card-header">
              <span class="card-title">3D 模型展示</span>
              <div class="header-actions">
                <el-button :icon="Refresh" circle @click="resetCamera" />
                <el-button :icon="FullScreen" circle @click="toggleFullscreen" />
              </div>
            </div>
          </template>
          <div ref="containerRef" class="model-container" @mousemove="onMouseMove" @mouseleave="onMouseLeave"></div>
          <div v-if="loading" class="loading-overlay">
            <el-icon class="is-loading"><Loading /></el-icon>
            <span>加载模型中...</span>
          </div>
          <div v-if="!hasModel" class="empty-overlay">
            <el-icon :size="64"><Box /></el-icon>
            <p>请将 GLB 模型文件放入 <code>public/models/</code> 目录</p>
            <p class="tip">文件名应命名为 <code>tank.glb</code></p>
          </div>
          <div v-show="tooltip.visible" class="model-tooltip" :style="{ left: tooltip.x + 'px', top: tooltip.y + 'px' }">
            <div class="tooltip-title">{{ tooltip.title }}</div>
            <div class="tooltip-value">
              <span class="value">{{ tooltip.value }}</span>
              <span class="unit">{{ tooltip.unit }}</span>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="data-panels">
      <el-col :xs="24" :sm="12" :md="6" v-for="varData in realtimeData" :key="varData.name">
        <el-card class="data-card" shadow="hover">
          <template #header>
            <div class="data-header">
              <span class="data-name">{{ varData.comment || varData.name }}</span>
            </div>
          </template>
          <div class="data-value" :class="getValueClass(varData)">
            <span class="value">{{ formatValue(varData.value) }}</span>
            <span class="unit">{{ varData.unit || '' }}</span>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="controls-panel">
      <el-col :span="24">
        <el-card>
          <template #header>
            <span>模型控制</span>
          </template>
          <el-space wrap>
            <el-button @click="autoRotate = !autoRotate" :type="autoRotate ? 'success' : 'default'">
              {{ autoRotate ? '停止旋转' : '自动旋转' }}
            </el-button>
            <el-button @click="showWireframe = !showWireframe">
              {{ showWireframe ? '实体模式' : '线框模式' }}
            </el-button>
            <el-button @click="resetCamera">重置视角</el-button>
          </el-space>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, reactive } from 'vue'
import * as THREE from 'three'
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js'
import { OrbitControls } from 'three/addons/controls/OrbitControls.js'
import { ElMessage } from 'element-plus'
import { Refresh, FullScreen, Loading, Box } from '@element-plus/icons-vue'
import { getConfig, getMonitorVariables, getRealtimeData } from '../api'
import { MODEL_COMPONENT_MAPPINGS } from '../config/modelMappings'

const containerRef = ref<HTMLElement | null>(null)
const loading = ref(false)
const hasModel = ref(true)
const autoRotate = ref(true)
const showWireframe = ref(false)
const realtimeData = ref<any[]>([])
const modelVariables = ref<any[]>([])

const tooltip = reactive({
  visible: false,
  x: 0,
  y: 0,
  title: '',
  value: '',
  unit: ''
})

let scene: THREE.Scene
let camera: THREE.PerspectiveCamera
let renderer: THREE.WebGLRenderer
let controls: OrbitControls
let model: THREE.Object3D
let animationId: number
let refreshInterval: number
let raycaster: THREE.Raycaster
let mouse: THREE.Vector2
let hoveredObject: THREE.Object3D | null = null
let originalMaterials: Map<THREE.Mesh, THREE.Material | THREE.Material[]> = new Map()

const MODEL_PATH = '/models/tank.glb'

const formatValue = (value: any) => {
  if (value === null || value === undefined) return '--'
  if (typeof value === 'number') {
    return value.toFixed(2)
  }
  return String(value)
}

const getValueClass = (varData: any) => {
  if (varData.value === null || varData.value === undefined) return 'no-data'
  const num = Number(varData.value)
  if (isNaN(num)) return 'normal'
  if (varData.min !== undefined && varData.max !== undefined) {
    if (num >= varData.max) return 'danger'
    if (num <= varData.min) return 'warning'
  }
  return 'normal'
}

const initThree = () => {
  if (!containerRef.value) return

  const width = containerRef.value.clientWidth
  const height = 500

  scene = new THREE.Scene()
  scene.background = new THREE.Color(0x1a1a2e)

  camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000)
  camera.position.set(5, 3, 5)

  renderer = new THREE.WebGLRenderer({ antialias: true })
  renderer.setSize(width, height)
  renderer.setPixelRatio(window.devicePixelRatio)
  renderer.shadowMap.enabled = true
  renderer.toneMapping = THREE.ACESFilmicToneMapping
  renderer.toneMappingExposure = 1.2
  renderer.outputColorSpace = THREE.SRGBColorSpace
  containerRef.value.appendChild(renderer.domElement)

  controls = new OrbitControls(camera, renderer.domElement)
  controls.enableDamping = true
  controls.dampingFactor = 0.05
  controls.autoRotate = autoRotate.value
  controls.autoRotateSpeed = 2

  raycaster = new THREE.Raycaster()
  mouse = new THREE.Vector2()

  const hemiLight = new THREE.HemisphereLight(0xffffff, 0x444444, 0.6)
  hemiLight.position.set(0, 20, 0)
  scene.add(hemiLight)

  const ambientLight = new THREE.AmbientLight(0xffffff, 0.3)
  scene.add(ambientLight)

  const mainLight = new THREE.DirectionalLight(0xffffff, 1.2)
  mainLight.position.set(5, 10, 5)
  mainLight.castShadow = true
  mainLight.shadow.mapSize.width = 2048
  mainLight.shadow.mapSize.height = 2048
  mainLight.shadow.camera.near = 0.5
  mainLight.shadow.camera.far = 50
  mainLight.shadow.camera.left = -10
  mainLight.shadow.camera.right = 10
  mainLight.shadow.camera.top = 10
  mainLight.shadow.camera.bottom = -10
  scene.add(mainLight)

  const fillLight = new THREE.DirectionalLight(0x8ec5fc, 0.5)
  fillLight.position.set(-5, 5, -5)
  scene.add(fillLight)

  const backLight = new THREE.DirectionalLight(0xc9d6ff, 0.3)
  backLight.position.set(0, 5, -10)
  scene.add(backLight)

  const gridHelper = new THREE.GridHelper(10, 10, 0x444444, 0x222222)
  scene.add(gridHelper)

  const loader = new GLTFLoader()
  loading.value = true

  loader.load(
    MODEL_PATH,
    (gltf) => {
      model = gltf.scene
      model.traverse((child) => {
        if ((child as THREE.Mesh).isMesh) {
          const mesh = child as THREE.Mesh
          mesh.castShadow = true
          mesh.receiveShadow = true
          originalMaterials.set(mesh, mesh.material)
          console.log('模型部件名称:', child.name)
        }
      })
      scene.add(model)
      loading.value = false
      hasModel.value = true
      ElMessage.success('模型加载成功')
    },
    undefined,
    (error) => {
      console.error('模型加载失败:', error)
      loading.value = false
      hasModel.value = false
    }
  )

  animate()

  window.addEventListener('resize', onWindowResize)
}

const animate = () => {
  animationId = requestAnimationFrame(animate)
  controls.autoRotate = autoRotate.value
  controls.update()
  renderer.render(scene, camera)
}

watch(showWireframe, (wireframe) => {
  if (!model) return
  model.traverse((child) => {
    if ((child as THREE.Mesh).isMesh) {
      const mesh = child as THREE.Mesh
      if (Array.isArray(mesh.material)) {
        mesh.material.forEach((mat: THREE.Material) => {
          if ('wireframe' in mat) mat.wireframe = wireframe
        })
      } else if (mesh.material && 'wireframe' in mesh.material) {
        (mesh.material as THREE.MeshStandardMaterial).wireframe = wireframe
      }
    }
  })
})

watch(autoRotate, (rotating) => {
  controls.autoRotate = rotating
})

const onWindowResize = () => {
  if (!containerRef.value) return
  const width = containerRef.value.clientWidth
  const height = 500
  camera.aspect = width / height
  camera.updateProjectionMatrix()
  renderer.setSize(width, height)
}

const resetCamera = () => {
  camera.position.set(5, 3, 5)
  camera.lookAt(0, 0, 0)
  controls.reset()
}

const toggleFullscreen = () => {
  if (!containerRef.value) return
  if (!document.fullscreenElement) {
    containerRef.value.requestFullscreen()
  } else {
    document.exitFullscreen()
  }
}

const onMouseMove = (event: MouseEvent) => {
  if (!containerRef.value || !model || !raycaster) return

  const rect = containerRef.value.getBoundingClientRect()
  mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1
  mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1

  raycaster.setFromCamera(mouse, camera)

  const meshes: THREE.Mesh[] = []
  model.traverse((child) => {
    if ((child as THREE.Mesh).isMesh) {
      meshes.push(child as THREE.Mesh)
    }
  })

  const intersects = raycaster.intersectObjects(meshes, false)

  const firstIntersect = intersects[0]
  if (firstIntersect) {
    const intersected = firstIntersect.object as THREE.Mesh
    const objectName = intersected.name || (intersected.parent && intersected.parent.name) || ''
    console.log('悬停部件:', objectName || '(无名称)', '| 完整路径:', intersected.parent?.name || '')

    if (hoveredObject !== intersected) {
      if (hoveredObject) {
        resetObjectHighlight(hoveredObject as THREE.Mesh)
      }
      highlightObject(intersected)
      hoveredObject = intersected
    }

    const mapping = findComponentMapping(objectName)
    console.log('查找映射:', objectName, '->', mapping)
    if (mapping) {
      console.log('realtimeData 变量名列表:', realtimeData.value.map(d => d.name))
      const varData = realtimeData.value.find(d => d.name === mapping.variable)
      console.log('查找变量:', mapping.variable, '->', varData)
      tooltip.visible = true
      tooltip.x = event.clientX - rect.left + 15
      tooltip.y = event.clientY - rect.top + 15
      tooltip.title = mapping.label
      tooltip.value = varData ? formatValue(varData.value) : '--'
      tooltip.unit = varData?.unit || ''
    } else {
      tooltip.visible = false
    }
  } else {
    if (hoveredObject) {
      resetObjectHighlight(hoveredObject as THREE.Mesh)
      hoveredObject = null
    }
    tooltip.visible = false
  }
}

const onMouseLeave = () => {
  if (hoveredObject) {
    resetObjectHighlight(hoveredObject as THREE.Mesh)
    hoveredObject = null
  }
  tooltip.visible = false
}

const findComponentMapping = (objectName: string): { variable: string; label: string } | null => {
  for (const [key, value] of Object.entries(MODEL_COMPONENT_MAPPINGS)) {
    if (objectName.toLowerCase().includes(key.toLowerCase())) {
      return value
    }
  }
  return null
}

const highlightObject = (mesh: THREE.Mesh) => {
  const originalMaterial = originalMaterials.get(mesh)
  if (!originalMaterial) return

  const highlightMaterial = new THREE.MeshStandardMaterial({
    color: 0x00ff88,
    emissive: 0x00ff88,
    emissiveIntensity: 0.3,
    metalness: 0.5,
    roughness: 0.5,
    transparent: true,
    opacity: 0.9
  })

  mesh.material = highlightMaterial
}

const resetObjectHighlight = (mesh: THREE.Mesh) => {
  const originalMaterial = originalMaterials.get(mesh)
  if (originalMaterial) {
    mesh.material = originalMaterial
  }
}

const fetchData = async () => {
  try {
    const configRes = await getConfig()
    if (!configRes.data.db_enabled) return

    const varsRes = await getMonitorVariables()
    if (!varsRes.data.success) return

    modelVariables.value = varsRes.data.variables.map((v: [string, string]) => ({
      name: v[0],
      type: v[1]
    }))

    if (varsRes.data.variables.length > 0) {
      const varNames = varsRes.data.variables.map((v: [string, string]) => v[0])
      const dataRes = await getRealtimeData(varNames)
      if (dataRes.data.success) {
        const dataMap = dataRes.data.data as Record<string, any>
        realtimeData.value = varsRes.data.variables.map((v: [string, string]) => {
          const item = dataMap[v[0]] || {}
          return {
            name: v[0],
            type: v[1],
            value: item.value ?? null,
            timestamp: item.timestamp
          }
        })
      }
    }
  } catch (error) {
    console.error('获取数据失败:', error)
  }
}

onMounted(() => {
  initThree()
  fetchData()
  refreshInterval = window.setInterval(fetchData, 2000)
})

onUnmounted(() => {
  cancelAnimationFrame(animationId)
  clearInterval(refreshInterval)
  window.removeEventListener('resize', onWindowResize)
  if (renderer) {
    renderer.dispose()
  }
})
</script>

<style scoped>
.model-view {
  padding: 20px 0;
}

.model-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-title {
  font-size: 18px;
  font-weight: 600;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.model-container {
  width: 100%;
  height: 500px;
  border-radius: 8px;
  overflow: hidden;
  position: relative;
}

.loading-overlay,
.empty-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  background: rgba(26, 26, 46, 0.9);
  color: #fff;
  gap: 16px;
}

.empty-overlay {
  background: rgba(26, 26, 46, 0.7);
}

.empty-overlay code {
  background: rgba(255, 255, 255, 0.1);
  padding: 2px 8px;
  border-radius: 4px;
  font-family: monospace;
}

.empty-overlay .tip {
  font-size: 12px;
  color: #909399;
}

.data-panels {
  margin-bottom: 20px;
}

.data-card {
  margin-bottom: 16px;
}

.data-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.data-name {
  font-weight: 500;
  color: #303133;
}

.data-value {
  text-align: center;
  padding: 16px 0;
}

.data-value .value {
  font-size: 32px;
  font-weight: 700;
  font-family: 'Roboto Mono', monospace;
}

.data-value .unit {
  font-size: 16px;
  color: #909399;
  margin-left: 4px;
}

.data-value.normal {
  color: #409eff;
}

.data-value.warning {
  color: #e6a23c;
}

.data-value.danger {
  color: #f56c6c;
}

.data-value.no-data {
  color: #c0c4cc;
}

.controls-panel {
  margin-bottom: 20px;
}

.model-tooltip {
  position: absolute;
  background: rgba(0, 0, 0, 0.85);
  border: 1px solid rgba(0, 255, 136, 0.5);
  border-radius: 8px;
  padding: 12px 16px;
  pointer-events: none;
  z-index: 100;
  min-width: 120px;
  box-shadow: 0 4px 12px rgba(0, 255, 136, 0.2);
}

.tooltip-title {
  font-size: 12px;
  color: #909399;
  margin-bottom: 4px;
}

.tooltip-value {
  display: flex;
  align-items: baseline;
  gap: 4px;
}

.tooltip-value .value {
  font-size: 20px;
  font-weight: 700;
  color: #00ff88;
  font-family: 'Roboto Mono', monospace;
}

.tooltip-value .unit {
  font-size: 12px;
  color: #67c23a;
}
</style>