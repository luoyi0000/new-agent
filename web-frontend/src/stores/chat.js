import { defineStore } from 'pinia'
import { ref, watch } from 'vue'

const STORAGE_KEY = 'chat_messages'

export const useChatStore = defineStore('chat', () => {
  // 从 localStorage 恢复历史消息
  const saved = localStorage.getItem(STORAGE_KEY)
  const messages = ref(
    saved
      ? JSON.parse(saved)
      : [
          {
            role: 'assistant',
            content:
              '您好！我是图书馆智能助手，可以帮您检索图书、预约座位、查询规则等。请问有什么可以帮您？',
          },
        ],
  )

  // 自动持久化到 localStorage
  watch(
    messages,
    (val) => {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(val))
    },
    { deep: true },
  )

  function addMessage(role, content) {
    messages.value.push({ role, content })
  }

  function clearMessages() {
    messages.value = [
      {
        role: 'assistant',
        content: '您好！我是图书馆智能助手，可以帮您检索图书、预约座位、查询规则等。请问有什么可以帮您？',
      },
    ]
  }

  return { messages, addMessage, clearMessages }
})
