<template>
  <div class="knowledge-layout">
    <div class="knowledge-sidebar">
      <div class="sidebar-header">
        <span class="sidebar-title">知识库</span>
        <el-button text size="small" @click="openGroupDialog()">
          <el-icon><Plus /></el-icon>
        </el-button>
      </div>
      <div class="sidebar-list">
        <div
          v-for="g in groups"
          :key="g.id"
          class="sidebar-item"
          :class="{ active: activeGroupId === g.id }"
          @click="selectGroup(g.id)"
          @contextmenu.prevent="openGroupContextMenu($event, g)"
        >
          <el-icon><Folder /></el-icon>
          <span class="sidebar-item-name">{{ g.name }}</span>
          <span class="sidebar-item-count">{{ g.file_count }}</span>
        </div>
      </div>
    </div>

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
            v-if="activeGroupId"
            :show-file-list="false"
            :http-request="handleUpload"
            accept=".txt,.md,.csv,.json,.py,.js,.html,.css,.pdf,.doc,.docx,.xls,.xlsx"
            multiple
          >
            <el-button type="primary" :loading="uploading">
              <el-icon><Upload /></el-icon> 上传文件
            </el-button>
          </el-upload>
        </div>
      </div>

      <div
        class="tab-content"
        v-show="activeTab === 'files'"
        @dragover.prevent="onDragOver"
        @dragleave.prevent="onDragLeave"
        @drop.prevent="onDrop"
        :class="{ 'drag-active': isDragging }"
      >
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

        <div class="file-table" v-else-if="files.length > 0">
          <el-table :data="files" stripe>
            <el-table-column label="文件" min-width="180">
              <template #default="{ row }">
                <div class="file-info" @click="openChunkDrawer(row)" style="cursor: pointer">
                  <div class="file-icon" :style="{ background: getFileIconBg(row.file_type) }">
                    {{ row.file_type?.toUpperCase()?.slice(0, 2) || '?' }}
                  </div>
                  <div class="file-detail">
                    <span class="file-name">{{ row.name.length > 20 ? row.name.slice(0, 20) + '...' : row.name }}</span>
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
                <el-tag size="small" :type="row.chunk_count > 0 ? 'success' : 'info'" class="chunk-tag" @click="openChunkDrawer(row)">
                  {{ row.chunk_count }}
                </el-tag>
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
                <el-button text size="small" class="action-btn" @click="openChunkDrawer(row)" title="查看切片"><el-icon :size="16"><Grid /></el-icon></el-button>
                <el-button text size="small" class="action-btn" @click="openFileEditDialog(row)" title="编辑"><el-icon :size="16"><Edit /></el-icon></el-button>
                <el-button text size="small" class="action-btn" @click="reindexFile(row.id)" title="重新索引"><el-icon :size="16"><Refresh /></el-icon></el-button>
                <el-button text size="small" class="action-btn action-btn-danger" @click="deleteFile(row.id)" title="删除"><el-icon :size="16"><Delete /></el-icon></el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>

        <div v-else class="empty-files drop-zone" @click="!uploading && triggerUpload()">
          <input
            type="file"
            ref="fileInputRef"
            multiple
            accept=".txt,.md,.csv,.json,.py,.js,.html,.css,.pdf,.doc,.docx,.xls,.xlsx"
            style="display: none"
            @change="onFileInputChange"
          />
          <div v-if="uploading" class="drop-zone-loading">
            <el-icon :size="48" class="is-loading"><Loading /></el-icon>
            <h3>正在上传中，请稍候...</h3>
          </div>
          <div v-else class="drop-zone-content">
            <el-icon :size="56" class="drop-icon"><UploadFilled /></el-icon>
            <h3>拖拽文件到此处上传</h3>
            <p>或点击选择文件</p>
            <p class="drop-hint">支持 TXT、Markdown、PDF、Word、Excel、CSV、JSON 等格式</p>
          </div>
        </div>
      </div>

      <div class="tab-content settings-content" v-show="activeTab === 'settings'">
        <div class="settings-hint" v-if="activeGroupId">
          <el-tag type="primary" size="small">当前知识库：{{ currentGroupName }}</el-tag>
        </div>
        <div class="settings-hint" v-else>
          <el-tag type="info" size="small">全局默认设置（所有知识库共享）</el-tag>
        </div>

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
                    v-for="m in embeddingModelList"
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

        <div class="settings-section">
          <div class="section-title">
            <el-icon><Sort /></el-icon>
            <span>重排模型</span>
          </div>
          <div class="section-body">
            <el-form label-position="top" class="settings-form">
              <el-form-item label="启用重排">
                <el-switch v-model="settingsForm.enable_rerank" active-text="开启" inactive-text="关闭" />
              </el-form-item>
              <el-form-item label="重排模型" v-if="settingsForm.enable_rerank">
                <el-select v-model="settingsForm.rerank_model_id" placeholder="选择重排模型" clearable style="width: 100%">
                  <el-option
                    v-for="m in rerankModelList"
                    :key="m.id"
                    :label="m.display_name"
                    :value="m.id"
                  />
                </el-select>
              </el-form-item>
              <div class="rerank-hint" v-if="settingsForm.enable_rerank">
                <p>重排模型会对向量检索的候选结果进行二次排序，提升召回精度。建议 Top K 适当调大以获得更多候选。</p>
              </div>
            </el-form>
          </div>
        </div>

        <div class="settings-footer">
          <el-button type="primary" @click="saveSettings" :loading="savingSettings">保存设置</el-button>
        </div>
      </div>

      <div class="tab-content recall-content" v-show="activeTab === 'recall'">
        <div class="recall-input-area">
          <div class="recall-scope" v-if="activeGroupId">
            <el-tag type="primary" size="small">限定知识库：{{ currentGroupName }}</el-tag>
          </div>
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

      <div class="tab-content rag-content" v-show="activeTab === 'rag'">
        <div class="rag-input-area">
          <div class="recall-scope" v-if="activeGroupId">
            <el-tag type="primary" size="small">限定知识库：{{ currentGroupName }}</el-tag>
          </div>
          <div class="recall-input-wrapper">
            <el-input
              v-model="ragQuery"
              placeholder="输入问题，系统将从知识库检索相关内容后由AI分析回答..."
              @keydown.enter.prevent="runRAGQuery"
              clearable
            />
            <el-button type="primary" @click="runRAGQuery" :loading="ragLoading" :disabled="!ragQuery.trim()">
              <el-icon><Promotion /></el-icon> 问答
            </el-button>
          </div>
        </div>

        <div class="rag-body" v-if="ragResults.length > 0 || ragAnswer">
          <div class="rag-chunks-panel" v-if="ragResults.length > 0">
            <div class="rag-panel-header">
              <h4>检索到的参考资料 ({{ ragResults.length }})</h4>
            </div>
            <div class="rag-chunks-list">
              <div v-for="(r, i) in ragResults" :key="i" class="rag-chunk-card glass-card">
                <div class="rag-chunk-header">
                  <span class="rag-rank">#{{ i + 1 }}</span>
                  <span class="rag-source">{{ r.knowledge_name }}</span>
                  <el-tag size="small" :type="r.score >= 0.8 ? 'success' : r.score >= 0.5 ? 'warning' : 'danger'">
                    {{ (r.score * 100).toFixed(1) }}%
                  </el-tag>
                  <el-tag v-if="r.chunk_type && r.chunk_type !== 'text'" size="small" type="info">{{ r.chunk_type }}</el-tag>
                  <el-tag v-if="r.page_idx != null" size="small" type="info">P{{ r.page_idx + 1 }}</el-tag>
                </div>
                <p class="rag-chunk-text">{{ r.content }}</p>
                <div v-if="r.content_path" class="rag-chunk-image">
                  <el-image :src="'/mineru-output/' + r.content_path.split('mineru_output/').pop()" fit="contain" style="max-height: 200px" :preview-src-list="['/mineru-output/' + r.content_path.split('mineru_output/').pop()]" />
                </div>
              </div>
            </div>
          </div>

          <div class="rag-answer-panel" v-if="ragAnswer || ragStreaming">
            <div class="rag-panel-header">
              <h4>AI 分析结果</h4>
              <el-tag v-if="ragStreaming" type="warning" size="small">
                <el-icon class="is-loading"><Loading /></el-icon> 生成中...
              </el-tag>
            </div>
            <div class="rag-answer-body" v-html="renderMarkdown(ragAnswer)"></div>
          </div>
        </div>

        <div class="recall-empty" v-else>
          <el-icon :size="40"><ChatDotRound /></el-icon>
          <p>输入问题进行知识库问答，检索到的参考片段将先展示，再由AI分析输出最终结果</p>
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

      <el-dialog v-model="showGroupDialog" :title="editingGroup ? '编辑知识库' : '新建知识库'" width="420">
        <el-form :model="groupForm" label-position="top">
          <el-form-item label="名称" required>
            <el-input v-model="groupForm.name" placeholder="输入知识库名称" />
          </el-form-item>
          <el-form-item label="描述">
            <el-input v-model="groupForm.description" type="textarea" :rows="2" placeholder="可选描述" />
          </el-form-item>
          <el-form-item label="颜色">
            <el-color-picker v-model="groupForm.color" />
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="showGroupDialog = false">取消</el-button>
          <el-button type="primary" @click="saveGroup" :loading="savingGroup">保存</el-button>
        </template>
      </el-dialog>

      <el-drawer
        v-model="showChunkDrawer"
        :title="`切片信息 - ${currentChunkFile?.name || ''}`"
        size="520px"
        direction="rtl"
      >
        <div class="chunk-drawer-content" v-loading="chunkLoading">
          <div class="chunk-summary">
            <el-tag type="info">共 {{ currentChunks.length }} 个切片</el-tag>
          </div>
          <div v-if="currentChunks.length === 0 && !chunkLoading" class="chunk-empty">
            <p>暂无切片数据，请先索引文件</p>
          </div>
          <div v-for="(chunk, i) in currentChunks" :key="i" class="chunk-card">
            <div class="chunk-card-header">
              <span class="chunk-index">#{{ chunk.chunk_index }}</span>
              <span class="chunk-chars">{{ chunk.char_count }} 字符</span>
              <el-button
                text
                size="small"
                @click="toggleChunkExpand(i)"
                class="chunk-expand-btn"
              >
                {{ expandedChunks.has(i) ? '收起' : '展开' }}
              </el-button>
            </div>
            <div class="chunk-text" :class="{ collapsed: !expandedChunks.has(i) }">
              {{ chunk.content }}
            </div>
          </div>
        </div>
      </el-drawer>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Loading } from '@element-plus/icons-vue'
import { marked } from 'marked'
import api from '../api'

const tabs = [
  { key: 'files', label: '文件列表', icon: 'FolderOpened' },
  { key: 'settings', label: '设置', icon: 'Setting' },
  { key: 'recall', label: '召回测试', icon: 'DataAnalysis' },
  { key: 'rag', label: '知识问答', icon: 'ChatDotRound' },
]

const activeTab = ref('files')
const activeGroupId = ref(null)
const groups = ref([])
const files = ref([])
const searchQuery = ref('')
const searchResults = ref([])
const uploading = ref(false)

const showGroupDialog = ref(false)
const editingGroup = ref(null)
const savingGroup = ref(false)
const groupForm = ref({ name: '', description: '', color: '#6366f1' })

const showFileEditDialog = ref(false)
const editingFile = ref(null)
const fileForm = ref({ name: '', description: '' })

const embeddingModels = ref([])
const savingSettings = ref(false)
const settingsForm = ref({
  embedding_model_id: null,
  enable_rerank: false,
  rerank_model_id: null,
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

const embeddingModelList = computed(() => embeddingModels.value.filter(m => m.model_type === 'embedding'))
const rerankModelList = computed(() => embeddingModels.value.filter(m => m.model_type === 'rerank'))

const totalFileCount = computed(() => groups.value.reduce((sum, g) => sum + (g.file_count || 0), 0))
const currentGroupName = computed(() => {
  const g = groups.value.find(g => g.id === activeGroupId.value)
  return g ? g.name : ''
})

const recallQuery = ref('')
const recallLoading = ref(false)
const recallResults = ref([])
const recallTested = ref(false)
const recallTopK = ref(5)

const isDragging = ref(false)
const fileInputRef = ref(null)
const showChunkDrawer = ref(false)
const currentChunkFile = ref(null)
const currentChunks = ref([])
const chunkLoading = ref(false)
const expandedChunks = ref(new Set())

const ragQuery = ref('')
const ragLoading = ref(false)
const ragResults = ref([])
const ragAnswer = ref('')
const ragStreaming = ref(false)

function selectGroup(groupId) {
  activeGroupId.value = groupId
  searchResults.value = []
  searchQuery.value = ''
  recallResults.value = []
  recallTested.value = false
  loadFiles()
  if (activeTab.value === 'settings') loadSettings()
}

const silentHeaders = { 'X-Silent-Error': '1' }

async function loadGroups() {
  try { groups.value = await api.get('/knowledge/groups', { headers: silentHeaders }) } catch (e) {
    ElMessage.error('加载知识库列表失败：' + (e.response?.data?.detail || e.message || '未知错误'))
  }
}

async function loadFiles() {
  try {
    const params = activeGroupId.value ? `?group_id=${activeGroupId.value}` : ''
    files.value = await api.get(`/knowledge/files${params}`, { headers: silentHeaders })
  } catch (e) {
    ElMessage.error('加载文件列表失败：' + (e.response?.data?.detail || e.message || '未知错误'))
  }
}

async function loadSettings() {
  try {
    const params = activeGroupId.value ? `?group_id=${activeGroupId.value}` : ''
    const data = await api.get(`/knowledge/settings${params}`, { headers: silentHeaders })
    settingsForm.value = {
      embedding_model_id: data.embedding_model_id,
      enable_rerank: data.enable_rerank || false,
      rerank_model_id: data.rerank_model_id,
      chunk_method: data.chunk_method || 'auto',
      chunk_size: data.chunk_size || 500,
      chunk_overlap: data.chunk_overlap || 50,
      retrieval_method: data.retrieval_method || 'pure',
      retrieval_top_k: data.retrieval_top_k || 5,
      score_threshold: data.score_threshold || '0.5',
    }
    recallTopK.value = data.retrieval_top_k || 5
  } catch (e) {
    ElMessage.error('加载设置失败：' + (e.response?.data?.detail || e.message || '未知错误'))
  }
}

async function loadEmbeddingModels() {
  try { embeddingModels.value = await api.get('/knowledge/embedding-models', { headers: silentHeaders }) } catch (e) {
    ElMessage.error('加载嵌入模型失败：' + (e.response?.data?.detail || e.message || '未知错误'))
  }
}

async function saveSettings() {
  savingSettings.value = true
  try {
    const payload = { ...settingsForm.value }
    if (activeGroupId.value) payload.group_id = activeGroupId.value
    await api.put('/knowledge/settings', payload, { headers: silentHeaders })
    ElMessage.success('设置已保存')
  } catch (e) {
    ElMessage.error('保存设置失败：' + (e.response?.data?.detail || e.message || '未知错误'))
  }
  finally { savingSettings.value = false }
}

function openGroupDialog(group = null) {
  editingGroup.value = group
  groupForm.value = group
    ? { name: group.name, description: group.description, color: group.color || '#6366f1' }
    : { name: '', description: '', color: '#6366f1' }
  showGroupDialog.value = true
}

async function saveGroup() {
  if (!groupForm.value.name.trim()) {
    ElMessage.warning('请输入知识库名称')
    return
  }
  savingGroup.value = true
  try {
    if (editingGroup.value) {
      await api.put(`/knowledge/groups/${editingGroup.value.id}`, groupForm.value, { headers: silentHeaders })
      ElMessage.success('更新成功')
    } else {
      await api.post('/knowledge/groups', groupForm.value, { headers: silentHeaders })
      ElMessage.success('创建成功')
    }
    showGroupDialog.value = false
    loadGroups()
  } catch (e) {
    ElMessage.error('操作失败：' + (e.response?.data?.detail || e.message || '未知错误'))
  }
  finally { savingGroup.value = false }
}

async function deleteGroup(group) {
  try {
    await ElMessageBox.confirm(
      `确定删除知识库「${group.name}」？文件将保留但移出该知识库。`,
      '提示',
      { type: 'warning' }
    )
    await api.delete(`/knowledge/groups/${group.id}`, { headers: silentHeaders })
    ElMessage.success('已删除')
    if (activeGroupId.value === group.id) selectGroup(null)
    else loadGroups()
  } catch (e) {
    if (e !== 'cancel' && e !== 'close') {
      ElMessage.error('删除失败：' + (e.response?.data?.detail || e.message || '未知错误'))
    }
  }
}

function openGroupContextMenu(e, group) {
  ElMessageBox({
    title: group.name,
    message: '请选择操作',
    showCancelButton: true,
    confirmButtonText: '编辑',
    cancelButtonText: '删除',
    distinguishCancelAndClose: true,
    type: 'info',
  })
    .then(() => openGroupDialog(group))
    .catch((action) => {
      if (action === 'cancel') deleteGroup(group)
    })
}

async function uploadSingleFile(file) {
  const fd = new FormData()
  fd.append('file', file)
  const params = activeGroupId.value ? `?group_id=${activeGroupId.value}` : ''
  return await api.post(`/knowledge/files/upload${params}`, fd, {
    headers: { 'Content-Type': 'multipart/form-data', ...silentHeaders },
    timeout: 300000,
  })
}

async function handleUpload(options) {
  uploading.value = true
  try {
    const result = await uploadSingleFile(options.file)
    if (result.extract_error) {
      ElMessage.error(`文件已上传，但文本提取失败：${result.extract_error}`)
    } else if (result.indexing_error) {
      ElMessage.warning(`文件已上传，但索引失败：${result.indexing_error}`)
    } else if (result.indexed) {
      ElMessage.success(`上传并索引成功，共 ${result.chunk_count} 个切片`)
    } else {
      ElMessage.warning('文件已上传，但未能提取到文本内容')
    }
    loadFiles()
    loadGroups()
  } catch (e) {
    ElMessage.error('上传失败：' + (e.response?.data?.detail || e.message || '未知错误'))
  }
  finally { uploading.value = false }
}

async function handleBatchUpload(fileList) {
  if (!fileList || fileList.length === 0) return
  uploading.value = true
  let successCount = 0
  let failCount = 0
  let indexFailCount = 0
  for (const file of fileList) {
    try {
      const result = await uploadSingleFile(file)
      if (result.indexing_error || !result.indexed) {
        indexFailCount++
      }
      successCount++
    } catch {
      failCount++
    }
  }
  uploading.value = false
  if (successCount > 0) {
    let msg = `上传完成：${successCount} 成功`
    if (indexFailCount > 0) msg += `（${indexFailCount} 个文件索引失败）`
    if (failCount > 0) msg += `，${failCount} 失败`
    if (indexFailCount > 0) {
      ElMessage.warning(msg)
    } else {
      ElMessage.success(msg)
    }
    loadFiles()
    loadGroups()
  } else {
    ElMessage.error('全部上传失败')
  }
}

function onDragOver() {
  isDragging.value = true
}

function onDragLeave() {
  isDragging.value = false
}

function onDrop(e) {
  isDragging.value = false
  if (uploading.value) return
  const droppedFiles = e.dataTransfer?.files
  if (droppedFiles && droppedFiles.length > 0) {
    handleBatchUpload(Array.from(droppedFiles))
  }
}

function triggerUpload() {
  fileInputRef.value?.click()
}

function onFileInputChange(e) {
  const selectedFiles = e.target.files
  if (selectedFiles && selectedFiles.length > 0) {
    handleBatchUpload(Array.from(selectedFiles))
    e.target.value = ''
  }
}

async function openChunkDrawer(file) {
  currentChunkFile.value = file
  currentChunks.value = []
  expandedChunks.value = new Set()
  showChunkDrawer.value = true
  chunkLoading.value = true
  try {
    const data = await api.get(`/knowledge/files/${file.id}/chunks`, { headers: silentHeaders })
    currentChunks.value = data.chunks || []
  } catch (e) {
    ElMessage.error('加载切片信息失败：' + (e.response?.data?.detail || e.message || '未知错误'))
  } finally {
    chunkLoading.value = false
  }
}

function toggleChunkExpand(index) {
  const s = new Set(expandedChunks.value)
  if (s.has(index)) s.delete(index)
  else s.add(index)
  expandedChunks.value = s
}

function openFileEditDialog(file) {
  editingFile.value = file
  fileForm.value = { name: file.name, description: file.description }
  showFileEditDialog.value = true
}

async function saveFile() {
  try {
    await api.put(`/knowledge/files/${editingFile.value.id}`, fileForm.value, { headers: silentHeaders })
    ElMessage.success('保存成功')
    showFileEditDialog.value = false
    loadFiles()
  } catch (e) {
    ElMessage.error('保存失败：' + (e.response?.data?.detail || e.message || '未知错误'))
  }
}

async function reindexFile(id) {
  try {
    const res = await api.post(`/knowledge/files/${id}/reindex`, null, { timeout: 300000, headers: silentHeaders })
    if (res.message === 'No content to index') {
      ElMessage.warning('重新索引失败：文件无文本内容')
    } else {
      ElMessage.success(`重新索引完成，共 ${res.chunks || 0} 个切片`)
    }
    loadFiles()
  } catch (e) {
    ElMessage.error('重新索引失败：' + (e.response?.data?.detail || e.message || '未知错误'))
  }
}

async function deleteFile(id) {
  try {
    await ElMessageBox.confirm('确定删除此文件？关联的分块索引也将被删除。', '提示', { type: 'warning' })
    await api.delete(`/knowledge/files/${id}`, { headers: silentHeaders })
    ElMessage.success('已删除')
    loadFiles()
    loadGroups()
  } catch (e) {
    if (e !== 'cancel' && e !== 'close') {
      ElMessage.error('删除失败：' + (e.response?.data?.detail || e.message || '未知错误'))
    }
  }
}

async function doSearch() {
  if (!searchQuery.value.trim()) return
  try {
    const payload = { query: searchQuery.value, top_k: 10 }
    if (activeGroupId.value) payload.group_id = activeGroupId.value
    searchResults.value = await api.post('/knowledge/search', payload, { timeout: 120000, headers: silentHeaders })
    if (searchResults.value.length === 0) ElMessage.info('未找到相关结果')
  } catch (e) {
    ElMessage.error('搜索失败：' + (e.response?.data?.detail || e.message || '未知错误'))
  }
}

async function runRecallTest() {
  if (!recallQuery.value.trim()) return
  recallLoading.value = true
  recallTested.value = true
  try {
    const payload = { query: recallQuery.value, top_k: recallTopK.value }
    if (activeGroupId.value) payload.group_id = activeGroupId.value
    recallResults.value = await api.post('/knowledge/recall-test', payload, { timeout: 120000, headers: silentHeaders })
    if (recallResults.value.length === 0) ElMessage.info('未找到相关结果')
  } catch (e) {
    ElMessage.error('召回测试失败：' + (e.response?.data?.detail || e.message || '未知错误'))
  }
  finally { recallLoading.value = false }
}

async function runRAGQuery() {
  if (!ragQuery.value.trim()) return
  ragLoading.value = true
  ragResults.value = []
  ragAnswer.value = ''
  ragStreaming.value = false

  const token = localStorage.getItem('token')
  const params = new URLSearchParams()
  if (activeGroupId.value) params.set('group_id', activeGroupId.value)

  try {
    const response = await fetch(`/api/knowledge/rag/answer-stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify({
        query: ragQuery.value,
        group_id: activeGroupId.value,
        top_k: 5,
      }),
    })

    if (!response.ok) {
      const err = await response.json()
      throw new Error(err.detail || '请求失败')
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        if (!line.startsWith('data: ')) continue
        try {
          const data = JSON.parse(line.slice(6))
          if (data.type === 'search_results') {
            ragResults.value = data.results || []
          } else if (data.type === 'chunk') {
            ragStreaming.value = true
            ragAnswer.value += data.content
          } else if (data.type === 'done') {
            ragStreaming.value = false
          } else if (data.type === 'error') {
            ElMessage.error(data.message || 'AI生成失败')
          }
        } catch (e) {
          // ignore parse errors
        }
      }
    }
  } catch (e) {
    ElMessage.error('知识问答失败：' + (e.message || '未知错误'))
  } finally {
    ragLoading.value = false
    ragStreaming.value = false
  }
}

function renderMarkdown(text) {
  if (!text) return ''
  return marked.parse(text, { breaks: true })
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
  const map = { md: '#2563eb', txt: '#0ea5e9', py: '#10b981', js: '#f59e0b', json: '#06b6d4', csv: '#ef4444', html: '#f97316', css: '#3b82f6', pdf: '#dc2626', doc: '#2563eb', docx: '#2563eb', xls: '#16a34a', xlsx: '#16a34a' }
  return `linear-gradient(135deg, ${map[ext] || '#64748b'}, ${map[ext] || '#64748b'}88)`
}

onMounted(() => { loadGroups(); loadFiles(); loadSettings(); loadEmbeddingModels() })

watch(activeTab, (tab) => {
  if (tab === 'settings') loadSettings()
})
</script>

<style scoped lang="scss">
.knowledge-layout {
  display: flex;
  height: 100%;
  overflow: hidden;
}

.knowledge-sidebar {
  width: 220px;
  flex-shrink: 0;
  border-right: 1px solid var(--border-color);
  background: var(--bg-card);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 16px 12px;
  flex-shrink: 0;
}

.sidebar-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
}

.sidebar-list {
  flex: 1;
  overflow-y: auto;
  padding: 0 8px 12px;
}

.sidebar-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 13px;
  color: var(--text-secondary);
  transition: var(--transition);
  margin-bottom: 2px;

  &:hover {
    background: rgba(37, 99, 235, 0.06);
    color: var(--text-primary);
  }

  &.active {
    background: rgba(37, 99, 235, 0.1);
    color: var(--primary);
    font-weight: 500;
  }

  .el-icon {
    font-size: 16px;
    flex-shrink: 0;
  }
}

.sidebar-item-name {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.sidebar-item-count {
  font-size: 11px;
  color: var(--text-muted);
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 10px;
  padding: 1px 7px;
  flex-shrink: 0;
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
  transition: background 0.2s;

  &.drag-active {
    background: rgba(37, 99, 235, 0.04);
    outline: 2px dashed var(--primary);
    outline-offset: -8px;
  }
}

.settings-hint {
  margin-bottom: 16px;
}

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

  :deep(.el-table) {
    --el-table-border-color: var(--border-color);

    th.el-table__cell {
      background: var(--bg-card) !important;
      font-size: 13px;
      font-weight: 600;
      color: var(--text-secondary);
      border-bottom: 1px solid var(--border-color);
    }

    td.el-table__cell {
      border-bottom: 1px solid var(--border-color);
    }
  }

  :deep(.el-table__row) {
    td .cell {
      display: flex;
      align-items: center;
    }
  }
}

.file-info {
  display: flex;
  align-items: center;
  gap: 10px;

  .file-icon {
    width: 28px;
    height: 28px;
    border-radius: 6px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 9px;
    font-weight: 700;
    color: white;
    flex-shrink: 0;
  }

  .file-detail {
    display: flex;
    flex-direction: column;
    overflow: hidden;
    .file-name { font-size: 13px; font-weight: 500; color: var(--text-primary); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 180px; }
    .file-desc { font-size: 11px; color: var(--text-muted); }
  }
}

.chunk-tag {
  cursor: pointer;
  &:hover { opacity: 0.8; }
}

.action-btn {
  padding: 4px 6px !important;
  color: var(--primary) !important;
  .el-icon {
    color: var(--primary) !important;
    font-size: 16px !important;
  }
  &:hover {
    background: rgba(37, 99, 235, 0.08) !important;
  }
}

.action-btn-danger {
  color: var(--el-color-danger, #f56c6c) !important;
  .el-icon {
    color: var(--el-color-danger, #f56c6c) !important;
  }
  &:hover {
    background: rgba(245, 108, 108, 0.08) !important;
  }
}

.drop-zone {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 400px;
  border: 2px dashed var(--border-color);
  border-radius: 16px;
  cursor: pointer;
  transition: all 0.25s;

  &:hover {
    border-color: var(--primary);
    background: rgba(37, 99, 235, 0.03);
  }
}

.drop-zone-loading {
  text-align: center;
  color: var(--primary);

  h3 {
    font-size: 16px;
    margin-top: 16px;
    color: var(--text-secondary);
  }
}

.drop-zone-content {
  text-align: center;
  color: var(--text-muted);

  .drop-icon {
    color: var(--primary);
    opacity: 0.5;
    margin-bottom: 12px;
  }

  h3 {
    font-size: 16px;
    color: var(--text-secondary);
    font-weight: 600;
    margin: 0 0 8px;
  }

  p {
    font-size: 13px;
    margin: 4px 0;
  }

  .drop-hint {
    font-size: 12px;
    opacity: 0.6;
    margin-top: 12px;
  }
}

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

.rerank-hint {
  margin-top: 4px;
  p {
    font-size: 12px;
    color: var(--text-muted);
    line-height: 1.6;
    padding: 8px 12px;
    background: rgba(37, 99, 235, 0.04);
    border-radius: 6px;
  }
}

.settings-footer {
  padding-top: 8px;
}

.recall-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.recall-scope {
  margin-bottom: 4px;
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

.chunk-drawer-content {
  padding: 0 4px;
}

.chunk-summary {
  margin-bottom: 16px;
}

.chunk-empty {
  text-align: center;
  padding: 40px;
  color: var(--text-muted);
}

.chunk-card {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 10px;
  padding: 14px;
  margin-bottom: 10px;
  transition: var(--transition);

  &:hover { border-color: var(--primary); }
}

.chunk-card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;

  .chunk-index {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-width: 32px;
    height: 24px;
    border-radius: 6px;
    background: var(--primary);
    color: white;
    font-size: 12px;
    font-weight: 700;
    padding: 0 6px;
  }

  .chunk-chars {
    font-size: 12px;
    color: var(--text-muted);
  }

  .chunk-expand-btn {
    margin-left: auto;
    color: var(--primary);
  }
}

.chunk-text {
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.7;
  white-space: pre-wrap;
  word-break: break-all;
  background: rgba(37, 99, 235, 0.03);
  border-radius: 8px;
  padding: 10px;

  &.collapsed {
    max-height: 100px;
    overflow: hidden;
    position: relative;

    &::after {
      content: '';
      position: absolute;
      bottom: 0;
      left: 0;
      right: 0;
      height: 40px;
      background: linear-gradient(transparent, rgba(255,255,255,0.9));
    }
  }
}

.rag-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.rag-input-area {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 20px;
  box-shadow: var(--shadow-card);
  flex-shrink: 0;
}

.rag-body {
  display: flex;
  gap: 20px;
  min-height: 0;
  flex: 1;
}

.rag-chunks-panel {
  width: 45%;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
}

.rag-answer-panel {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.rag-panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  h4 { color: var(--primary); font-size: 15px; }
}

.rag-chunks-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  overflow-y: auto;
  max-height: 600px;
}

.rag-chunk-card {
  padding: 14px;
  transition: var(--transition);
  &:hover { border-color: var(--primary); }
}

.rag-chunk-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;

  .rag-rank {
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

  .rag-source {
    font-weight: 600;
    font-size: 13px;
    color: var(--text-primary);
    flex: 1;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
}

.rag-chunk-text {
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.7;
  background: rgba(37, 99, 235, 0.03);
  border-radius: 8px;
  padding: 10px;
  white-space: pre-wrap;
  word-break: break-all;
  max-height: 120px;
  overflow: hidden;
}

.rag-chunk-image {
  margin-top: 8px;
  text-align: center;
}

.rag-answer-body {
  flex: 1;
  font-size: 14px;
  line-height: 1.8;
  color: var(--text-primary);
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 20px;
  box-shadow: var(--shadow-card);
  overflow-y: auto;
  max-height: 600px;

  :deep(h1), :deep(h2), :deep(h3), :deep(h4) {
    color: var(--text-primary);
    margin: 16px 0 8px;
  }

  :deep(p) {
    margin: 8px 0;
  }

  :deep(code) {
    background: rgba(37, 99, 235, 0.06);
    padding: 2px 6px;
    border-radius: 4px;
    font-size: 13px;
  }

  :deep(pre) {
    background: rgba(0, 0, 0, 0.04);
    padding: 12px;
    border-radius: 8px;
    overflow-x: auto;
    margin: 8px 0;
  }

  :deep(pre code) {
    background: none;
    padding: 0;
  }

  :deep(ol), :deep(ul) {
    padding-left: 20px;
  }

  :deep(blockquote) {
    border-left: 3px solid var(--primary);
    padding-left: 12px;
    color: var(--text-secondary);
    margin: 8px 0;
  }
}
</style>
