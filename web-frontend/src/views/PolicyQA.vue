<template>
  <div class="page-card">
    <h3 style="margin-bottom:16px;">政策问答</h3>

    <el-input
      v-model="keyword"
      placeholder="搜索图书馆规则，如「开馆时间」「借阅期限」"
      clearable
      style="margin-bottom:16px;"
      @keyup.enter="search"
    >
      <template #append>
        <el-button @click="search">搜索</el-button>
      </template>
    </el-input>

    <el-collapse v-model="activeNames" v-loading="loading">
      <el-collapse-item v-for="item in policies" :key="item.id" :title="item.title" :name="item.id">
        <div style="white-space:pre-wrap;line-height:1.8;">{{ item.content }}</div>
        <div v-if="item.category" style="margin-top:8px;">
          <el-tag size="small" type="info">{{ item.category }}</el-tag>
        </div>
      </el-collapse-item>
    </el-collapse>

    <el-empty v-if="!loading && policies.length === 0" description="暂未找到相关规则" />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { policiesAPI } from '../api'

const keyword = ref('')
const policies = ref([])
const loading = ref(false)
const activeNames = ref([])

async function search() {
  loading.value = true
  try {
    const res = await policiesAPI.list({ keyword: keyword.value || undefined })
    policies.value = res.data.items || []
  } catch { policies.value = [] }
  finally { loading.value = false }
}

// 页面加载时自动检索所有规则
onMounted(() => search())
</script>
