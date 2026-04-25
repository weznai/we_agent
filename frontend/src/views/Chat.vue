<template>
  <div class="chat-page">
    <div class="chat-sidebar" :class="{ collapsed: sidebarCollapsed }">
      <div class="sidebar-header">
        <div v-if="!sidebarCollapsed" class="new-chat-trigger" @click="newSession">
          <span class="circle-plus"><el-icon :size="14"><Plus /></el-icon></span>
          <span class="new-chat-text">新对话</span>
        </div>
        <div class="icon-action" :title="sidebarCollapsed ? '展开' : '收起'" @click="sidebarCollapsed = !sidebarCollapsed">
          <el-icon :size="17">
            <Fold v-if="!sidebarCollapsed" />
            <Expand v-else />
          </el-icon>
        </div>
      </div>
      <div v-if="!sidebarCollapsed" class="session-list">
        <div
          v-for="s in sessions"
          :key="s.session_id"
          class="session-item"
          :class="{ active: currentSession === s.session_id }"
          @click="switchSession(s.session_id)"
        >
          <el-icon><ChatDotRound /></el-icon>
          <span class="session-text">{{ s.last_message || '新对话' }}</span>
          <el-icon class="delete-icon" @click.stop="deleteSession(s.session_id)"><Close /></el-icon>
        </div>
        <div v-if="sessions.length === 0" class="no-sessions">暂无对话记录</div>
      </div>
    </div>

    <div class="chat-main">
      <div class="chat-toolbar">
        <div class="toolbar-left">
          <span class="toolbar-title">智能聊天</span>
        </div>
        <div class="toolbar-right">
          <el-select
            v-model="selectedModelId"
            placeholder="默认模型"
            clearable
            size="default"
            class="model-select"
          >
            <template #prefix>
              <el-icon><Cpu /></el-icon>
            </template>
            <el-option
              v-for="m in availableModels"
              :key="m.id"
              :label="m.display_name || m.name"
              :value="m.id"
            >
              <span class="model-option">
                <span class="model-name">{{ m.display_name || m.name }}</span>
                <span class="model-provider">{{ getProviderName(m.provider_id) }}</span>
              </span>
            </el-option>
          </el-select>
        </div>
      </div>

      <div class="chat-messages" ref="messagesRef">
        <div v-if="messages.length === 0" class="empty-chat">
          <div class="empty-icon">
            <svg viewBox="0 0 100 100" fill="none" width="80" height="80">
              <circle cx="50" cy="50" r="45" stroke="url(#cg)" stroke-width="2" fill="rgba(37,99,235,0.08)"/>
              <path d="M35 58c0-10 7-16 15-16s15 6 15 16" stroke="url(#cg)" stroke-width="2" stroke-linecap="round"/>
              <circle cx="42" cy="42" r="2.5" fill="#3b82f6"/>
              <circle cx="58" cy="42" r="2.5" fill="#3b82f6"/>
              <defs><linearGradient id="cg" x1="0" y1="0" x2="100" y2="100"><stop stop-color="#2563eb"/><stop offset="1" stop-color="#0ea5e9"/></linearGradient></defs>
            </svg>
          </div>
          <h3>开始新的对话</h3>
          <p>向 AI 助手提问任何问题</p>
        </div>

        <div v-for="(msg, i) in messages" :key="i" :class="['message', msg.role]">
          <div class="message-avatar">
            <div v-if="msg.role === 'user'" class="message-icon user-icon">
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
                <circle cx="12" cy="8" r="4" stroke="var(--primary)" stroke-width="2"/>
                <path d="M4 20c0-4 3.6-7 8-7s8 3 8 7" stroke="var(--primary)" stroke-width="2" stroke-linecap="round"/>
              </svg>
            </div>
            <div v-else class="message-icon ai-icon">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                <rect x="3" y="3" width="18" height="18" rx="5" stroke="#2563eb" stroke-width="1.8"/>
                <circle cx="9" cy="10" r="1.8" fill="#2563eb"/>
                <circle cx="15" cy="10" r="1.8" fill="#2563eb"/>
                <path d="M9 15h6" stroke="#2563eb" stroke-width="1.8" stroke-linecap="round"/>
                <path d="M8.5 5.5V3" stroke="#2563eb" stroke-width="1.5" stroke-linecap="round"/>
                <path d="M15.5 5.5V3" stroke="#2563eb" stroke-width="1.5" stroke-linecap="round"/>
              </svg>
            </div>
          </div>
          <div class="message-content">
            <div class="message-bubble" v-html="renderMarkdown(msg.content)"></div>
            <div class="message-actions" v-if="msg.role === 'assistant'">
              <span class="action-btn" @click="copyText(msg.content)" title="复制">
                <el-icon><CopyDocument /></el-icon>
              </span>
            </div>
          </div>
        </div>

        <div v-if="isLoading" class="message assistant">
          <div class="message-avatar">
            <div class="message-icon ai-icon">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                <rect x="3" y="3" width="18" height="18" rx="5" stroke="#2563eb" stroke-width="1.8"/>
                <circle cx="9" cy="10" r="1.8" fill="#2563eb"/>
                <circle cx="15" cy="10" r="1.8" fill="#2563eb"/>
                <path d="M9 15h6" stroke="#2563eb" stroke-width="1.8" stroke-linecap="round"/>
                <path d="M8.5 5.5V3" stroke="#2563eb" stroke-width="1.5" stroke-linecap="round"/>
                <path d="M15.5 5.5V3" stroke="#2563eb" stroke-width="1.5" stroke-linecap="round"/>
              </svg>
            </div>
          </div>
          <div class="message-content">
            <div class="message-bubble typing">
              <span class="dot"></span>
              <span class="dot"></span>
              <span class="dot"></span>
            </div>
          </div>
        </div>
      </div>

      <div class="chat-input-area">
        <div class="input-wrapper">
          <el-input
            v-model="inputText"
            type="textarea"
            :rows="2"
            placeholder="输入消息，按 Enter 发送..."
            resize="none"
            @keydown.enter.exact.prevent="sendMessage"
          />
          <el-button
            type="primary"
            class="send-btn"
            :disabled="!inputText.trim() || isLoading"
            @click="sendMessage"
          >
            <el-icon><Promotion /></el-icon>
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { useUserStore } from '../store/user'
import { ElMessage } from 'element-plus'
import api from '../api'
import { marked } from 'marked'

const userStore = useUserStore()
const messagesRef = ref(null)
const inputText = ref('')
const messages = ref([])
const sessions = ref([])
const currentSession = ref('')
const isLoading = ref(false)
const sidebarCollapsed = ref(false)
const selectedModelId = ref(null)
const availableModels = ref([])
const providers = ref([])

function renderMarkdown(text) {
  return marked(text || '')
}

function copyText(text) {
  navigator.clipboard.writeText(text)
  ElMessage.success('已复制')
}

function getProviderName(providerId) {
  const p = providers.value.find(p => p.id === providerId)
  return p ? (p.display_name || p.name) : ''
}

async function loadModels() {
  try {
    const [allModels, allProviders] = await Promise.all([
      api.get('/models'),
      api.get('/providers'),
    ])
    providers.value = allProviders
    availableModels.value = allModels.filter(m => m.is_active && m.model_type === 'chat')
  } catch {}
}

async function loadSessions() {
  try {
    const all = await api.get('/chat/sessions')
    sessions.value = all.filter(s => s.agent_type === 'chat')
  } catch {}
}

async function newSession() {
  const data = await api.post('/chat/sessions/new')
  currentSession.value = data.session_id
  messages.value = []
}

async function switchSession(sessionId) {
  currentSession.value = sessionId
  const history = await api.get(`/chat/history/${sessionId}`)
  messages.value = history
  await nextTick()
  scrollToBottom()
}

async function sendMessage() {
  if (!inputText.value.trim() || isLoading.value) return

  if (!currentSession.value) {
    await newSession()
  }

  const text = inputText.value
  inputText.value = ''
  messages.value.push({ role: 'user', content: text })
  isLoading.value = true
  await nextTick()
  scrollToBottom()

  try {
    const token = localStorage.getItem('token')
    const body = {
      session_id: currentSession.value,
      content: text,
      agent_type: 'chat',
    }
    if (selectedModelId.value) {
      body.model_id = selectedModelId.value
    }

    const response = await fetch('/api/chat/message/stream', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify(body),
    })

    if (!response.ok) {
      const err = await response.json()
      throw new Error(err.detail || '请求失败')
    }

    const assistantMsg = { role: 'assistant', content: '' }
    messages.value.push(assistantMsg)
    isLoading.value = false

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
        if (line.startsWith('data: ')) {
          const data = JSON.parse(line.slice(6))
          if (data.error) {
            assistantMsg.content += `\n\n[错误] ${data.error}`
          } else if (data.done) {
            await loadSessions()
          } else if (data.content) {
            assistantMsg.content += data.content
          }
        }
      }
      await nextTick()
      scrollToBottom()
    }
  } catch (e) {
    isLoading.value = false
    messages.value.push({ role: 'assistant', content: e.message || '抱歉，发生了错误，请稍后重试。' })
  } finally {
    await nextTick()
    scrollToBottom()
  }
}

async function deleteSession(sessionId) {
  await api.delete(`/chat/sessions/${sessionId}`)
  if (currentSession.value === sessionId) {
    await newSession()
  }
  await loadSessions()
}

function scrollToBottom() {
  if (messagesRef.value) {
    messagesRef.value.scrollTop = messagesRef.value.scrollHeight
  }
}

onMounted(() => {
  loadModels()
  loadSessions()
  newSession()
})
</script>

<style scoped lang="scss">
.chat-page {
  display: flex;
  height: 100%;
  overflow: hidden;
}

// ===== Sidebar =====
.chat-sidebar {
  width: 280px;
  border-right: 1px solid var(--border-color);
  background: var(--bg-sidebar, var(--bg-card));
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  transition: width 0.25s ease;

  &.collapsed {
    width: 60px;

    .sidebar-header {
      flex-direction: column;
      gap: 10px;
      padding: 14px 10px;
    }
  }
}

.sidebar-header {
  padding: 12px 14px;
  border-bottom: 1px solid var(--border-color);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.new-chat-trigger {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 4px 0;
}

.circle-plus {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  border: 1.5px solid var(--primary);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--primary);
  flex-shrink: 0;
}

.new-chat-text {
  font-size: 13px;
  color: var(--text-primary);
  font-weight: 500;
  line-height: 20px;
}

.icon-action {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  cursor: pointer;
  color: var(--text-secondary);
  flex-shrink: 0;
  transition: var(--transition);

  &:hover {
    color: var(--primary);
    background: rgba(37, 99, 235, 0.06);
  }
}

.session-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.session-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 11px 14px;
  border-radius: 10px;
  cursor: pointer;
  transition: var(--transition);
  margin-bottom: 3px;

  &:hover {
    background: var(--bg-card-hover);
    .delete-icon { opacity: 1; }
  }

  &.active {
    background: rgba(37, 99, 235, 0.06);
    color: var(--primary);
    .el-icon { color: var(--primary); }
    .session-text { font-weight: 500; }
    .delete-icon { color: var(--text-muted); &:hover { color: var(--danger); } }
  }

  .el-icon { font-size: 16px; color: var(--text-secondary); }

  .session-text {
    font-size: 13px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    flex: 1;
  }

  .delete-icon {
    font-size: 14px;
    opacity: 0;
    color: var(--text-muted);
    transition: var(--transition);
    flex-shrink: 0;
    &:hover { color: var(--danger); }
  }
}

.no-sessions {
  text-align: center;
  padding: 24px 12px;
  font-size: 13px;
  color: var(--text-muted);
}

// ===== Main =====
.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-width: 0;
}

.chat-toolbar {
  height: 52px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  border-bottom: 1px solid var(--border-color);
  background: var(--bg-topbar, var(--bg-card));
  flex-shrink: 0;
}

.toolbar-title {
  font-size: 16px;
  font-weight: 700;
  color: var(--text-primary);
}

.toolbar-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.model-select {
  width: 220px;

  :deep(.el-input__wrapper) {
    border-radius: 10px !important;
  }
}

.model-option {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;

  .model-name { font-size: 13px; }
  .model-provider {
    font-size: 12px;
    color: var(--text-muted);
    margin-left: 12px;
  }
}

// ===== Messages =====
.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 28px 32px;
  background: var(--bg-dark);
}

.empty-chat {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  gap: 14px;
  opacity: 0.6;

  h3 { font-size: 20px; color: var(--text-primary); font-weight: 600; }
  p { color: var(--text-secondary); font-size: 15px; }
}

.message {
  display: flex;
  gap: 14px;
  margin-bottom: 24px;
  animation: slideUp 0.3s ease;

  &.user {
    flex-direction: row-reverse;
    .message-bubble {
      background: #e8f1fb;
      color: var(--text-primary);
      border: 1px solid #c6daf2;
      border-radius: 18px 18px 4px 18px;
    }
  }

  &.assistant {
    .message-bubble {
      background: var(--bg-card);
      border-radius: 18px 18px 18px 4px;
    }
  }
}

@keyframes slideUp {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.message-avatar { flex-shrink: 0; }

.message-icon {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.user-icon {
  color: var(--primary);
}

.ai-icon {
  color: #2563eb;
}

.message-content { max-width: 70%; }

.message-actions {
  opacity: 0;
  transition: var(--transition);
  margin-top: 6px;
  display: flex;
  gap: 4px;

  .action-btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 28px;
    height: 28px;
    border-radius: 6px;
    cursor: pointer;
    color: var(--text-muted);
    transition: var(--transition);

    &:hover {
      color: var(--primary);
      background: rgba(37, 99, 235, 0.06);
    }

    .el-icon { font-size: 14px; }
  }
}

.message:hover .message-actions { opacity: 1; }

.message-bubble {
  padding: 14px 18px;
  font-size: 15px;
  line-height: 1.75;

  :deep(p) { margin: 0 0 8px; &:last-child { margin: 0; } }
  :deep(ul), :deep(ol) { padding-left: 20px; margin: 4px 0; }
  :deep(li) { margin-bottom: 2px; }
  :deep(code) {
    background: rgba(37, 99, 235, 0.06);
    padding: 2px 6px;
    border-radius: 4px;
    font-size: 13px;
    color: var(--primary-dark);
  }
  :deep(pre) {
    background: #e4e9f0;
    border-radius: 10px;
    padding: 14px 16px;
    overflow-x: auto;
    margin: 10px 0;

    code {
      background: none;
      color: #334155;
      padding: 0;
      font-size: 13px;
      line-height: 1.6;
    }
  }
  :deep(blockquote) {
    border-left: 3px solid var(--primary-light);
    padding-left: 12px;
    margin: 8px 0;
    color: var(--text-secondary);
  }
  :deep(table) {
    border-collapse: collapse;
    width: 100%;
    margin: 8px 0;

    th, td {
      border: 1px solid var(--border-color);
      padding: 6px 12px;
      text-align: left;
      font-size: 13px;
    }
    th { background: rgba(37, 99, 235, 0.04); font-weight: 600; }
  }
}

.message.user .message-bubble {
  :deep(pre) { background: rgba(255,255,255,0.15); }
  :deep(code) { background: rgba(255,255,255,0.2); color: white; }
}

.message-bubble.typing {
  display: flex;
  gap: 6px;
  padding: 18px 22px;

  .dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: var(--primary);
    animation: typing 1.4s ease-in-out infinite;

    &:nth-child(2) { animation-delay: 0.2s; }
    &:nth-child(3) { animation-delay: 0.4s; }
  }
}

@keyframes typing {
  0%, 60%, 100% { transform: translateY(0); opacity: 0.3; }
  30% { transform: translateY(-8px); opacity: 1; }
}

// ===== Input =====
.chat-input-area {
  padding: 18px 48px;
  border-top: 1px solid var(--border-color);
  background: var(--bg-topbar, var(--bg-card));
}

.input-wrapper {
  display: flex;
  gap: 12px;
  align-items: flex-end;
  max-width: 100%;
  margin: 0 auto;

  :deep(.el-textarea) { flex: 1; }

  :deep(.el-textarea__inner) {
    background: #f8f9fb !important;
    border: 1.5px solid #e8ecf1 !important;
    border-radius: 14px !important;
    padding: 13px 18px;
    color: var(--text-primary) !important;
    font-size: 14px;
    line-height: 1.5;

    &:focus {
      border-color: var(--primary) !important;
      box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1) !important;
    }
  }
}

.send-btn {
  width: 48px;
  height: 48px;
  border-radius: 14px;
  flex-shrink: 0;
  font-size: 20px;
  background: var(--gradient-primary) !important;
  border: none !important;
  transition: all 0.25s ease !important;

  &:hover {
    box-shadow: 0 4px 16px rgba(37, 99, 235, 0.3) !important;
    transform: translateY(-1px);
  }
}
</style>
