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
} from '../api/knowledge'

const documents = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const submitting = ref(false)
const detailDialogVisible = ref(false)
const detailLoading = ref(false)
const selectedDocument = ref(null)
const deletingDocumentId = ref(null)
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

function resetDocumentForm() {
  documentForm.title = ''
  documentForm.content = ''
  documentForm.source = ''
}

function openCreateDialog() {
  resetDocumentForm()
  dialogVisible.value = true
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

  submitting.value = true

  try {
    await createKnowledgeDocument({
      title,
      content,
      source: documentForm.source,
    })

    ElMessage.success('知识文档创建成功')
    dialogVisible.value = false
    resetDocumentForm()

    await loadDocuments()
  } catch (error) {
    ElMessage.error(
      error instanceof Error
        ? error.message
        : '知识文档创建失败',
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
                width="100"
                fixed="right"
            >
        <template #default="{ row }">
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
      title="新建知识文档"
      width="620px"
      :close-on-click-modal="false"
      @closed="resetDocumentForm"
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
          创建文档
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
</style>