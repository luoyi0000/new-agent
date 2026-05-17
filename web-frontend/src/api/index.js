import axios from 'axios'
import { ElMessage } from 'element-plus'

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
})

// 请求拦截器：自动注入 JWT Token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 响应拦截器：统一错误处理
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const msg = error.response?.data?.detail || '请求失败'
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      window.location.href = '/login'
    }
    ElMessage.error(msg)
    return Promise.reject(error)
  },
)

export default api

// ---- Auth ----
export const authAPI = {
  login: (data) => api.post('/auth/login', data),
  register: (data) => api.post('/auth/register', data),
  getMe: () => api.get('/auth/me'),
}

// ---- Books ----
export const booksAPI = {
  list: (params) => api.get('/books/', { params }),
  get: (id) => api.get(`/books/${id}`),
}

// ---- Seats ----
export const seatsAPI = {
  list: (params) => api.get('/seats/', { params }),
  available: (params) => api.get('/seats/available', { params }),
  book: (params) => api.post('/seats/book', null, { params }),
}

// ---- Appointments ----
export const appointmentsAPI = {
  list: () => api.get('/appointments/'),
  cancel: (id) => api.post(`/appointments/${id}/cancel`),
}

// ---- Chat ----
export const chatAPI = {
  send: (data) => api.post('/chat/', data),

  /** SSE 流式问答：onToken(content) / onDone(reply, intent) */
  sendStream: (data, onToken, onDone) => {
    const token = localStorage.getItem('token')
    const controller = new AbortController()

    fetch('/api/v1/chat/stream', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify(data),
      signal: controller.signal,
    })
      .then(async (response) => {
        if (!response.ok) {
          const err = await response.json().catch(() => ({}))
          ElMessage.error(err.detail || '请求失败')
          if (onDone) onDone('', 'other')
          return
        }
        const reader = response.body.getReader()
        const decoder = new TextDecoder()
        let buffer = ''
        let finished = false

        while (true) {
          const { done, value } = await reader.read()
          if (done) break
          buffer += decoder.decode(value, { stream: true })

          const lines = buffer.split('\n')
          buffer = lines.pop() || '' // 保留未完成的行
          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const payload = line.slice(6)
              if (payload === '[DONE]') {
                finished = true
                return
              }
              try {
                const evt = JSON.parse(payload)
                if (evt.type === 'token') onToken(evt.content)
                else if (evt.type === 'done') {
                  finished = true
                  onDone(evt.content, evt.intent)
                }
              } catch {
                // 忽略解析失败的行
              }
            }
          }
        }
        // 流正常结束但未收到 done 事件
        if (!finished && onDone) onDone('', 'other')
      })
      .catch((err) => {
        if (err.name !== 'AbortError') {
          ElMessage.error('网络异常，请稍后重试')
        }
        if (onDone) onDone('', 'other')
      })

    return controller // 外部可调用 controller.abort() 取消
  },
}

// ---- Policies ----
export const policiesAPI = {
  list: (params) => api.get('/policies/', { params }),
}
