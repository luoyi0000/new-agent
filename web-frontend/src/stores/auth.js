import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authAPI } from '../api'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('token') || '')
  const user = ref(JSON.parse(localStorage.getItem('user') || '{}'))

  const isLoggedIn = computed(() => !!token.value)
  const isAdmin = computed(() => user.value?.role === 'admin')
  const username = computed(() => user.value?.username || '')

  async function login(credentials) {
    const res = await authAPI.login(credentials)
    token.value = res.data.access_token
    user.value = {
      user_id: res.data.user_id,
      username: res.data.username,
      role: res.data.role,
    }
    localStorage.setItem('token', res.data.access_token)
    localStorage.setItem('user', JSON.stringify(user.value))
    return res.data
  }

  async function register(data) {
    const res = await authAPI.register(data)
    token.value = res.data.access_token
    user.value = {
      user_id: res.data.user_id,
      username: res.data.username,
      role: res.data.role,
    }
    localStorage.setItem('token', res.data.access_token)
    localStorage.setItem('user', JSON.stringify(user.value))
    return res.data
  }

  function logout() {
    token.value = ''
    user.value = {}
    localStorage.removeItem('token')
    localStorage.removeItem('user')
  }

  return { token, user, isLoggedIn, isAdmin, username, login, register, logout }
})
