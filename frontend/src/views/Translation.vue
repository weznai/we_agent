<template>
  <div class="chat-page">
    <div class="chat-sidebar translate-sidebar">
      <div class="sidebar-header">
        <h3>翻译设置</h3>
      </div>
      <div class="sidebar-body">
        <el-form label-position="top" size="default">
          <el-form-item label="源语言">
            <el-select v-model="sourceLang" style="width: 100%">
              <el-option label="自动检测" value="auto" />
              <el-option label="中文" value="zh" />
              <el-option label="英文" value="en" />
              <el-option label="日文" value="ja" />
              <el-option label="韩文" value="ko" />
              <el-option label="法文" value="fr" />
              <el-option label="德文" value="de" />
              <el-option label="西班牙文" value="es" />
            </el-select>
          </el-form-item>
          <el-form-item label="目标语言">
            <el-select v-model="targetLang" style="width: 100%">
              <el-option label="英文" value="en" />
              <el-option label="中文" value="zh" />
              <el-option label="日文" value="ja" />
              <el-option label="韩文" value="ko" />
              <el-option label="法文" value="fr" />
              <el-option label="德文" value="de" />
              <el-option label="西班牙文" value="es" />
            </el-select>
          </el-form-item>
        </el-form>

        <div class="history-section">
          <h4>翻译历史</h4>
          <div class="session-list">
            <div
              v-for="s in sessions"
              :key="s.session_id"
              class="session-item"
              :class="{ active: currentSession === s.session_id }"
              @click="switchSession(s.session_id)"
            >
              <el-icon><Document /></el-icon>
              <span class="session-text">{{ s.last_message || '翻译记录' }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="chat-main">
      <div class="translate-container">
        <div class="translate-panels">
          <div class="panel source-panel">
            <div class="panel-header">
              <span>输入文本</span>
              <el-button text size="small" @click="sourceText = ''">
                <el-icon><Delete /></el-icon> 清空
              </el-button>
            </div>
            <el-input
              v-model="sourceText"
              type="textarea"
              :rows="12"
              placeholder="输入需要翻译的文本..."
              resize="none"
            />
            <div class="panel-footer">
              <span class="char-count">{{ sourceText.length }} 字符</span>
              <el-button type="primary" :loading="isTranslating" @click="translate">
                <el-icon><Promotion /></el-icon> 翻译
              </el-button>
            </div>
          </div>

          <div class="panel-arrow">
            <el-icon :size="24"><Right /></el-icon>
          </div>

          <div class="panel target-panel">
            <div class="panel-header">
              <span>翻译结果</span>
              <el-button text size="small" @click="copyResult">
                <el-icon><CopyDocument /></el-icon> 复制
              </el-button>
            </div>
            <div class="result-area">
              <div v-if="resultText" class="result-text" v-html="renderMarkdown(resultText)"></div>
              <div v-else class="empty-result">
                <el-icon :size="40"><Document /></el-icon>
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
.chat-page {
  display: flex;
  height: 100%;
  overflow: hidden;
}

.translate-sidebar {
  width: 260px;
  border-right: 1px solid var(--border-color);
  background: var(--bg-card);
  display: flex;
  flex-direction: column;
  flex-shrink: 0;

  .sidebar-header {
    padding: 16px;
    border-bottom: 1px solid var(--border-color);
    h3 { color: var(--text-primary); font-size: 16px; }
  }

  .sidebar-body {
    padding: 16px;
    flex: 1;
    overflow-y: auto;
  }

  .history-section {
    margin-top: 24px;

    h4 {
      font-size: 13px;
      color: var(--text-secondary);
      margin-bottom: 8px;
    }
  }
}

.session-list {
  max-height: 200px;
  overflow-y: auto;
}

.session-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: var(--transition);
  margin-bottom: 4px;
  font-size: 13px;
  color: var(--text-secondary);

  &:hover { background: var(--bg-card-hover); }
  &.active { background: var(--gradient-primary); color: white; }
}

.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.translate-container {
  flex: 1;
  padding: 24px;
  overflow-y: auto;
}

.translate-panels {
  display: flex;
  gap: 24px;
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
  overflow: hidden;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border-color);
  font-weight: 600;
  font-size: 14px;
  color: var(--text-secondary);
}

.source-panel {
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

.panel-arrow {
  display: flex;
  align-items: center;
  color: var(--text-muted);
}

.target-panel {
  .result-area {
    flex: 1;
    padding: 20px;
    min-height: 300px;
    overflow-y: auto;
  }

  .result-text {
    font-size: 15px;
    line-height: 1.8;
    color: var(--text-primary);
  }

  .empty-result {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 100%;
    gap: 8px;
    color: var(--text-muted);
  }
}
</style>
