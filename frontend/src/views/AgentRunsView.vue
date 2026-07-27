<script setup>
import {
  ref,
  watch,
} from 'vue'
import {
  useRoute,
  useRouter,
} from 'vue-router'
import MarkdownIt from 'markdown-it'

import {
  createAgentRun,
  listAgentRuns,
  resolveAgentApproval,
} from '../api/agentRuns'
import { getRequirement } from '../api/requirements'

const markdown = new MarkdownIt({
  html: false,
  linkify: true,
  breaks: true,
})
const route = useRoute()
const router = useRouter()

function formatRequirementCode(requirementId) {
  return `REQ-${String(requirementId).padStart(4, '0')}`
}

async function showAllRuns() {
  await router.push({
    name: 'agent-runs',
  })
}
const runs = ref([])
const currentRequirement = ref(null)
const totalRuns = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)
const loading = ref(false)
const errorMessage = ref('')

const detailVisible = ref(false)
const selectedRun = ref(null)
const approvalLoading = ref(false)
const approvalError = ref('')
const createVisible = ref(false)
const createLoading = ref(false)
const createError = ref('')

const createForm = ref({
  message: '',
  maxSteps: 5,
})
const statusMap = {
  completed: {
    label: '已完成',
    type: 'success',
  },
  running: {
    label: '运行中',
    type: 'primary',
  },
  waiting_approval: {
    label: '等待审批',
    type: 'warning',
  },
  failed: {
    label: '执行失败',
    type: 'danger',
  },
  max_steps_exceeded: {
    label: '超过最大步数',
    type: 'warning',
  },
}

function getStatusLabel(status) {
  return statusMap[status]?.label ?? status ?? '未知状态'
}

function getStatusType(status) {
  return statusMap[status]?.type ?? 'info'
}

function openRunDetail(run) {
  selectedRun.value = run
  approvalError.value = ''
  detailVisible.value = true
}

function formatJson(value) {
  return JSON.stringify(value ?? [], null, 2)
}

function renderMarkdown(value) {
  return markdown.render(value || '暂无最终回答')
}

function openCreateDialog() {
  createError.value = ''

  createForm.value = {
    message: '',
    maxSteps: 5,
  }

  createVisible.value = true
}

async function submitCreate() {
  const message = createForm.value.message.trim()

  if (!message) {
    createError.value = '请输入要交给 Agent 分析的需求'
    return
  }

  createLoading.value = true
  createError.value = ''

  try {
    const newRun = await createAgentRun(
      message,
      createForm.value.maxSteps,
      currentRequirement.value?.id ?? null,
    )

    currentPage.value = 1
    await loadRuns()

    createVisible.value = false
    openRunDetail(newRun)
  } catch (error) {
    createError.value =
      error instanceof Error
        ? error.message
        : '创建 Agent 运行失败'
  } finally {
    createLoading.value = false
  }
}

async function submitApproval(approved) {
  if (!selectedRun.value) {
    return
  }

  approvalLoading.value = true
  approvalError.value = ''

  try {
    const updatedRun = await resolveAgentApproval(
      selectedRun.value.run_id,
      approved,
    )

    selectedRun.value = updatedRun

    runs.value = runs.value.map((run) =>
      run.run_id === updatedRun.run_id
        ? updatedRun
        : run,
    )
  } catch (error) {
    approvalError.value =
      error instanceof Error
        ? error.message
        : '处理 Agent 审批失败'
  } finally {
    approvalLoading.value = false
  }
}

async function loadRuns() {
  loading.value = true
  errorMessage.value = ''

  try {
    const requirementId =
      Number(route.query.requirement_id) || null

    if (requirementId === null) {
      currentRequirement.value = null
    } else {
      currentRequirement.value =
        await getRequirement(requirementId)
    }

    const offset =
      (currentPage.value - 1) * pageSize.value

    const result = await listAgentRuns(
      requirementId,
      pageSize.value,
      offset,
    )

    runs.value = result.items
    totalRuns.value = result.total
  } catch (error) {
    runs.value = []
    totalRuns.value = 0
    errorMessage.value =
      error instanceof Error
        ? error.message
        : '获取 Agent 运行记录失败'
  } finally {
    loading.value = false
  }
}

function handleCurrentChange() {
  loadRuns()
}

function handleSizeChange() {
  currentPage.value = 1
  loadRuns()
}

watch(
  () => route.query.requirement_id,
  () => {
    currentPage.value = 1
    loadRuns()
  },
  { immediate: true },
)
</script>

<template>
  <section class="agent-runs-page">
    <div class="page-heading">
      <div>
        <p class="eyebrow">
          AGENT RUNTIME
        </p>

        <h2>
          {{
            currentRequirement
              ? '需求 Agent 运行历史'
              : '运行记录'
          }}
        </h2>

        <div
          v-if="currentRequirement"
          class="requirement-context"
        >
          <span class="requirement-code">
            {{ formatRequirementCode(currentRequirement.id) }}
          </span>

          <strong class="requirement-title">
            {{ currentRequirement.title }}
          </strong>

          <span class="run-count">
            共 {{ totalRuns }} 次运行
          </span>
        </div>

        <p
          v-else
          class="description"
        >
          查看每次 Agent 执行的状态、工具调用和最终结果。
        </p>
      </div>

      <div class="heading-actions">
        <el-button
          v-if="currentRequirement"
          @click="showAllRuns"
        >
          返回全部记录
        </el-button>

        <el-button @click="openCreateDialog">
          <el-icon>
            <Plus />
          </el-icon>

          新建运行
        </el-button>

        <el-button
          type="primary"
          :loading="loading"
          @click="loadRuns"
        >
          <el-icon>
            <Refresh />
          </el-icon>

          刷新记录
        </el-button>
      </div>
    </div>

    <el-card
      v-loading="loading"
      shadow="never"
      class="runs-card"
    >
      <el-alert
        v-if="errorMessage"
        :title="errorMessage"
        type="error"
        show-icon
        :closable="false"
        class="error-alert"
      />

      <el-empty
        v-else-if="runs.length === 0"
        description="暂无 Agent 运行记录"
      >
        <template #image>
          <div class="empty-mark">
            <el-icon>
              <Operation />
            </el-icon>
          </div>
        </template>
      </el-empty>

      <el-table
        v-else
        :data="runs"
        row-key="run_id"
        style="width: 100%"
      >
        <el-table-column
          label="运行 ID"
          min-width="260"
        >
          <template #default="{ row }">
            <code class="run-id">
              {{ row.run_id }}
            </code>
          </template>
        </el-table-column>

        <el-table-column
          label="状态"
          width="120"
        >
          <template #default="{ row }">
            <el-tag
              :type="getStatusType(row.status)"
              effect="light"
            >
              {{ getStatusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column
          prop="step_count"
          label="执行步数"
          width="110"
        />

        <el-table-column
          label="工具结果"
          width="110"
        >
          <template #default="{ row }">
            {{ row.tool_results?.length ?? 0 }}
          </template>
        </el-table-column>

        <el-table-column
          label="最终回答"
          min-width="320"
          show-overflow-tooltip
        >
          <template #default="{ row }">
            {{ row.final_answer || '—' }}
          </template>
        </el-table-column>

        <el-table-column
          label="操作"
          width="100"
          fixed="right"
        >
          <template #default="{ row }">
            <el-button
              type="primary"
              link
              @click="openRunDetail(row)"
            >
              查看详情
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div
        v-if="!errorMessage && totalRuns > 0"
        class="pagination-row"
      >
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="totalRuns"
          layout="total, sizes, prev, pager, next, jumper"
          background
          @current-change="handleCurrentChange"
          @size-change="handleSizeChange"
        />
      </div>
    </el-card>

    <el-dialog
      v-model="createVisible"
      title="新建 Agent 运行"
      width="560px"
      :close-on-click-modal="!createLoading"
      :close-on-press-escape="!createLoading"
    >
      <el-form
        label-position="top"
        class="create-form"
      >
        <el-form-item
          label="需求内容"
          required
        >
          <el-input
            v-model="createForm.message"
            type="textarea"
            :rows="7"
            maxlength="2000"
            show-word-limit
            placeholder="例如：用户登录连续失败 5 次后锁定账号 30 分钟，并记录安全日志，优先级为 1。"
            :disabled="createLoading"
          />
        </el-form-item>

        <el-form-item label="最大执行步数">
          <el-input-number
            v-model="createForm.maxSteps"
            :min="1"
            :max="20"
            :step="1"
            controls-position="right"
            :disabled="createLoading"
          />

          <p class="form-help">
            限制 Agent 本次运行最多执行多少个步骤，默认值为 5。
          </p>
        </el-form-item>

        <el-alert
          v-if="createError"
          :title="createError"
          type="error"
          show-icon
          :closable="false"
        />
      </el-form>

      <template #footer>
        <el-button
          :disabled="createLoading"
          @click="createVisible = false"
        >
          取消
        </el-button>

        <el-button
          type="primary"
          :loading="createLoading"
          @click="submitCreate"
        >
          启动 Agent
        </el-button>
      </template>
    </el-dialog>

    <el-drawer
      v-model="detailVisible"
      title="Agent 运行详情"
      size="52%"
      destroy-on-close
    >
      <div
        v-if="selectedRun"
        class="run-detail"
      >
        <el-descriptions
          :column="2"
          border
        >
          <el-descriptions-item label="运行 ID">
            <code class="run-id">
              {{ selectedRun.run_id }}
            </code>
          </el-descriptions-item>

          <el-descriptions-item label="状态">
            <el-tag
              :type="getStatusType(selectedRun.status)"
              effect="light"
            >
              {{ getStatusLabel(selectedRun.status) }}
            </el-tag>
          </el-descriptions-item>

          <el-descriptions-item label="执行步数">
            {{ selectedRun.step_count }}
          </el-descriptions-item>

          <el-descriptions-item label="工具结果数量">
            {{ selectedRun.tool_results?.length ?? 0 }}
          </el-descriptions-item>
        </el-descriptions>

        <section
          v-if="selectedRun.status === 'waiting_approval'"
          class="approval-section"
        >
          <div>
            <h3>工具执行审批</h3>

            <p>
              当前 Agent 正在等待人工确认。批准后将继续执行待审批工具；
              拒绝后本次运行将终止。
            </p>
          </div>

          <el-alert
            v-if="approvalError"
            :title="approvalError"
            type="error"
            show-icon
            :closable="false"
          />

          <div class="approval-actions">
            <el-button
              type="danger"
              plain
              :loading="approvalLoading"
              @click="submitApproval(false)"
            >
              拒绝执行
            </el-button>

            <el-button
              type="primary"
              :loading="approvalLoading"
              @click="submitApproval(true)"
            >
              批准执行
            </el-button>
          </div>
        </section>

        <section class="detail-section">
          <h3>最终回答</h3>

          <div
            class="answer-box markdown-body"
            v-html="renderMarkdown(selectedRun.final_answer)"
          />
        </section>

        <section
          v-if="selectedRun.error"
          class="detail-section"
        >
          <h3>错误信息</h3>

          <el-alert
            :title="selectedRun.error"
            type="error"
            show-icon
            :closable="false"
          />
        </section>

        <section class="detail-section">
          <h3>
            工具调用

            <span class="section-count">
              {{ selectedRun.tool_calls?.length ?? 0 }}
            </span>
          </h3>

          <pre class="json-box">{{
            formatJson(selectedRun.tool_calls)
          }}</pre>
        </section>

        <section
          v-if="selectedRun.pending_tool_calls?.length"
          class="detail-section"
        >
          <h3>
            待审批工具

            <span class="section-count">
              {{ selectedRun.pending_tool_calls.length }}
            </span>
          </h3>

          <pre class="json-box">{{
            formatJson(selectedRun.pending_tool_calls)
          }}</pre>
        </section>

        <section class="detail-section">
          <h3>
            工具结果

            <span class="section-count">
              {{ selectedRun.tool_results?.length ?? 0 }}
            </span>
          </h3>

          <pre class="json-box">{{
            formatJson(selectedRun.tool_results)
          }}</pre>
        </section>
      </div>
    </el-drawer>
  </section>
</template>

<style scoped>
.agent-runs-page {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.page-heading {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 24px;
  margin: 0;
}
.heading-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.eyebrow {
  margin: 0 0 8px;
  color: #0f766e;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.12em;
}

h2 {
  margin: 0;
  color: #172033;
  font-size: 26px;
  letter-spacing: -0.02em;
}

.description {
  margin: 10px 0 0;
  color: #667085;
  line-height: 1.7;
}

.requirement-context {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 12px;
}

.requirement-code {
  padding: 4px 8px;
  border: 1px solid #d0d5dd;
  border-radius: 6px;
  background: #f9fafb;
  color: #475467;
  font-family: Consolas, monospace;
  font-size: 12px;
}

.requirement-title {
  color: #344054;
  font-size: 14px;
  font-weight: 600;
}

.run-count {
  color: #667085;
  font-size: 13px;
}

.runs-card {
  min-height: 420px;
  overflow: hidden;
  border: 1px solid #e4e7ec;
  border-radius: 16px;
  background: #ffffff;
}

:deep(.runs-card .el-card__body) {
  min-height: 420px;
  padding: 0;
}

:deep(.runs-card .el-empty) {
  min-height: 420px;
  display: flex;
  justify-content: center;
}

.error-alert {
  width: calc(100% - 32px);
  margin: 16px;
}

.pagination-row {
  display: flex;
  justify-content: flex-end;
  padding: 16px 20px;
  border-top: 1px solid #e4e7ec;
  background: #ffffff;
}

.empty-mark {
  width: 76px;
  height: 76px;
  display: grid;
  place-items: center;
  border: 1px solid #cfe2df;
  border-radius: 20px;
  background: #eef6f4;
  color: #0f766e;
  font-size: 34px;
}

.run-id {
  color: #475467;
  font-family:
    Consolas,
    "Courier New",
    monospace;
  font-size: 12px;
  word-break: break-all;
}

.run-detail {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.approval-section {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 18px;
  border: 1px solid #f5d38a;
  border-radius: 12px;
  background: #fffbeb;
}

.approval-section h3 {
  margin: 0;
  color: #92400e;
  font-size: 15px;
  font-weight: 700;
}

.approval-section p {
  margin: 8px 0 0;
  color: #92400e;
  font-size: 13px;
  line-height: 1.7;
}

.approval-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.detail-section {
  margin: 0;
}

.detail-section h3 {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0 0 12px;
  color: #172033;
  font-size: 15px;
  font-weight: 600;
}

.answer-box {
  padding: 20px;
  overflow-x: auto;
  border: 1px solid #e4e7ec;
  border-radius: 10px;
  background: #f8faf9;
  color: #344054;
}
.create-form {
  padding-top: 4px;
}

.form-help {
  width: 100%;
  margin: 8px 0 0;
  color: #667085;
  font-size: 12px;
  line-height: 1.6;
}

:deep(.markdown-body > :first-child) {
  margin-top: 0;
}

:deep(.markdown-body > :last-child) {
  margin-bottom: 0;
}

:deep(.markdown-body h1),
:deep(.markdown-body h2),
:deep(.markdown-body h3),
:deep(.markdown-body h4) {
  margin: 24px 0 12px;
  color: #172033;
  font-weight: 700;
  line-height: 1.35;
}

:deep(.markdown-body h1) {
  padding-bottom: 10px;
  border-bottom: 1px solid #e4e7ec;
  font-size: 24px;
}

:deep(.markdown-body h2) {
  font-size: 20px;
}

:deep(.markdown-body h3) {
  font-size: 17px;
}

:deep(.markdown-body h4) {
  font-size: 15px;
}

:deep(.markdown-body p),
:deep(.markdown-body li) {
  color: #344054;
  font-size: 14px;
  line-height: 1.8;
}

:deep(.markdown-body ul),
:deep(.markdown-body ol) {
  margin: 12px 0;
  padding-left: 24px;
}

:deep(.markdown-body table) {
  width: 100%;
  margin: 16px 0;
  border-collapse: collapse;
  background: #ffffff;
}

:deep(.markdown-body th),
:deep(.markdown-body td) {
  padding: 10px 12px;
  border: 1px solid #dfe5e8;
  text-align: left;
  vertical-align: top;
  line-height: 1.6;
}

:deep(.markdown-body th) {
  background: #eef6f4;
  color: #172033;
  font-weight: 700;
}

:deep(.markdown-body blockquote) {
  margin: 16px 0;
  padding: 12px 16px;
  border-left: 4px solid #0f766e;
  background: #eef6f4;
  color: #475467;
}

:deep(.markdown-body code) {
  padding: 2px 6px;
  border-radius: 5px;
  background: #e8efed;
  color: #0f5f59;
  font-family:
    Consolas,
    "Courier New",
    monospace;
  font-size: 12px;
}

:deep(.markdown-body pre) {
  margin: 16px 0;
  padding: 16px;
  overflow-x: auto;
  border-radius: 10px;
  background: #172033;
}

:deep(.markdown-body pre code) {
  padding: 0;
  background: transparent;
  color: #e7f3f1;
  line-height: 1.7;
}

:deep(.markdown-body a) {
  color: #0f766e;
  font-weight: 600;
  text-decoration: none;
}

:deep(.markdown-body a:hover) {
  text-decoration: underline;
}

:deep(.markdown-body hr) {
  margin: 24px 0;
  border: 0;
  border-top: 1px solid #e4e7ec;
}

.section-count {
  display: inline-block;
  min-width: 22px;
  padding: 2px 7px;
  border-radius: 999px;
  background: #eef6f4;
  color: #0f766e;
  font-size: 12px;
  font-weight: 600;
  text-align: center;
}

.json-box {
  max-height: 320px;
  margin: 0;
  padding: 16px;
  overflow: auto;
  border: 1px solid #263348;
  border-radius: 10px;
  background: #172033;
  color: #e7f3f1;
  font-family:
    Consolas,
    "Courier New",
    monospace;
  font-size: 12px;
  line-height: 1.7;
  white-space: pre-wrap;
  word-break: break-word;
}

:deep(.el-drawer__header) {
  margin-bottom: 0;
  padding-bottom: 20px;
  border-bottom: 1px solid #e4e7ec;
  color: #172033;
  font-weight: 700;
}

:deep(.el-drawer__body) {
  padding: 24px;
}
</style>
