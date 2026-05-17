<template>
  <div style="display:flex;gap:24px;height:calc(100vh - 48px);">
    <!-- 聊天区域 -->
    <div class="page-card" style="flex:1;display:flex;flex-direction:column;overflow:hidden;">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;">
        <h3 style="margin:0;">AI 智能问答</h3>
        <el-button text size="small" @click="chatStore.clearMessages()">清除历史</el-button>
      </div>

      <div ref="msgContainer" style="flex:1;overflow-y:auto;margin-bottom:16px;padding:8px 0;">
        <div v-for="(msg, i) in chatStore.messages" :key="i" style="margin-bottom:16px;">
          <div v-if="msg.role === 'user'" style="display:flex;justify-content:flex-end;margin-bottom:8px;">
            <el-card shadow="never" style="max-width:70%;background:#ecf5ff;padding:8px 12px;border-radius:12px 4px 12px 12px;">
              <span>{{ msg.content }}</span>
            </el-card>
          </div>
          <div v-else style="display:flex;gap:8px;">
            <el-avatar :size="36" icon="UserFilled" style="background:#409eff;flex-shrink:0;" />
            <el-card shadow="never" style="max-width:70%;background:#fff;padding:8px 12px;border-radius:4px 12px 12px 12px;white-space:pre-wrap;">
              <span v-if="msg.content">{{ msg.content }}</span>
              <span v-else-if="loading && i === chatStore.messages.length - 1" style="color:#999;">正在思考...</span>
            </el-card>
          </div>
        </div>
      </div>

      <div style="display:flex;gap:8px;">
        <el-input
          v-model="inputMsg"
          placeholder="请输入您的问题，如「帮我找一本 Python 的书」"
          clearable
          @keyup.enter="sendMessage"
        />
        <el-button type="primary" @click="sendMessage" :disabled="!inputMsg.trim()">发送</el-button>
      </div>
    </div>

    <!-- 快捷功能区 -->
    <div style="width:240px;flex-shrink:0;">
      <div class="page-card" style="margin-bottom:16px;">
        <h4 style="margin-bottom:12px;">快捷功能</h4>
        <el-space direction="vertical" fill style="width:100%;">
          <el-button @click="$router.push('/books')" style="width:100%;justify-content:flex-start;">
            <el-icon><Reading /></el-icon> 馆藏检索
          </el-button>
          <el-button @click="$router.push('/seats')" style="width:100%;justify-content:flex-start;">
            <el-icon><Money /></el-icon> 预约座位
          </el-button>
          <el-button @click="$router.push('/appointments')" style="width:100%;justify-content:flex-start;">
            <el-icon><Calendar /></el-icon> 我的预约
          </el-button>
          <el-button @click="$router.push('/profile')" style="width:100%;justify-content:flex-start;">
            <el-icon><User /></el-icon> 读者画像
          </el-button>
        </el-space>
      </div>

      <div class="page-card">
        <h4 style="margin-bottom:12px;">常见问题</h4>
        <el-space direction="vertical" fill style="width:100%;">
          <el-button text @click="quickQuestion('开馆时间')">开馆时间</el-button>
          <el-button text @click="quickQuestion('借阅规则')">借阅规则</el-button>
          <el-button text @click="quickQuestion('如何预约座位')">如何预约座位</el-button>
        </el-space>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted } from 'vue'
import { chatAPI } from '../api'
import { useChatStore } from '../stores/chat'

const chatStore = useChatStore()
const inputMsg = ref('')
const loading = ref(false)
const msgContainer = ref(null)

// 进入页面时自动滚动到最新消息
onMounted(() => {
  scrollToBottom()
})

function buildHistory() {
  // 将 messages 转换为后端需要的 [{user, assistant}, ...] 格式
  const msgs = chatStore.messages
  const history = []
  for (let i = 1; i < msgs.length - 1; i += 2) {
    const userMsg = msgs[i]
    const asstMsg = msgs[i + 1]
    if (userMsg && userMsg.role === 'user' && asstMsg && asstMsg.role === 'assistant') {
      history.push({ user: userMsg.content, assistant: asstMsg.content })
    }
  }
  return history
}

async function sendMessage() {
  const msg = inputMsg.value.trim()
  if (!msg || loading.value) return
  chatStore.addMessage('user', msg)
  inputMsg.value = ''
  loading.value = true
  scrollToBottom()

  // 先插入一条空消息占位，后续流式填充
  const msgIdx = chatStore.messages.length
  chatStore.addMessage('assistant', '')
  scrollToBottom()

  chatAPI.sendStream(
    { message: msg, history: buildHistory() },
    // onToken: 逐步追加内容
    (token) => {
      chatStore.messages[msgIdx].content += token
      scrollToBottom()
    },
    // onDone: 结束（网络异常也会触发）
    (reply, intent) => {
      if (!chatStore.messages[msgIdx].content) {
        chatStore.messages[msgIdx].content = reply
      }
      loading.value = false
      scrollToBottom()
    },
  )
}

function quickQuestion(text) {
  inputMsg.value = text
  sendMessage()
}

async function scrollToBottom() {
  await nextTick()
  if (msgContainer.value) {
    msgContainer.value.scrollTop = msgContainer.value.scrollHeight
  }
}
</script>
