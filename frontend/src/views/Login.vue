<template>
  <div class="login-page">
    <div class="login-container">
      <div class="login-left">
        <div class="brand-section">
          <div class="brand-icon">
            <svg viewBox="0 0 48 48" fill="none">
              <rect width="48" height="48" rx="12" fill="white" fill-opacity="0.2"/>
              <path d="M16 28c0-6 4-10 8-10s8 4 8 10" stroke="white" stroke-width="2.5" stroke-linecap="round"/>
              <circle cx="20" cy="22" r="2" fill="white"/>
              <circle cx="28" cy="22" r="2" fill="white"/>
              <path d="M14 32 L34 32" stroke="white" stroke-width="1.5" stroke-linecap="round" opacity="0.5"/>
              <circle cx="24" cy="24" r="18" stroke="white" stroke-width="1" opacity="0.3"/>
            </svg>
          </div>
          <h1>Super Agent</h1>
          <p>超级智能体平台</p>
        </div>

        <div class="features">
          <div class="feature-item">
            <div class="feature-icon">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/></svg>
            </div>
            <span>AI 智能对话</span>
          </div>
          <div class="feature-item">
            <div class="feature-icon">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6"/><path d="M16 13H8"/><path d="M16 17H8"/><path d="M10 9H8"/></svg>
            </div>
            <span>多语言翻译</span>
          </div>
          <div class="feature-item">
            <div class="feature-icon">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></svg>
            </div>
            <span>知识库管理</span>
          </div>
          <div class="feature-item">
            <div class="feature-icon">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><rect x="4" y="4" width="16" height="16" rx="2"/><rect x="9" y="9" width="6" height="6"/><path d="M15 2v2"/><path d="M15 20v2"/><path d="M2 15h2"/><path d="M2 9h2"/><path d="M20 15h2"/><path d="M20 9h2"/><path d="M9 2v2"/><path d="M9 20v2"/></svg>
            </div>
            <span>多模型支持</span>
          </div>
        </div>

        <div class="decoration-circles">
          <div class="circle c1"></div>
          <div class="circle c2"></div>
          <div class="circle c3"></div>
        </div>
      </div>

      <div class="login-right">
        <div class="login-card">
          <div class="login-header">
            <h2>欢迎回来</h2>
            <p class="subtitle">登录您的账户以继续</p>
          </div>

          <el-form ref="formRef" :model="form" :rules="rules" size="large" @submit.prevent="handleLogin">
            <el-form-item prop="login">
              <el-input
                v-model="form.login"
                placeholder="用户名或邮箱"
                :prefix-icon="User"
              />
            </el-form-item>

            <el-form-item prop="password">
              <el-input
                v-model="form.password"
                type="password"
                placeholder="密码"
                show-password
                :prefix-icon="Lock"
                @keyup.enter="handleLogin"
              />
            </el-form-item>

            <el-form-item>
              <el-button
                type="primary"
                class="login-btn"
                :loading="loading"
                @click="handleLogin"
              >
                {{ loading ? '登录中...' : '登 录' }}
              </el-button>
            </el-form-item>
          </el-form>

          <div class="login-footer">
            <span>还没有账户？</span>
            <router-link to="/register" class="link">立即注册</router-link>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../store/user'
import { User, Lock } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const router = useRouter()
const userStore = useUserStore()
const formRef = ref(null)
const loading = ref(false)

const form = reactive({
  login: 'admin',
  password: 'admin123',
})

const rules = {
  login: [{ required: true, message: '请输入用户名或邮箱', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

async function handleLogin() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    await userStore.login(form)
    ElMessage.success('登录成功')
    router.push('/')
  } catch (e) {
    loading.value = false
  }
}
</script>

<style scoped lang="scss">
.login-page {
  width: 100%;
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #eef2ff 0%, #f0f9ff 50%, #f8fafc 100%);
  position: relative;
  overflow: hidden;

  &::before {
    content: '';
    position: absolute;
    width: 600px;
    height: 600px;
    background: radial-gradient(circle, rgba(37, 99, 235, 0.06) 0%, transparent 70%);
    top: -200px;
    right: -100px;
  }

  &::after {
    content: '';
    position: absolute;
    width: 500px;
    height: 500px;
    background: radial-gradient(circle, rgba(14, 165, 233, 0.05) 0%, transparent 70%);
    bottom: -150px;
    left: -100px;
  }
}

.login-container {
  display: flex;
  width: 920px;
  min-height: 540px;
  border-radius: 20px;
  overflow: hidden;
  box-shadow:
    0 0 0 1px rgba(0, 0, 0, 0.04),
    0 4px 8px rgba(0, 0, 0, 0.02),
    0 12px 40px rgba(0, 0, 0, 0.06);
  position: relative;
  z-index: 1;
}

.login-left {
  width: 400px;
  background: linear-gradient(160deg, #1e40af 0%, #2563eb 40%, #0ea5e9 100%);
  padding: 48px 40px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  position: relative;
  overflow: hidden;

  &::after {
    content: '';
    position: absolute;
    inset: 0;
    background:
      radial-gradient(ellipse at 20% 80%, rgba(255,255,255,0.08) 0%, transparent 50%),
      radial-gradient(ellipse at 80% 20%, rgba(255,255,255,0.06) 0%, transparent 50%);
    pointer-events: none;
  }

  .brand-section {
    position: relative;
    z-index: 2;
    margin-bottom: 48px;
  }

  .brand-icon {
    width: 56px;
    height: 56px;
    margin-bottom: 24px;

    svg {
      width: 100%;
      height: 100%;
    }
  }

  h1 {
    font-size: 30px;
    font-weight: 700;
    color: white;
    margin-bottom: 8px;
    letter-spacing: -0.5px;
  }

  p {
    font-size: 15px;
    color: rgba(255, 255, 255, 0.75);
    font-weight: 400;
  }

  .features {
    position: relative;
    z-index: 2;
    display: flex;
    flex-direction: column;
    gap: 10px;
  }

  .feature-item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px 16px;
    background: rgba(255, 255, 255, 0.12);
    border-radius: 12px;
    backdrop-filter: blur(10px);
    color: white;
    font-size: 14px;
    font-weight: 500;
    transition: all 0.2s ease;

    &:hover {
      background: rgba(255, 255, 255, 0.2);
      transform: translateX(4px);
    }

    .feature-icon {
      width: 36px;
      height: 36px;
      display: flex;
      align-items: center;
      justify-content: center;
      background: rgba(255, 255, 255, 0.15);
      border-radius: 8px;
      flex-shrink: 0;
    }
  }

  .decoration-circles {
    position: absolute;
    inset: 0;
    z-index: 1;
    pointer-events: none;

    .circle {
      position: absolute;
      border-radius: 50%;
      border: 1px solid rgba(255, 255, 255, 0.1);
    }

    .c1 {
      width: 300px;
      height: 300px;
      top: -80px;
      right: -60px;
    }

    .c2 {
      width: 200px;
      height: 200px;
      bottom: -40px;
      left: -40px;
    }

    .c3 {
      width: 120px;
      height: 120px;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
    }
  }
}

.login-right {
  flex: 1;
  background: #f8fafc;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 48px 56px;
}

.login-card {
  width: 100%;
  max-width: 360px;

  .login-header {
    margin-bottom: 36px;
  }

  h2 {
    font-size: 26px;
    font-weight: 700;
    color: #0f172a;
    margin-bottom: 8px;
    letter-spacing: -0.3px;
  }

  .subtitle {
    color: #64748b;
    font-size: 15px;
    margin-bottom: 0;
  }
}

.login-btn {
  width: 100%;
  height: 46px;
  font-size: 15px;
  font-weight: 600;
  border-radius: 10px !important;
  background: linear-gradient(135deg, #2563eb 0%, #0ea5e9 100%) !important;
  border: none !important;
  letter-spacing: 2px;
  transition: all 0.25s ease !important;

  &:hover {
    box-shadow: 0 4px 16px rgba(37, 99, 235, 0.3) !important;
    transform: translateY(-1px);
  }

  &:active {
    transform: translateY(0);
  }
}

.login-footer {
  text-align: center;
  margin-top: 28px;
  color: #94a3b8;
  font-size: 14px;

  .link {
    color: #2563eb;
    text-decoration: none;
    font-weight: 500;
    margin-left: 4px;
    transition: color 0.2s;

    &:hover {
      color: #1d4ed8;
    }
  }
}
</style>
