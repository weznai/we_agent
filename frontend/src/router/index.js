import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login.vue'),
    meta: { requiresAuth: false },
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('../views/Register.vue'),
    meta: { requiresAuth: false },
  },
  {
    path: '/',
    component: () => import('../components/Layout.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        name: 'Home',
        component: () => import('../views/Home.vue'),
        meta: { title: '首页' },
      },
      {
        path: 'chat',
        name: 'Chat',
        component: () => import('../views/Chat.vue'),
        meta: { title: '智能聊天' },
      },
      {
        path: 'translation',
        name: 'Translation',
        component: () => import('../views/Translation.vue'),
        meta: { title: '智能翻译' },
      },
      {
        path: 'customer-service',
        name: 'CustomerService',
        component: () => import('../views/CustomerService.vue'),
        meta: { title: '智能客服' },
      },
      {
        path: 'knowledge',
        name: 'Knowledge',
        component: () => import('../views/Knowledge.vue'),
        meta: { title: '知识库管理' },
      },
      {
        path: 'providers',
        name: 'Providers',
        component: () => import('../views/Providers.vue'),
        meta: { requiresAdmin: true, title: '大模型供应商' },
      },
      {
        path: 'models',
        name: 'Models',
        component: () => import('../views/Models.vue'),
        meta: { requiresAdmin: true, title: '模型管理' },
      },
      {
        path: 'model-mappings',
        name: 'ModelMappings',
        component: () => import('../views/ModelMappings.vue'),
        meta: { requiresAdmin: true, title: '模型映射' },
      },
      {
        path: 'users',
        name: 'Users',
        component: () => import('../views/Users.vue'),
        meta: { requiresSuper: true, title: '用户管理' },
      },
      {
        path: 'profile',
        name: 'Profile',
        component: () => import('../views/Profile.vue'),
        meta: { title: '个人中心' },
      },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  const user = JSON.parse(localStorage.getItem('user') || 'null')

  if (to.meta.requiresAuth !== false && !token) {
    next('/login')
    return
  }

  if ((to.path === '/login' || to.path === '/register') && token) {
    next('/')
    return
  }

  if (to.meta.requiresSuper && user?.role !== 'super') {
    next('/')
    return
  }

  if (to.meta.requiresAdmin && user?.role !== 'super' && user?.role !== 'admin') {
    next('/')
    return
  }

  document.title = to.meta.title ? `${to.meta.title} - Super Agent` : 'Super Agent'

  next()
})

export default router
