<template>
  <div class="page-container">
    <div class="page-header">
      <h2>模型配置</h2>
    </div>

    <el-tabs v-model="activeTab" class="config-tabs">
      <el-tab-pane label="供应商" name="providers">
        <div class="tab-toolbar">
          <el-button type="primary" @click="openProviderDialog()">
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
              <el-button text @click="openProviderDialog(p)"><el-icon><Edit /></el-icon></el-button>
              <el-button text type="danger" @click="deleteProvider(p.id)"><el-icon><Delete /></el-icon></el-button>
            </div>
          </div>
        </div>
      </el-tab-pane>

      <el-tab-pane label="模型管理" name="models">
        <div class="tab-toolbar">
          <el-button type="primary" @click="openModelDialog()">
            <el-icon><Plus /></el-icon> 添加模型
          </el-button>
        </div>
        <div class="table-wrapper glass-card">
          <el-table :data="sortedModels" stripe :span-method="providerSpanMethod">
            <el-table-column label="供应商" min-width="120" class-name="provider-cell">
              <template #default="{ row }">
                {{ getRowProviderName(row) }}
              </template>
            </el-table-column>
            <el-table-column prop="name" label="模型ID" min-width="150" />
            <el-table-column prop="display_name" label="显示名称" min-width="120" />
            <el-table-column prop="model_type" label="类型" width="110">
              <template #default="{ row }">
                <el-tag :type="modelTypeTag(row.model_type)" size="small">
                  {{ modelTypeLabel(row.model_type) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="model_path" label="模型路径" min-width="150">
              <template #default="{ row }">
                <span class="text-muted">{{ row.model_path || '-' }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="embedding_dimension" label="维度" width="80">
              <template #default="{ row }">
                {{ row.embedding_dimension || '-' }}
              </template>
            </el-table-column>
            <el-table-column prop="max_tokens" label="最大Token" width="110">
              <template #default="{ row }">
                {{ row.max_tokens || '-' }}
              </template>
            </el-table-column>
            <el-table-column prop="is_active" label="状态" width="80">
              <template #default="{ row }">
                <el-tag :type="row.is_active ? 'success' : 'danger'" size="small">
                  {{ row.is_active ? '启用' : '禁用' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="140" fixed="right">
              <template #default="{ row }">
                <el-button text size="small" @click="openModelDialog(row)">
                  <el-icon :size="16"><Edit /></el-icon>
                </el-button>
                <el-button text size="small" type="danger" @click="deleteModel(row.id)">
                  <el-icon :size="16"><Delete /></el-icon>
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </el-tab-pane>

      <el-tab-pane label="模型映射" name="mappings">
        <div class="tab-toolbar">
          <el-button type="primary" @click="openMappingDialog()">
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
                <el-button text size="small" @click="openMappingDialog(row)">
                  <el-icon :size="16"><Edit /></el-icon>
                </el-button>
                <el-button text size="small" type="danger" @click="deleteMapping(row.id)">
                  <el-icon :size="16"><Delete /></el-icon>
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </el-tab-pane>
    </el-tabs>

    <!-- 供应商 Dialog -->
    <el-dialog v-model="providerDialogVisible" :title="editingProvider ? '编辑供应商' : '添加供应商'" width="550">
      <el-form :model="providerForm" label-position="top">
        <el-form-item label="名称（唯一标识）">
          <el-input v-model="providerForm.name" placeholder="如 openai, zhipu, baidu" />
        </el-form-item>
        <el-form-item label="显示名称">
          <el-input v-model="providerForm.display_name" placeholder="如 OpenAI, 智谱AI" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="providerForm.description" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="API Base URL">
          <el-input v-model="providerForm.api_base" placeholder="https://api.openai.com/v1" />
        </el-form-item>
        <el-form-item label="API Key">
          <el-input v-model="providerForm.api_key" type="password" show-password />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="providerDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveProvider">保存</el-button>
      </template>
    </el-dialog>

    <!-- 模型 Dialog -->
    <el-dialog v-model="modelDialogVisible" :title="editingModel ? '编辑模型' : '添加模型'" width="600">
      <el-form :model="modelForm" label-position="top">
        <el-form-item label="供应商">
          <el-select v-model="modelForm.provider_id" style="width: 100%" clearable placeholder="本地模型无需选择供应商">
            <el-option v-for="p in providers" :key="p.id" :label="p.display_name || p.name" :value="p.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="模型名称">
          <el-input v-model="modelForm.name" placeholder="如 gpt-4, bge-large-zh-v1.5" />
        </el-form-item>
        <el-form-item label="显示名称">
          <el-input v-model="modelForm.display_name" placeholder="如 GPT-4, BGE Large" />
        </el-form-item>
        <el-form-item label="模型类型">
          <el-select v-model="modelForm.model_type" style="width: 100%">
            <el-option label="对话 (Chat)" value="chat" />
            <el-option label="多模态 (Multimodal)" value="multimodal" />
            <el-option label="生图 (Image Generation)" value="image_generation" />
            <el-option label="生视频 (Video Generation)" value="video_generation" />
            <el-option label="嵌入 (Embedding)" value="embedding" />
            <el-option label="重排序 (Rerank)" value="rerank" />
          </el-select>
        </el-form-item>
        <el-form-item label="本地模型路径" v-if="modelForm.model_type === 'embedding' || modelForm.model_type === 'rerank'">
          <el-input v-model="modelForm.model_path" placeholder="如 BAAI/bge-small-zh-v1.5 或 ./models/bge-small-zh">
            <template #prepend>路径/Model ID</template>
          </el-input>
          <div class="form-hint">支持 HuggingFace Model ID 或本地路径，填写后优先使用本地加载，留空则使用供应商 API</div>
        </el-form-item>
        <el-form-item label="向量维度" v-if="modelForm.model_type === 'embedding'">
          <el-input-number v-model="modelForm.embedding_dimension" :min="0" :max="8192" placeholder="0=自动检测" />
          <div class="form-hint">嵌入向量的维度，本地模型会自动检测，API模型需手动填写</div>
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="modelForm.description" type="textarea" :rows="2" />
        </el-form-item>
        <template v-if="modelForm.model_type === 'chat' || modelForm.model_type === 'multimodal'">
          <el-form-item label="最大Token">
            <el-input-number v-model="modelForm.max_tokens" :min="0" />
          </el-form-item>
          <el-form-item label="温度">
            <el-input v-model="modelForm.temperature" placeholder="0.7" />
          </el-form-item>
        </template>
      </el-form>
      <template #footer>
        <el-button @click="modelDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveModel">保存</el-button>
      </template>
    </el-dialog>

    <!-- 映射 Dialog -->
    <el-dialog v-model="mappingDialogVisible" :title="editingMapping ? '编辑映射' : '添加映射'" width="500">
      <el-form :model="mappingForm" label-position="top">
        <el-form-item label="智能体类型">
          <el-select v-model="mappingForm.agent_type" style="width: 100%">
            <el-option label="智能聊天" value="chat" />
            <el-option label="智能翻译" value="translation" />
            <el-option label="智能客服" value="customer_service" />
            <el-option label="订单销售" value="order_sales" />
          </el-select>
        </el-form-item>
        <el-form-item label="模型">
          <el-select v-model="mappingForm.model_id" style="width: 100%">
            <el-option v-for="m in models" :key="m.id" :label="m.display_name || m.name" :value="m.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="优先级">
          <el-input-number v-model="mappingForm.priority" :min="0" :max="100" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="mappingDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveMapping">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '../api'

const activeTab = ref('providers')

const providers = ref([])
const models = ref([])
const mappings = ref([])

const sortedModels = computed(() => {
  return [...models.value].sort((a, b) => {
    const pa = a.model_path ? '本地' : getProviderName(a.provider_id)
    const pb = b.model_path ? '本地' : getProviderName(b.provider_id)
    return pa.localeCompare(pb, 'zh-CN')
  })
})

const providerDialogVisible = ref(false)
const modelDialogVisible = ref(false)
const mappingDialogVisible = ref(false)

const editingProvider = ref(null)
const editingModel = ref(null)
const editingMapping = ref(null)

const providerForm = ref({ name: '', display_name: '', description: '', api_base: '', api_key: '', logo: '' })
const modelForm = ref({ provider_id: null, name: '', display_name: '', model_type: 'chat', description: '', max_tokens: 0, temperature: '0.7', model_path: '', embedding_dimension: 0 })
const mappingForm = ref({ agent_type: 'chat', model_id: null, priority: 0 })

const modelTypeLabel = (type) => ({ chat: '对话', multimodal: '多模态', image_generation: '生图', video_generation: '生视频', embedding: '嵌入', rerank: '重排序' }[type] || type)
const modelTypeTag = (type) => ({ chat: '', multimodal: 'danger', image_generation: 'primary', video_generation: 'primary', embedding: 'success', rerank: 'warning' }[type] || 'info')

function getProviderName(id) {
  const p = providers.value.find(p => p.id === id)
  return p ? (p.display_name || p.name) : '-'
}

function getRowProviderName(row) {
  return row.model_path ? '本地' : getProviderName(row.provider_id)
}

function providerSpanMethod({ column, rowIndex, columnIndex }) {
  if (columnIndex !== 0) return { rowspan: 1, colspan: 1 }
  const list = sortedModels.value
  const currentName = getRowProviderName(list[rowIndex])
  if (rowIndex > 0 && getRowProviderName(list[rowIndex - 1]) === currentName) {
    return { rowspan: 0, colspan: 0 }
  }
  let count = 1
  for (let i = rowIndex + 1; i < list.length && getRowProviderName(list[i]) === currentName; i++) {
    count++
  }
  return { rowspan: count, colspan: 1 }
}

function getAgentLabel(type) {
  const map = { chat: '智能聊天', translation: '智能翻译', customer_service: '智能客服', order_sales: '订单销售' }
  return map[type] || type
}

async function loadAll() {
  const [p, m, mm] = await Promise.all([
    api.get('/providers'),
    api.get('/models'),
    api.get('/model-mappings'),
  ])
  providers.value = p
  models.value = m
  mappings.value = mm
}

function openProviderDialog(item = null) {
  editingProvider.value = item
  providerForm.value = item
    ? { ...item }
    : { name: '', display_name: '', description: '', api_base: '', api_key: '', logo: '' }
  providerDialogVisible.value = true
}

async function saveProvider() {
  if (editingProvider.value) {
    await api.put(`/providers/${editingProvider.value.id}`, providerForm.value)
  } else {
    await api.post('/providers', providerForm.value)
  }
  ElMessage.success('保存成功')
  providerDialogVisible.value = false
  loadAll()
}

async function deleteProvider(id) {
  await ElMessageBox.confirm('确定删除此供应商？', '提示', { type: 'warning' })
  await api.delete(`/providers/${id}`)
  ElMessage.success('已删除')
  loadAll()
}

function openModelDialog(item = null) {
  editingModel.value = item
  modelForm.value = item
    ? { ...item }
    : { provider_id: providers.value[0]?.id || null, name: '', display_name: '', model_type: 'chat', description: '', max_tokens: 0, temperature: '0.7', model_path: '', embedding_dimension: 0 }
  modelDialogVisible.value = true
}

async function saveModel() {
  if (editingModel.value) {
    await api.put(`/models/${editingModel.value.id}`, modelForm.value)
  } else {
    await api.post('/models', modelForm.value)
  }
  ElMessage.success('保存成功')
  modelDialogVisible.value = false
  loadAll()
}

async function deleteModel(id) {
  await ElMessageBox.confirm('确定删除此模型？', '提示', { type: 'warning' })
  await api.delete(`/models/${id}`)
  ElMessage.success('已删除')
  loadAll()
}

function openMappingDialog(item = null) {
  editingMapping.value = item
  mappingForm.value = item
    ? { agent_type: item.agent_type, model_id: item.model_id, priority: item.priority }
    : { agent_type: 'chat', model_id: models.value[0]?.id || null, priority: 0 }
  mappingDialogVisible.value = true
}

async function saveMapping() {
  if (editingMapping.value) {
    await api.put(`/model-mappings/${editingMapping.value.id}`, mappingForm.value)
  } else {
    await api.post('/model-mappings', mappingForm.value)
  }
  ElMessage.success('保存成功')
  mappingDialogVisible.value = false
  loadAll()
}

async function deleteMapping(id) {
  await ElMessageBox.confirm('确定删除此映射？', '提示', { type: 'warning' })
  await api.delete(`/model-mappings/${id}`)
  ElMessage.success('已删除')
  loadAll()
}

onMounted(loadAll)
</script>

<style scoped lang="scss">
.config-tabs {
  :deep(.el-tabs__header) {
    margin-bottom: 20px;
  }

  :deep(.el-tabs__item) {
    font-size: 15px;
    font-weight: 500;
  }
}

.tab-toolbar {
  margin-bottom: 16px;
}

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

.table-wrapper {
  padding: 0;
  overflow: hidden;

  :deep(.provider-cell .cell) {
    display: flex;
    align-items: center;
  }

  :deep(.el-table .provider-cell) {
    border-right: 1px solid var(--el-table-border-color);
  }
}

.form-hint {
  font-size: 12px;
  color: var(--text-muted);
  margin-top: 4px;
  line-height: 1.4;
}

.text-muted {
  color: var(--text-muted);
  font-size: 12px;
}
</style>
