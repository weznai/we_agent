<template>
  <div class="page-container">
    <div class="page-header">
      <h2>模型管理</h2>
      <el-button type="primary" @click="openDialog()">
        <el-icon><Plus /></el-icon> 添加模型
      </el-button>
    </div>

    <div class="table-wrapper glass-card">
      <el-table :data="models" stripe>
        <el-table-column prop="name" label="模型名称" min-width="150" />
        <el-table-column prop="display_name" label="显示名称" min-width="120" />
        <el-table-column prop="model_type" label="类型" width="100">
          <template #default="{ row }">
            <el-tag size="small">{{ row.model_type }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="provider_id" label="供应商" width="120">
          <template #default="{ row }">
            {{ getProviderName(row.provider_id) }}
          </template>
        </el-table-column>
        <el-table-column prop="max_tokens" label="最大Token" width="120" />
        <el-table-column prop="temperature" label="温度" width="80" />
        <el-table-column prop="is_active" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'danger'" size="small">
              {{ row.is_active ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="140" fixed="right">
          <template #default="{ row }">
            <el-button text size="small" @click="openDialog(row)">
              <el-icon><Edit /></el-icon>
            </el-button>
            <el-button text size="small" type="danger" @click="handleDelete(row.id)">
              <el-icon><Delete /></el-icon>
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <el-dialog v-model="showDialog" :title="editingItem ? '编辑模型' : '添加模型'" width="550">
      <el-form :model="formData" label-position="top">
        <el-form-item label="供应商">
          <el-select v-model="formData.provider_id" style="width: 100%">
            <el-option v-for="p in providers" :key="p.id" :label="p.display_name || p.name" :value="p.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="模型名称">
          <el-input v-model="formData.name" placeholder="如 gpt-4, glm-4" />
        </el-form-item>
        <el-form-item label="显示名称">
          <el-input v-model="formData.display_name" placeholder="如 GPT-4, GLM-4" />
        </el-form-item>
        <el-form-item label="模型类型">
          <el-select v-model="formData.model_type" style="width: 100%">
            <el-option label="对话" value="chat" />
            <el-option label="翻译" value="translation" />
            <el-option label="嵌入" value="embedding" />
          </el-select>
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="formData.description" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="最大Token">
          <el-input-number v-model="formData.max_tokens" :min="1" :max="128000" />
        </el-form-item>
        <el-form-item label="温度">
          <el-input v-model="formData.temperature" placeholder="0.7" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showDialog = false">取消</el-button>
        <el-button type="primary" @click="saveModel">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '../api'

const models = ref([])
const providers = ref([])
const showDialog = ref(false)
const editingItem = ref(null)
const formData = ref({
  provider_id: null, name: '', display_name: '', model_type: 'chat',
  description: '', max_tokens: 4096, temperature: '0.7',
})

function getProviderName(id) {
  const p = providers.value.find(p => p.id === id)
  return p ? (p.display_name || p.name) : '-'
}

async function loadData() {
  providers.value = await api.get('/providers')
  models.value = await api.get('/models')
}

function openDialog(item = null) {
  editingItem.value = item
  if (item) {
    formData.value = { ...item }
  } else {
    formData.value = {
      provider_id: providers.value[0]?.id || null, name: '', display_name: '',
      model_type: 'chat', description: '', max_tokens: 4096, temperature: '0.7',
    }
  }
  showDialog.value = true
}

async function saveModel() {
  if (editingItem.value) {
    await api.put(`/models/${editingItem.value.id}`, formData.value)
  } else {
    await api.post('/models', formData.value)
  }
  ElMessage.success('保存成功')
  showDialog.value = false
  loadData()
}

async function handleDelete(id) {
  await ElMessageBox.confirm('确定删除此模型？', '提示', { type: 'warning' })
  await api.delete(`/models/${id}`)
  ElMessage.success('已删除')
  loadData()
}

onMounted(loadData)
</script>

<style scoped lang="scss">
.table-wrapper {
  padding: 0;
  overflow: hidden;
}
</style>
