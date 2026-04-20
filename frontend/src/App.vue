<template>
  <el-container class="app-container">
    <el-header height="60px" class="app-header">
      <div class="header-content">
        <div class="logo">
          <div class="mode-switch" :class="{ active: isRoamingMode }" @click="toggleRoamingMode">
            <div class="switch-track" :class="{ active: isRoamingMode }">
              <div class="switch-thumb">
                <el-icon v-if="isRoamingMode"><Monitor /></el-icon>
                <el-icon v-else><FullScreen /></el-icon>
              </div>
            </div>
            <span class="switch-label">{{ isRoamingMode ? '退出漫游' : '数字漫游' }}</span>
          </div>
          <el-avatar :size="40" :src="logoUrl" />
          <h1 class="app-title">工业语音控制系统</h1>
        </div>
        <el-menu
          :default-active="activeIndex"
          class="el-menu-demo"
          mode="horizontal"
          @select="handleMenuSelect"
          background-color="#3a8ee6"
          text-color="#fff"
          active-text-color="#ffd04b"
        >
          <el-menu-item index="/">
            <el-icon><ChatDotSquare /></el-icon>
            <span>语音控制</span>
          </el-menu-item>
          <el-menu-item index="/plc">
            <el-icon><Monitor /></el-icon>
            <span>PLC监控</span>
          </el-menu-item>
          <el-menu-item index="/model">
            <el-icon><Box /></el-icon>
            <span>3D模型</span>
          </el-menu-item>
          <el-menu-item index="/data">
            <el-icon><DataLine /></el-icon>
            <span>数据可视化</span>
          </el-menu-item>
          <el-menu-item index="/database">
            <el-icon><Coin /></el-icon>
            <span>数据库管理</span>
          </el-menu-item>
          <el-menu-item index="/knowledge">
            <el-icon><Reading /></el-icon>
            <span>知识库</span>
          </el-menu-item>
            <el-menu-item index="/config">
            <el-icon><Setting /></el-icon>
            <span>配置管理</span>
          </el-menu-item>
          <el-menu-item index="/about">
            <el-icon><InfoFilled /></el-icon>
            <span>关于</span>
          </el-menu-item>
        </el-menu>
      </div>
    </el-header>

    <el-main class="app-main" :class="{ 'roaming-active': isRoamingMode }">
      <RouterView />
    </el-main>

    <el-footer height="40px" class="app-footer" v-if="!isRoamingMode">
      <p>© 2026 Voice PLC Controller. 保留所有权利。</p>
    </el-footer>

    <Transition name="roaming-fade">
      <div v-if="isRoamingMode" class="roaming-overlay">
        <DigitalRoamingView @exit="toggleRoamingMode" />
      </div>
    </Transition>
  </el-container>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, provide } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ChatDotSquare, Monitor, Box, DataLine, Setting, InfoFilled, Reading, Coin, FullScreen } from '@element-plus/icons-vue'
import DigitalRoamingView from './views/DigitalRoamingView.vue'

const route = useRoute()
const router = useRouter()
const isRoamingMode = ref(false)

provide('isRoamingMode', isRoamingMode)

const activeIndex = computed(() => {
  return route.path
})

import logoUrl from '@/assets/logo.jpg'

const handleMenuSelect = (key: string) => {
  router.push(key)
}

const toggleRoamingMode = () => {
  isRoamingMode.value = !isRoamingMode.value
}

onMounted(() => {
})
</script>

<style scoped>
.app-container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.app-header {
  background-color: #3a8ee6;
  color: white;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  position: sticky;
  top: 0;
  z-index: 100;
}

.header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 100%;
  max-width: 100%;
  padding: 0 20px;
  flex-wrap: nowrap;
}

.logo {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
}

.mode-switch {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 10px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 20px;
  cursor: pointer;
  transition: all 0.3s ease;
  border: 1px solid rgba(255, 255, 255, 0.2);
  flex-shrink: 0;
}

.mode-switch:hover {
  background: rgba(255, 255, 255, 0.2);
  transform: scale(1.05);
}

.switch-track {
  width: 44px;
  height: 24px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  position: relative;
  transition: all 0.4s cubic-bezier(0.68, -0.55, 0.265, 1.55);
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.4);
}

.switch-track.active {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  box-shadow: 0 2px 12px rgba(245, 87, 108, 0.5);
}

.switch-thumb {
  width: 20px;
  height: 20px;
  background: white;
  border-radius: 50%;
  position: absolute;
  top: 2px;
  left: 2px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.4s cubic-bezier(0.68, -0.55, 0.265, 1.55);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

.switch-track.active .switch-thumb {
  left: 22px;
}

.switch-thumb .el-icon {
  font-size: 12px;
  color: #667eea;
  transition: color 0.3s;
}

.switch-track.active .switch-thumb .el-icon {
  color: #f5576c;
}

.switch-label {
  font-size: 13px;
  font-weight: 500;
  color: white;
  white-space: nowrap;
}

.app-title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.app-main {
  flex: 1;
  padding: 20px;
  max-width: 1200px;
  width: 100%;
  margin: 0 auto;
  transition: all 0.5s cubic-bezier(0.4, 0, 0.2, 1);
}

.app-main.roaming-active {
  opacity: 0;
  transform: scale(0.95);
  pointer-events: none;
  max-width: none;
  padding: 0;
}

.roaming-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  z-index: 9999;
  background: linear-gradient(135deg, #0c0c1e 0%, #1a1a3e 50%, #0d0d2b 100%);
}

.roaming-fade-enter-active {
  animation: roaming-in 0.6s cubic-bezier(0.4, 0, 0.2, 1) forwards;
}

.roaming-fade-leave-active {
  animation: roaming-out 0.4s cubic-bezier(0.4, 0, 0.2, 1) forwards;
}

@keyframes roaming-in {
  0% {
    opacity: 0;
    transform: scale(1.1) translateY(20px);
    filter: blur(10px);
  }
  50% {
    opacity: 0.5;
    filter: blur(5px);
  }
  100% {
    opacity: 1;
    transform: scale(1) translateY(0);
    filter: blur(0);
  }
}

@keyframes roaming-out {
  0% {
    opacity: 1;
    transform: scale(1) translateY(0);
    filter: blur(0);
  }
  100% {
    opacity: 0;
    transform: scale(0.9) translateY(-20px);
    filter: blur(10px);
  }
}

.app-footer {
  background-color: #f5f7fa;
  border-top: 1px solid #e4e7ed;
  text-align: center;
  padding: 10px 0;
  color: #606266;
  font-size: 14px;
}

@media (max-width: 768px) {
  .header-content {
    flex-direction: column;
    height: auto;
    padding: 10px;
  }

  .logo {
    margin-bottom: 10px;
  }

  .app-title {
    font-size: 16px;
  }

  .el-menu {
    width: 100%;
  }

  .app-main {
    padding: 10px;
  }

  .mode-switch {
    margin-left: 0;
    margin-top: 8px;
  }

  .switch-label {
    display: none;
  }
}
</style>