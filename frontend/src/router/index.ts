import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView,
      meta: {
        title: '首页 - 语音PLC控制'
      }
    },
    {
      path: '/plc',
      name: 'plc',
      component: () => import('../views/PlcMonitorView.vue'),
      meta: {
        title: 'PLC监控 - 语音PLC控制'
      }
    },
    {
      path: '/model',
      name: 'model',
      component: () => import('../views/ModelView.vue'),
      meta: {
        title: '3D模型 - 语音PLC控制'
      }
    },
    {
      path: '/data',
      name: 'data',
      component: () => import('../views/DataView.vue'),
      meta: {
        title: '数据可视化 - 语音PLC控制'
      }
    },
    {
      path: '/config',
      name: 'config',
      component: () => import('../views/ConfigView.vue'),
      meta: {
        title: '配置管理 - 语音PLC控制'
      }
    },
    {
      path: '/about',
      name: 'about',
      component: () => import('../views/AboutView.vue'),
      meta: {
        title: '关于 - 语音PLC控制'
      }
    },
  ],
})

router.beforeEach((to, from, next) => {
  document.title = to.meta.title as string || '语音PLC控制'
  next()
})

export default router