<template>
  <div class="page-container profile-page">
    <div class="page-header">
      <h2>个人中心</h2>
    </div>

    <div class="profile-content">
      <div class="profile-card glass-card">
        <div class="profile-avatar-section">
          <el-upload
            :show-file-list="false"
            :http-request="handleAvatarUpload"
            accept="image/*"
          >
            <div class="avatar-large" title="点击更换头像">
              <img v-if="userStore.user?.avatar" :src="userStore.user.avatar" class="avatar-img" />
              <span v-else>{{ userStore.nickname?.charAt(0)?.toUpperCase() }}</span>
              <div class="avatar-overlay">
                <el-icon :size="20"><Camera /></el-icon>
              </div>
            </div>
          </el-upload>
          <h3>{{ userStore.nickname }}</h3>
          <el-tag :type="userStore.isSuperUser ? 'danger' : userStore.isAdmin ? 'warning' : 'info'" size="small">
            {{ userStore.isSuperUser ? '超级用户' : userStore.isAdmin ? '管理员' : '普通用户' }}
          </el-tag>
          <p class="email-text">{{ userStore.user?.email }}</p>
          <p class="join-date">注册于 {{ formatDate(userStore.user?.created_at) }}</p>
        </div>

        <div class="profile-form-section">
          <el-tabs v-model="activeTab">
            <el-tab-pane label="基本信息" name="info">
              <el-form :model="profileForm" label-position="top" class="profile-form">
                <el-form-item label="用户名">
                  <el-input v-model="profileForm.username" disabled>
                    <template #prefix><el-icon><User /></el-icon></template>
                  </el-input>
                </el-form-item>
                <el-form-item label="邮箱">
                  <el-input v-model="profileForm.email" disabled>
                    <template #prefix><el-icon><Message /></el-icon></template>
                  </el-input>
                </el-form-item>
                <el-form-item label="昵称">
                  <el-input v-model="profileForm.nickname" placeholder="输入昵称">
                    <template #prefix><el-icon><UserFilled /></el-icon></template>
                  </el-input>
                </el-form-item>
                <el-form-item>
                  <el-button type="primary" :loading="saving" @click="updateProfile">保存修改</el-button>
                </el-form-item>
              </el-form>
            </el-tab-pane>

            <el-tab-pane label="修改密码" name="password">
              <el-form :model="passwordForm" label-position="top" class="profile-form">
                <el-form-item label="当前密码">
                  <el-input v-model="passwordForm.old_password" type="password" show-password placeholder="输入当前密码">
                    <template #prefix><el-icon><Lock /></el-icon></template>
                  </el-input>
                </el-form-item>
                <el-form-item label="新密码">
                  <el-input v-model="passwordForm.new_password" type="password" show-password placeholder="输入新密码（至少6位）">
                    <template #prefix><el-icon><Lock /></el-icon></template>
                  </el-input>
                </el-form-item>
                <el-form-item>
                  <el-button type="primary" :loading="changingPwd" @click="changePassword">修改密码</el-button>
                </el-form-item>
              </el-form>
            </el-tab-pane>
          </el-tabs>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useUserStore } from '../store/user'
import { ElMessage } from 'element-plus'
import api from '../api'

const userStore = useUserStore()
const activeTab = ref('info')
const saving = ref(false)
const changingPwd = ref(false)

const profileForm = reactive({
  username: '',
  email: '',
  nickname: '',
})

const passwordForm = reactive({
  old_password: '',
  new_password: '',
})

function formatDate(dt) {
  if (!dt) return '-'
  return new Date(dt).toLocaleDateString('zh-CN')
}

onMounted(() => {
  profileForm.username = userStore.user?.username || ''
  profileForm.email = userStore.user?.email || ''
  profileForm.nickname = userStore.user?.nickname || ''
})

async function handleAvatarUpload(options) {
  const fd = new FormData()
  fd.append('file', options.file)
  try {
    const resp = await api.post('/knowledge/upload', fd, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    await userStore.updateProfile({ avatar: resp.file_path })
    ElMessage.success('头像已更新')
  } catch {
    ElMessage.error('头像上传失败')
  }
}

async function updateProfile() {
  saving.value = true
  try {
    await userStore.updateProfile({ nickname: profileForm.nickname })
    ElMessage.success('信息已更新')
  } finally {
    saving.value = false
  }
}

async function changePassword() {
  if (!passwordForm.old_password || !passwordForm.new_password) {
    ElMessage.warning('请填写完整密码信息')
    return
  }
  if (passwordForm.new_password.length < 6) {
    ElMessage.warning('新密码至少6个字符')
    return
  }
  changingPwd.value = true
  try {
    await api.put('/users/me/password', passwordForm)
    ElMessage.success('密码已修改')
    passwordForm.old_password = ''
    passwordForm.new_password = ''
  } finally {
    changingPwd.value = false
  }
}
</script>

<style scoped lang="scss">
.profile-page {
  overflow-y: auto;
}

.profile-content {
  max-width: 800px;
  margin: 0 auto;
}

.profile-card {
  display: flex;
  gap: 40px;
  padding: 40px;
}

.profile-avatar-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  min-width: 200px;

  .avatar-large {
    width: 100px;
    height: 100px;
    border-radius: 24px;
    background: var(--gradient-primary);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 40px;
    font-weight: 700;
    color: white;
    margin-bottom: 8px;
    cursor: pointer;
    position: relative;
    overflow: hidden;
    transition: var(--transition);

    &:hover {
      .avatar-overlay { opacity: 1; }
      transform: scale(1.05);
    }

    .avatar-img {
      width: 100%;
      height: 100%;
      object-fit: cover;
    }

    .avatar-overlay {
      position: absolute;
      inset: 0;
      background: rgba(0, 0, 0, 0.5);
      display: flex;
      align-items: center;
      justify-content: center;
      opacity: 0;
      transition: var(--transition);
    }
  }

  h3 {
    font-size: 20px;
    font-weight: 600;
    color: var(--text-primary);
  }

  .email-text {
    font-size: 13px;
    color: var(--text-secondary);
  }

  .join-date {
    font-size: 12px;
    color: var(--text-muted);
  }
}

.profile-form-section {
  flex: 1;
  min-width: 0;
}

.profile-form {
  max-width: 400px;
  margin-top: 16px;
}
</style>
