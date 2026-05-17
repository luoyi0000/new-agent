import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/login', name: 'Login', component: () => import('../views/Login.vue') },
  { path: '/', name: 'ChatHome', component: () => import('../views/ChatHome.vue'), meta: { requiresAuth: true } },
  { path: '/seats', name: 'SeatMap', component: () => import('../views/SeatMap.vue'), meta: { requiresAuth: true } },
  { path: '/books', name: 'BookSearch', component: () => import('../views/BookSearch.vue'), meta: { requiresAuth: true } },
  { path: '/appointments', name: 'MyAppointments', component: () => import('../views/MyAppointments.vue'), meta: { requiresAuth: true } },
  { path: '/profile', name: 'UserProfile', component: () => import('../views/UserProfile.vue'), meta: { requiresAuth: true } },
  { path: '/policies', name: 'PolicyQA', component: () => import('../views/PolicyQA.vue'), meta: { requiresAuth: true } },
  { path: '/admin/knowledge', name: 'KnowledgeMgmt', component: () => import('../views/KnowledgeMgmt.vue'), meta: { requiresAuth: true, requiresAdmin: true } },
  { path: '/admin/staff', name: 'StaffMgmt', component: () => import('../views/StaffMgmt.vue'), meta: { requiresAuth: true, requiresAdmin: true } },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  if (to.meta.requiresAuth && !token) {
    next('/login')
  } else {
    next()
  }
})

export default router
