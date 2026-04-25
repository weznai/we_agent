import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '../api'

export const useUserStore = defineStore('user', () => {
  const token = ref(localStorage.getItem('token') || '')
  const user = ref(JSON.parse(localStorage.getItem('user') || 'null'))

  const isLoggedIn = computed(() => !!token.value)
  const isSuperUser = computed(() => user.value?.role === 'super')
  const isAdmin = computed(() => user.value?.role === 'super' || user.value?.role === 'admin')
  const nickname = computed(() => user.value?.nickname || user.value?.username || '')

  async function login(loginData) {
    const data = await api.post('/auth/login', loginData)
    token.value = data.access_token
    user.value = data.user
    localStorage.setItem('token', data.access_token)
    localStorage.setItem('user', JSON.stringify(data.user))
    return data
  }

  async function register(registerData) {
    const data = await api.post('/auth/register', registerData)
    token.value = data.access_token
    user.value = data.user
    localStorage.setItem('token', data.access_token)
    localStorage.setItem('user', JSON.stringify(data.user))
    return data
  }

  async function fetchProfile() {
    const data = await api.get('/users/me')
    user.value = data
    localStorage.setItem('user', JSON.stringify(data))
    return data
  }

  async function updateProfile(profileData) {
    const data = await api.put('/users/me', profileData)
    user.value = data
    localStorage.setItem('user', JSON.stringify(data))
    return data
  }

  function logout() {
    token.value = ''
    user.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('user')
  }

  return { token, user, isLoggedIn, isSuperUser, isAdmin, nickname, login, register, fetchProfile, updateProfile, logout }
})
