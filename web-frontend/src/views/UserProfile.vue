<template>
  <div class="page-card">
    <h3 style="margin-bottom:16px;">读者画像</h3>

    <el-row :gutter="24">
      <el-col :span="8">
        <el-card shadow="never">
          <div style="text-align:center;">
            <el-avatar :size="80" icon="UserFilled" style="background:#409eff;margin-bottom:12px;" />
            <h4>{{ profile.username || '未知' }}</h4>
            <p style="color:#909399;font-size:14px;">学号：{{ profile.student_id || '未绑定' }}</p>
          </div>
          <el-divider />
          <div>
            <el-tag v-for="tag in profile.tags" :key="tag" style="margin:4px;" type="success" effect="plain">{{ tag }}</el-tag>
            <span v-if="!profile.tags?.length" style="color:#909399;font-size:13px;">暂无标签</span>
          </div>
        </el-card>
      </el-col>

      <el-col :span="16">
        <el-card shadow="never">
          <h4 style="margin-bottom:16px;">预约统计</h4>
          <el-row :gutter="16">
            <el-col :span="6" v-for="item in stats" :key="item.label">
              <el-statistic :value="item.value" :title="item.label" />
            </el-col>
          </el-row>
        </el-card>

        <el-card shadow="never" style="margin-top:16px;">
          <h4 style="margin-bottom:16px;">推荐图书</h4>
          <div v-if="recommendations.length === 0" style="color:#909399;font-size:14px;">暂无推荐</div>
          <el-table v-else :data="recommendations" stripe>
            <el-table-column prop="title" label="书名" />
            <el-table-column prop="author" label="作者" />
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { authAPI, booksAPI } from '../api'

const profile = ref({})
const recommendations = ref([])

const stats = computed(() => [
  { label: '总预约', value: profile.value.stats?.total_appointments || 0 },
  { label: '已完成', value: profile.value.stats?.completed || 0 },
  { label: '已取消', value: profile.value.stats?.cancelled || 0 },
  { label: '座位预约', value: profile.value.stats?.seat_appointments || 0 },
])

async function fetchProfile() {
  try { const res = await authAPI.getMe(); profile.value = res.data } catch { /* handled */ }
}

async function fetchBooks() {
  try {
    const res = await booksAPI.list({})
    recommendations.value = (res.data.items || []).slice(0, 5).map(b => ({ title: b.title, author: b.author }))
  } catch { recommendations.value = [] }
}

onMounted(() => { fetchProfile(); fetchBooks() })
</script>
