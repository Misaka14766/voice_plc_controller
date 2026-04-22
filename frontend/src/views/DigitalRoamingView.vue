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
          :key="item.title"
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
      <div class="footer-right">
        <span class="scan-line"></span>
      </div>
    </div>

    <div class="play-controls" @click="toggleAutoPlay">
      <el-button :icon="isPlaying ? VideoPause : VideoPlay" circle />
      <span class="play-label">{{ isPlaying ? '自动播放中' : '已暂停' }}</span>
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
import { ref, computed, onMounted, onUnmounted, h, nextTick } from 'vue'
import { VideoPlay, VideoPause, Monitor } from '@element-plus/icons-vue'
import * as THREE from 'three'
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js'
import { RGBELoader } from 'three/addons/loaders/RGBELoader.js'
import * as echarts from 'echarts'
import { getStatus, getChartData, getMonitorVariables, getSystemMetrics } from '@/api'

const emit = defineEmits(['exit'])
const currentIndex = ref(0)
const carouselDirection = ref('right')
const isPlaying = ref(true)
const currentTime = ref('')
const currentDate = ref('')

// 3D模型面板组件
const ModelPanel = {
  setup() {
    const containerRef = ref<HTMLElement | null>(null)
    let scene: THREE.Scene
    let camera: THREE.PerspectiveCamera
    let renderer: THREE.WebGLRenderer
    let model: THREE.Object3D
    let animationId: number
    
    // 鼠标交互相关变量
    let isDragging = false
    let previousMousePosition = { x: 0, y: 0 }

    onMounted(() => {
      if (containerRef.value) {
        // 强制设置容器尺寸
        containerRef.value.style.width = '100%'
        containerRef.value.style.height = '100%'
        containerRef.value.style.minHeight = '400px'
        containerRef.value.style.minWidth = '600px'
        containerRef.value.style.position = 'relative'
        
        // 强制浏览器重新计算布局
        containerRef.value.offsetHeight
        
        // 初始化 Three.js
        initThree()
        
        // 添加鼠标事件监听器
        addMouseEventListeners()
      }
      
      window.addEventListener('resize', handleResize)
    })

    onUnmounted(() => {
      if (animationId) cancelAnimationFrame(animationId)
      if (renderer) renderer.dispose()
      window.removeEventListener('resize', handleResize)
      
      // 移除鼠标事件监听器
      if (containerRef.value) {
        containerRef.value.removeEventListener('mousedown', onMouseDown)
        containerRef.value.removeEventListener('mousemove', onMouseMove)
        containerRef.value.removeEventListener('mouseup', onMouseUp)
        containerRef.value.removeEventListener('wheel', onWheel)
      }
    })

    const initThree = () => {
      if (!containerRef.value) return

      const width = containerRef.value.clientWidth
      const height = containerRef.value.clientHeight

      if (width === 0 || height === 0) return

      // 创建场景
      scene = new THREE.Scene()
      scene.background = new THREE.Color(0x0a0a1a)

      // 创建相机
      camera = new THREE.PerspectiveCamera(60, width / height, 0.1, 1000)
      camera.position.set(0, 2, 5)

      // 创建渲染器
      renderer = new THREE.WebGLRenderer({ antialias: true })
      renderer.setSize(width, height)
      renderer.setPixelRatio(window.devicePixelRatio)
      renderer.toneMapping = THREE.ACESFilmicToneMapping
      renderer.toneMappingExposure = 1.0
      renderer.outputEncoding = THREE.sRGBEncoding
      containerRef.value.appendChild(renderer.domElement)

      // 加载HDRI环境贴图
      const rgbeLoader = new RGBELoader()
      rgbeLoader.load(
        '/hdri/qwantani_moon_noon_puresky_1k.hdr',
        (texture) => {
          texture.mapping = THREE.EquirectangularReflectionMapping
          scene.environment = texture
          scene.background = texture
        }
      )

      // 添加光源（增强光照）
      const ambientLight = new THREE.AmbientLight(0xffffff, 0.8) // 增强环境光
      scene.add(ambientLight)

      // 添加半球光（模拟天空光）
      const hemisphereLight = new THREE.HemisphereLight(0xffffff, 0x444444, 1.2)
      hemisphereLight.position.set(0, 20, 0)
      scene.add(hemisphereLight)

      // 添加方向光（主光源）
      const directionalLight = new THREE.DirectionalLight(0xffffff, 1.5)
      directionalLight.position.set(5, 10, 7.5)
      scene.add(directionalLight)

      // 添加点光源（辅助光源）
      const pointLight = new THREE.PointLight(0xffffff, 1.0)
      pointLight.position.set(0, 5, 0)
      scene.add(pointLight)

      // 添加网格辅助线
      const gridHelper = new THREE.GridHelper(20, 40, 0x00ffff, 0x004444)
      scene.add(gridHelper)

      // 添加 torus
      const torusGeo = new THREE.TorusGeometry(2, 0.05, 16, 100)
      const torusMat = new THREE.MeshBasicMaterial({ color: 0x00ffff })
      const torus = new THREE.Mesh(torusGeo, torusMat)
      torus.rotation.x = Math.PI / 2
      torus.position.y = -1
      scene.add(torus)

      // 加载模型
      const loader = new GLTFLoader()
      loader.load(
        '/models/tank_textured.glb',
        (gltf) => {
          model = gltf.scene
          model.scale.set(2.0, 2.0, 2.0) // 增加模型缩放系数
          model.position.set(0, 2.0, 0) // 增加位置偏移，整体往上挪
          scene.add(model)
        },
        undefined,
        (error) => {
          console.error('模型加载失败:', error)
        }
      )

      // 开始动画
      animate()
    }

    const handleResize = () => {
      if (!containerRef.value || !renderer || !camera) return

      const width = containerRef.value.clientWidth
      const height = containerRef.value.clientHeight

      if (width === 0 || height === 0) return

      camera.aspect = width / height
      camera.updateProjectionMatrix()
      renderer.setSize(width, height)
    }

    // 鼠标事件处理函数
    const onMouseDown = (event: MouseEvent) => {
      isDragging = true
      previousMousePosition = {
        x: event.clientX,
        y: event.clientY
      }
    }

    const onMouseMove = (event: MouseEvent) => {
      if (!isDragging || !model) return

      const deltaMove = {
        x: event.clientX - previousMousePosition.x,
        y: event.clientY - previousMousePosition.y
      }

      // 旋转模型
      model.rotation.y += deltaMove.x * 0.01
      model.rotation.x += deltaMove.y * 0.01

      // 限制x轴旋转范围，防止过度旋转
      model.rotation.x = Math.max(-Math.PI / 2, Math.min(Math.PI / 2, model.rotation.x))

      previousMousePosition = {
        x: event.clientX,
        y: event.clientY
      }
    }

    const onMouseUp = () => {
      isDragging = false
    }

    const onWheel = (event: WheelEvent) => {
      event.preventDefault()
      if (!camera) return

      // 缩放相机距离
      const zoomSpeed = 0.1
      camera.position.z += event.deltaY * zoomSpeed * 0.01
      
      // 限制相机距离范围
      camera.position.z = Math.max(1, Math.min(10, camera.position.z))
    }

    const addMouseEventListeners = () => {
      if (!containerRef.value) return

      containerRef.value.addEventListener('mousedown', onMouseDown)
      containerRef.value.addEventListener('mousemove', onMouseMove)
      containerRef.value.addEventListener('mouseup', onMouseUp)
      containerRef.value.addEventListener('wheel', onWheel, { passive: false })
    }

    const animate = () => {
      animationId = requestAnimationFrame(animate)
      if (model && !isDragging) {
        model.rotation.y += 0.005
      }
      renderer.render(scene, camera)
    }

    return () => h('div', { class: 'panel-content model-panel' }, [
      h('div', { 
        ref: containerRef, 
        class: 'model-container'
      })
    ])
  }
}

const DataPanel = {
  setup() {
    const loading = ref(false)
    const chartRef = ref<HTMLElement | null>(null)
    let chart: echarts.ECharts | null = null
    let chartInterval: number | null = null

    const variables = ref<string[]>([])
    const selectedVariable = ref('')
    const timeRange = ref('1h')
    const chartData = ref<any[]>([])
    
    const STORAGE_KEY = 'digital_roaming_selected_variable'
    const TIME_RANGE_KEY = 'digital_roaming_time_range'

    const loadConfig = () => {
      const saved = localStorage.getItem(STORAGE_KEY)
      if (saved) {
        selectedVariable.value = saved
      }
      const savedTimeRange = localStorage.getItem(TIME_RANGE_KEY)
      if (savedTimeRange) {
        timeRange.value = savedTimeRange
      }
    }

    const saveConfig = () => {
      localStorage.setItem(STORAGE_KEY, selectedVariable.value)
      localStorage.setItem(TIME_RANGE_KEY, timeRange.value)
    }

    const loadVariables = async () => {
      try {
        const response = await getMonitorVariables()
        if (response.data.success && response.data.variables) {
          variables.value = response.data.variables.map((v: [string, string]) => v[0])
        }
      } catch (error) {
        console.error('获取变量列表失败:', error)
      }
    }

    const loadChartData = async () => {
      if (!selectedVariable.value) {
        chartData.value = []
        return
      }

      loading.value = true
      try {
        const response = await getChartData(selectedVariable.value, timeRange.value, 'mean')
        if (response.data.success) {
          chartData.value = response.data.data || []
        }
      } catch (error) {
        console.error('获取图表数据失败:', error)
      } finally {
        loading.value = false
        nextTick(() => {
          if (chart && !chart.isDisposed()) {
            updateChart()
          }
        })
      }
    }

    const initChart = () => {
      if (!chartRef.value) return
      
      const { clientWidth, clientHeight } = chartRef.value
      if (clientWidth > 0 && clientHeight > 0) {
        if (chart && !chart.isDisposed()) {
          chart.dispose()
        }
        chart = echarts.init(chartRef.value)
        updateChart()
      } else {
        if ((chartRef.value as any).__retryCount === undefined) {
          (chartRef.value as any).__retryCount = 0
        }
        (chartRef.value as any).__retryCount++
        if ((chartRef.value as any).__retryCount < 50) {
          setTimeout(initChart, 100)
        }
      }
    }

    const updateChart = () => {
      if (!chart) return
      
      const times = chartData.value.map(d => d.timestamp)
      const values = chartData.value.map(d => d.value)

      const option = {
        tooltip: {
          trigger: 'axis',
          formatter: (params: any) => {
            const data = params[0]
            return `${data.axisValue}<br/>${data.marker} ${selectedVariable.value || '数值'}: <b>${data.value.toFixed(2)}</b>`
          }
        },
        grid: {
          left: '3%',
          right: '4%',
          bottom: '3%',
          top: '15%',
          containLabel: true
        },
        xAxis: {
          type: 'category',
          boundaryGap: false,
          data: times,
          axisLabel: {
            formatter: (value: string) => {
              const date = new Date(value)
              return `${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`
            },
            color: '#00ffff',
            fontSize: 10
          },
          axisLine: {
            lineStyle: {
              color: '#00ffff'
            }
          }
        },
        yAxis: {
          type: 'value',
          scale: true,
          axisLabel: {
            color: '#00ffff'
          },
          axisLine: {
            lineStyle: {
              color: '#00ffff'
            }
          },
          splitLine: {
            lineStyle: {
              color: 'rgba(0, 255, 255, 0.1)'
            }
          }
        },
        series: [
          {
            name: selectedVariable.value || '数值',
            type: 'line',
            smooth: true,
            symbol: 'circle',
            symbolSize: 6,
            sampling: 'lttb',
            itemStyle: {
              color: '#00ffff'
            },
            areaStyle: {
              color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                { offset: 0, color: 'rgba(0, 255, 255, 0.3)' },
                { offset: 1, color: 'rgba(0, 255, 255, 0.05)' }
              ])
            },
            data: values
          }
        ]
      }

      chart.setOption(option)
    }

    const handleResize = () => {
      if (chart) {
        chart.resize()
      }
    }

    onMounted(async () => {
      loadConfig()
      await loadVariables()
      if (!selectedVariable.value && variables.value.length > 0) {
        selectedVariable.value = variables.value[0] || ''
        saveConfig()
      }
      await loadChartData()
      
      chartInterval = setInterval(loadChartData, 5000)
      
      nextTick(() => {
        initChart()
      })
      
      window.addEventListener('resize', handleResize)
    })

    onUnmounted(() => {
      if (chart) chart.dispose()
      if (chartInterval) clearInterval(chartInterval)
      window.removeEventListener('resize', handleResize)
    })

    return () => h('div', { class: 'panel-content data-panel' }, [
      h('div', { class: 'panel-header' }, [
        h('h3', { class: 'panel-title' }, 'PLC数据监控'),
        h('div', { class: 'panel-controls' }, [
          h('select', {
            class: 'control-select',
            value: selectedVariable.value,
            onChange: (e: Event) => {
              selectedVariable.value = (e.target as HTMLSelectElement).value
              saveConfig()
              loadChartData()
            }
          }, [
            h('option', { value: '' }, '请选择变量'),
            ...variables.value.map(varName =>
              h('option', { value: varName }, varName)
            )
          ]),
          h('select', {
            class: 'control-select',
            value: timeRange.value,
            onChange: (e: Event) => {
              timeRange.value = (e.target as HTMLSelectElement).value
              saveConfig()
              loadChartData()
            }
          }, [
            h('option', { value: '30m' }, '最近30分钟'),
            h('option', { value: '1h' }, '最近1小时'),
            h('option', { value: '6h' }, '最近6小时'),
            h('option', { value: '12h' }, '最近12小时'),
            h('option', { value: '24h' }, '最近24小时'),
            h('option', { value: '7d' }, '最近7天')
          ])
        ])
      ]),
      h('div', { class: 'chart-wrapper' }, [
        h('div', { class: 'chart-header' }, [
          h('span', { class: 'chart-title' }, [
            h('span', { class: 'title-icon' }, '📈'),
            selectedVariable.value ? `${selectedVariable.value} - 历史趋势` : '请选择变量查看趋势'
          ])
        ]),
        h('div', { 
          class: 'chart-container',
          ref: chartRef
        }),
        !selectedVariable.value ? h('div', { class: 'empty-chart' }, '请从上方选择要查看的变量') : null
      ])
    ])
  }
}



const StatusPanel = {
  setup() {
    const systemStatus = ref({
      cpu: 0,
      memory: 0,
      network: 0,
      uptime: '00:00:00'
    })
    const plcConnected = ref(false)
    const templateEnabled = ref(false)
    let refreshInterval: number | null = null

    const fetchStatus = async () => {
      try {
        const statusRes = await getStatus()
        plcConnected.value = statusRes.data.plc_connected
        templateEnabled.value = statusRes.data.template_matching

        // 从后端获取真实系统状态数据
        try {
          const metricsRes = await getSystemMetrics()
          systemStatus.value = metricsRes.data
        } catch (metricsError) {
          console.error('获取系统性能指标失败:', metricsError)
          // 失败时使用默认值
          systemStatus.value = {
            cpu: 0,
            memory: 0,
            network: 0,
            uptime: '00:00:00'
          }
        }
      } catch (error) {
        console.error('获取系统状态失败:', error)
      }
    }

    onMounted(() => {
      fetchStatus()
      refreshInterval = window.setInterval(fetchStatus, 3000)
    })

    onUnmounted(() => {
      if (refreshInterval) clearInterval(refreshInterval)
    })

    return () => h('div', { class: 'panel-content status-panel' }, [
      h('h3', { class: 'panel-title' }, '系统状态'),
      h('div', { class: 'status-overview' }, [
        h('div', { class: 'status-card cpu-card' }, [
          h('div', { class: 'status-header' }, [
            h('div', { class: 'status-icon cpu' }),
            h('span', { class: 'status-label' }, 'CPU使用率')
          ]),
          h('div', { class: 'status-value' }, `${systemStatus.value.cpu}%`),
          h('div', { class: 'status-progress' }, [
            h('div', { 
              class: 'progress-fill', 
              style: { 
                width: `${systemStatus.value.cpu}%`,
                background: `linear-gradient(90deg, #ff6600, #ffaa00)`
              } 
            })
          ]),
          h('div', { class: 'status-glow' })
        ]),
        h('div', { class: 'status-card memory-card' }, [
          h('div', { class: 'status-header' }, [
            h('div', { class: 'status-icon memory' }),
            h('span', { class: 'status-label' }, '内存使用率')
          ]),
          h('div', { class: 'status-value' }, `${systemStatus.value.memory}%`),
          h('div', { class: 'status-progress' }, [
            h('div', { 
              class: 'progress-fill', 
              style: { 
                width: `${systemStatus.value.memory}%`,
                background: `linear-gradient(90deg, #9900ff, #cc66ff)`
              } 
            })
          ]),
          h('div', { class: 'status-glow' })
        ]),
        h('div', { class: 'status-card network-card' }, [
          h('div', { class: 'status-header' }, [
            h('div', { class: 'status-icon network' }),
            h('span', { class: 'status-label' }, '网络带宽')
          ]),
          h('div', { class: 'status-value' }, `${systemStatus.value.network} Mbps`),
          h('div', { class: 'status-glow' })
        ]),
        h('div', { class: 'status-card uptime-card' }, [
          h('div', { class: 'status-header' }, [
            h('div', { class: 'status-icon uptime' }),
            h('span', { class: 'status-label' }, '运行时间')
          ]),
          h('div', { class: 'status-value' }, systemStatus.value.uptime),
          h('div', { class: 'status-glow' })
        ])
      ])
    ])
  }
}

const LabPanel = {
  setup() {
    return () => h('div', { class: 'panel-content lab-panel' }, [
      h('h3', { class: 'panel-title' }, '实验室介绍'),
      h('div', { class: 'lab-content' }, [
        h('div', { class: 'lab-image-container' }, [
          h('div', { class: 'lab-image' }),
          h('div', { class: 'image-glow' })
        ]),
        h('div', { class: 'lab-info' }, [
          h('h4', { class: 'lab-name' }, 'PLC科创实验室'),
          h('p', { class: 'lab-title' }, '工业自动化控制研究中心'),
          h('div', { class: 'lab-description' }, [
            h('p', null, 'PLC科创实验室成立于2026年，是专注于工业自动化控制技术研究与应用的创新实验室。'),
            h('p', null, '实验室拥有先进的工业控制设备和测试平台，包括Beckhoff TwinCAT3系统、西门子S7系列PLC、ABB机器人等。'),
            h('p', null, '主要研究方向包括：PLC编程技术、工业物联网、智能控制系统、机器视觉、运动控制等。'),
            h('p', null, '实验室与多家企业建立了产学研合作关系，致力于将科研成果转化为实际应用，为工业自动化领域培养高素质技术人才。')
          ]),
          h('div', { class: 'lab-equipments' }, [
            h('span', { class: 'equipment-tag' }, 'Beckhoff TwinCAT3'),
            h('span', { class: 'equipment-tag' }, '西门子S7 PLC'),
            h('span', { class: 'equipment-tag' }, 'ABB机器人'),
            h('span', { class: 'equipment-tag' }, '机器视觉系统'),
            h('span', { class: 'equipment-tag' }, '工业物联网平台')
          ])
        ])
      ])
    ])
  }
}

const carouselItems = [
  { title: '3D模型', component: ModelPanel },
  { title: '数据监控', component: DataPanel },
  { title: '系统状态', component: StatusPanel },
  { title: '实验室介绍', component: LabPanel }
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
  height: calc(100vh - 120px);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-start;
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
  gap: 10px;
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
  bottom: 15px;
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

:deep(.panel-title) {
  font-size: 24px;
  color: #00ffff;
  margin: 0;
  letter-spacing: 4px;
  text-shadow: 0 0 15px rgba(0, 255, 255, 0.8);
  font-family: 'Orbitron', 'Rajdhani', 'Microsoft YaHei', sans-serif;
}

:deep(.panel-header) {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  flex-wrap: wrap;
  gap: 15px;
}

:deep(.panel-controls) {
  display: flex;
  gap: 15px;
  align-items: center;
  flex-wrap: wrap;
}

:deep(.panel-controls .control-select) {
  min-width: 160px;
  margin: 0;
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

.data-container {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

:deep(.config-bar) {
  display: flex;
  flex-wrap: wrap;
  gap: 20px;
  padding: 16px 20px;
  background: rgba(0, 20, 40, 0.6);
  border: 1px solid rgba(0, 255, 255, 0.2);
  border-radius: 8px;
}

:deep(.config-section) {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

:deep(.config-label) {
  font-size: 13px;
  color: rgba(0, 255, 255, 0.8);
  letter-spacing: 1px;
  white-space: nowrap;
}



:deep(.control-bar) {
  display: flex;
  flex-wrap: wrap;
  gap: 20px;
  margin-bottom: 20px;
  padding: 16px;
  background: rgba(0, 20, 40, 0.8);
  border: 1px solid rgba(0, 255, 255, 0.2);
  border-radius: 8px;
}

:deep(.control-item) {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

:deep(.control-item label) {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.8);
  font-weight: 500;
  letter-spacing: 1px;
}

:deep(.control-select) {
  padding: 8px 16px;
  font-size: 12px;
  color: #00ffff;
  background: rgba(0, 20, 40, 0.9);
  border: 1px solid rgba(0, 255, 255, 0.3);
  border-radius: 4px;
  cursor: pointer;
  outline: none;
  min-width: 160px;
  font-family: 'Orbitron', 'Rajdhani', 'Microsoft YaHei', sans-serif;
}

:deep(.control-select:hover) {
  border-color: rgba(0, 255, 255, 0.6);
  box-shadow: 0 0 10px rgba(0, 255, 255, 0.2);
}

:deep(.control-select option) {
  background: rgba(0, 20, 40, 0.95);
  color: #00ffff;
  font-family: 'Orbitron', 'Rajdhani', 'Microsoft YaHei', sans-serif;
}

:deep(.chart-wrapper) {
  background: rgba(0, 20, 40, 0.8);
  border: 1px solid rgba(0, 255, 255, 0.2);
  border-radius: 8px;
  overflow: hidden;
}

:deep(.chart-header) {
  padding: 16px 20px;
  border-bottom: 1px solid rgba(0, 255, 255, 0.2);
  background: rgba(0, 30, 60, 0.9);
}

:deep(.chart-title) {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 14px;
  font-weight: 600;
  color: #00ffff;
  letter-spacing: 1px;
  font-family: 'Orbitron', 'Rajdhani', 'Microsoft YaHei', sans-serif;
}

:deep(.title-icon) {
  font-size: 18px;
}

:deep(.chart-container) {
  height: 350px;
  width: 100%;
  position: relative;
}

:deep(.empty-chart) {
  height: 350px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: rgba(255, 255, 255, 0.6);
  font-size: 16px;
  letter-spacing: 2px;
  font-family: 'Orbitron', 'Rajdhani', 'Microsoft YaHei', sans-serif;
  background: rgba(0, 20, 40, 0.6);
}

:deep(.chart-container canvas) {
  background: rgba(0, 10, 20, 0.5) !important;
}

:deep(.data-grid) {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 16px;
}

.chart-container {
  width: 100%;
  height: 300px;
  background: rgba(0, 20, 40, 0.8);
  border: 1px solid rgba(0, 255, 255, 0.2);
  border-radius: 8px;
  padding: 20px;
}

:deep(.data-card) {
  background: rgba(0, 20, 40, 0.8);
  border: 1px solid rgba(0, 255, 255, 0.2);
  border-radius: 8px;
  padding: 16px;
  transition: all 0.3s ease;
}

:deep(.data-card:hover) {
  border-color: rgba(0, 255, 255, 0.5);
  box-shadow: 0 0 20px rgba(0, 255, 255, 0.2);
}

:deep(.no-data) {
  grid-column: 1 / -1;
  text-align: center;
  padding: 60px 20px;
  color: rgba(255, 255, 255, 0.6);
  font-size: 16px;
  letter-spacing: 2px;
}

:deep(.data-header) {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

:deep(.data-name) {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.8);
  letter-spacing: 1px;
  text-shadow: 0 0 8px rgba(255, 255, 255, 0.3);
}

:deep(.data-indicator) {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  box-shadow: 0 0 8px currentColor;
}

:deep(.data-value) {
  display: flex;
  align-items: baseline;
}

:deep(.data-value .value) {
  font-size: 28px;
  font-weight: 700;
  color: #00ffff;
  text-shadow: 0 0 10px rgba(0, 255, 255, 0.5);
}



.lab-panel {
  padding: 40px;
  display: flex;
  flex-direction: column;
  align-items: center;
  overflow-y: auto;
}

:deep(.lab-content) {
  display: flex;
  gap: 80px;
  align-items: center;
  width: 100%;
  max-width: 900px;
  animation: slideIn 1s ease-out;
  position: relative;
  z-index: 10;
  flex-wrap: nowrap;
  justify-content: flex-start;
}

:deep(.lab-image-container) {
  position: relative;
  width: 200px;
  height: 200px;
  animation: pulse 2s ease-in-out infinite alternate;
}

:deep(.lab-image) {
  width: 100%;
  height: 100%;
  background-image: url('/lab.jpg');
  background-size: cover;
  background-position: center;
  border-radius: 50%;
  box-shadow: 0 0 30px rgba(0, 255, 255, 0.5);
  position: relative;
  overflow: hidden;
  display: block;
  min-width: 200px;
  min-height: 200px;
}

:deep(.lab-image::before) {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.3);
  border-radius: 50%;
}

:deep(.image-glow) {
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

:deep(.lab-info) {
  flex: 1;
  animation: fadeIn 1.5s ease-out;
  min-width: 0;
}

:deep(.lab-name) {
  font-size: 24px;
  font-weight: 700;
  color: #00ffff;
  text-shadow: 0 0 15px rgba(0, 255, 255, 0.8);
  margin: 0 0 10px 0;
  letter-spacing: 2px;
}

:deep(.lab-title) {
  font-size: 16px;
  color: rgba(26, 162, 220, 0.9);
  text-shadow: 0 0 10px rgba(255, 255, 255, 0.5);
  margin: 0 0 20px 0;
  letter-spacing: 1px;
}

:deep(.lab-description) {
  margin: 0 0 20px 0;
  line-height: 1.6;
}

:deep(.lab-description p) {
  color: rgba(74, 218, 243, 0.95);
  text-shadow: 0 0 8px rgba(255, 255, 255, 0.3);
  margin: 0 0 10px 0;
  font-size: 14px;
  letter-spacing: 0.5px;
}

:deep(.lab-equipments) {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

:deep(.equipment-tag) {
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

:deep(.equipment-tag:hover) {
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
  :deep(.mentor-content) {
    flex-direction: column;
    text-align: center;
  }
  
  :deep(.mentor-image-container) {
    width: 150px;
    height: 150px;
  }
}



.status-panel {
  overflow-y: auto;
}

:deep(.status-overview) {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
  margin-top: 10px;
}

:deep(.status-card) {
  position: relative;
  background: rgba(0, 20, 40, 0.8);
  border: 1px solid rgba(0, 255, 255, 0.2);
  border-radius: 12px;
  padding: 24px;
  backdrop-filter: blur(10px);
  box-shadow: 0 4px 20px rgba(0, 255, 255, 0.1);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
}

:deep(.status-card:hover) {
  transform: translateY(-5px);
  box-shadow: 0 8px 30px rgba(0, 255, 255, 0.2);
  border-color: rgba(0, 255, 255, 0.4);
}

:deep(.status-header) {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

:deep(.status-icon) {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  position: relative;
  overflow: hidden;
}

:deep(.status-icon::before) {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
  transition: left 0.6s;
}

:deep(.status-card:hover .status-icon::before) {
  left: 100%;
}

:deep(.status-icon.cpu) {
  background: linear-gradient(135deg, rgba(255, 100, 0, 0.3), rgba(255, 100, 0, 0.1));
  color: #ff6600;
}

:deep(.status-icon.memory) {
  background: linear-gradient(135deg, rgba(100, 0, 255, 0.3), rgba(100, 0, 255, 0.1));
  color: #9900ff;
}

:deep(.status-icon.network) {
  background: linear-gradient(135deg, rgba(0, 255, 100, 0.3), rgba(0, 255, 100, 0.1));
  color: #00ff88;
}

:deep(.status-icon.uptime) {
  background: linear-gradient(135deg, rgba(255, 255, 0, 0.3), rgba(255, 255, 0, 0.1));
  color: #ffff00;
}

:deep(.status-label) {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.8);
  font-weight: 500;
  letter-spacing: 1px;
  text-shadow: 0 0 6px rgba(255, 255, 255, 0.3);
  font-family: 'Orbitron', 'Rajdhani', 'Microsoft YaHei', sans-serif;
}

:deep(.status-value) {
  font-size: 32px;
  font-weight: 700;
  color: #00ffff;
  text-shadow: 0 0 15px rgba(0, 255, 255, 0.7);
  margin-bottom: 16px;
  font-family: 'Orbitron', 'Rajdhani', 'Microsoft YaHei', sans-serif;
  letter-spacing: 2px;
}

:deep(.status-progress) {
  width: 100%;
  height: 6px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 3px;
  overflow: hidden;
  position: relative;
}

:deep(.progress-fill) {
  height: 100%;
  border-radius: 3px;
  transition: width 0.8s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
}

:deep(.progress-fill::after) {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.4), transparent);
  animation: progressFlow 2s infinite;
}

@keyframes progressFlow {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(100%); }
}

:deep(.status-glow) {
  position: absolute;
  top: -50%;
  right: -50%;
  width: 200%;
  height: 200%;
  background: radial-gradient(circle, rgba(0, 255, 255, 0.1) 0%, transparent 70%);
  animation: glowPulse 3s ease-in-out infinite;
}

@keyframes glowPulse {
  0%, 100% { opacity: 0.3; }
  50% { opacity: 0.6; }
}



@media (max-width: 768px) {
  :deep(.status-overview) {
    grid-template-columns: 1fr;
  }
  
  :deep(.status-value) {
    font-size: 24px;
  }
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

  :deep(.data-grid) {
    grid-template-columns: repeat(2, 1fr);
  }

  :deep(.status-grid) {
    grid-template-columns: 1fr;
  }

  .carousel-indicators {
    gap: 15px;
  }

  .indicator-label {
    font-size: 10px;
  }
}

.play-controls {
  position: fixed;
  bottom: 40px;
  right: 30px;
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
  z-index: 1000;
}

.play-controls:hover {
  background: rgba(0, 255, 255, 0.15);
  box-shadow: 0 6px 30px rgba(0, 255, 255, 0.3);
  transform: translateY(-2px);
}

.play-controls .el-button {
  background: linear-gradient(135deg, #00ffff, #00aaff) !important;
  border: 1px solid rgba(255, 255, 255, 0.3) !important;
  color: rgba(255, 255, 255, 0.9) !important;
  font-size: 16px;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(0, 255, 255, 0.4);
  animation: thumbGlow 2s ease-in-out infinite alternate;
}

.play-controls .el-button:hover {
  background: linear-gradient(135deg, #00aaff, #00ffff) !important;
  border: 1px solid rgba(255, 255, 255, 0.5) !important;
  color: #ffffff !important;
  box-shadow: 0 4px 16px rgba(0, 255, 255, 0.8);
}

.play-label {
  font-size: 14px;
  font-weight: 600;
  color: #00ffff;
  text-shadow: 0 0 8px rgba(0, 255, 255, 0.5);
  letter-spacing: 1px;
  transition: all 0.3s ease;
  margin: 0;
}

.play-controls:hover .play-label {
  color: #ffffff;
  text-shadow: 0 0 12px rgba(255, 255, 255, 0.8);
}

</style>
