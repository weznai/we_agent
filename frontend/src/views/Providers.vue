<template>
  <div class="page-container">
    <div class="page-header">
      <h2>大模型供应商</h2>
      <el-button type="primary" @click="openDialog()">
        <el-icon><Plus /></el-icon> 添加供应商
      </el-button>
    </div>

    <div class="provider-grid">
      <div v-for="p in providers" :key="p.id" class="provider-card glass-card">
        <div class="provider-logo">
          <el-icon :size="40"><Connection /></el-icon>
        </div>
        <div class="provider-info">
          <h4>{{ p.display_name || p.name }}</h4>
          <p>{{ p.description || '暂无描述' }}</p>
          <div class="provider-meta">
            <el-tag :type="p.is_active ? 'success' : 'danger'" size="small">
              {{ p.is_active ? '启用' : '禁用' }}
            </el-tag>
            <span class="api-base">{{ p.api_base || '未配置' }}</span>
          </div>
        </div>
        <div class="provider-actions">
          <el-button text @click="openDialog(p)"><el-icon><Edit /></el-icon></el-button>
          <el-button text type="danger" @click="handleDelete(p.id)"><el-icon><Delete /></el-icon></el-button>
        </div>
      </div>
    </div>

    <el-dialog v-model="showDialog" :title="editingItem ? '编辑供应商' : '添加供应商'" width="550">
      <el-form :model="formData" label-position="top">
        <el-form-item label="名称（唯一标识）">
          <el-input v-model="formData.name" placeholder="如 openai, zhipu, baidu" />
        </el-form-item>
        <el-form-item label="显示名称">
          <el-input v-model="formData.display_name" placeholder="如 OpenAI, 智谱AI" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="formData.description" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="API Base URL">
          <el-input v-model="formData.api_base" placeholder="https://api.openai.com/v1" />
        </el-form-item>
        <el-form-item label="API Key">
          <el-input v-model="formData.api_key" type="password" show-password />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showDialog = false">取消</el-button>
        <el-button type="primary" @click="saveProvider">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '../api'

const providers = ref([])
const showDialog = ref(false)
const editingItem = ref(null)
const formData = ref({ name: '', display_name: '', description: '', api_base: '', api_key: '', logo: '' })

async function loadProviders() {
  providers.value = await api.get('/providers')
}

function openDialog(item = null) {
  editingItem.value = item
  if (item) {
    formData.value = { ...item }
  } else {
    formData.value = { name: '', display_name: '', description: '', api_base: '', api_key: '', logo: '' }
  }
  showDialog.value = true
}

async function saveProvider() {
  if (editingItem.value) {
    await api.put(`/providers/${editingItem.value.id}`, formData.value)
  } else {
    await api.post('/providers', formData.value)
  }
  ElMessage.success('保存成功')
  showDialog.value = false
  loadProviders()
}

async function handleDelete(id) {
  await ElMessageBox.confirm('确定删除此供应商？', '提示', { type: 'warning' })
  await api.delete(`/providers/${id}`)
  ElMessage.success('已删除')
  loadProviders()
}

onMounted(loadProviders)
</script>

<style scoped lang="scss">
.provider-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
  gap: 16px;
}

.provider-card {
  display: flex;
  gap: 16px;
  padding: 20px;
  transition: var(--transition);

  &:hover {
    transform: translateY(-2px);

    .provider-actions { opacity: 1; }
  }
}

.provider-logo {
  width: 60px;
  height: 60px;
  border-radius: 14px;
  background: var(--gradient-card);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  color: var(--primary);
}

.provider-info {
  flex: 1;
  min-width: 0;

  h4 {
    font-size: 16px;
    font-weight: 600;
    color: var(--text-primary);
    margin-bottom: 4px;
  }

  p {
    font-size: 13px;
    color: var(--text-secondary);
    margin-bottom: 8px;
  }

  .provider-meta {
    display: flex;
    align-items: center;
    gap: 8px;

    .api-base {
      font-size: 12px;
      color: var(--text-muted);
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
  }
}

.provider-actions {
  display: flex;
  gap: 4px;
  opacity: 0;
  transition: var(--transition);
}
</style>
