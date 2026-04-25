<template>
  <div class="page-container">
    <div class="page-header">
      <h2>用户管理</h2>
    </div>

    <div class="table-wrapper glass-card">
      <el-table :data="users" stripe>
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="username" label="用户名" min-width="120" />
        <el-table-column prop="email" label="邮箱" min-width="180" />
        <el-table-column prop="nickname" label="昵称" min-width="100" />
        <el-table-column prop="role" label="角色" width="100">
          <template #default="{ row }">
            <el-tag :type="row.role === 'super' ? 'danger' : row.role === 'admin' ? 'warning' : 'info'" size="small">
              {{ getRoleLabel(row.role) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="is_active" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'danger'" size="small">
              {{ row.is_active ? '正常' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="email_verified" label="邮箱验证" width="100">
          <template #default="{ row }">
            <el-tag :type="row.email_verified ? 'success' : 'warning'" size="small">
              {{ row.email_verified ? '已验证' : '未验证' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="注册时间" width="170">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-select
              v-model="row.role"
              size="small"
              style="width: 100px; margin-right: 8px"
              @change="updateRole(row)"
            >
              <el-option label="普通用户" value="user" />
              <el-option label="管理员" value="admin" />
              <el-option label="超级用户" value="super" />
            </el-select>
            <el-button
              text
              size="small"
              :type="row.is_active ? 'danger' : 'success'"
              @click="toggleStatus(row)"
            >
              {{ row.is_active ? '禁用' : '启用' }}
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '../api'

const users = ref([])

function getRoleLabel(role) {
  const map = { super: '超级用户', admin: '管理员', user: '普通用户' }
  return map[role] || role
}

function formatDate(dt) {
  if (!dt) return '-'
  return new Date(dt).toLocaleString('zh-CN')
}

async function loadUsers() {
  users.value = await api.get('/users')
}

async function updateRole(user) {
  await api.put(`/users/${user.id}/role?role=${user.role}`)
  ElMessage.success('角色已更新')
}

async function toggleStatus(user) {
  await api.put(`/users/${user.id}/status`)
  user.is_active = !user.is_active
  ElMessage.success('状态已更新')
}

onMounted(loadUsers)
</script>

<style scoped lang="scss">
.table-wrapper {
  padding: 0;
  overflow: hidden;
}
</style>
