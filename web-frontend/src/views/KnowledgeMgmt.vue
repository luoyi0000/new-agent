<template>
  <div class="page-card">
    <h3 style="margin-bottom:16px;">知识库管理</h3>

    <el-tabs v-model="activeTab">
      <el-tab-pane label="图书管理" name="books">
        <el-button type="primary" style="margin-bottom:12px;">新增图书</el-button>
        <el-table :data="books" v-loading="loading" stripe>
          <el-table-column prop="title" label="书名" min-width="200" />
          <el-table-column prop="author" label="作者" width="150" />
          <el-table-column prop="category" label="分类" width="100" />
          <el-table-column prop="location" label="馆藏位置" width="120" />
          <el-table-column label="操作" width="150">
            <template #default="{ row }">
              <el-button text type="primary" size="small">编辑</el-button>
              <el-button text type="danger" size="small">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <el-tab-pane label="政策管理" name="policies">
        <el-button type="primary" style="margin-bottom:12px;">新增政策</el-button>
        <el-table :data="policies" v-loading="loading" stripe>
          <el-table-column prop="title" label="标题" min-width="200" />
          <el-table-column prop="category" label="分类" width="100" />
          <el-table-column label="操作" width="150">
            <template #default="{ row }">
              <el-button text type="primary" size="small">编辑</el-button>
              <el-button text type="danger" size="small">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { booksAPI } from '../api'

const activeTab = ref('books')
const books = ref([])
const policies = ref([])
const loading = ref(false)

async function fetchBooks() {
  loading.value = true
  try {
    const res = await booksAPI.list({})
    books.value = res.data.items || []
  } catch { books.value = [] }
  finally { loading.value = false }
}

onMounted(fetchBooks)
</script>
