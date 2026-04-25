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
          <el-menu-item index="/translation">
            <el-icon class="menu-icon-child"><Document /></el-icon>
            <template #title>智能翻译</template>
          </el-menu-item>
          <el-menu-item index="/customer-service">
            <el-icon class="menu-icon-child"><Service /></el-icon>
            <template #title>智能客服</template>
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
          <el-menu-item index="/providers">
            <el-icon class="menu-icon-child"><Connection /></el-icon>
            <template #title>大模型供应商</template>
          </el-menu-item>
          <el-menu-item index="/models">
            <el-icon class="menu-icon-child"><Cpu /></el-icon>
            <template #title>模型管理</template>
          </el-menu-item>
          <el-menu-item index="/model-mappings">
            <el-icon class="menu-icon-child"><Switch /></el-icon>
            <template #title>模型映射</template>
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
  if (path.startsWith('/chat') || path.startsWith('/translation') || path.startsWith('/customer-service')) return ['agent']
  if (path.startsWith('/providers') || path.startsWith('/models') || path.startsWith('/model-mappings')) return ['system']
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
  width: 260px;
  background: linear-gradient(180deg, #f0f4f8 0%, #e2e8f0 100%);
  display: flex;
  flex-direction: column;
  transition: width 0.3s ease;
  overflow: hidden;
  flex-shrink: 0;
  border-right: 1px solid #cbd5e1;

  &.collapsed {
    width: 64px;
  }
}

.sidebar-header {
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-bottom: 1px solid #cbd5e1;
  padding: 0 16px;
  flex-shrink: 0;
}

.logo {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;

  .logo-icon {
    width: 36px;
    height: 36px;
    flex-shrink: 0;
  }

  .logo-text {
    font-size: 18px;
    font-weight: 700;
    background: var(--gradient-primary);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
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
  padding: 8px;

  :deep(.el-menu-item),
  :deep(.el-sub-menu__title) {
    border-radius: 8px;
    margin: 2px 0;
    height: 44px;
    line-height: 44px;
    color: var(--text-secondary);

    &:hover {
      background: rgba(37, 99, 235, 0.08) !important;
      color: var(--text-primary);
    }

    &.is-active {
      background: linear-gradient(135deg, #60a5fa 0%, #38bdf8 100%) !important;
      color: #ffffff !important;

      .el-icon {
        color: #ffffff !important;
      }
    }
  }

  :deep(.el-sub-menu .el-menu-item) {
    padding-left: 52px !important;
    min-width: auto;
    height: 40px;
    line-height: 40px;
    color: var(--text-secondary);
  }

  :deep(.el-icon) {
    font-size: 18px;
  }

  .menu-icon-top {
    color: #2563eb;
  }

  .menu-icon-parent {
    color: #1d4ed8;
  }

  .menu-icon-child {
    color: #0ea5e9;
  }

  :deep(.el-menu-item.is-active) .menu-icon-top,
  :deep(.el-menu-item.is-active) .menu-icon-child {
    color: white !important;
  }

  :deep(.el-sub-menu .el-sub-menu__icon-arrow) {
    color: var(--text-secondary);
  }
}

.main-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-width: 0;
}

.topbar {
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  border-bottom: 1px solid var(--border-color);
  background: var(--bg-topbar);
  flex-shrink: 0;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
}

.topbar-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.collapse-btn {
  font-size: 20px;
  cursor: pointer;
  color: var(--text-secondary);
  transition: var(--transition);
  padding: 8px;
  border-radius: 8px;

  &:hover {
    background: rgba(37, 99, 235, 0.06);
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
  gap: 10px;
  cursor: pointer;
  padding: 4px 12px;
  border-radius: 20px;
  transition: var(--transition);

  &:hover {
    background: rgba(37, 99, 235, 0.06);
  }

  .user-name {
    font-size: 14px;
    color: var(--text-primary);
    font-weight: 500;
  }

  .el-icon {
    color: var(--text-secondary);
    font-size: 12px;
  }
}

.content-area {
  flex: 1;
  overflow: hidden;
  background: #f1f5f9;
}
</style>
