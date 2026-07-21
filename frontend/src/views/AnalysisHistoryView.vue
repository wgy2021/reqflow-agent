<script setup>
import { computed } from 'vue'

const props = defineProps({
  requirements: {
    type: Array,
    default: () => [],
  },
  selectedRequirementId: {
    type: Number,
    default: null,
  },
  historyRecords: {
    type: Array,
    default: () => [],
  },
  historyLoading: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits([
  'update:selectedRequirementId',
  'refresh',
  'change',
  'open-record',
])

const selectedRequirement = computed(() => {
  return props.requirements.find(
    (item) => item.id === props.selectedRequirementId,
  )
})

function handleRequirementChange(requirementId) {
  emit('update:selectedRequirementId', requirementId)
  emit('change', requirementId)
}

function formatDateTime(value) {
  if (!value) {
    return '--'
  }

  return value.replace('T', ' ').slice(0, 19)
}

function getToolLabel(toolName) {
  const labels = {
    completeness_check: '完整性检查',
    ambiguity_check: '歧义检测',
    priority_suggestion: '优先级建议',
  }

  return labels[toolName] ?? toolName
}
</script>

<template>
  <section class="page-heading history-page-heading">
    <div>
      <h2>分析历史</h2>
      <p>
        按需求查看 Agent 的历次分析记录、工具计划和最终报告。
      </p>
    </div>

    <el-button
      :loading="historyLoading"
      @click="emit('refresh')"
    >
      <el-icon><Refresh /></el-icon>
      刷新历史
    </el-button>
  </section>

  <section class="history-selector-panel">
    <div>
      <span class="history-selector-label">选择需求</span>
      <p>选择一条需求后查看其全部分析记录。</p>
    </div>

    <el-select
      :model-value="selectedRequirementId"
      placeholder="请选择需求"
      filterable
      class="history-requirement-select"
      @change="handleRequirementChange"
    >
      <el-option
        v-for="requirement in requirements"
        :key="requirement.id"
        :label="requirement.title"
        :value="requirement.id"
      >
        <div class="history-option">
          <span>{{ requirement.title }}</span>
          <small>
            REQ-{{
              String(requirement.id).padStart(4, '0')
            }}
          </small>
        </div>
      </el-option>
    </el-select>
  </section>

  <section class="history-summary-grid">
    <article class="history-summary-card">
      <span>当前需求</span>
      <strong>
        {{ selectedRequirement?.title ?? '暂未选择' }}
      </strong>
      <p>
        {{
          selectedRequirement
            ? `REQ-${String(
                selectedRequirement.id,
              ).padStart(4, '0')}`
            : '--'
        }}
      </p>
    </article>

    <article class="history-summary-card">
      <span>历史记录数</span>
      <strong>{{ historyRecords.length }}</strong>
      <p>当前需求已保存的分析记录</p>
    </article>

    <article class="history-summary-card">
      <span>最近分析时间</span>
      <strong class="history-time-value">
        {{
          historyRecords.length > 0
            ? formatDateTime(historyRecords[0].created_at)
            : '--'
        }}
      </strong>
      <p>按最新记录倒序展示</p>
    </article>
  </section>

  <section class="history-table-panel">
    <div class="panel-toolbar">
      <div>
        <h3>分析记录</h3>
        <p>最多展示最近 100 条记录</p>
      </div>
    </div>

    <el-table
      v-loading="historyLoading"
      :data="historyRecords"
      row-key="id"
      empty-text="该需求暂无分析历史"
      class="history-table"
    >
      <el-table-column
        label="分析时间"
        width="180"
      >
        <template #default="{ row }">
          <span class="history-date">
            {{ formatDateTime(row.created_at) }}
          </span>
        </template>
      </el-table-column>

      <el-table-column
        label="检查结果"
        width="130"
      >
        <template #default="{ row }">
          <el-tag
            :type="row.passed ? 'success' : 'warning'"
            effect="light"
            round
          >
            {{ row.passed ? '检查通过' : '需要改进' }}
          </el-tag>
        </template>
      </el-table-column>

      <el-table-column
        label="执行工具"
        min-width="250"
      >
        <template #default="{ row }">
          <div class="history-tool-tags">
            <el-tag
              v-for="tool in row.planned_tools"
              :key="tool"
              size="small"
              effect="plain"
            >
              {{ getToolLabel(tool) }}
            </el-tag>
          </div>
        </template>
      </el-table-column>

      <el-table-column
        label="问题数"
        width="100"
        align="center"
      >
        <template #default="{ row }">
          <span
            class="history-issue-count"
            :class="{ warning: row.issues.length > 0 }"
          >
            {{ row.issues.length }}
          </span>
        </template>
      </el-table-column>

      <el-table-column
        label="模型状态"
        width="130"
      >
        <template #default="{ row }">
          <span
            class="model-status"
            :class="{ fallback: row.llm_fallback_used }"
          >
            <span></span>
            {{
              row.llm_fallback_used
                ? '已降级'
                : '正常'
            }}
          </span>
        </template>
      </el-table-column>

      <el-table-column
        label="操作"
        width="120"
        fixed="right"
      >
        <template #default="{ row }">
          <el-button
            link
            type="primary"
            @click="emit('open-record', row)"
          >
            <el-icon><View /></el-icon>
            查看报告
          </el-button>
        </template>
      </el-table-column>
    </el-table>
  </section>
</template>

<style scoped>
.page-heading {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 25px;
}

.page-heading h2 {
  margin: 0;
  color: #101828;
  font-size: 25px;
  letter-spacing: -0.5px;
}

.page-heading p {
  margin: 9px 0 0;
  color: #667085;
  font-size: 14px;
}

.history-page-heading {
  align-items: center;
}

.history-selector-panel {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 28px;
  margin-bottom: 18px;
  padding: 20px 22px;
  border: 1px solid #eaecf0;
  border-radius: 13px;
  background: white;
  box-shadow: 0 1px 3px rgba(16, 24, 40, 0.03);
}

.history-selector-label {
  color: #344054;
  font-size: 14px;
  font-weight: 600;
}

.history-selector-panel p {
  margin: 6px 0 0;
  color: #98a2b3;
  font-size: 12px;
}

.history-requirement-select {
  width: 360px;
}

.history-option {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
}

.history-option small {
  color: #98a2b3;
  font-family: Consolas, monospace;
}

.history-summary-grid {
  display: grid;
  grid-template-columns: 1.4fr 0.8fr 1fr;
  gap: 18px;
  margin-bottom: 20px;
}

.history-summary-card {
  padding: 19px 20px;
  border: 1px solid #eaecf0;
  border-radius: 13px;
  background: white;
  box-shadow: 0 1px 3px rgba(16, 24, 40, 0.03);
}

.history-summary-card span {
  color: #667085;
  font-size: 12px;
}

.history-summary-card strong {
  display: block;
  margin-top: 8px;
  overflow: hidden;
  color: #101828;
  font-size: 20px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.history-summary-card p {
  margin: 7px 0 0;
  color: #98a2b3;
  font-size: 11px;
}

.history-summary-card .history-time-value {
  font-size: 16px;
}

.history-table-panel {
  min-height: 430px;
  overflow: hidden;
  border: 1px solid #eaecf0;
  border-radius: 14px;
  background: white;
  box-shadow:
    0 1px 3px rgba(16, 24, 40, 0.04),
    0 8px 24px rgba(16, 24, 40, 0.025);
}

.panel-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  padding: 20px 22px;
  border-bottom: 1px solid #eaecf0;
}

.panel-toolbar h3 {
  margin: 0;
  color: #101828;
  font-size: 17px;
}

.panel-toolbar p {
  margin: 5px 0 0;
  color: #98a2b3;
  font-size: 12px;
}

.history-table {
  width: 100%;
}

:deep(.el-table th.el-table__cell) {
  height: 50px;
  background: #f9fafb;
  color: #667085;
  font-size: 13px;
  font-weight: 600;
}

:deep(.el-table td.el-table__cell) {
  padding: 16px 0;
}

.history-date {
  color: #475467;
  font-family: Consolas, monospace;
  font-size: 12px;
}

.history-tool-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.history-issue-count {
  display: inline-grid;
  width: 28px;
  height: 28px;
  place-items: center;
  border-radius: 50%;
  background: #ecfdf3;
  color: #067647;
  font-size: 12px;
  font-weight: 700;
}

.history-issue-count.warning {
  background: #fff4ed;
  color: #b54708;
}

.model-status {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  color: #067647;
  font-size: 12px;
}

.model-status span {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #12b76a;
}

.model-status.fallback {
  color: #b54708;
}

.model-status.fallback span {
  background: #f79009;
}

@media (max-width: 900px) {
  .history-selector-panel {
    align-items: flex-start;
    flex-direction: column;
  }

  .history-requirement-select {
    width: 100%;
  }

  .history-summary-grid {
    grid-template-columns: 1fr;
  }
}
</style>
