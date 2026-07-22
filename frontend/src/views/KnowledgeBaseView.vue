<script setup>
import {
  onMounted,
  reactive,
  ref,
} from 'vue'
import {
  ElMessage,
  ElMessageBox,
} from 'element-plus'

import {
  createKnowledgeDocument,
  deleteKnowledgeDocument,
  getKnowledgeDocument,
  listKnowledgeDocuments,
  searchKnowledge,
  updateKnowledgeDocument,
} from '../api/knowledge'

const documents = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const submitting = ref(false)
const detailDialogVisible = ref(false)
const detailLoading = ref(false)
const selectedDocument = ref(null)
const deletingDocumentId = ref(null)
const editingDocumentId = ref(null)
const searchQuery = ref('')
const searchLoading = ref(false)
const searchResults = ref([])
const hasSearched = ref(false)
const searchTopK = ref(5)
const searchMinScore = ref(0)
const documentForm = reactive({
  title: '',
  content: '',
  source: '',
})

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

function formatSimilarity(score) {
  const numericScore = Number(score)

  if (Number.isNaN(numericScore)) {
    return '-'
  }

  return `${(numericScore * 100).toFixed(1)}%`
}

function resetDocumentForm() {
  documentForm.title = ''
  documentForm.content = ''
  documentForm.source = ''
}

function openCreateDialog() {
  editingDocumentId.value = null
  resetDocumentForm()
  dialogVisible.value = true
}

function openEditDialog(document) {
  editingDocumentId.value = document.id

  documentForm.title = document.title
  documentForm.content = document.content
  documentForm.source = document.source || ''

  dialogVisible.value = true
}

function handleDialogClosed() {
  editingDocumentId.value = null
  resetDocumentForm()
}

async function openDocumentDetail(documentId) {
  detailDialogVisible.value = true
  detailLoading.value = true
  selectedDocument.value = null

  try {
    selectedDocument.value = await getKnowledgeDocument(
      documentId,
    )
  } catch (error) {
    detailDialogVisible.value = false

    ElMessage.error(
      error instanceof Error
        ? error.message
        : '知识文档详情加载失败',
    )
  } finally {
    detailLoading.value = false
  }
}

async function confirmDeleteDocument(document) {
  try {
    await ElMessageBox.confirm(
      `确定删除知识文档“${document.title}”吗？相关知识片段也会一起删除。`,
      '删除知识文档',
      {
        confirmButtonText: '确认删除',
        cancelButtonText: '取消',
        type: 'warning',
        confirmButtonClass: 'danger-confirm-button',
      },
    )
  } catch (action) {
    if (
      action === 'cancel'
      || action === 'close'
    ) {
      return
    }

    throw action
  }

  deletingDocumentId.value = document.id

  try {
    await deleteKnowledgeDocument(document.id)

    if (
      selectedDocument.value?.id
      === document.id
    ) {
      detailDialogVisible.value = false
      selectedDocument.value = null
    }

    ElMessage.success('知识文档删除成功')

    await loadDocuments()
  } catch (error) {
    ElMessage.error(
      error instanceof Error
        ? error.message
        : '知识文档删除失败',
    )
  } finally {
    deletingDocumentId.value = null
  }
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

async function runKnowledgeSearch() {
  const query = searchQuery.value.trim()

  if (!query) {
    ElMessage.warning('请输入需要检索的内容')
    return
  }

  searchLoading.value = true
  hasSearched.value = false

  try {
    searchResults.value = await searchKnowledge({
      query,
      topK: searchTopK.value,
      minScore: searchMinScore.value,
    })

    hasSearched.value = true

    ElMessage.success(
      `语义检索完成，共找到 ${searchResults.value.length} 条结果`,
    )
  } catch (error) {
    searchResults.value = []

    ElMessage.error(
      error instanceof Error
        ? error.message
        : '知识库语义检索失败',
    )
  } finally {
    searchLoading.value = false
  }
}

async function submitDocument() {
  const title = documentForm.title.trim()
  const content = documentForm.content.trim()

  if (!title) {
    ElMessage.warning('请输入文档标题')
    return
  }

  if (!content) {
    ElMessage.warning('请输入文档内容')
    return
  }

  const isEditing = editingDocumentId.value !== null

  submitting.value = true

  try {
    const documentData = {
      title,
      content,
      source: documentForm.source,
    }

    if (isEditing) {
      await updateKnowledgeDocument(
        editingDocumentId.value,
        documentData,
      )
    } else {
      await createKnowledgeDocument(documentData)
    }

    ElMessage.success(
      isEditing
        ? '知识文档更新成功'
        : '知识文档创建成功',
    )

    dialogVisible.value = false
    editingDocumentId.value = null
    resetDocumentForm()

    await loadDocuments()
  } catch (error) {
    ElMessage.error(
      error instanceof Error
        ? error.message
        : (
          isEditing
            ? '知识文档更新失败'
            : '知识文档创建失败'
        ),
    )
  } finally {
    submitting.value = false
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
          @click="openCreateDialog"
        >
          新建知识文档
        </el-button>
      </div>
    </div>

    <el-card
      shadow="never"
      class="search-card"
    >
      <div class="search-header">
        <div>
          <strong>知识库语义检索</strong>
          <p>输入需求描述，检索语义最相关的知识片段。</p>
        </div>
      </div>

      <el-input
        v-model="searchQuery"
        clearable
        maxlength="1000"
        placeholder="例如：用户连续登录失败后应该如何处理？"
        @keyup.enter="runKnowledgeSearch"
      >
        <template #append>
          <el-button
            :loading="searchLoading"
            @click="runKnowledgeSearch"
          >
            语义检索
          </el-button>
        </template>
      </el-input>

      <div class="search-options">
        <div class="search-option">
          <span>返回数量</span>

          <el-input-number
            v-model="searchTopK"
            :min="1"
            :max="20"
            :step="1"
            controls-position="right"
          />
        </div>

        <div class="search-option">
          <span>
            最低相似度
            {{ formatSimilarity(searchMinScore) }}
          </span>

          <el-input-number
            v-model="searchMinScore"
            :min="0"
            :max="1"
            :step="0.05"
            :precision="2"
            controls-position="right"
          />
        </div>
      </div>

      <p
        v-if="hasSearched"
        class="search-summary"
      >
        检索完成，共找到
        <strong>{{ searchResults.length }}</strong>
        条相关知识片段
      </p>

      <div
        v-if="hasSearched && searchResults.length > 0"
        class="search-results"
      >
        <article
          v-for="result in searchResults"
          :key="result.chunk_id"
          class="search-result-item"
        >
          <div class="result-header">
            <div>
              <el-button
                type="primary"
                link
                class="result-title"
                @click="openDocumentDetail(result.document_id)"
              >
                {{ result.document_title }}
              </el-button>

              <span class="result-source">
                {{ result.source || '未标注来源' }}
              </span>
            </div>

            <el-tag
              type="success"
              effect="plain"
            >
              相似度 {{ formatSimilarity(result.score) }}
            </el-tag>
          </div>

          <p class="result-content">
            {{ result.content }}
          </p>

          <div class="result-footer">
            <span>文档 ID：{{ result.document_id }}</span>
            <span>片段序号：{{ result.chunk_index + 1 }}</span>
          </div>
        </article>
      </div>

      <el-empty
        v-else-if="hasSearched"
        description="没有找到相关知识片段"
        :image-size="70"
      />
    </el-card>

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
          label="文档标题"
          min-width="180"
        >
          <template #default="{ row }">
            <el-button
              class="title-button"
              type="primary"
              link
              @click="openDocumentDetail(row.id)"
            >
              {{ row.title }}
            </el-button>
          </template>
        </el-table-column>

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

        <el-table-column
          label="操作"
          width="150"
          fixed="right"
        >
          <template #default="{ row }">
            <el-button
              type="primary"
              link
              :disabled="deletingDocumentId !== null"
              @click="openEditDialog(row)"
            >
              编辑
            </el-button>

            <el-button
              type="danger"
              link
              :loading="deletingDocumentId === row.id"
              :disabled="
                deletingDocumentId !== null
                && deletingDocumentId !== row.id
              "
              @click="confirmDeleteDocument(row)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog
      v-model="dialogVisible"
      :title="
        editingDocumentId === null
          ? '新建知识文档'
          : '编辑知识文档'
      "
      width="620px"
      :close-on-click-modal="false"
      @closed="handleDialogClosed"
    >
      <el-form
        label-position="top"
        class="document-form"
      >
        <el-form-item
          label="文档标题"
          required
        >
          <el-input
            v-model="documentForm.title"
            maxlength="200"
            show-word-limit
            placeholder="例如：用户登录安全规范"
          />
        </el-form-item>

        <el-form-item
          label="文档内容"
          required
        >
          <el-input
            v-model="documentForm.content"
            type="textarea"
            :rows="9"
            resize="vertical"
            placeholder="请输入用于 RAG 检索的知识内容"
          />
        </el-form-item>

        <el-form-item label="文档来源">
          <el-input
            v-model="documentForm.source"
            maxlength="200"
            placeholder="例如：security-policy.md，可不填"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button
          :disabled="submitting"
          @click="dialogVisible = false"
        >
          取消
        </el-button>

        <el-button
          type="primary"
          :loading="submitting"
          @click="submitDocument"
        >
          {{ editingDocumentId === null ? '创建文档' : '保存修改' }}
        </el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="detailDialogVisible"
      title="知识文档详情"
      width="680px"
    >
      <div
        v-loading="detailLoading"
        class="detail-panel"
      >
        <template v-if="selectedDocument">
          <div class="detail-meta-grid">
            <div class="detail-meta-item">
              <span>文档 ID</span>
              <strong>{{ selectedDocument.id }}</strong>
            </div>

            <div class="detail-meta-item">
              <span>创建时间</span>
              <strong>
                {{ formatDate(selectedDocument.created_at) }}
              </strong>
            </div>

            <div class="detail-meta-item full-width">
              <span>文档标题</span>
              <strong>{{ selectedDocument.title }}</strong>
            </div>

            <div class="detail-meta-item full-width">
              <span>文档来源</span>
              <strong>
                {{ selectedDocument.source || '未标注来源' }}
              </strong>
            </div>
          </div>

          <div class="detail-content">
            <strong>完整内容</strong>

            <p>{{ selectedDocument.content }}</p>
          </div>
        </template>
      </div>

      <template #footer>
        <el-button @click="detailDialogVisible = false">
          关闭
        </el-button>
      </template>
    </el-dialog>
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

.document-form {
  padding: 0 4px;
}
.title-button {
  height: auto;
  padding: 0;
  font-weight: 600;
  white-space: normal;
  text-align: left;
}

.detail-panel {
  min-height: 220px;
}

.detail-meta-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  margin-bottom: 18px;
}

.detail-meta-item {
  padding: 12px 14px;
  background: #f7f8fa;
  border-radius: 6px;
}

.detail-meta-item.full-width {
  grid-column: 1 / -1;
}

.detail-meta-item span {
  display: block;
  margin-bottom: 6px;
  color: #86909c;
  font-size: 12px;
}

.detail-meta-item strong {
  color: #1d2129;
  font-size: 14px;
  word-break: break-word;
}

.detail-content {
  padding-top: 16px;
  border-top: 1px solid #ebeef5;
}

.detail-content > strong {
  color: #1d2129;
  font-size: 14px;
}

.detail-content p {
  margin: 10px 0 0;
  color: #4e5969;
  line-height: 1.85;
  white-space: pre-wrap;
  word-break: break-word;
}

.search-card {
  border-radius: 6px;
}

.search-header {
  margin-bottom: 14px;
}

.search-header strong {
  color: #172033;
  font-size: 15px;
}

.search-header p {
  margin: 6px 0 0;
  color: #86909c;
  font-size: 12px;
}

.search-summary {
  margin: 12px 0 0;
  color: #4e5969;
  font-size: 13px;
}

.search-summary strong {
  color: #0f8f7a;
}
.search-results {
  display: grid;
  gap: 12px;
  margin-top: 14px;
}

.search-result-item {
  padding: 14px 16px;
  border: 1px solid #e5e6eb;
  border-radius: 6px;
  background: #fafbfc;
}

.result-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.result-header > div {
  min-width: 0;
}

.result-title {
  height: auto;
  padding: 0;
  font-weight: 600;
  white-space: normal;
  text-align: left;
}

.result-source {
  display: block;
  margin-top: 5px;
  color: #86909c;
  font-size: 12px;
  word-break: break-all;
}

.result-content {
  margin: 12px 0;
  color: #4e5969;
  font-size: 13px;
  line-height: 1.75;
  white-space: pre-wrap;
  word-break: break-word;
}

.result-footer {
  display: flex;
  gap: 18px;
  color: #86909c;
  font-size: 12px;
}
.search-options {
  display: flex;
  flex-wrap: wrap;
  gap: 18px;
  margin-top: 12px;
}

.search-option {
  display: flex;
  align-items: center;
  gap: 10px;
}

.search-option > span {
  color: #4e5969;
  font-size: 13px;
}

.search-option :deep(.el-input-number) {
  width: 130px;
}
</style>