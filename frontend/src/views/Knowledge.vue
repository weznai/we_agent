<template>
  <div class="knowledge-layout">
    <div class="group-sidebar">
      <div class="sidebar-top">
        <h3>知识库分组</h3>
        <el-button text size="small" @click="openGroupDialog()">
          <el-icon><Plus /></el-icon>
        </el-button>
      </div>

      <div
        class="group-item"
        :class="{ active: currentGroupId === null }"
        @click="currentGroupId = null"
      >
        <el-icon><FolderOpened /></el-icon>
        <span class="group-name">全部文件</span>
        <span class="group-count">{{ totalCount }}</span>
      </div>

      <div
        v-for="g in groups"
        :key="g.id"
        class="group-item"
        :class="{ active: currentGroupId === g.id }"
        @click="currentGroupId = g.id"
      >
        <el-icon><Folder /></el-icon>
        <span class="group-name">{{ g.name }}</span>
        <span class="group-count">{{ g.file_count }}</span>
        <el-dropdown trigger="click" @command="(cmd) => handleGroupCmd(cmd, g)" @click.stop>
          <el-icon class="group-more" @click.stop><MoreFilled /></el-icon>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="edit">编辑</el-dropdown-item>
              <el-dropdown-item command="delete" divided>删除</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>

      <div class="sidebar-bottom">
        <div class="search-box">
          <el-input v-model="searchQuery" placeholder="搜索知识库..." :prefix-icon="Search" @keyup.enter="doSearch" />
        </div>
      </div>
    </div>

    <div class="file-area">
      <div class="file-header">
        <h2>{{ currentGroupName }}</h2>
        <div class="header-actions">
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
              <el-button text size="small" @click="moveFile(row)"><el-icon><Rank /></el-icon></el-button>
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

      <el-dialog v-model="showGroupDialog" :title="editingGroup ? '编辑分组' : '新建分组'" width="450">
        <el-form :model="groupForm" label-position="top">
          <el-form-item label="分组名称">
            <el-input v-model="groupForm.name" placeholder="如：技术文档、产品手册" />
          </el-form-item>
          <el-form-item label="描述">
            <el-input v-model="groupForm.description" type="textarea" :rows="2" />
          </el-form-item>
          <el-form-item label="颜色">
            <el-color-picker v-model="groupForm.color" />
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="showGroupDialog = false">取消</el-button>
          <el-button type="primary" @click="saveGroup">保存</el-button>
        </template>
      </el-dialog>

      <el-dialog v-model="showFileEditDialog" title="编辑文件" width="450">
        <el-form :model="fileForm" label-position="top">
          <el-form-item label="文件名">
            <el-input v-model="fileForm.name" />
          </el-form-item>
          <el-form-item label="描述">
            <el-input v-model="fileForm.description" type="textarea" :rows="2" />
          </el-form-item>
          <el-form-item label="所属分组">
            <el-select v-model="fileForm.group_id" placeholder="选择分组" clearable style="width: 100%">
              <el-option label="无分组" :value="null" />
              <el-option v-for="g in groups" :key="g.id" :label="g.name" :value="g.id" />
            </el-select>
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="showFileEditDialog = false">取消</el-button>
          <el-button type="primary" @click="saveFile">保存</el-button>
        </template>
      </el-dialog>

      <el-dialog v-model="showMoveDialog" title="移动到分组" width="400">
        <el-select v-model="moveTargetGroupId" placeholder="选择目标分组" clearable style="width: 100%">
          <el-option label="无分组" :value="null" />
          <el-option v-for="g in groups" :key="g.id" :label="g.name" :value="g.id" />
        </el-select>
        <template #footer>
          <el-button @click="showMoveDialog = false">取消</el-button>
          <el-button type="primary" @click="confirmMove">移动</el-button>
        </template>
      </el-dialog>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search } from '@element-plus/icons-vue'
import api from '../api'

const groups = ref([])
const files = ref([])
const currentGroupId = ref(null)
const searchQuery = ref('')
const searchResults = ref([])
const uploading = ref(false)
const totalCount = ref(0)

const showGroupDialog = ref(false)
const editingGroup = ref(null)
const groupForm = ref({ name: '', description: '', color: '#2563eb' })

const showFileEditDialog = ref(false)
const editingFile = ref(null)
const fileForm = ref({ name: '', description: '', group_id: null })

const showMoveDialog = ref(false)
const movingFileId = ref(null)
const moveTargetGroupId = ref(null)

const currentGroupName = computed(() => {
  if (currentGroupId.value === null) return '全部文件'
  const g = groups.value.find(g => g.id === currentGroupId.value)
  return g ? g.name : '全部文件'
})

async function loadGroups() {
  try { groups.value = await api.get('/knowledge/groups') } catch {}
}

async function loadFiles() {
  try {
    const config = {}
    if (currentGroupId.value !== null) config.params = { group_id: currentGroupId.value }
    files.value = await api.get('/knowledge/files', config)
  } catch {}
}

async function loadAllCount() {
  try {
    const all = await api.get('/knowledge/files')
    totalCount.value = all.length
  } catch {}
}

watch(currentGroupId, loadFiles)

function handleGroupCmd(cmd, group) {
  if (cmd === 'edit') {
    editingGroup.value = group
    groupForm.value = { name: group.name, description: group.description, color: group.color }
    showGroupDialog.value = true
  } else if (cmd === 'delete') {
    ElMessageBox.confirm(`确定删除分组「${group.name}」？文件不会被删除。`, '提示', { type: 'warning' })
      .then(async () => {
        await api.delete(`/knowledge/groups/${group.id}`)
        ElMessage.success('分组已删除')
        if (currentGroupId.value === group.id) currentGroupId.value = null
        loadGroups()
        loadFiles()
      }).catch(() => {})
  }
}

function openGroupDialog() {
  editingGroup.value = null
  groupForm.value = { name: '', description: '', color: '#2563eb' }
  showGroupDialog.value = true
}

async function saveGroup() {
  if (!groupForm.value.name) { ElMessage.warning('请输入分组名称'); return }
  if (editingGroup.value) {
    await api.put(`/knowledge/groups/${editingGroup.value.id}`, groupForm.value)
  } else {
    await api.post('/knowledge/groups', groupForm.value)
  }
  ElMessage.success('保存成功')
  showGroupDialog.value = false
  loadGroups()
}

async function handleUpload(options) {
  const fd = new FormData()
  fd.append('file', options.file)
  if (currentGroupId.value) fd.append('group_id', currentGroupId.value)
  uploading.value = true
  try {
    await api.post('/knowledge/files/upload', fd, {
      headers: { 'Content-Type': 'multipart/form-data' },
      params: currentGroupId.value ? { group_id: currentGroupId.value } : {},
    })
    ElMessage.success('上传并索引成功')
    loadFiles()
    loadGroups()
    loadAllCount()
  } catch { ElMessage.error('上传失败') }
  finally { uploading.value = false }
}

function openFileEditDialog(file) {
  editingFile.value = file
  fileForm.value = { name: file.name, description: file.description, group_id: file.group_id }
  showFileEditDialog.value = true
}

async function saveFile() {
  await api.put(`/knowledge/files/${editingFile.value.id}`, fileForm.value)
  ElMessage.success('保存成功')
  showFileEditDialog.value = false
  loadFiles()
  loadGroups()
}

function moveFile(file) {
  movingFileId.value = file.id
  moveTargetGroupId.value = file.group_id
  showMoveDialog.value = true
}

async function confirmMove() {
  await api.put(`/knowledge/files/${movingFileId.value}`, { group_id: moveTargetGroupId.value })
  ElMessage.success('已移动')
  showMoveDialog.value = false
  loadFiles()
  loadGroups()
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
  loadGroups()
  loadAllCount()
}

async function doSearch() {
  if (!searchQuery.value.trim()) return
  try {
    const params = { query: searchQuery.value, top_k: 10 }
    if (currentGroupId.value) params.group_id = currentGroupId.value
    searchResults.value = await api.post('/knowledge/search', params)
    if (searchResults.value.length === 0) ElMessage.info('未找到相关结果')
  } catch { ElMessage.error('搜索失败') }
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

onMounted(() => { loadGroups(); loadFiles(); loadAllCount() })
</script>

<style scoped lang="scss">
.knowledge-layout {
  display: flex;
  height: 100%;
  overflow: hidden;
}

.group-sidebar {
  width: 240px;
  background: var(--bg-card);
  border-right: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}

.sidebar-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  border-bottom: 1px solid var(--border-color);

  h3 {
    font-size: 14px;
    font-weight: 600;
    color: var(--text-primary);
  }
}

.group-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  cursor: pointer;
  transition: var(--transition);
  font-size: 13px;
  color: var(--text-secondary);
  position: relative;

  &:hover { background: var(--bg-card-hover); }
  &.active {
    background: var(--gradient-primary);
    color: white;
    .el-icon, .group-count, .group-more { color: white; }
  }

  .el-icon { font-size: 16px; flex-shrink: 0; }
  .group-name { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .group-count {
    font-size: 11px;
    background: rgba(255,255,255,0.15);
    padding: 1px 6px;
    border-radius: 8px;
    color: var(--text-muted);
  }
  .group-more {
    font-size: 14px;
    opacity: 0;
    transition: var(--transition);
    &:hover { color: var(--primary); }
  }
  &:hover .group-more { opacity: 1; }
  &.active:hover .group-more { color: white; }
}

.sidebar-bottom {
  padding: 12px;
  border-top: 1px solid var(--border-color);
  margin-top: auto;
}

.file-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-width: 0;
}

.file-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  border-bottom: 1px solid var(--border-color);
  flex-shrink: 0;

  h2 {
    font-size: 18px;
    font-weight: 600;
    color: var(--text-primary);
  }

  .header-actions { display: flex; gap: 12px; }
}

.search-results {
  flex: 1;
  overflow-y: auto;
  padding: 16px 24px;

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
  flex: 1;
  overflow-y: auto;
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
</style>
