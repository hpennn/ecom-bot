/**
 * 应用状态管理
 */
import { defineStore } from 'pinia'
import { ref } from 'vue'
import storesApi from '@/api/stores'

export const useAppStore = defineStore('app', () => {
  const stores = ref([])
  const currentStoreId = ref(localStorage.getItem('currentStoreId') || '')
  const sidebarCollapsed = ref(false)

  async function fetchStores() {
    try {
      const res = await storesApi.getList()
      stores.value = res
      // 如果有当前店铺但没有在列表中，清空
      if (currentStoreId.value && !res.find(s => s.id == currentStoreId.value)) {
        currentStoreId.value = res.length ? String(res[0].id) : ''
      } else if (!currentStoreId.value && res.length) {
        currentStoreId.value = String(res[0].id)
      }
    } catch (e) {
      stores.value = []
    }
  }

  function setCurrentStore(id) {
    currentStoreId.value = String(id)
    localStorage.setItem('currentStoreId', String(id))
  }

  function toggleSidebar() {
    sidebarCollapsed.value = !sidebarCollapsed.value
  }

  return { stores, currentStoreId, sidebarCollapsed, fetchStores, setCurrentStore, toggleSidebar }
})
