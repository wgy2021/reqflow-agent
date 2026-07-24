<script setup>
import { onMounted, ref } from 'vue'

import { listAgentRuns } from '../api/agentRuns'

const runs = ref([])
const loading = ref(false)
const errorMessage = ref('')

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
    label: '超过步数',
    type: 'warning',
  },
}

function getStatusLabel(status) {
  return statusMap[status]?.label ?? status
}

function getStatusType(status) {
  return statusMap[status]?.type ?? 'info'
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
        <p class="eyebrow">AGENT RUNTIME</p>
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
        <el-icon><Refresh /></el-icon>
        刷新记录
      </el-button>
    </div>

    <el-card
  v-loading="loading"
  shadow="never"
  class="placeholder-card"
>
  <el-alert
    v-if="errorMessage"
    :title="errorMessage"
    type="error"
    show-icon
    :closable="false"
  />

  <el-empty
    v-else-if="runs.length === 0"
    description="暂无 Agent 运行记录"
  >
    <template #image>
      <div class="empty-mark">
        <el-icon><Operation /></el-icon>
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
        <code>{{ row.run_id }}</code>
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
  </el-table>
</el-card>
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

.placeholder-card {
  min-height: 420px;
  border: 1px solid #e4e7ec;
  border-radius: 16px;
  background: #ffffff;
}

:deep(.placeholder-card .el-card__body) {
  min-height: 420px;
  display: grid;
  place-items: center;
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
</style>
