<script setup>
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'

import { listKnowledgeDocuments } from '../api/knowledge'

const documents = ref([])
const loading = ref(false)

function formatDate(value) {
  if (!value) {
    return '-'
  }

  const date = new Date(value)

  if (Number.isNaN(date.getTime())) {
    return value
  }

  return date.toLocaleString('zh-CN', {
    hour12: false,
  })
}

function previewContent(content) {
  const normalized = String(content ?? '')
    .replace(/\s+/g, ' ')
    .trim()

  if (normalized.length <= 80) {
    return normalized || '-'
  }

  return `${normalized.slice(0, 80)}...`
}

async function loadDocuments() {
  loading.value = true

  try {
    documents.value = await listKnowledgeDocuments({
      limit: 100,
      offset: 0,
    })
  } catch (error) {
    documents.value = []

    ElMessage.error(
      error instanceof Error
        ? error.message
        : '知识文档加载失败',
    )
  } finally {
    loading.value = false
  }
}

onMounted(loadDocuments)
</script>

<template>
  <section class="knowledge-page">
    <div class="knowledge-toolbar">
      <div>
        <h2>知识库管理</h2>
        <p>维护用于 RAG 检索与需求分析的知识文档。</p>
      </div>

      <div class="toolbar-actions">
        <el-button
          :loading="loading"
          @click="loadDocuments"
        >
          刷新
        </el-button>

        <el-button
          type="primary"
          disabled
        >
          新建知识文档
        </el-button>
      </div>
    </div>

    <el-card
      shadow="never"
      class="knowledge-card"
    >
      <div class="card-header">
        <div>
          <strong>知识文档列表</strong>
          <span>共 {{ documents.length }} 条文档</span>
        </div>
      </div>

      <el-table
        v-loading="loading"
        :data="documents"
        empty-text="暂无知识文档"
        border
      >
        <el-table-column
          prop="id"
          label="ID"
          width="80"
        />

        <el-table-column
          prop="title"
          label="文档标题"
          min-width="180"
        />

        <el-table-column
          label="内容摘要"
          min-width="320"
        >
          <template #default="{ row }">
            <span class="content-preview">
              {{ previewContent(row.content) }}
            </span>
          </template>
        </el-table-column>

        <el-table-column
          label="来源"
          min-width="180"
        >
          <template #default="{ row }">
            {{ row.source || '未标注来源' }}
          </template>
        </el-table-column>

        <el-table-column
          label="创建时间"
          width="190"
        >
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </section>
</template>

<style scoped>
.knowledge-page {
  display: grid;
  gap: 16px;
}

.knowledge-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
}

.knowledge-toolbar h2 {
  margin: 0;
  color: #172033;
  font-size: 20px;
}

.knowledge-toolbar p {
  margin: 6px 0 0;
  color: #86909c;
  font-size: 13px;
}

.toolbar-actions {
  display: flex;
  gap: 10px;
}

.knowledge-card {
  min-height: 360px;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.card-header div {
  display: flex;
  align-items: center;
  gap: 12px;
}

.card-header strong {
  color: #172033;
  font-size: 15px;
}

.card-header span {
  color: #86909c;
  font-size: 12px;
}

.content-preview {
  color: #4e5969;
  line-height: 1.7;
}
</style>