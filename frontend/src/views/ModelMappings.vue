<template>
  <div class="page-container">
    <div class="page-header">
      <h2>模型映射</h2>
      <el-button type="primary" @click="openDialog()">
        <el-icon><Plus /></el-icon> 添加映射
      </el-button>
    </div>

    <div class="table-wrapper glass-card">
      <el-table :data="mappings" stripe>
        <el-table-column prop="agent_type" label="智能体类型" min-width="150">
          <template #default="{ row }">
            <el-tag :type="row.agent_type === 'chat' ? 'primary' : 'success'" size="small">
              {{ getAgentLabel(row.agent_type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="model_name" label="模型" min-width="150" />
        <el-table-column prop="provider_name" label="供应商" min-width="120" />
        <el-table-column prop="priority" label="优先级" width="100" />
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

    <el-dialog v-model="showDialog" :title="editingItem ? '编辑映射' : '添加映射'" width="500">
      <el-form :model="formData" label-position="top">
        <el-form-item label="智能体类型">
          <el-select v-model="formData.agent_type" style="width: 100%">
            <el-option label="智能聊天" value="chat" />
            <el-option label="智能翻译" value="translation" />
          </el-select>
        </el-form-item>
        <el-form-item label="模型">
          <el-select v-model="formData.model_id" style="width: 100%">
            <el-option v-for="m in models" :key="m.id" :label="m.display_name || m.name" :value="m.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="优先级">
          <el-input-number v-model="formData.priority" :min="0" :max="100" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showDialog = false">取消</el-button>
        <el-button type="primary" @click="saveMapping">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '../api'

const mappings = ref([])
const models = ref([])
const showDialog = ref(false)
const editingItem = ref(null)
const formData = ref({ agent_type: 'chat', model_id: null, priority: 0 })

function getAgentLabel(type) {
  const map = { chat: '智能聊天', translation: '智能翻译' }
  return map[type] || type
}

async function loadData() {
  models.value = await api.get('/models')
  mappings.value = await api.get('/model-mappings')
}

function openDialog(item = null) {
  editingItem.value = item
  if (item) {
    formData.value = { agent_type: item.agent_type, model_id: item.model_id, priority: item.priority }
  } else {
    formData.value = { agent_type: 'chat', model_id: models.value[0]?.id || null, priority: 0 }
  }
  showDialog.value = true
}

async function saveMapping() {
  if (editingItem.value) {
    await api.put(`/model-mappings/${editingItem.value.id}`, formData.value)
  } else {
    await api.post('/model-mappings', formData.value)
  }
  ElMessage.success('保存成功')
  showDialog.value = false
  loadData()
}

async function handleDelete(id) {
  await ElMessageBox.confirm('确定删除此映射？', '提示', { type: 'warning' })
  await api.delete(`/model-mappings/${id}`)
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
