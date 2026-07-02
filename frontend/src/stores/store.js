/**
 * 店铺状态管理
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { getStores, createStore, updateStore, deleteStore, getStoreStats } from '@/api/stores'

export const useStoreStore = defineStore('store', () => {
  // 状态
  const stores = ref([])
  const currentStore = ref(null)
  const loading = ref(false)
  const stats = ref(null)

  // 计算属性
  const storeCount = computed(() => stores.value.length)
  const currentStoreId = computed(() => currentStore.value?.id)

  // 获取店铺列表
  const fetchStores = async () => {
    loading.value = true
    try {
      const res = await getStores()
      stores.value = res.stores || res || []
      return stores.value
    } finally {
      loading.value = false
    }
  }

  // 获取单个店铺
  const fetchStore = async (id) => {
    loading.value = true
    try {
      const res = await getStore(id)
      currentStore.value = res.store || res
      return currentStore.value
    } finally {
      loading.value = false
    }
  }

  // 创建店铺
  const createStoreAction = async (data) => {
    loading.value = true
    try {
      const res = await createStore(data)
      const newStore = res.store || res
      stores.value.push(newStore)
      return newStore
    } finally {
      loading.value = false
    }
  }

  // 更新店铺
  const updateStoreAction = async (id, data) => {
    loading.value = true
    try {
      const res = await updateStore(id, data)
      const updatedStore = res.store || res
      const index = stores.value.findIndex(s => s.id === id)
      if (index !== -1) {
        stores.value[index] = { ...stores.value[index], ...updatedStore }
      }
      if (currentStore.value?.id === id) {
        currentStore.value = { ...currentStore.value, ...updatedStore }
      }
      return updatedStore
    } finally {
      loading.value = false
    }
  }

  // 删除店铺
  const deleteStoreAction = async (id) => {
    loading.value = true
    try {
      await deleteStore(id)
      stores.value = stores.value.filter(s => s.id !== id)
      if (currentStore.value?.id === id) {
        currentStore.value = null
      }
    } finally {
      loading.value = false
    }
  }

  // 获取店铺统计
  const fetchStats = async (id) => {
    try {
      const res = await getStoreStats(id)
      stats.value = res.stats || res
      return stats.value
    } catch (error) {
      stats.value = null
      return null
    }
  }

  // 设置当前店铺
  const setCurrentStore = (store) => {
    currentStore.value = store
    localStorage.setItem('currentStoreId', store?.id?.toString() || '')
  }

  // 从本地存储恢复当前店铺
  const restoreCurrentStore = () => {
    const savedId = localStorage.getItem('currentStoreId')
    if (savedId && stores.value.length > 0) {
      const store = stores.value.find(s => s.id.toString() === savedId)
      if (store) {
        currentStore.value = store
      }
    }
  }

  return {
    stores,
    currentStore,
    loading,
    stats,
    storeCount,
    currentStoreId,
    fetchStores,
    fetchStore,
    createStoreAction,
    updateStoreAction,
    deleteStoreAction,
    fetchStats,
    setCurrentStore,
    restoreCurrentStore
  }
})
