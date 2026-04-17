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
          <div ref="containerRef" class="model-container"></div>
          <div v-if="loading" class="loading-overlay">
            <el-icon class="is-loading"><Loading /></el-icon>
            <span>加载模型中...</span>
          </div>
          <div v-if="!hasModel" class="empty-overlay">
            <el-icon :size="64"><Box /></el-icon>
            <p>请将 GLB 模型文件放入 <code>public/models/</code> 目录</p>
            <p class="tip">文件名应命名为 <code>tank.glb</code></p>
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
import { ref, onMounted, onUnmounted, watch } from 'vue'
import * as THREE from 'three'
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js'
import { OrbitControls } from 'three/addons/controls/OrbitControls.js'
import { ElMessage } from 'element-plus'
import { Refresh, FullScreen, Loading, Box } from '@element-plus/icons-vue'
import { getConfig, listPLCVariables, getRealtimeData } from '../api'

const containerRef = ref<HTMLElement | null>(null)
const loading = ref(false)
const hasModel = ref(true)
const autoRotate = ref(true)
const showWireframe = ref(false)
const realtimeData = ref<any[]>([])
const modelVariables = ref<any[]>([])

let scene: THREE.Scene
let camera: THREE.PerspectiveCamera
let renderer: THREE.WebGLRenderer
let controls: OrbitControls
let model: THREE.Object3D
let animationId: number
let refreshInterval: number

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
          child.castShadow = true
          child.receiveShadow = true
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

const fetchData = async () => {
  try {
    const configRes = await getConfig()
    if (!configRes.data.db_enabled) return

    const varsRes = await listPLCVariables()
    if (!varsRes.data.success) return

    modelVariables.value = varsRes.data.variables

    if (varsRes.data.variables.length > 0) {
      const varNames = varsRes.data.variables.map((v: any) => v.name)
      const dataRes = await getRealtimeData(varNames)
      if (dataRes.data.success) {
        realtimeData.value = dataRes.data.data.map((item: any, idx: number) => ({
          ...item,
          comment: varsRes.data.variables[idx]?.comment || '',
          unit: varsRes.data.variables[idx]?.unit || '',
          min: varsRes.data.variables[idx]?.min,
          max: varsRes.data.variables[idx]?.max
        }))
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
</style>