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
          <p>创建您的智能体账户</p>
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
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></svg>
            </div>
            <span>多模型接入</span>
          </div>
          <div class="feature-item">
            <div class="feature-icon">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></svg>
            </div>
            <span>知识库管理</span>
          </div>
          <div class="feature-item">
            <div class="feature-icon">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
            </div>
            <span>安全可靠</span>
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
            <h2>创建账户</h2>
            <p class="subtitle">填写信息以注册新账户</p>
          </div>

          <el-form ref="formRef" :model="form" :rules="rules" size="large" @submit.prevent="handleRegister">
            <el-form-item prop="username">
              <el-input v-model="form.username" placeholder="用户名" :prefix-icon="User" />
            </el-form-item>

            <el-form-item prop="email">
              <el-input v-model="form.email" placeholder="邮箱地址" :prefix-icon="Message" />
            </el-form-item>

            <el-form-item prop="password">
              <el-input v-model="form.password" type="password" placeholder="密码" show-password :prefix-icon="Lock" />
            </el-form-item>

            <el-form-item prop="confirmPassword">
              <el-input v-model="form.confirmPassword" type="password" placeholder="确认密码" show-password :prefix-icon="Lock" />
            </el-form-item>

            <el-form-item prop="verificationCode">
              <div class="code-input">
                <el-input v-model="form.verificationCode" placeholder="邮箱验证码（可选）" />
                <el-button type="primary" @click="sendCode" :disabled="codeCooldown > 0">
                  {{ codeCooldown > 0 ? `${codeCooldown}s 后重发` : '获取验证码' }}
                </el-button>
              </div>
            </el-form-item>

            <el-form-item>
              <el-button type="primary" class="register-btn" :loading="loading" @click="handleRegister">
                {{ loading ? '注册中...' : '注 册' }}
              </el-button>
            </el-form-item>
          </el-form>

          <div class="login-footer">
            <span>已有账户？</span>
            <router-link to="/login" class="link">立即登录</router-link>
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
import { User, Lock, Message } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import api from '../api'

const router = useRouter()
const userStore = useUserStore()
const formRef = ref(null)
const loading = ref(false)
const codeCooldown = ref(0)

const form = reactive({
  username: '',
  email: '',
  password: '',
  confirmPassword: '',
  verificationCode: '',
})

const validateConfirm = (rule, value, callback) => {
  if (value !== form.password) {
    callback(new Error('两次密码不一致'))
  } else {
    callback()
  }
}

const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度为3-20个字符', trigger: 'blur' },
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入有效的邮箱地址', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少6个字符', trigger: 'blur' },
  ],
  confirmPassword: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    { validator: validateConfirm, trigger: 'blur' },
  ],
}

async function sendCode() {
  if (!form.email) {
    ElMessage.warning('请先输入邮箱')
    return
  }
  try {
    await api.get(`/auth/send-code?email=${form.email}`)
    ElMessage.success('验证码已发送')
    codeCooldown.value = 60
    const timer = setInterval(() => {
      codeCooldown.value--
      if (codeCooldown.value <= 0) clearInterval(timer)
    }, 1000)
  } catch {}
}

async function handleRegister() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    await userStore.register({
      username: form.username,
      email: form.email,
      password: form.password,
      verification_code: form.verificationCode || undefined,
    })
    ElMessage.success('注册成功')
    router.push('/')
  } finally {
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
  min-height: 620px;
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
  padding: 40px 56px;
}

.login-card {
  width: 100%;
  max-width: 360px;

  .login-header {
    margin-bottom: 28px;
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

.code-input {
  display: flex;
  gap: 12px;
  width: 100%;

  .el-input {
    flex: 1;
  }

  .el-button {
    white-space: nowrap;
    border-radius: 10px;
  }
}

.register-btn {
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
  margin-top: 24px;
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
