<template>
  <div class="page-card">
    <h3 style="margin-bottom:16px;">馆员管理</h3>

    <el-table :data="staff" v-loading="loading" stripe>
      <el-table-column prop="username" label="用户名" min-width="150" />
      <el-table-column prop="email" label="邮箱" width="200" />
      <el-table-column prop="role" label="角色" width="100">
        <template #default="{ row }">
          <el-tag :type="row.role === 'admin' ? 'danger' : 'primary'" size="small">{{ row.role }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="is_active" label="状态" width="80">
        <template #default="{ row }">
          <el-tag :type="row.is_active ? 'success' : 'danger'" size="small">{{ row.is_active ? '正常' : '禁用' }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="150">
        <template #default="{ row }">
          <el-button text type="primary" size="small">编辑</el-button>
          <el-button v-if="row.is_active" text type="danger" size="small">禁用</el-button>
          <el-button v-else text type="success" size="small">启用</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-empty v-if="!loading && staff.length === 0" description="暂无馆员数据" />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const staff = ref([])
const loading = ref(false)

onMounted(async () => {
  // TODO: 集成馆员管理 API
  loading.value = false
})
</script>
