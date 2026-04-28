<template>
  <div class="layout">
    <div class="sidebar" :class="{ collapsed: isCollapsed }">
      <div class="sidebar-header">
        <div class="logo" v-show="!isCollapsed">
          <div class="logo-icon">
            <svg viewBox="0 0 40 40" fill="none">
              <circle cx="20" cy="20" r="18" stroke="url(#g1)" stroke-width="2.5" fill="rgba(37,99,235,0.1)"/>
              <path d="M14 24c0-4 3-6 6-6s6 2 6 6" stroke="url(#g1)" stroke-width="2" stroke-linecap="round"/>
              <circle cx="16" cy="17" r="1.5" fill="#3b82f6"/>
              <circle cx="24" cy="17" r="1.5" fill="#3b82f6"/>
              <defs><linearGradient id="g1" x1="0" y1="0" x2="40" y2="40"><stop stop-color="#2563eb"/><stop offset="1" stop-color="#0ea5e9"/></linearGradient></defs>
            </svg>
          </div>
          <span class="logo-text">Super Agent</span>
        </div>
        <div class="logo-mini" v-show="isCollapsed">
          <svg viewBox="0 0 40 40" fill="none" width="32" height="32">
            <circle cx="20" cy="20" r="18" stroke="url(#g1)" stroke-width="2.5" fill="rgba(37,99,235,0.1)"/>
            <path d="M14 24c0-4 3-6 6-6s6 2 6 6" stroke="url(#g1)" stroke-width="2" stroke-linecap="round"/>
            <circle cx="16" cy="17" r="1.5" fill="#3b82f6"/>
            <circle cx="24" cy="17" r="1.5" fill="#3b82f6"/>
          </svg>
        </div>
      </div>

      <el-menu
        :default-active="activeMenu"
        :default-openeds="defaultOpeneds"
        :collapse="isCollapsed"
        :collapse-transition="false"
        router
        class="sidebar-menu"
      >
        <el-menu-item index="/">
          <el-icon class="menu-icon-top"><HomeFilled /></el-icon>
          <template #title>首页</template>
        </el-menu-item>

        <el-sub-menu index="agent">
          <template #title>
            <el-icon class="menu-icon-parent"><MagicStick /></el-icon>
            <span>智能体</span>
          </template>
          <el-menu-item index="/chat">
            <el-icon class="menu-icon-child"><ChatDotRound /></el-icon>
            <template #title>智能聊天</template>
          </el-menu-item>
          <el-menu-item index="/smart-assistant">
            <el-icon class="menu-icon-child"><Monitor /></el-icon>
            <template #title>智能助手</template>
          </el-menu-item>
          <el-menu-item index="/translation">
            <el-icon class="menu-icon-child"><Document /></el-icon>
            <template #title>智能翻译</template>
          </el-menu-item>
          <el-menu-item index="/customer-service">
            <el-icon class="menu-icon-child"><Service /></el-icon>
            <template #title>智能客服</template>
          </el-menu-item>
          <el-menu-item index="/smart-measurement">
            <el-icon class="menu-icon-child"><DataAnalysis /></el-icon>
            <template #title>智能测量</template>
          </el-menu-item>
        </el-sub-menu>

        <el-menu-item index="/knowledge">
          <el-icon class="menu-icon-top"><FolderOpened /></el-icon>
          <template #title>知识库</template>
        </el-menu-item>

        <el-sub-menu v-if="userStore.isAdmin" index="system">
          <template #title>
            <el-icon class="menu-icon-parent"><Setting /></el-icon>
            <span>系统管理</span>
          </template>
          <el-menu-item index="/model-config">
            <el-icon class="menu-icon-child"><Cpu /></el-icon>
            <template #title>模型配置</template>
          </el-menu-item>
        </el-sub-menu>

        <el-menu-item v-if="userStore.isSuperUser" index="/users">
          <el-icon class="menu-icon-top"><User /></el-icon>
          <template #title>用户管理</template>
        </el-menu-item>
      </el-menu>
    </div>

    <div class="main-area">
      <header class="topbar">
        <div class="topbar-left">
          <el-icon class="collapse-btn" @click="isCollapsed = !isCollapsed">
            <Expand v-if="isCollapsed" />
            <Fold v-else />
          </el-icon>
          <el-breadcrumb separator="/">
            <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
            <el-breadcrumb-item v-if="$route.name !== 'Home'">{{ $route.meta.title || $route.name }}</el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        <div class="topbar-right">
          <el-dropdown trigger="click" @command="handleCommand">
            <div class="user-avatar">
              <el-avatar :size="36" :src="userStore.user?.avatar || ''">
                {{ userStore.nickname?.charAt(0)?.toUpperCase() }}
              </el-avatar>
              <span class="user-name">{{ userStore.nickname }}</span>
              <el-icon><ArrowDown /></el-icon>
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile">
                  <el-icon><UserFilled /></el-icon>个人中心
                </el-dropdown-item>
                <el-dropdown-item divided command="logout">
                  <el-icon><SwitchButton /></el-icon>退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </header>

      <main class="content-area">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '../store/user'
import { ElMessageBox } from 'element-plus'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const isCollapsed = ref(false)

const activeMenu = computed(() => route.path)
const defaultOpeneds = computed(() => {
  const path = route.path
  if (path.startsWith('/chat') || path.startsWith('/translation') || path.startsWith('/customer-service') || path.startsWith('/smart-assistant') || path.startsWith('/smart-measurement')) return ['agent']
  if (path.startsWith('/model-config')) return ['system']
  return ['agent', 'system']
})

async function handleCommand(cmd) {
  if (cmd === 'profile') {
    router.push('/profile')
  } else if (cmd === 'logout') {
    try {
      await ElMessageBox.confirm('确定要退出登录吗？', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      })
      userStore.logout()
      router.push('/login')
    } catch {}
  }
}
</script>

<style scoped lang="scss">
.layout {
  display: flex;
  height: 100vh;
  overflow: hidden;
}

.sidebar {
  width: 240px;
  background: #ffffff;
  display: flex;
  flex-direction: column;
  transition: width 0.28s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
  flex-shrink: 0;
  border-right: 1px solid #eef2f7;

  &.collapsed {
    width: 64px;
  }
}

.sidebar-header {
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 16px;
  flex-shrink: 0;
  margin-bottom: 4px;
}

.logo {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding-left: 4px;

  .logo-icon {
    width: 32px;
    height: 32px;
    flex-shrink: 0;
  }

  .logo-text {
    font-size: 17px;
    font-weight: 700;
    color: var(--primary);
    letter-spacing: -0.3px;
    white-space: nowrap;
  }
}

.logo-mini {
  display: flex;
  align-items: center;
  justify-content: center;
}

.sidebar-menu {
  flex: 1;
  overflow-y: auto;
  background: transparent !important;
  padding: 4px 12px;

  :deep(.el-sub-menu) {
    margin: 0;
    border-radius: 0;
    background: transparent;
    border: none;
    overflow: visible;
  }

  :deep(.el-sub-menu__title) {
    height: 36px;
    line-height: 36px;
    color: var(--text-secondary);
    font-size: 13px;
    font-weight: 600;
    letter-spacing: 0;
    text-transform: none;
    background: transparent !important;
    padding-left: 20px !important;

    &:hover {
      background: transparent !important;
    color: var(--text-primary);
    }

    .el-icon {
      display: none;
    }

    .el-sub-menu__icon-arrow {
      display: none;
    }
  }

  :deep(.el-sub-menu .el-menu) {
    background: transparent !important;
  }

  :deep(.el-sub-menu .el-menu-item) {
    padding-left: 32px !important;
    margin: 1px 0;
    min-width: auto;
    height: 38px;
    line-height: 38px;
    border-radius: 8px;
    color: var(--text-secondary);
    font-size: 14px;
    background: transparent !important;
    border: none;
    position: relative;
    transition: all 0.2s ease;

    &:hover {
      background: #f0f5ff !important;
      color: var(--primary);
    }

    &.is-active {
      background: #eff6ff !important;
      color: var(--primary) !important;
      font-weight: 500;

      &::before {
        content: '';
        position: absolute;
        left: 0;
        top: 8px;
        bottom: 8px;
        width: 3px;
        border-radius: 0 3px 3px 0;
        background: var(--primary);
      }
    }
  }

  :deep(.el-menu-item:not(.el-sub-menu .el-menu-item)) {
    border-radius: 8px;
    margin: 1px 0;
    height: 38px;
    line-height: 38px;
    color: var(--text-secondary);
    font-size: 14px;
    background: transparent !important;
    border: none;
    position: relative;
    transition: all 0.2s ease;

    &:hover {
      background: #f0f5ff !important;
      color: var(--primary);
    }

    &.is-active {
      background: #eff6ff !important;
      color: var(--primary) !important;
      font-weight: 500;

      &::before {
        content: '';
        position: absolute;
        left: 0;
        top: 8px;
        bottom: 8px;
        width: 3px;
        border-radius: 0 3px 3px 0;
        background: var(--primary);
      }

      .el-icon {
        color: var(--primary) !important;
      }
    }
  }

  :deep(.el-icon) {
    font-size: 17px;
    transition: color 0.2s ease;
  }

  .menu-icon-top {
    color: var(--primary);
  }

  .menu-icon-parent {
    color: var(--primary);
  }

  .menu-icon-child {
    color: var(--secondary);
  }

  :deep(.el-menu-item:hover) .menu-icon-child {
    color: var(--secondary);
  }

  :deep(.el-menu-item.is-active) .menu-icon-child {
    color: var(--primary) !important;
  }

  :deep(.el-sub-menu .el-sub-menu__icon-arrow) {
    color: var(--text-muted);
  }
}

.sidebar-section-label {
  padding: 16px 20px 6px;
  font-size: 11px;
  font-weight: 600;
  color: var(--text-muted);
  letter-spacing: 0.8px;
  text-transform: uppercase;
  user-select: none;
}

.main-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-width: 0;
}

.topbar {
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  border-bottom: 1px solid #eef2f7;
  background: #ffffff;
  flex-shrink: 0;
}

.topbar-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.collapse-btn {
  font-size: 24px;
  cursor: pointer;
  color: #60a5fa;
  transition: all 0.2s ease;
  padding: 6px;
  border-radius: 6px;

  &:hover {
    background: #f0f5ff;
    color: var(--primary);
  }
}

.topbar-right {
  display: flex;
  align-items: center;
}

.user-avatar {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 4px 10px 4px 4px;
  border-radius: 20px;
  transition: all 0.2s ease;

  &:hover {
    background: #f0f5ff;
  }

  .user-name {
    font-size: 13px;
    color: var(--text-primary);
    font-weight: 500;
  }

  .el-icon {
    color: var(--text-muted);
    font-size: 12px;
  }
}

.content-area {
  flex: 1;
  overflow: hidden;
  background: #f5f7fa;
}
</style>
