<template>
  <div class="page-card">
    <h3 style="margin-bottom:16px;">馆藏检索</h3>

    <el-form :inline="true" style="margin-bottom:16px;">
      <el-form-item>
        <el-input v-model="query" placeholder="搜索书名、作者" clearable style="width:300px;" @keyup.enter="search" />
      </el-form-item>
      <el-form-item>
        <el-select v-model="category" placeholder="分类筛选" clearable style="width:150px;">
          <el-option label="计算机" value="计算机" />
          <el-option label="文学" value="文学" />
          <el-option label="历史" value="历史" />
          <el-option label="科学" value="科学" />
          <el-option label="艺术" value="艺术" />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="search">检索</el-button>
      </el-form-item>
    </el-form>

    <el-table :data="books" v-loading="loading" stripe style="width:100%;">
      <el-table-column prop="title" label="书名" min-width="200" />
      <el-table-column prop="author" label="作者" width="160" />
      <el-table-column prop="category" label="分类" width="100" />
      <el-table-column prop="location" label="馆藏位置" width="150" />
      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="row.status === 'available' ? 'success' : 'warning'" size="small">
            {{ row.status === 'available' ? '可借' : row.status }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="100">
        <template #default="{ row }">
          <el-button text type="primary" size="small" @click="showDetail(row)">详情</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-empty v-if="!loading && books.length === 0" description="请输入关键词检索图书" />

    <el-dialog v-model="detailVisible" width="700px" :show-close="true" class="book-detail-dialog">
      <div class="book-detail-card">
        <div class="book-detail-header">
          <div class="book-detail-title-area">
            <el-tag type="warning" size="small" effect="dark">图书</el-tag>
            <span class="book-title">{{ detailBook?.title }}</span>
          </div>
          <div class="book-detail-actions">
            <el-button text type="primary" size="small">收藏</el-button>
            <el-button text type="primary" size="small">引用</el-button>
            <el-button text type="primary" size="small">翻译</el-button>
          </div>
        </div>

        <div class="book-detail-body">
          <div class="book-detail-row">
            <div class="book-detail-label">作 者</div>
            <div class="book-detail-value">{{ detailBook?.author || '未知' }}</div>
          </div>
          <div class="book-detail-row">
            <div class="book-detail-label">出 版 社</div>
            <div class="book-detail-value publisher">{{ detailBook?.category || '未知' }}</div>
          </div>
          <div class="book-detail-row">
            <div class="book-detail-label">摘 要</div>
            <div class="book-detail-value">
              <div :class="['book-abstract', { 'book-abstract-expanded': detailExpanded }]">
                {{ detailBook?.description || '暂无' }}
              </div>
              <el-button
                v-if="(detailBook?.description?.length || 0) > 120"
                text
                type="primary"
                size="small"
                @click="detailExpanded = !detailExpanded"
              >
                {{ detailExpanded ? '收起' : '更多' }}
              </el-button>
            </div>
          </div>
          <div class="book-detail-row">
            <div class="book-detail-label">关 键 词</div>
            <div class="book-detail-value keywords">{{ detailBook?.category || '未知' }}</div>
          </div>
          <div class="book-detail-row">
            <div class="book-detail-label">文 献 获 取</div>
            <div class="book-detail-value">{{ detailBook?.location || '未知' }}</div>
          </div>
        </div>

        <div class="book-detail-footer">
          <el-button type="primary">馆藏纸本状态</el-button>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { booksAPI } from '../api'

const query = ref('')
const category = ref('')
const books = ref([])
const loading = ref(false)
const detailVisible = ref(false)
const detailBook = ref(null)
const detailExpanded = ref(false)

async function search() {
  loading.value = true
  try {
    const res = await booksAPI.list({ query: query.value, category: category.value || undefined })
    books.value = res.data.items || []
  } catch { books.value = [] }
  finally { loading.value = false }
}

function showDetail(book) {
  detailBook.value = book
  detailExpanded.value = false
  detailVisible.value = true
}

// 页面加载时自动检索所有图书
onMounted(() => search())
</script>

<style scoped>
.book-detail-dialog :deep(.el-dialog__header) {
  display: none;
}

.book-detail-card {
  padding: 8px;
}

.book-detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #ebeef5;
}

.book-detail-title-area {
  display: flex;
  align-items: center;
  gap: 8px;
}

.book-title {
  font-size: 18px;
  font-weight: 600;
  color: #409eff;
  text-decoration: underline;
}

.book-detail-actions {
  display: flex;
  gap: 4px;
}

.book-detail-body {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.book-detail-row {
  display: flex;
  align-items: flex-start;
}

.book-detail-label {
  width: 80px;
  text-align: right;
  padding-right: 12px;
  color: #666;
  font-size: 14px;
  line-height: 22px;
  letter-spacing: 2px;
  flex-shrink: 0;
}

.book-detail-value {
  flex: 1;
  color: #333;
  font-size: 14px;
  line-height: 22px;
  word-break: break-all;
}

.book-detail-value.publisher {
  color: #333;
  text-decoration: underline;
}

.book-detail-value.keywords {
  color: #333;
  text-decoration: underline;
}

.book-abstract {
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
  line-height: 22px;
  margin-bottom: 4px;
}

.book-abstract-expanded {
  -webkit-line-clamp: unset;
  display: block;
}

.book-detail-footer {
  margin-top: 20px;
  padding-top: 12px;
  border-top: 1px solid #ebeef5;
  display: flex;
  justify-content: center;
}
</style>
