<template>
  <div class="page-layout">
    <div class="translate-sidebar">
      <div class="sidebar-header">
        <div class="sidebar-logo">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
            <rect x="3" y="3" width="18" height="18" rx="5" fill="url(#slg)"/>
            <path d="M7 10h3M10 7v3M13 14h4M14 17h2" stroke="white" stroke-width="1.8" stroke-linecap="round"/>
            <defs><linearGradient id="slg" x1="3" y1="3" x2="24" y2="24"><stop stop-color="#06b6d4"/><stop offset="1" stop-color="#3b82f6"/></linearGradient></defs>
          </svg>
        </div>
        <span class="sidebar-title">翻译设置</span>
      </div>
      <div class="sidebar-body">
        <div class="setting-group">
          <div class="setting-label">源语言</div>
          <el-select v-model="sourceLang" style="width: 100%" size="default">
            <el-option label="自动检测" value="auto" />
            <el-option label="中文" value="zh" />
            <el-option label="英文" value="en" />
            <el-option label="日文" value="ja" />
            <el-option label="韩文" value="ko" />
            <el-option label="法文" value="fr" />
            <el-option label="德文" value="de" />
            <el-option label="西班牙文" value="es" />
          </el-select>
        </div>
        <div class="lang-swap" @click="swapLangs">
          <div class="swap-line"></div>
          <div class="swap-icon-wrap">
            <el-icon :size="16"><Sort /></el-icon>
          </div>
          <div class="swap-line"></div>
        </div>
        <div class="setting-group">
          <div class="setting-label">目标语言</div>
          <el-select v-model="targetLang" style="width: 100%" size="default">
            <el-option label="英文" value="en" />
            <el-option label="中文" value="zh" />
            <el-option label="日文" value="ja" />
            <el-option label="韩文" value="ko" />
            <el-option label="法文" value="fr" />
            <el-option label="德文" value="de" />
            <el-option label="西班牙文" value="es" />
          </el-select>
        </div>

        <div class="history-section">
          <div class="history-header">
            <span>翻译历史</span>
            <el-icon :size="14" style="opacity:.5"><Clock /></el-icon>
          </div>
          <div class="session-list">
            <div
              v-for="s in sessions"
              :key="s.session_id"
              class="session-item"
              :class="{ active: currentSession === s.session_id }"
              @click="switchSession(s.session_id)"
            >
              <div class="session-dot"></div>
              <span class="session-text">{{ s.last_message || '翻译记录' }}</span>
            </div>
            <div v-if="sessions.length === 0" class="no-history">暂无翻译历史</div>
          </div>
        </div>
      </div>
    </div>

    <div class="translate-main">
      <div class="panels-container">
        <div class="translate-panels">
          <div class="panel source-panel">
            <div class="panel-header">
              <div class="panel-title">
                <div class="panel-dot source-dot"></div>
                <span>输入文本</span>
              </div>
              <el-button text size="small" class="panel-action" @click="sourceText = ''">
                <el-icon><Delete /></el-icon> 清空
              </el-button>
            </div>
            <div class="panel-body source-body">
              <el-input
                v-model="sourceText"
                type="textarea"
                :rows="14"
                placeholder="输入需要翻译的文本..."
                resize="none"
              />
            </div>
            <div class="panel-footer">
              <span class="char-count">{{ sourceText.length }} 字符</span>
              <el-button type="primary" :loading="isTranslating" @click="translate" class="translate-btn">
                <el-icon><Promotion /></el-icon> 翻译
              </el-button>
            </div>
          </div>

          <div class="panel-divider">
            <div class="divider-line"></div>
            <div class="divider-icon">
              <el-icon :size="20"><Right /></el-icon>
            </div>
            <div class="divider-line"></div>
          </div>

          <div class="panel target-panel">
            <div class="panel-header">
              <div class="panel-title">
                <div class="panel-dot target-dot"></div>
                <span>翻译结果</span>
              </div>
              <el-button text size="small" class="panel-action" @click="copyResult">
                <el-icon><CopyDocument /></el-icon> 复制
              </el-button>
            </div>
            <div class="panel-body result-body">
              <div v-if="resultText" class="result-text" v-html="renderMarkdown(resultText)"></div>
              <div v-else class="empty-result">
                <svg viewBox="0 0 80 80" fill="none" width="64" height="64">
                  <circle cx="40" cy="40" r="35" fill="url(#erg)" opacity="0.1"/>
                  <path d="M25 35h30M25 45h20" stroke="url(#erg)" stroke-width="2" stroke-linecap="round" opacity="0.25"/>
                  <defs><linearGradient id="erg" x1="0" y1="0" x2="80" y2="80"><stop stop-color="#06b6d4"/><stop offset="1" stop-color="#3b82f6"/></linearGradient></defs>
                </svg>
                <p>翻译结果将在这里显示</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '../api'
import { marked } from 'marked'

const sourceText = ref('')
const resultText = ref('')
const sourceLang = ref('auto')
const targetLang = ref('en')
const isTranslating = ref(false)
const sessions = ref([])
const currentSession = ref('')

function renderMarkdown(text) {
  return marked(text || '')
}

function swapLangs() {
  if (sourceLang.value === 'auto') return
  const tmp = sourceLang.value
  sourceLang.value = targetLang.value
  targetLang.value = tmp
}

async function translate() {
  if (!sourceText.value.trim()) {
    ElMessage.warning('请输入需要翻译的文本')
    return
  }

  isTranslating.value = true
  resultText.value = ''
  try {
    const prompt = `请将以下文本翻译为${getLangName(targetLang.value)}，只返回翻译结果：\n\n${sourceText.value}`
    if (!currentSession.value) {
      const data = await api.post('/chat/sessions/new')
      currentSession.value = data.session_id
    }

    const token = localStorage.getItem('token')
    const response = await fetch('/api/chat/message/stream', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify({
        session_id: currentSession.value,
        content: prompt,
        agent_type: 'translation',
      }),
    })

    if (!response.ok) {
      const err = await response.json()
      throw new Error(err.detail || '翻译失败')
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
        if (line.startsWith('data: ')) {
          const data = JSON.parse(line.slice(6))
          if (data.error) {
            resultText.value += data.error
          } else if (data.done) {
            await loadSessions()
          } else if (data.content) {
            resultText.value += data.content
          }
        }
      }
    }
  } catch (e) {
    ElMessage.error(e.message || '翻译失败，请重试')
  } finally {
    isTranslating.value = false
  }
}

function getLangName(code) {
  const map = { zh: '中文', en: '英文', ja: '日文', ko: '韩文', fr: '法文', de: '德文', es: '西班牙文' }
  return map[code] || code
}

async function loadSessions() {
  try {
    const all = await api.get('/chat/sessions')
    sessions.value = all.filter(s => s.agent_type === 'translation')
  } catch {}
}

async function switchSession(sessionId) {
  currentSession.value = sessionId
  const history = await api.get(`/chat/history/${sessionId}`)
  const userMessages = history.filter(m => m.role === 'user')
  const assistantMessages = history.filter(m => m.role === 'assistant')
  if (userMessages.length > 0) {
    const raw = userMessages[userMessages.length - 1].content
    const match = raw.match(/：\n\n([\s\S]+)$/)
    sourceText.value = match ? match[1] : raw
  }
  if (assistantMessages.length > 0) {
    resultText.value = assistantMessages[assistantMessages.length - 1].content
  }
}

function copyResult() {
  navigator.clipboard.writeText(resultText.value)
  ElMessage.success('已复制到剪贴板')
}

onMounted(() => {
  loadSessions()
})
</script>

<style scoped lang="scss">
.page-layout {
  display: flex;
  height: 100%;
  overflow: hidden;
  background: #f1f4f9;
}

// ===== Sidebar =====
.translate-sidebar {
  width: 260px;
  background: var(--bg-card);
  border-right: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}

.sidebar-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 16px;
  border-bottom: 1px solid var(--border-color);
}

.sidebar-logo {
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.sidebar-title {
  font-size: 16px;
  font-weight: 700;
  color: var(--text-primary);
}

.sidebar-body {
  padding: 20px 16px;
  flex: 1;
  overflow-y: auto;
}

.setting-group {
  margin-bottom: 4px;
}

.setting-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary);
  margin-bottom: 8px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.lang-swap {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 0;
  cursor: pointer;

  .swap-line {
    flex: 1;
    height: 1px;
    background: var(--border-color);
  }

  .swap-icon-wrap {
    width: 28px;
    height: 28px;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #06b6d4;
    background: rgba(6, 182, 212, 0.08);
    transition: var(--transition);

    &:hover {
      background: rgba(6, 182, 212, 0.15);
    }
  }
}

.history-section {
  margin-top: 24px;
  padding-top: 20px;
  border-top: 1px solid var(--border-color);
}

.history-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary);
  margin-bottom: 10px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.session-list {
  max-height: 200px;
  overflow-y: auto;
}

.session-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 9px 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: var(--transition);
  margin-bottom: 2px;

  &:hover { background: var(--bg-card-hover); }

  &.active {
    background: rgba(6, 182, 212, 0.08);
    .session-text { color: #06b6d4; font-weight: 600; }
    .session-dot { background: #06b6d4; }
  }

  .session-dot {
    width: 6px;
    height: 6px;
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
}

.no-history {
  text-align: center;
  padding: 20px 0;
  font-size: 13px;
  color: var(--text-muted);
}

// ===== Main =====
.translate-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: var(--bg-card);
}

.panels-container {
  flex: 1;
  padding: 28px;
  overflow-y: auto;
}

.translate-panels {
  display: flex;
  gap: 0;
  align-items: stretch;
  height: 100%;
  max-width: 1200px;
  margin: 0 auto;
}

.panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-card);
  overflow: hidden;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 20px;
  border-bottom: 1px solid var(--border-color);
}

.panel-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  font-size: 14px;
  color: var(--text-primary);
}

.panel-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;

  &.source-dot { background: linear-gradient(135deg, #06b6d4, #3b82f6); }
  &.target-dot { background: linear-gradient(135deg, #3b82f6, #2563eb); }
}

.panel-action {
  color: var(--text-muted) !important;
  font-size: 12px;

  &:hover { color: #06b6d4 !important; }
}

.source-body {
  flex: 1;

  :deep(.el-textarea__inner) {
    border: none !important;
    background: transparent !important;
    padding: 20px;
    font-size: 15px;
    line-height: 1.8;
    height: 100% !important;
    min-height: 300px;
  }
}

.panel-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 20px;
  border-top: 1px solid var(--border-color);

  .char-count {
    font-size: 12px;
    color: var(--text-muted);
  }
}

.translate-btn {
  background: linear-gradient(135deg, #06b6d4, #3b82f6) !important;
  border: none !important;
  border-radius: 10px !important;
  font-weight: 600 !important;
  box-shadow: 0 2px 8px rgba(6, 182, 212, 0.25) !important;

  &:hover {
    box-shadow: 0 4px 14px rgba(6, 182, 212, 0.4) !important;
    transform: translateY(-1px);
  }
}

.panel-divider {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 0 16px;

  .divider-line {
    width: 1px;
    flex: 1;
    background: var(--border-color);
  }

  .divider-icon {
    width: 36px;
    height: 36px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #06b6d4;
    background: rgba(6, 182, 212, 0.08);
    flex-shrink: 0;
  }
}

.result-body {
  flex: 1;
  padding: 20px;
  min-height: 300px;
  overflow-y: auto;
}

.result-text {
  font-size: 15px;
  line-height: 1.8;
  color: var(--text-primary);

  :deep(p) { margin: 0 0 8px; &:last-child { margin: 0; } }
}

.empty-result {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  gap: 12px;

  p {
    font-size: 14px;
    color: var(--text-muted);
  }
}
</style>
