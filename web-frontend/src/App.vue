<template>
  <div class="app-layout">
    <!-- 侧边栏 -->
    <div class="app-sidebar" v-if="showSidebar">
      <div class="logo">
        <el-icon :size="22" style="margin-right:8px"><School /></el-icon>
        图书馆智能服务
      </div>
      <el-menu
        :default-active="route.path"
        router
        :collapse="false"
      >
        <el-menu-item index="/">
          <el-icon><ChatDotRound /></el-icon>
          <span>AI 智能问答</span>
        </el-menu-item>
        <el-menu-item index="/seats">
          <el-icon><Money /></el-icon>
          <span>座位置位图</span>
        </el-menu-item>
        <el-menu-item index="/books">
          <el-icon><Reading /></el-icon>
          <span>馆藏检索</span>
        </el-menu-item>
        <el-menu-item index="/appointments">
          <el-icon><Calendar /></el-icon>
          <span>我的预约</span>
        </el-menu-item>
        <el-menu-item index="/profile">
          <el-icon><User /></el-icon>
          <span>读者画像</span>
        </el-menu-item>
        <el-menu-item index="/policies">
          <el-icon><Document /></el-icon>
          <span>政策问答</span>
        </el-menu-item>

        <!-- 管理员菜单 -->
        <template v-if="authStore.isAdmin">
          <el-divider style="margin:8px 0" />
          <el-menu-item index="/admin/knowledge">
            <el-icon><Setting /></el-icon>
            <span>知识库管理</span>
          </el-menu-item>
          <el-menu-item index="/admin/staff">
            <el-icon><UserFilled /></el-icon>
            <span>馆员管理</span>
          </el-menu-item>
        </template>
      </el-menu>

      <div style="margin-top:auto;padding:16px 20px;border-top:1px solid #e4e7ed;">
        <el-row justify="space-between" align="middle">
          <span style="font-size:14px;color:#909399">{{ authStore.username }}</span>
          <el-button text type="primary" size="small" @click="handleLogout">退出</el-button>
        </el-row>
      </div>
    </div>

    <!-- 主内容 -->
    <div class="app-main">
      <router-view />
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from './stores/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const showSidebar = computed(() => route.path !== '/login')

function handleLogout() {
  authStore.logout()
  router.push('/login')
}
</script>
