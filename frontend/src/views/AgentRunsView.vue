<script setup>
import { onMounted, ref } from 'vue'

import { listAgentRuns } from '../api/agentRuns'

const runs = ref([])
const loading = ref(false)
const errorMessage = ref('')

const detailVisible = ref(false)
const selectedRun = ref(null)

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
  detailVisible.value = true
}

function formatJson(value) {
  return JSON.stringify(value ?? [], null, 2)
}

async function loadRuns() {
  loading.value = true
  errorMessage.value = ''

  try {
    runs.value = await listAgentRuns()
  } catch (error) {
    errorMessage.value =
      error instanceof Error
        ? error.message
        : '获取 Agent 运行记录失败'
  } finally {
    loading.value = false
  }
}

onMounted(loadRuns)
</script>

<template>
  <section class="agent-runs-page">
    <div class="page-heading">
      <div>
        <p class="eyebrow">
          AGENT RUNTIME
        </p>

        <h2>运行记录</h2>

        <p class="description">
          查看每次 Agent 执行的状态、工具调用和最终结果。
        </p>
      </div>

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
    </el-card>

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

        <section class="detail-section">
          <h3>最终回答</h3>

          <div class="answer-box">
            {{ selectedRun.final_answer || '暂无最终回答' }}
          </div>
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
  padding: 16px;
  border: 1px solid #e4e7ec;
  border-radius: 10px;
  background: #f8faf9;
  color: #344054;
  line-height: 1.8;
  white-space: pre-wrap;
  word-break: break-word;
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