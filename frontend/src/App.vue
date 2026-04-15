<template>
  <el-container class="app-container">
    <el-header height="60px" class="app-header">
      <div class="header-content">
        <div class="logo">
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

    <el-main class="app-main">
      <RouterView />
    </el-main>

    <el-footer height="40px" class="app-footer">
      <p>© 2026 Voice PLC Controller. 保留所有权利。</p>
    </el-footer>
  </el-container>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ChatDotSquare, Monitor, Setting, InfoFilled } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()

const activeIndex = computed(() => {
  return route.path
})

import logoUrl from '@/assets/logo.jpg'

const handleMenuSelect = (key: string) => {
  router.push(key)
}

onMounted(() => {
  // 初始化时的逻辑
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
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px;
}

.logo {
  display: flex;
  align-items: center;
  gap: 12px;
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
}

.app-footer {
  background-color: #f5f7fa;
  border-top: 1px solid #e4e7ed;
  text-align: center;
  padding: 10px 0;
  color: #606266;
  font-size: 14px;
}

/* 响应式设计 */
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
}
</style>
