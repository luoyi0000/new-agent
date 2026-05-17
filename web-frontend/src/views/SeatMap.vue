<template>
  <div class="page-card">
    <h3 style="margin-bottom:16px;">座位置位图</h3>

    <el-radio-group v-model="currentFloor" style="margin-bottom:20px;">
      <el-radio-button value="3F">3F</el-radio-button>
      <el-radio-button value="4F">4F</el-radio-button>
      <el-radio-button value="5F">5F</el-radio-button>
    </el-radio-group>

    <el-row :gutter="16">
      <el-col :span="18">
        <div v-if="loading">加载中...</div>
        <div v-else style="display:grid;grid-template-columns:repeat(6,1fr);gap:12px;">
          <div
            v-for="seat in filteredSeats" :key="seat.id"
            :class="['seat-card', seat.status, { selected: selectedSeat?.id === seat.id }]"
            @click="selectSeat(seat)"
          >
            <div class="seat-code">{{ seat.code }}</div>
            <div class="seat-zone">{{ seat.zone || '通用' }}</div>
            <el-tag :type="seat.status === 'available' ? 'success' : 'danger'" size="small" effect="plain">
              {{ seat.status === 'available' ? '空闲' : seat.status === 'reserved' ? '已预约' : '占用' }}
            </el-tag>
          </div>
        </div>
      </el-col>

      <el-col :span="6">
        <div style="background:#f5f7fa;padding:16px;border-radius:8px;">
          <h4 style="margin-bottom:12px;">操作面板</h4>
          <div v-if="!selectedSeat">
            <p style="color:#909399;font-size:14px;">请选择一个座位</p>
          </div>
          <div v-else>
            <p><strong>座位：</strong>{{ selectedSeat.code }}</p>
            <p><strong>楼层：</strong>{{ selectedSeat.floor }}</p>
            <p><strong>类型：</strong>{{ selectedSeat.seat_type }}</p>
            <el-divider />
            <el-form label-width="60px">
              <el-form-item label="开始">
                <el-date-picker v-model="startTime" type="datetime" placeholder="开始时间" style="width:100%;" />
              </el-form-item>
              <el-form-item label="结束">
                <el-date-picker v-model="endTime" type="datetime" placeholder="结束时间" style="width:100%;" />
              </el-form-item>
            </el-form>
            <el-button type="primary" style="width:100%;margin-top:8px;" @click="bookSeat" :loading="booking">
              立即预约
            </el-button>
          </div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { seatsAPI } from '../api'

const currentFloor = ref('3F')
const allSeats = ref([])
const selectedSeat = ref(null)
const startTime = ref(null)
const endTime = ref(null)
const loading = ref(false)
const booking = ref(false)

const filteredSeats = computed(() => allSeats.value.filter(s => s.floor === currentFloor.value))

watch(currentFloor, () => { selectedSeat.value = null; fetchSeats() })

async function fetchSeats() {
  loading.value = true
  try {
    const res = await seatsAPI.list({ floor: currentFloor.value })
    allSeats.value = res.data.items || []
  } catch { allSeats.value = [] }
  finally { loading.value = false }
}

function selectSeat(seat) {
  selectedSeat.value = seat
  const now = new Date()
  startTime.value = now
  endTime.value = new Date(now.getTime() + 4 * 60 * 60 * 1000)
}

async function bookSeat() {
  if (!startTime.value || !endTime.value) {
    ElMessage.warning('请选择预约时间段')
    return
  }
  booking.value = true
  try {
    await seatsAPI.book({
      seat_id: selectedSeat.value.id,
      start_time: startTime.value.toISOString(),
      end_time: endTime.value.toISOString(),
    })
    ElMessage.success('预约成功！')
    selectedSeat.value = null
    fetchSeats()
  } catch { /* handled by interceptor */ }
  finally { booking.value = false }
}

fetchSeats()
</script>

<style scoped>
.seat-card {
  padding: 16px 8px;
  border-radius: 8px;
  text-align: center;
  cursor: pointer;
  border: 2px solid transparent;
  transition: all 0.2s;
  background: #fff;
  box-shadow: 0 1px 4px rgba(0,0,0,0.05);
}
.seat-card:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
.seat-card.available { border-color: #67c23a; }
.seat-card.occupied, .seat-card.reserved { border-color: #f56c6c; opacity: 0.7; cursor: not-allowed; }
.seat-card.selected { border-color: #409eff; box-shadow: 0 0 0 3px rgba(64,158,255,0.2); }
.seat-code { font-size: 16px; font-weight: 600; margin-bottom: 4px; }
.seat-zone { font-size: 12px; color: #909399; margin-bottom: 8px; }
</style>
