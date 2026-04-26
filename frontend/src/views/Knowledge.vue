<template>
  <div class="knowledge-layout">
    <div class="knowledge-main">
      <div class="knowledge-header">
        <div class="header-tabs">
          <div
            v-for="tab in tabs"
            :key="tab.key"
            class="tab-item"
            :class="{ active: activeTab === tab.key }"
            @click="activeTab = tab.key"
          >
            <el-icon><component :is="tab.icon" /></el-icon>
            <span>{{ tab.label }}</span>
          </div>
        </div>
        <div class="header-actions" v-if="activeTab === 'files'">
          <el-input
            v-model="searchQuery"
            placeholder="搜索知识库..."
            :prefix-icon="Search"
            class="search-input"
            @keyup.enter="doSearch"
            clearable
            @clear="searchResults = []"
          />
          <el-upload
            :show-file-list="false"
            :http-request="handleUpload"
            accept=".txt,.md,.csv,.json,.py,.js,.html,.css,.pdf,.doc,.docx"
          >
            <el-button type="primary" :loading="uploading">
              <el-icon><Upload /></el-icon> 上传文件
            </el-button>
          </el-upload>
        </div>
      </div>

      <!-- 全部知识库 -->
      <div class="tab-content" v-show="activeTab === 'files'">
        <div class="search-results" v-if="searchResults.length > 0">
          <div class="search-header">
            <h4>搜索结果</h4>
            <el-button text size="small" @click="searchResults = []">关闭</el-button>
          </div>
          <div v-for="r in searchResults" :key="r.chunk_id" class="search-result-card glass-card">
            <div class="result-header">
              <el-icon><Document /></el-icon>
              <span class="result-name">{{ r.knowledge_name }}</span>
              <el-tag size="small" type="success">{{ (r.score * 100).toFixed(1) }}%</el-tag>
            </div>
            <p class="result-content">{{ r.content }}</p>
          </div>
        </div>

        <div class="file-table" v-else>
          <el-table :data="files" stripe>
            <el-table-column label="文件" min-width="240">
              <template #default="{ row }">
                <div class="file-info">
                  <div class="file-icon" :style="{ background: getFileIconBg(row.file_type) }">
                    {{ row.file_type?.toUpperCase()?.slice(0, 2) || '?' }}
                  </div>
                  <div class="file-detail">
                    <span class="file-name">{{ row.name }}</span>
                    <span class="file-desc">{{ row.description || row.file_type }}</span>
                  </div>
                </div>
              </template>
            </el-table-column>
            <el-table-column prop="file_size" label="大小" width="100">
              <template #default="{ row }">{{ formatSize(row.file_size) }}</template>
            </el-table-column>
            <el-table-column prop="chunk_count" label="分块" width="80">
              <template #default="{ row }">
                <el-tag size="small" :type="row.chunk_count > 0 ? 'success' : 'info'">{{ row.chunk_count }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="indexed" label="索引" width="80">
              <template #default="{ row }">
                <el-tag size="small" :type="row.indexed ? 'success' : 'warning'">{{ row.indexed ? '已索引' : '待处理' }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="created_at" label="上传时间" width="160">
              <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
            </el-table-column>
            <el-table-column label="操作" width="200" fixed="right">
              <template #default="{ row }">
                <el-button text size="small" @click="openFileEditDialog(row)"><el-icon><Edit /></el-icon></el-button>
                <el-button text size="small" type="primary" @click="reindexFile(row.id)"><el-icon><Refresh /></el-icon></el-button>
                <el-button text size="small" type="danger" @click="deleteFile(row.id)"><el-icon><Delete /></el-icon></el-button>
              </template>
            </el-table-column>
          </el-table>

          <div v-if="files.length === 0" class="empty-files">
            <el-icon :size="48"><FolderOpened /></el-icon>
            <p>暂无文件，点击上传按钮添加</p>
          </div>
        </div>
      </div>

      <!-- 设置 -->
      <div class="tab-content settings-content" v-show="activeTab === 'settings'">
        <div class="settings-section">
          <div class="section-title">
            <el-icon><Cpu /></el-icon>
            <span>嵌入模型</span>
          </div>
          <div class="section-body">
            <el-form label-position="top" class="settings-form">
              <el-form-item label="嵌入模型">
                <el-select v-model="settingsForm.embedding_model_id" placeholder="选择嵌入模型" clearable style="width: 100%">
                  <el-option
                    v-for="m in embeddingModels"
                    :key="m.id"
                    :label="m.display_name"
                    :value="m.id"
                  />
                </el-select>
              </el-form-item>
            </el-form>
          </div>
        </div>

        <div class="settings-section">
          <div class="section-title">
            <el-icon><Scissor /></el-icon>
            <span>切割分段方式</span>
          </div>
          <div class="section-body">
            <el-form label-position="top" class="settings-form">
              <el-form-item label="分段方式">
                <el-select v-model="settingsForm.chunk_method" style="width: 100%">
                  <el-option label="自动分段" value="auto" />
                  <el-option label="按段落分段" value="paragraph" />
                  <el-option label="按句子分段" value="sentence" />
                  <el-option label="固定长度分段" value="fixed" />
                </el-select>
              </el-form-item>
              <div class="form-row">
                <el-form-item label="分段最大长度">
                  <el-input-number v-model="settingsForm.chunk_size" :min="100" :max="4000" :step="100" style="width: 100%" />
                </el-form-item>
                <el-form-item label="重叠长度">
                  <el-input-number v-model="settingsForm.chunk_overlap" :min="0" :max="500" :step="10" style="width: 100%" />
                </el-form-item>
              </div>
            </el-form>
          </div>
        </div>

        <div class="settings-section">
          <div class="section-title">
            <el-icon><Search /></el-icon>
            <span>检索方式</span>
          </div>
          <div class="section-body">
            <el-form label-position="top" class="settings-form">
              <el-form-item label="检索模式">
                <el-select v-model="settingsForm.retrieval_method" style="width: 100%">
                  <el-option label="纯向量检索" value="pure" />
                  <el-option label="混合检索（向量 + 关键词）" value="hybrid" />
                </el-select>
              </el-form-item>
              <div class="form-row">
                <el-form-item label="召回数量 (Top K)">
                  <el-input-number v-model="settingsForm.retrieval_top_k" :min="1" :max="50" :step="1" style="width: 100%" />
                </el-form-item>
                <el-form-item label="相似度阈值">
                  <el-input-number v-model="scoreThresholdNum" :min="0" :max="1" :step="0.05" :precision="2" style="width: 100%" />
                </el-form-item>
              </div>
            </el-form>
          </div>
        </div>

        <div class="settings-footer">
          <el-button type="primary" @click="saveSettings" :loading="savingSettings">保存设置</el-button>
        </div>
      </div>

      <!-- 召回测试 -->
      <div class="tab-content recall-content" v-show="activeTab === 'recall'">
        <div class="recall-input-area">
          <div class="recall-input-wrapper">
            <el-input
              v-model="recallQuery"
              placeholder="输入测试查询语句，验证知识库召回效果..."
              @keydown.enter.prevent="runRecallTest"
              clearable
            />
            <el-button type="primary" @click="runRecallTest" :loading="recallLoading" :disabled="!recallQuery.trim()">
              <el-icon><Promotion /></el-icon> 测试
            </el-button>
          </div>
          <div class="recall-tips">
            <span>Top K: {{ recallTopK }}</span>
            <el-slider v-model="recallTopK" :min="1" :max="20" :step="1" style="width: 200px; margin-left: 12px;" />
          </div>
        </div>

        <div class="recall-results" v-if="recallResults.length > 0">
          <div class="recall-summary">
            <span>共召回 <strong>{{ recallResults.length }}</strong> 条结果</span>
            <el-tag type="info" size="small">{{ recallResults[0]?.retrieval_method === 'hybrid' ? '混合检索' : '纯向量检索' }}</el-tag>
          </div>
          <div v-for="(r, i) in recallResults" :key="r.chunk_id" class="recall-card glass-card">
            <div class="recall-card-header">
              <span class="recall-rank">#{{ i + 1 }}</span>
              <el-icon><Document /></el-icon>
              <span class="recall-name">{{ r.knowledge_name }}</span>
              <el-tag size="small" :type="r.score >= 0.8 ? 'success' : r.score >= 0.5 ? 'warning' : 'danger'">
                {{ (r.score * 100).toFixed(1) }}%
              </el-tag>
              <el-tag size="small" type="info">分块 #{{ r.chunk_index }}</el-tag>
            </div>
            <p class="recall-content">{{ r.content }}</p>
          </div>
        </div>

        <div class="recall-empty" v-else-if="recallTested">
          <el-icon :size="40"><Search /></el-icon>
          <p>未找到相关结果，请尝试调整查询语句或检查知识库是否有已索引的文件</p>
        </div>

        <div class="recall-empty" v-else>
          <el-icon :size="40"><DataAnalysis /></el-icon>
          <p>输入查询语句测试知识库召回效果</p>
        </div>
      </div>

      <el-dialog v-model="showFileEditDialog" title="编辑文件" width="450">
        <el-form :model="fileForm" label-position="top">
          <el-form-item label="文件名">
            <el-input v-model="fileForm.name" />
          </el-form-item>
          <el-form-item label="描述">
            <el-input v-model="fileForm.description" type="textarea" :rows="2" />
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="showFileEditDialog = false">取消</el-button>
          <el-button type="primary" @click="saveFile">保存</el-button>
        </template>
      </el-dialog>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search } from '@element-plus/icons-vue'
import api from '../api'

const tabs = [
  { key: 'files', label: '全部知识库', icon: 'FolderOpened' },
  { key: 'settings', label: '设置', icon: 'Setting' },
  { key: 'recall', label: '召回测试', icon: 'DataAnalysis' },
]

const activeTab = ref('files')
const files = ref([])
const searchQuery = ref('')
const searchResults = ref([])
const uploading = ref(false)

const showFileEditDialog = ref(false)
const editingFile = ref(null)
const fileForm = ref({ name: '', description: '' })

const embeddingModels = ref([])
const savingSettings = ref(false)
const settingsForm = ref({
  embedding_model_id: null,
  chunk_method: 'auto',
  chunk_size: 500,
  chunk_overlap: 50,
  retrieval_method: 'pure',
  retrieval_top_k: 5,
  score_threshold: '0.5',
})

const scoreThresholdNum = computed({
  get: () => parseFloat(settingsForm.value.score_threshold) || 0.5,
  set: (v) => { settingsForm.value.score_threshold = String(v) },
})

const recallQuery = ref('')
const recallLoading = ref(false)
const recallResults = ref([])
const recallTested = ref(false)
const recallTopK = ref(5)

async function loadFiles() {
  try { files.value = await api.get('/knowledge/files') } catch {}
}

async function loadSettings() {
  try {
    const data = await api.get('/knowledge/settings')
    settingsForm.value = {
      embedding_model_id: data.embedding_model_id,
      chunk_method: data.chunk_method || 'auto',
      chunk_size: data.chunk_size || 500,
      chunk_overlap: data.chunk_overlap || 50,
      retrieval_method: data.retrieval_method || 'pure',
      retrieval_top_k: data.retrieval_top_k || 5,
      score_threshold: data.score_threshold || '0.5',
    }
    recallTopK.value = data.retrieval_top_k || 5
  } catch {}
}

async function loadEmbeddingModels() {
  try { embeddingModels.value = await api.get('/knowledge/embedding-models') } catch {}
}

async function saveSettings() {
  savingSettings.value = true
  try {
    await api.put('/knowledge/settings', settingsForm.value)
    ElMessage.success('设置已保存')
  } catch { ElMessage.error('保存失败') }
  finally { savingSettings.value = false }
}

async function handleUpload(options) {
  const fd = new FormData()
  fd.append('file', options.file)
  uploading.value = true
  try {
    await api.post('/knowledge/files/upload', fd, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    ElMessage.success('上传并索引成功')
    loadFiles()
  } catch { ElMessage.error('上传失败') }
  finally { uploading.value = false }
}

function openFileEditDialog(file) {
  editingFile.value = file
  fileForm.value = { name: file.name, description: file.description }
  showFileEditDialog.value = true
}

async function saveFile() {
  await api.put(`/knowledge/files/${editingFile.value.id}`, fileForm.value)
  ElMessage.success('保存成功')
  showFileEditDialog.value = false
  loadFiles()
}

async function reindexFile(id) {
  await api.post(`/knowledge/files/${id}/reindex`)
  ElMessage.success('重新索引完成')
  loadFiles()
}

async function deleteFile(id) {
  await ElMessageBox.confirm('确定删除此文件？关联的分块索引也将被删除。', '提示', { type: 'warning' })
  await api.delete(`/knowledge/files/${id}`)
  ElMessage.success('已删除')
  loadFiles()
}

async function doSearch() {
  if (!searchQuery.value.trim()) return
  try {
    searchResults.value = await api.post('/knowledge/search', { query: searchQuery.value, top_k: 10 })
    if (searchResults.value.length === 0) ElMessage.info('未找到相关结果')
  } catch { ElMessage.error('搜索失败') }
}

async function runRecallTest() {
  if (!recallQuery.value.trim()) return
  recallLoading.value = true
  recallTested.value = true
  try {
    recallResults.value = await api.post('/knowledge/recall-test', {
      query: recallQuery.value,
      top_k: recallTopK.value,
    })
    if (recallResults.value.length === 0) ElMessage.info('未找到相关结果')
  } catch { ElMessage.error('召回测试失败') }
  finally { recallLoading.value = false }
}

function formatSize(bytes) {
  if (!bytes) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB']
  let i = 0, size = bytes
  while (size >= 1024 && i < units.length - 1) { size /= 1024; i++ }
  return `${size.toFixed(1)} ${units[i]}`
}

function formatDate(dt) {
  if (!dt) return '-'
  return new Date(dt).toLocaleString('zh-CN')
}

function getFileIconBg(ext) {
  const map = { md: '#2563eb', txt: '#0ea5e9', py: '#10b981', js: '#f59e0b', json: '#06b6d4', csv: '#ef4444', html: '#f97316', css: '#3b82f6' }
  return `linear-gradient(135deg, ${map[ext] || '#64748b'}, ${map[ext] || '#64748b'}88)`
}

onMounted(() => { loadFiles(); loadSettings(); loadEmbeddingModels() })
</script>

<style scoped lang="scss">
.knowledge-layout {
  display: flex;
  height: 100%;
  overflow: hidden;
}

.knowledge-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-width: 0;
}

.knowledge-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 24px;
  border-bottom: 1px solid var(--border-color);
  background: var(--bg-topbar, var(--bg-card));
  flex-shrink: 0;
  height: 56px;
}

.header-tabs {
  display: flex;
  gap: 4px;
}

.tab-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 18px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  color: var(--text-secondary);
  transition: var(--transition);

  &:hover {
    color: var(--primary);
    background: rgba(37, 99, 235, 0.06);
  }

  &.active {
    color: var(--primary);
    background: rgba(37, 99, 235, 0.1);
  }

  .el-icon { font-size: 16px; }
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.search-input {
  width: 260px;
}

.tab-content {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}

// ===== Files =====
.search-results {
  .search-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
    h4 { color: var(--primary); font-size: 15px; }
  }
}

.search-result-card {
  padding: 16px;
  margin-bottom: 10px;
  transition: var(--transition);
  &:hover { border-color: var(--primary); }

  .result-header {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 8px;
    .result-name { font-weight: 600; font-size: 14px; color: var(--text-primary); flex: 1; }
  }
  .result-content {
    font-size: 13px;
    color: var(--text-secondary);
    line-height: 1.7;
    max-height: 80px;
    overflow: hidden;
    text-overflow: ellipsis;
    display: -webkit-box;
    -webkit-line-clamp: 3;
    -webkit-box-orient: vertical;
  }
}

.file-table {
  padding: 0;
}

.file-info {
  display: flex;
  align-items: center;
  gap: 12px;

  .file-icon {
    width: 36px;
    height: 36px;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 11px;
    font-weight: 700;
    color: white;
    flex-shrink: 0;
  }

  .file-detail {
    display: flex;
    flex-direction: column;
    .file-name { font-size: 13px; font-weight: 500; color: var(--text-primary); }
    .file-desc { font-size: 11px; color: var(--text-muted); }
  }
}

.empty-files {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px;
  color: var(--text-muted);
  gap: 12px;
}

// ===== Settings =====
.settings-content {
  max-width: 720px;
}

.settings-section {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  margin-bottom: 20px;
  overflow: hidden;
  box-shadow: var(--shadow-card);
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 14px 20px;
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  border-bottom: 1px solid var(--border-color);
  background: rgba(37, 99, 235, 0.04);

  .el-icon { color: var(--primary); font-size: 16px; }
}

.section-body {
  padding: 20px;
}

.settings-form {
  .form-row {
    display: flex;
    gap: 20px;

    .el-form-item {
      flex: 1;
    }
  }
}

.settings-footer {
  padding-top: 8px;
}

// ===== Recall Test =====
.recall-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.recall-input-area {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 20px;
  box-shadow: var(--shadow-card);
  flex-shrink: 0;
}

.recall-input-wrapper {
  display: flex;
  gap: 12px;

  .el-input { flex: 1; }
}

.recall-tips {
  display: flex;
  align-items: center;
  margin-top: 12px;
  font-size: 13px;
  color: var(--text-secondary);
}

.recall-summary {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 14px;
  color: var(--text-secondary);

  strong { color: var(--primary); }
}

.recall-results {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.recall-card {
  padding: 16px;
  transition: var(--transition);
  &:hover { border-color: var(--primary); }

  .recall-card-header {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 10px;

    .recall-rank {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 24px;
      height: 24px;
      border-radius: 6px;
      background: var(--primary);
      color: white;
      font-size: 12px;
      font-weight: 700;
      flex-shrink: 0;
    }

    .recall-name { font-weight: 600; font-size: 14px; color: var(--text-primary); flex: 1; }
  }

  .recall-content {
    font-size: 13px;
    color: var(--text-secondary);
    line-height: 1.7;
    background: rgba(37, 99, 235, 0.03);
    border-radius: 8px;
    padding: 12px;
    white-space: pre-wrap;
    word-break: break-all;
  }
}

.recall-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px;
  color: var(--text-muted);
  gap: 12px;

  p { font-size: 14px; }
}
</style>
