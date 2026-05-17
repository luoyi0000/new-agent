<template>
  <div class="page-card">
    <h3 style="margin-bottom:16px;">我的预约</h3>

    <el-table :data="appointments" v-loading="loading" stripe style="width:100%;">
      <el-table-column label="类型" width="100">
        <template #default="{ row }">
          <el-tag>{{ row.resource_type }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="resource_code" label="座位编号" width="120" />
      <el-table-column label="开始时间" width="180">
        <template #default="{ row }">{{ formatTime(row.start_time) }}</template>
      </el-table-column>
      <el-table-column label="结束时间" width="180">
        <template #default="{ row }">{{ formatTime(row.end_time) }}</template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="statusType(row.status)" size="small">{{ row.status }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="120">
        <template #default="{ row }">
          <el-button
            v-if="row.status === 'pending' || row.status === 'confirmed'"
            text type="danger" size="small"
            @click="cancelAppointment(row.id)"
          >取消</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-empty v-if="!loading && appointments.length === 0" description="暂无预约记录" />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { appointmentsAPI } from '../api'

const appointments = ref([])
const loading = ref(false)

async function fetchAppointments() {
  loading.value = true
  try {
    const res = await appointmentsAPI.list()
    appointments.value = res.data.items || []
  } catch { appointments.value = [] }
  finally { loading.value = false }
}

async function cancelAppointment(id) {
  try {
    await appointmentsAPI.cancel(id)
    ElMessage.success('预约已取消')
    fetchAppointments()
  } catch { /* handled */ }
}

function formatTime(iso) {
  if (!iso) return ''
  return new Date(iso).toLocaleString('zh-CN')
}

function statusType(status) {
  const map = { pending: 'warning', confirmed: 'primary', cancelled: 'danger', completed: 'success' }
  return map[status] || 'info'
}

onMounted(fetchAppointments)
</script>
