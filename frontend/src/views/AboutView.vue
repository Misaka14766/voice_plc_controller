<template>
  <div class="about-view">
    <el-card class="card-container">
      <template #header>
        <div class="card-header">
          <h2>关于项目</h2>
        </div>
      </template>

      <div class="about-content">
        <div class="project-info">
          <el-avatar size="120" :src="logoUrl" class="project-logo" />
          <h3>Voice PLC Controller</h3>
          <p class="project-version">版本 1.0.0</p>
        </div>

        <div class="project-description">
          <el-divider content-position="left">项目介绍</el-divider>
          <p>
            Voice PLC Controller 是一个基于语音识别和大语言模型的 PLC 控制器，
            支持通过语音指令控制工业设备。该项目旨在简化工业自动化控制流程，
            提高操作效率和便捷性。
          </p>
        </div>

        <div class="features">
          <el-divider content-position="left">核心功能</el-divider>
          <el-row :gutter="20">
            <el-col :span="8">
              <el-card shadow="hover" class="feature-card">
                <template #header>
                  <div class="feature-header">
                    <el-icon class="feature-icon"><Mic /></el-icon>
                    <span>语音交互</span>
                  </div>
                </template>
                <p>通过语音指令控制 PLC 设备，支持自然语言交互</p>
              </el-card>
            </el-col>
            <el-col :span="8">
              <el-card shadow="hover" class="feature-card">
                <template #header>
                  <div class="feature-header">
                    <el-icon class="feature-icon"><Monitor /></el-icon>
                    <span>实时监控</span>
                  </div>
                </template>
                <p>实时监控 PLC 变量状态，支持变量读写操作</p>
              </el-card>
            </el-col>
            <el-col :span="8">
              <el-card shadow="hover" class="feature-card">
                <template #header>
                  <div class="feature-header">
                    <el-icon class="feature-icon"><Cpu /></el-icon>
                    <span>模块化设计</span>
                  </div>
                </template>
                <p>支持多种 ASR、TTS 和 LLM 提供商，易于扩展</p>
              </el-card>
            </el-col>
          </el-row>
        </div>

        <div class="tech-stack">
          <el-divider content-position="left">技术栈</el-divider>
          <el-table :data="techStack" style="width: 100%">
            <el-table-column prop="name" label="技术" width="120" />
            <el-table-column prop="description" label="描述" />
          </el-table>
        </div>

        <div class="license">
          <el-divider content-position="left">许可证</el-divider>
          <el-card shadow="hover">
            <p>本项目采用 MIT 许可证，详见 LICENSE 文件。</p>
          </el-card>
        </div>

        <div class="contact">
          <el-divider content-position="left">联系方式</el-divider>
          <p>如有问题或建议，请通过 GitHub Issues 提交。</p>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { Mic, Monitor, Cpu } from '@element-plus/icons-vue'

const logoUrl = '/src/assets/logo.svg'

const techStack = [
  { name: '后端', description: 'Python 3.8+, FastAPI' },
  { name: '前端', description: 'Vue 3, TypeScript, Element Plus' },
  { name: '语音识别', description: '阿里云 ASR, FunASR' },
  { name: '语音合成', description: 'Edge TTS' },
  { name: '大语言模型', description: 'OpenAI 兼容 API (DeepSeek, ARK)' },
  { name: 'PLC 通信', description: 'pyads (Beckhoff PLC)' },
  { name: '工具库', description: 'pyaudio, pynput, pygame' }
]
</script>

<style scoped>
.about-view {
  padding: 20px;
}

.card-container {
  max-width: 1000px;
  margin: 0 auto;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header h2 {
  margin: 0;
  font-size: 20px;
}

.about-content {
  margin-top: 30px;
}

.project-info {
  text-align: center;
  margin-bottom: 40px;
}

.project-logo {
  margin-bottom: 20px;
}

.project-info h3 {
  margin: 0 0 10px 0;
  font-size: 24px;
}

.project-version {
  color: #606266;
  margin: 0;
}

.project-description {
  margin-bottom: 40px;
}

.features {
  margin-bottom: 40px;
}

.feature-card {
  height: 100%;
}

.feature-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.feature-icon {
  font-size: 20px;
  color: #409eff;
}

.tech-stack {
  margin-bottom: 40px;
}

.license {
  margin-bottom: 40px;
}

.contact {
  margin-bottom: 20px;
}

@media (min-width: 1024px) {
  .about-view {
    min-height: 100vh;
    display: flex;
    align-items: center;
  }
}
</style>

