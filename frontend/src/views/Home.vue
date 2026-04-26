<template>
  <div class="page-container home-page">
    <div class="welcome-section">
      <div class="welcome-bg">
        <div class="bg-circle c1"></div>
        <div class="bg-circle c2"></div>
        <div class="bg-circle c3"></div>
      </div>
      <div class="welcome-text">
        <h1>
          <span class="greeting">{{ greeting }}，</span>
          <span class="name">{{ userStore.nickname }}</span>
        </h1>
        <p class="sub-text">欢迎使用 Super Agent 超级智能体平台，探索 AI 的无限可能</p>
        <div class="welcome-tags">
          <span class="w-tag"><el-icon><MagicStick /></el-icon> 多智能体</span>
          <span class="w-tag"><el-icon><Cpu /></el-icon> 多模型</span>
          <span class="w-tag"><el-icon><ChatDotRound /></el-icon> 多场景</span>
        </div>
      </div>
      <div class="welcome-illustration">
        <svg viewBox="0 0 200 200" fill="none" width="160" height="160">
          <circle cx="100" cy="100" r="90" stroke="rgba(255,255,255,0.2)" stroke-width="2" fill="rgba(255,255,255,0.06)"/>
          <circle cx="100" cy="100" r="70" stroke="rgba(255,255,255,0.15)" stroke-width="1.5" fill="none"/>
          <circle cx="100" cy="100" r="50" stroke="rgba(255,255,255,0.1)" stroke-width="1" fill="none"/>
          <circle cx="100" cy="85" r="20" fill="rgba(255,255,255,0.9)"/>
          <path d="M75 120c0-12 10-20 25-20s25 8 25 20" stroke="rgba(255,255,255,0.9)" stroke-width="2.5" stroke-linecap="round" fill="none"/>
          <circle cx="60" cy="40" r="4" fill="rgba(255,255,255,0.5)"/>
          <circle cx="150" cy="50" r="3" fill="rgba(255,255,255,0.4)"/>
          <circle cx="40" cy="130" r="5" fill="rgba(255,255,255,0.3)"/>
          <circle cx="160" cy="140" r="4" fill="rgba(255,255,255,0.5)"/>
        </svg>
      </div>
    </div>

    <div class="stats-grid">
      <div class="stat-card" style="--accent: #2563eb">
        <div class="stat-accent"></div>
        <div class="stat-top">
          <div>
            <div class="stat-value">{{ stats.agents }}</div>
            <div class="stat-label">智能体</div>
          </div>
          <div class="stat-icon-wrap">
            <el-icon><MagicStick /></el-icon>
          </div>
        </div>
      </div>
      <div class="stat-card" style="--accent: #0ea5e9">
        <div class="stat-accent"></div>
        <div class="stat-top">
          <div>
            <div class="stat-value">{{ stats.models }}</div>
            <div class="stat-label">AI 模型</div>
          </div>
          <div class="stat-icon-wrap">
            <el-icon><Cpu /></el-icon>
          </div>
        </div>
      </div>
      <div class="stat-card" style="--accent: #10b981">
        <div class="stat-accent"></div>
        <div class="stat-top">
          <div>
            <div class="stat-value">{{ stats.knowledge }}</div>
            <div class="stat-label">知识库</div>
          </div>
          <div class="stat-icon-wrap">
            <el-icon><FolderOpened /></el-icon>
          </div>
        </div>
      </div>
      <div class="stat-card" style="--accent: #8b5cf6">
        <div class="stat-accent"></div>
        <div class="stat-top">
          <div>
            <div class="stat-value">{{ stats.chats }}</div>
            <div class="stat-label">对话数</div>
          </div>
          <div class="stat-icon-wrap">
            <el-icon><ChatDotRound /></el-icon>
          </div>
        </div>
      </div>
    </div>

    <div class="quick-actions">
      <h3>快速开始</h3>
      <div class="action-grid">
        <router-link to="/chat" class="action-card">
          <div class="action-icon-wrap" style="--card-accent: #2563eb">
            <div class="action-icon-bg"></div>
            <el-icon class="action-icon-el"><ChatDotRound /></el-icon>
          </div>
          <div class="action-info">
            <h4>智能聊天</h4>
            <p>与 AI 进行自然语言对话</p>
          </div>
          <el-icon class="action-arrow"><ArrowRight /></el-icon>
        </router-link>

        <router-link to="/translation" class="action-card">
          <div class="action-icon-wrap" style="--card-accent: #06b6d4">
            <div class="action-icon-bg"></div>
            <el-icon class="action-icon-el"><Document /></el-icon>
          </div>
          <div class="action-info">
            <h4>智能翻译</h4>
            <p>多语言实时翻译服务</p>
          </div>
          <el-icon class="action-arrow"><ArrowRight /></el-icon>
        </router-link>

        <router-link to="/knowledge" class="action-card">
          <div class="action-icon-wrap" style="--card-accent: #10b981">
            <div class="action-icon-bg"></div>
            <el-icon class="action-icon-el"><FolderOpened /></el-icon>
          </div>
          <div class="action-info">
            <h4>知识库</h4>
            <p>管理您的知识文档</p>
          </div>
          <el-icon class="action-arrow"><ArrowRight /></el-icon>
        </router-link>

        <router-link v-if="userStore.isSuperUser" to="/providers" class="action-card">
          <div class="action-icon-wrap" style="--card-accent: #f59e0b">
            <div class="action-icon-bg"></div>
            <el-icon class="action-icon-el"><Setting /></el-icon>
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

// ===== Welcome =====
.welcome-section {
  position: relative;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 40px 36px;
  background: linear-gradient(135deg, #2563eb 0%, #0ea5e9 60%, #06b6d4 100%);
  border-radius: 16px;
  margin-bottom: 24px;
  overflow: hidden;
  box-shadow: 0 4px 20px rgba(37, 99, 235, 0.25);
}

.welcome-bg {
  position: absolute;
  inset: 0;
  pointer-events: none;

  .bg-circle {
    position: absolute;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.06);
  }
  .c1 { width: 300px; height: 300px; top: -80px; right: -40px; }
  .c2 { width: 200px; height: 200px; bottom: -60px; left: 10%; }
  .c3 { width: 120px; height: 120px; top: 20px; left: 40%; background: rgba(255, 255, 255, 0.04); }
}

.welcome-text {
  position: relative;
  z-index: 1;

  h1 {
    font-size: 28px;
    font-weight: 700;
    margin-bottom: 10px;
    color: #ffffff;

    .greeting { opacity: 0.85; }
    .name { color: #ffffff; }
  }

  .sub-text {
    color: rgba(255, 255, 255, 0.8);
    font-size: 15px;
    margin-bottom: 18px;
  }
}

.welcome-tags {
  display: flex;
  gap: 10px;

  .w-tag {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    padding: 5px 14px;
    border-radius: 20px;
    background: rgba(255, 255, 255, 0.15);
    backdrop-filter: blur(4px);
    color: rgba(255, 255, 255, 0.9);
    font-size: 12px;
    font-weight: 500;

    .el-icon { font-size: 13px; }
  }
}

.welcome-illustration {
  position: relative;
  z-index: 1;
  opacity: 0.9;
}

// ===== Stats =====
.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 28px;
}

.stat-card {
  position: relative;
  padding: 24px;
  border-radius: var(--radius-lg);
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  box-shadow: var(--shadow-card);
  transition: var(--transition);
  overflow: hidden;

  &:hover {
    transform: translateY(-3px);
    box-shadow: 0 6px 24px rgba(37, 99, 235, 0.12);
    border-color: var(--accent);
  }

  .stat-accent {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 3px;
    background: var(--accent);
    border-radius: 3px 3px 0 0;
    opacity: 0.8;
    transition: opacity 0.25s;
  }

  &:hover .stat-accent {
    opacity: 1;
  }

  .stat-top {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .stat-value {
    font-size: 32px;
    font-weight: 700;
    color: var(--accent);
  }

  .stat-label {
    font-size: 13px;
    color: var(--text-secondary);
    margin-top: 2px;
  }

  .stat-icon-wrap {
    width: 48px;
    height: 48px;
    border-radius: 12px;
    background: color-mix(in srgb, var(--accent) 10%, transparent);
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;

    .el-icon {
      font-size: 22px;
      color: var(--accent);
    }
  }
}

// ===== Quick Actions =====
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
  padding: 22px 24px;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-card);
  text-decoration: none;
  transition: var(--transition);

  &:hover {
    border-color: var(--card-accent, var(--primary));
    box-shadow: 0 4px 16px rgba(37, 99, 235, 0.1);
    transform: translateY(-2px);

    .action-arrow {
      transform: translateX(4px);
      color: var(--card-accent, var(--primary));
    }

    .action-icon-bg {
      transform: scale(1.08);
    }
  }
}

.action-icon-wrap {
  position: relative;
  width: 52px;
  height: 52px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;

  .action-icon-bg {
    position: absolute;
    inset: 0;
    border-radius: 14px;
    background: var(--card-accent);
    opacity: 0.1;
    transition: var(--transition);
  }

  .action-icon-el {
    position: relative;
    font-size: 24px;
    color: var(--card-accent);
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
</style>
