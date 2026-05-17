<template>
  <div style="display:flex;justify-content:center;align-items:center;height:100vh;background:#f5f7fa;">
    <el-card style="width:420px;padding:20px;">
      <h2 style="text-align:center;margin-bottom:24px;color:#409eff;">
        <el-icon :size="24" style="vertical-align:middle;margin-right:8px"><School /></el-icon>
        图书馆智能服务系统
      </h2>

      <el-tabs v-model="activeTab" stretch>
        <el-tab-pane label="登录" name="login">
          <el-form ref="loginForm" :model="loginData" :rules="rules" label-width="0">
            <el-form-item prop="username">
              <el-input v-model="loginData.username" placeholder="用户名" prefix-icon="User" />
            </el-form-item>
            <el-form-item prop="password">
              <el-input v-model="loginData.password" type="password" placeholder="密码" prefix-icon="Lock" show-password />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="loading" style="width:100%" @click="handleLogin">登 录</el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <el-tab-pane label="注册" name="register">
          <el-form ref="registerForm" :model="registerData" :rules="rules" label-width="0">
            <el-form-item prop="username">
              <el-input v-model="registerData.username" placeholder="用户名" prefix-icon="User" />
            </el-form-item>
            <el-form-item prop="password">
              <el-input v-model="registerData.password" type="password" placeholder="密码" prefix-icon="Lock" show-password />
            </el-form-item>
            <el-form-item>
              <el-input v-model="registerData.student_id" placeholder="学号（可选）" prefix-icon="CreditCard" />
            </el-form-item>
            <el-form-item>
              <el-input v-model="registerData.email" placeholder="邮箱（可选）" prefix-icon="Message" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="loading" style="width:100%" @click="handleRegister">注 册</el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const authStore = useAuthStore()
const activeTab = ref('login')
const loading = ref(false)

const loginData = reactive({ username: '', password: '' })
const registerData = reactive({ username: '', password: '', student_id: '', email: '' })

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

async function handleLogin() {
  loading.value = true
  try {
    await authStore.login(loginData)
    ElMessage.success('登录成功')
    router.push('/')
  } catch { /* handled by interceptor */ }
  finally { loading.value = false }
}

async function handleRegister() {
  loading.value = true
  try {
    await authStore.register(registerData)
    ElMessage.success('注册成功')
    router.push('/')
  } catch { /* handled by interceptor */ }
  finally { loading.value = false }
}
</script>
