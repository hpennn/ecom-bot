/**
 * 知识库状态管理
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { 
  getKnowledgeList, 
  addKnowledge, 
  updateKnowledge, 
  deleteKnowledge,
  batchImportKnowledge,
  testReply 
} from '@/api/knowledge'

export const useKnowledgeStore = defineStore('knowledge', () => {
  // 状态
  const knowledgeList = ref([])
  const loading = ref(false)
  const total = ref(0)
  const currentCategory = ref('')
  const testResult = ref(null)
  const testing = ref(false)

  // 计算属性
  const faqCount = computed(() => 
    knowledgeList.value.filter(k => k.category === 'FAQ').length
  )
  const productCount = computed(() => 
    knowledgeList.value.filter(k => k.category === '商品信息').length
  )
  const afterSalesCount = computed(() => 
    knowledgeList.value.filter(k => k.category === '售后政策').length
  )
  const logisticsCount = computed(() => 
    knowledgeList.value.filter(k => k.category === '物流信息').length
  )

  // 获取知识列表
  const fetchKnowledgeList = async (storeId, params = {}) => {
    loading.value = true
    try {
      if (currentCategory.value && !params.category) {
        params.category = currentCategory.value
      }
      const res = await getKnowledgeList(storeId, params)
      knowledgeList.value = res.items || res.list || res.knowledge || res || []
      total.value = res.total || knowledgeList.value.length
      return knowledgeList.value
    } finally {
      loading.value = false
    }
  }

  // 添加知识
  const addKnowledgeAction = async (storeId, data) => {
    loading.value = true
    try {
      const res = await addKnowledge(storeId, data)
      const newItem = res.item || res
      knowledgeList.value.unshift(newItem)
      total.value++
      return newItem
    } finally {
      loading.value = false
    }
  }

  // 更新知识
  const updateKnowledgeAction = async (id, data) => {
    loading.value = true
    try {
      const res = await updateKnowledge(id, data)
      const updatedItem = res.item || res
      const index = knowledgeList.value.findIndex(k => k.id === id)
      if (index !== -1) {
        knowledgeList.value[index] = { ...knowledgeList.value[index], ...updatedItem }
      }
      return updatedItem
    } finally {
      loading.value = false
    }
  }

  // 删除知识
  const deleteKnowledgeAction = async (id) => {
    loading.value = true
    try {
      await deleteKnowledge(id)
      knowledgeList.value = knowledgeList.value.filter(k => k.id !== id)
      total.value--
    } finally {
      loading.value = false
    }
  }

  // 批量导入
  const batchImportAction = async (storeId, file) => {
    loading.value = true
    try {
      const formData = new FormData()
      formData.append('file', file)
      const res = await batchImportKnowledge(storeId, formData)
      // 刷新列表
      await fetchKnowledgeList(storeId)
      return res
    } finally {
      loading.value = false
    }
  }

  // 测试回复
  const testReplyAction = async (storeId, question) => {
    testing.value = true
    testResult.value = null
    try {
      const res = await testReply(storeId, question)
      testResult.value = res.reply || res
      return testResult.value
    } finally {
      testing.value = false
    }
  }

  // 设置分类筛选
  const setCategory = (category) => {
    currentCategory.value = category
  }

  // 清空测试结果
  const clearTestResult = () => {
    testResult.value = null
  }

  return {
    knowledgeList,
    loading,
    total,
    currentCategory,
    testResult,
    testing,
    faqCount,
    productCount,
    afterSalesCount,
    logisticsCount,
    fetchKnowledgeList,
    addKnowledgeAction,
    updateKnowledgeAction,
    deleteKnowledgeAction,
    batchImportAction,
    testReplyAction,
    setCategory,
    clearTestResult
  }
})
