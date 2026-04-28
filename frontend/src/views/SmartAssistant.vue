<template>
  <div class="chat-page">
    <div class="chat-sidebar" :class="{ collapsed: sidebarCollapsed }">
      <div class="sidebar-header">
        <div v-if="!sidebarCollapsed" class="new-chat-btn" @click="newSession">
          <el-icon :size="16"><Plus /></el-icon>
          <span>新对话</span>
        </div>
        <div class="icon-action" :title="sidebarCollapsed ? '展开' : '收起'" @click="sidebarCollapsed = !sidebarCollapsed">
          <el-icon :size="14">
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
          <div class="session-dot"></div>
          <span class="session-text">{{ s.last_message || '新对话' }}</span>
          <el-icon class="delete-icon" @click.stop="deleteSession(s.session_id)"><Close /></el-icon>
        </div>
        <div v-if="sessions.length === 0" class="no-sessions">
          <el-icon :size="28" style="opacity:.4"><ChatDotRound /></el-icon>
          <span>暂无对话记录</span>
        </div>
      </div>
    </div>

    <div class="chat-main">
      <div class="chat-toolbar">
        <div class="toolbar-left">
          <div class="toolbar-logo">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
              <rect x="3" y="3" width="18" height="18" rx="5" fill="url(#salg)"/>
              <path d="M12 7v2M12 13v2M8 11h2M14 11h2" stroke="white" stroke-width="1.8" stroke-linecap="round"/>
              <circle cx="12" cy="12" r="3" stroke="white" stroke-width="1.5" fill="none"/>
              <defs><linearGradient id="salg" x1="3" y1="3" x2="24" y2="24"><stop stop-color="#8b5cf6"/><stop offset="1" stop-color="#6366f1"/></linearGradient></defs>
            </svg>
          </div>
          <span class="toolbar-title">智能助手</span>
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
          <div class="empty-illustration">
            <svg viewBox="0 0 160 160" fill="none" width="140" height="140">
              <circle cx="80" cy="80" r="70" fill="url(#saeg)" opacity="0.12"/>
              <circle cx="80" cy="80" r="50" fill="url(#saeg)" opacity="0.08"/>
              <rect x="45" y="45" width="70" height="70" rx="16" fill="url(#saeg)" opacity="0.15"/>
              <circle cx="80" cy="80" r="12" stroke="#8b5cf6" stroke-width="3" fill="none" opacity="0.6"/>
              <path d="M80 68v4M80 88v4M68 80h4M88 80h4" stroke="#8b5cf6" stroke-width="2.5" stroke-linecap="round" opacity="0.5"/>
              <circle cx="30" cy="40" r="3" fill="#8b5cf6" opacity="0.3"/>
              <circle cx="135" cy="50" r="2.5" fill="#6366f1" opacity="0.3"/>
              <circle cx="25" cy="120" r="2" fill="#8b5cf6" opacity="0.3"/>
              <circle cx="140" cy="125" r="3.5" fill="#6366f1" opacity="0.2"/>
              <defs><linearGradient id="saeg" x1="0" y1="0" x2="160" y2="160"><stop stop-color="#8b5cf6"/><stop offset="1" stop-color="#6366f1"/></linearGradient></defs>
            </svg>
          </div>
          <h3>智能助手</h3>
          <p>我是您的智能助手，有什么可以帮您？</p>
        </div>

        <div v-for="(msg, i) in messages" :key="i" :class="['message', msg.role]">
          <div class="message-avatar">
            <div v-if="msg.role === 'user'" class="avatar-circle user-avatar">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none">
                <circle cx="12" cy="8" r="4" stroke="white" stroke-width="2"/>
                <path d="M4 20c0-4 3.6-7 8-7s8 3 8 7" stroke="white" stroke-width="2" stroke-linecap="round"/>
              </svg>
            </div>
            <div v-else class="avatar-circle ai-avatar">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
                <rect x="3" y="3" width="18" height="18" rx="5" stroke="white" stroke-width="1.8" fill="none"/>
                <circle cx="12" cy="12" r="3" stroke="white" stroke-width="1.5" fill="none"/>
                <path d="M12 8v2M12 14v2M8 12h2M14 12h2" stroke="white" stroke-width="1.2" stroke-linecap="round"/>
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
            <div class="avatar-circle ai-avatar">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
                <rect x="3" y="3" width="18" height="18" rx="5" stroke="white" stroke-width="1.8" fill="none"/>
                <circle cx="12" cy="12" r="3" stroke="white" stroke-width="1.5" fill="none"/>
                <path d="M12 8v2M12 14v2M8 12h2M14 12h2" stroke="white" stroke-width="1.2" stroke-linecap="round"/>
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
        <div class="input-container">
          <div class="input-wrapper">
            <el-input
              v-model="inputText"
              type="textarea"
              :rows="2"
              placeholder="输入您的问题，按 Enter 发送..."
              resize="none"
              @keydown.enter.exact.prevent="sendMessage"
            />
          </div>
          <el-button
            type="primary"
            class="send-btn"
            :disabled="!inputText.trim() || isLoading"
            @click="sendMessage"
          >
            <el-icon :size="18"><Promotion /></el-icon>
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, watch } from 'vue'
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
const selectedModelId = ref(localStorage.getItem('chat_selected_model_smart_assistant') ? Number(localStorage.getItem('chat_selected_model_smart_assistant')) : null)
const availableModels = ref([])
const providers = ref([])

watch(selectedModelId, (val) => {
  if (val) {
    localStorage.setItem('chat_selected_model_smart_assistant', val)
  } else {
    localStorage.removeItem('chat_selected_model_smart_assistant')
  }
})

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
    sessions.value = all.filter(s => s.agent_type === 'smart_assistant')
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
      agent_type: 'smart_assistant',
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
  background: #f1f4f9;
}

.chat-sidebar {
  width: 280px;
  background: var(--bg-card);
  border-right: 1px solid var(--border-color);
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
  padding: 14px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.new-chat-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 7px;
  flex: 1;
  padding: 9px 0;
  border-radius: 10px;
  cursor: pointer;
  font-size: 13px;
  font-weight: 600;
  color: white;
  background: linear-gradient(135deg, #8b5cf6, #6366f1);
  box-shadow: 0 2px 8px rgba(139, 92, 246, 0.25);
  transition: var(--transition);

  &:hover {
    box-shadow: 0 4px 14px rgba(139, 92, 246, 0.35);
    transform: translateY(-1px);
  }

  &:active { transform: translateY(0); }
}

.icon-action {
  width: 34px;
  height: 34px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  cursor: pointer;
  color: #60a5fa;
  flex-shrink: 0;
  transition: var(--transition);

  &:hover {
    color: #8b5cf6;
    background: rgba(139, 92, 246, 0.06);
  }
}

.session-list {
  flex: 1;
  overflow-y: auto;
  padding: 10px;
}

.session-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 11px 14px;
  border-radius: 10px;
  cursor: pointer;
  transition: var(--transition);
  margin-bottom: 2px;

  &:hover {
    background: var(--bg-card-hover);
    .delete-icon { opacity: 1; }
  }

  &.active {
    background: rgba(139, 92, 246, 0.07);
    .session-text { color: #8b5cf6; font-weight: 600; }
    .session-dot { background: #8b5cf6; }
    .delete-icon { color: var(--text-muted); &:hover { color: var(--danger); } }
  }

  .session-dot {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: var(--border-color);
    flex-shrink: 0;
    transition: var(--transition);
  }

  .session-text {
    font-size: 13px;
    color: var(--text-secondary);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    flex: 1;
    transition: var(--transition);
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
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 40px 12px;
  font-size: 13px;
  color: var(--text-muted);
}

.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-width: 0;
  background: var(--bg-card);
}

.chat-toolbar {
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  border-bottom: 1px solid var(--border-color);
  background: var(--bg-card);
  flex-shrink: 0;
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.toolbar-logo {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
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

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 32px 0;
  background: linear-gradient(180deg, #f6f8fb 0%, #f1f4f9 100%);
}

.empty-chat {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  gap: 16px;

  .empty-illustration { opacity: 0.85; margin-bottom: 4px; }

  h3 { font-size: 22px; color: var(--text-primary); font-weight: 700; }
  p { color: var(--text-secondary); font-size: 15px; margin-top: -4px; }
}

.message {
  display: flex;
  gap: 12px;
  margin-bottom: 24px;
  padding: 0 40px;
  animation: slideUp 0.3s ease;

  &.user {
    flex-direction: row-reverse;
    .message-bubble {
      background: #f0ecfb;
      color: var(--text-primary);
      border: 1px solid #e8e2f5;
      border-radius: 20px 20px 4px 20px;
    }
  }

  &.assistant {
    .message-bubble {
      background: var(--bg-card);
      border: 1px solid var(--border-color);
      border-radius: 20px 20px 20px 4px;
      box-shadow: 0 1px 4px rgba(139, 92, 246, 0.05);
    }
  }
}

@keyframes slideUp {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.message-avatar { flex-shrink: 0; }

.avatar-circle {
  width: 26px;
  height: 26px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.user-avatar {
  background: linear-gradient(135deg, #8b5cf6, #6366f1);
  box-shadow: 0 2px 8px rgba(139, 92, 246, 0.25);
}

.ai-avatar {
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  box-shadow: 0 2px 8px rgba(99, 102, 241, 0.2);
}

.message-content { max-width: 68%; }

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
    width: 30px;
    height: 30px;
    border-radius: 8px;
    cursor: pointer;
    color: var(--text-muted);
    background: var(--bg-card);
    border: 1px solid var(--border-color);
    transition: var(--transition);

    &:hover {
      color: #8b5cf6;
      border-color: #8b5cf6;
      background: rgba(139, 92, 246, 0.04);
    }

    .el-icon { font-size: 14px; }
  }
}

.message:hover .message-actions { opacity: 1; }

.message-bubble {
  padding: 5px 8px;
  font-size: 14px;
  line-height: 1.75;

  :deep(p) { margin: 0 0 8px; &:last-child { margin: 0; } }
  :deep(ul), :deep(ol) { padding-left: 20px; margin: 4px 0; }
  :deep(li) { margin-bottom: 2px; }
  :deep(code) {
    background: rgba(139, 92, 246, 0.08);
    padding: 2px 6px;
    border-radius: 4px;
    font-size: 13px;
    color: #7c3aed;
  }
  :deep(pre) {
    background: #1e293b;
    border-radius: 10px;
    padding: 16px 18px;
    overflow-x: auto;
    margin: 10px 0;

    code {
      background: none;
      color: #e2e8f0;
      padding: 0;
      font-size: 13px;
      line-height: 1.6;
    }
  }
  :deep(blockquote) {
    border-left: 3px solid #8b5cf6;
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
    th { background: rgba(139, 92, 246, 0.04); font-weight: 600; }
  }
}

.message.user .message-bubble {
  :deep(pre) { background: #e4e9f0; }
  :deep(code) { background: rgba(139, 92, 246, 0.08); color: #7c3aed; }
}

.message-bubble.typing {
  display: flex;
  gap: 6px;
  padding: 18px 22px;

  .dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: linear-gradient(135deg, #8b5cf6, #6366f1);
    animation: typing 1.4s ease-in-out infinite;

    &:nth-child(2) { animation-delay: 0.2s; }
    &:nth-child(3) { animation-delay: 0.4s; }
  }
}

@keyframes typing {
  0%, 60%, 100% { transform: translateY(0); opacity: 0.3; }
  30% { transform: translateY(-8px); opacity: 1; }
}

.chat-input-area {
  padding: 16px 24px 20px;
  background: var(--bg-card);
  border-top: 0.5px solid var(--border-color);
}

.input-container {
  max-width: 800px;
  margin: 0 auto;
  display: flex;
  gap: 12px;
  align-items: flex-end;
}

.input-wrapper {
  flex: 1;

  :deep(.el-textarea__inner) {
    background: #f0f5ff !important;
    border: 0.5px solid #dbe4f3 !important;
    border-radius: 14px !important;
    padding: 13px 18px;
    color: var(--text-primary) !important;
    font-size: 14px;
    line-height: 1.5;

    &:focus {
      border-color: #8b5cf6 !important;
      box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.1) !important;
    }
  }
}

.send-btn {
  width: 48px;
  height: 48px;
  border-radius: 14px;
  flex-shrink: 0;
  font-size: 18px;
  background: linear-gradient(135deg, #8b5cf6, #6366f1) !important;
  border: none !important;
  transition: all 0.25s ease !important;
  box-shadow: 0 2px 8px rgba(139, 92, 246, 0.25);

  &:hover {
    box-shadow: 0 4px 16px rgba(139, 92, 246, 0.4) !important;
    transform: translateY(-1px);
  }

  &:active { transform: translateY(0); }

  &.is-disabled {
    opacity: 0.5;
    box-shadow: none !important;
    transform: none !important;
  }
}
</style>
