<template>
  <div class="page-container home-page">
    <div class="welcome-section">
      <div class="welcome-text">
        <h1>
          <span class="greeting">{{ greeting }}，</span>
          <span class="name">{{ userStore.nickname }}</span>
        </h1>
        <p class="sub-text">欢迎使用 Super Agent 超级智能体平台，探索 AI 的无限可能</p>
      </div>
      <div class="welcome-illustration">
        <svg viewBox="0 0 200 200" fill="none" width="180" height="180">
          <circle cx="100" cy="100" r="90" stroke="url(#hg)" stroke-width="2" fill="rgba(37,99,235,0.05)"/>
          <circle cx="100" cy="100" r="70" stroke="url(#hg)" stroke-width="1.5" fill="none" opacity="0.5"/>
          <circle cx="100" cy="100" r="50" stroke="url(#hg)" stroke-width="1" fill="none" opacity="0.3"/>
          <circle cx="100" cy="85" r="20" fill="url(#hg)" opacity="0.8"/>
          <path d="M75 120c0-12 10-20 25-20s25 8 25 20" stroke="url(#hg)" stroke-width="2" stroke-linecap="round" fill="none"/>
          <circle cx="60" cy="40" r="4" fill="#3b82f6" opacity="0.6"/>
          <circle cx="150" cy="50" r="3" fill="#06b6d4" opacity="0.6"/>
          <circle cx="40" cy="130" r="5" fill="#60a5fa" opacity="0.5"/>
          <circle cx="160" cy="140" r="4" fill="#2563eb" opacity="0.6"/>
          <defs><linearGradient id="hg" x1="0" y1="0" x2="200" y2="200"><stop stop-color="#2563eb"/><stop offset="1" stop-color="#0ea5e9"/></linearGradient></defs>
        </svg>
      </div>
    </div>

    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-top">
          <div>
            <div class="stat-value">{{ stats.agents }}</div>
            <div class="stat-label">智能体</div>
          </div>
          <el-icon class="stat-icon"><MagicStick /></el-icon>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-top">
          <div>
            <div class="stat-value">{{ stats.models }}</div>
            <div class="stat-label">AI 模型</div>
          </div>
          <el-icon class="stat-icon"><Cpu /></el-icon>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-top">
          <div>
            <div class="stat-value">{{ stats.knowledge }}</div>
            <div class="stat-label">知识库</div>
          </div>
          <el-icon class="stat-icon"><FolderOpened /></el-icon>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-top">
          <div>
            <div class="stat-value">{{ stats.chats }}</div>
            <div class="stat-label">对话数</div>
          </div>
          <el-icon class="stat-icon"><ChatDotRound /></el-icon>
        </div>
      </div>
    </div>

    <div class="quick-actions">
      <h3>快速开始</h3>
      <div class="action-grid">
        <router-link to="/chat" class="action-card">
          <div class="action-icon" style="background: linear-gradient(135deg, #2563eb, #0ea5e9)">
            <el-icon><ChatDotRound /></el-icon>
          </div>
          <div class="action-info">
            <h4>智能聊天</h4>
            <p>与 AI 进行自然语言对话</p>
          </div>
          <el-icon class="action-arrow"><ArrowRight /></el-icon>
        </router-link>

        <router-link to="/translation" class="action-card">
          <div class="action-icon" style="background: linear-gradient(135deg, #06b6d4, #3b82f6)">
            <el-icon><Document /></el-icon>
          </div>
          <div class="action-info">
            <h4>智能翻译</h4>
            <p>多语言实时翻译服务</p>
          </div>
          <el-icon class="action-arrow"><ArrowRight /></el-icon>
        </router-link>

        <router-link to="/knowledge" class="action-card">
          <div class="action-icon" style="background: linear-gradient(135deg, #10b981, #34d399)">
            <el-icon><FolderOpened /></el-icon>
          </div>
          <div class="action-info">
            <h4>知识库</h4>
            <p>管理您的知识文档</p>
          </div>
          <el-icon class="action-arrow"><ArrowRight /></el-icon>
        </router-link>

        <router-link v-if="userStore.isSuperUser" to="/providers" class="action-card">
          <div class="action-icon" style="background: linear-gradient(135deg, #f59e0b, #f97316)">
            <el-icon><Setting /></el-icon>
          </div>
          <div class="action-info">
            <h4>系统管理</h4>
            <p>配置模型和供应商</p>
          </div>
          <el-icon class="action-arrow"><ArrowRight /></el-icon>
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useUserStore } from '../store/user'
import api from '../api'

const userStore = useUserStore()
const stats = ref({ agents: 2, models: 0, knowledge: 0, chats: 0 })

const greeting = computed(() => {
  const h = new Date().getHours()
  if (h < 6) return '夜深了'
  if (h < 12) return '早上好'
  if (h < 18) return '下午好'
  return '晚上好'
})

onMounted(async () => {
  try {
    const models = await api.get('/models')
    stats.value.models = models.length
  } catch {}
  try {
    const knowledge = await api.get('/knowledge/files')
    stats.value.knowledge = knowledge.length
  } catch {}
  try {
    const sessions = await api.get('/chat/sessions')
    stats.value.chats = sessions.length
  } catch {}
})
</script>

<style scoped lang="scss">
.home-page {
  overflow-y: auto;
}

.welcome-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 32px;
  background: var(--gradient-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  margin-bottom: 24px;
}

.welcome-text {
  h1 {
    font-size: 28px;
    font-weight: 700;
    margin-bottom: 8px;

    .greeting {
      color: var(--text-secondary);
    }

    .name {
      background: var(--gradient-primary);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
    }
  }

  .sub-text {
    color: var(--text-secondary);
    font-size: 15px;
  }
}

.welcome-illustration {
  opacity: 0.8;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 32px;
}

.stat-card {
  padding: 24px;
  border-radius: var(--radius-lg);
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  transition: var(--transition);

  &:hover {
    transform: translateY(-4px);
    box-shadow: var(--shadow-glow);
    border-color: var(--primary);
  }

  .stat-top {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .stat-value {
    font-size: 36px;
    font-weight: 700;
    background: var(--gradient-primary);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }

  .stat-label {
    font-size: 14px;
    color: var(--text-secondary);
    margin-top: 4px;
  }

  .stat-icon {
    font-size: 40px;
    color: var(--primary);
    opacity: 0.6;
  }
}

.quick-actions {
  h3 {
    font-size: 18px;
    font-weight: 600;
    color: var(--text-primary);
    margin-bottom: 16px;
  }
}

.action-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.action-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px 24px;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  text-decoration: none;
  transition: var(--transition);

  &:hover {
    border-color: var(--primary);
    box-shadow: var(--shadow-glow);
    transform: translateY(-2px);

    .action-arrow {
      transform: translateX(4px);
      color: var(--primary);
    }
  }

  .action-icon {
    width: 48px;
    height: 48px;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;

    .el-icon {
      font-size: 24px;
      color: white;
    }
  }

  .action-info {
    flex: 1;

    h4 {
      font-size: 15px;
      font-weight: 600;
      color: var(--text-primary);
      margin-bottom: 4px;
    }

    p {
      font-size: 13px;
      color: var(--text-secondary);
    }
  }

  .action-arrow {
    font-size: 18px;
    color: var(--text-muted);
    transition: var(--transition);
  }
}
</style>
