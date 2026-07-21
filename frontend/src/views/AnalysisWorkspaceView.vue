<script setup>
import { computed, ref, watch } from 'vue'

const props = defineProps({
  requirements: {
    type: Array,
    default: () => [],
  },
  backendHealthy: {
    type: Boolean,
    default: false,
  },
  analysisResultsByRequirement: {
    type: Object,
    default: () => ({}),
  },
  analyzingRequirementId: {
    type: Number,
    default: null,
  },
})

const emit = defineEmits([
  'open-detail',
  'analyze',
])

const selectedRequirementId = ref(null)

watch(
  () => props.requirements,
  (items) => {
    if (
      selectedRequirementId.value === null &&
      items.length > 0
    ) {
      selectedRequirementId.value = items[0].id
    }

    if (
      selectedRequirementId.value !== null &&
      !items.some(
        (item) => item.id === selectedRequirementId.value,
      )
    ) {
      selectedRequirementId.value = items[0]?.id ?? null
    }
  },
  {
    immediate: true,
  },
)

const selectedRequirement = computed(() => {
  return props.requirements.find(
    (item) => item.id === selectedRequirementId.value,
  ) ?? null
})

const selectedAnalysis = computed(() => {
  if (!selectedRequirement.value) {
    return null
  }

  return (
    props.analysisResultsByRequirement[
      selectedRequirement.value.id
    ] ?? null
  )
})

const isAnalyzing = computed(() => {
  return (
    selectedRequirement.value !== null &&
    props.analyzingRequirementId ===
      selectedRequirement.value.id
  )
})

const analyzedCount = computed(() => {
  return props.requirements.filter(
    (item) => props.analysisResultsByRequirement[item.id],
  ).length
})

const pendingCount = computed(() => {
  return props.requirements.length - analyzedCount.value
})

function getPriorityLabel(priority) {
  const labels = {
    1: '高优先级',
    2: '中优先级',
    3: '低优先级',
  }

  return labels[priority] ?? '未设置'
}

function getPriorityType(priority) {
  const types = {
    1: 'danger',
    2: 'warning',
    3: 'success',
  }

  return types[priority] ?? 'info'
}

function getToolLabel(toolName) {
  const labels = {
    completeness_check: '完整性检查',
    ambiguity_check: '歧义检测',
    priority_suggestion: '优先级建议',
  }

  return labels[toolName] ?? toolName
}

function startAnalysis() {
  if (!selectedRequirement.value) {
    return
  }

  emit('analyze', selectedRequirement.value)
}
</script>

<template>
  <section class="page-heading">
    <div>
      <h2>智能分析</h2>
      <p>
        选择需求并启动 Agent 工具链，查看规划、执行和报告状态。
      </p>
    </div>

    <el-tag
      :type="backendHealthy ? 'success' : 'danger'"
      effect="light"
      round
    >
      {{ backendHealthy ? '服务可用' : '服务异常' }}
    </el-tag>
  </section>

  <section class="summary-strip">
    <article>
      <span>需求总数</span>
      <strong>{{ requirements.length }}</strong>
    </article>

    <article>
      <span>已完成分析</span>
      <strong>{{ analyzedCount }}</strong>
    </article>

    <article>
      <span>待分析需求</span>
      <strong>{{ pendingCount }}</strong>
    </article>

    <article>
      <span>当前执行状态</span>
      <strong class="status-text">
        {{ isAnalyzing ? '分析中' : '空闲' }}
      </strong>
    </article>
  </section>

  <section class="workspace-grid">
    <article class="panel requirement-panel">
      <div class="panel-heading">
        <div>
          <h3>选择分析需求</h3>
          <p>从现有需求中选择一条并启动 Agent 分析。</p>
        </div>
      </div>

      <div class="requirement-selector">
        <el-select
          v-model="selectedRequirementId"
          class="requirement-select"
          placeholder="请选择需求"
          filterable
        >
          <el-option
            v-for="item in requirements"
            :key="item.id"
            :label="item.title"
            :value="item.id"
          />
        </el-select>
      </div>

      <div
        v-if="selectedRequirement"
        class="requirement-detail"
      >
        <div class="requirement-title">
          <div class="requirement-avatar">
            {{ selectedRequirement.title.slice(0, 1) }}
          </div>

          <div>
            <h4>{{ selectedRequirement.title }}</h4>
            <span>
              REQ-{{
                String(selectedRequirement.id).padStart(4, '0')
              }}
            </span>
          </div>

          <el-tag
            :type="
              getPriorityType(selectedRequirement.priority)
            "
            effect="light"
            round
          >
            {{
              getPriorityLabel(selectedRequirement.priority)
            }}
          </el-tag>
        </div>

        <div class="requirement-content">
          {{ selectedRequirement.content }}
        </div>

        <div class="requirement-meta">
          <span>
            当前状态：
            <strong
              :class="{
                analyzed: selectedAnalysis,
              }"
            >
              {{ selectedAnalysis ? '已分析' : '待分析' }}
            </strong>
          </span>

          <span>
            缓存状态：
            <strong>
              {{ selectedAnalysis ? '已有结果' : '无缓存' }}
            </strong>
          </span>
        </div>

        <div class="requirement-actions">
          <el-button
            @click="emit('open-detail', selectedRequirement)"
          >
            查看详情
          </el-button>

          <el-button
            type="primary"
            :loading="isAnalyzing"
            :disabled="!backendHealthy"
            @click="startAnalysis"
          >
            <el-icon><MagicStick /></el-icon>
            {{
              selectedAnalysis
                ? '重新执行 Agent 分析'
                : '启动 Agent 分析'
            }}
          </el-button>
        </div>
      </div>

      <el-empty
        v-else
        description="暂无可分析需求"
        :image-size="90"
      />
    </article>

    <aside class="panel pipeline-panel">
      <div class="panel-heading">
        <div>
          <h3>Agent 执行流程</h3>
          <p>从工具规划到最终报告的完整闭环。</p>
        </div>
      </div>

      <div class="pipeline-list">
        <div class="pipeline-item active">
          <span class="pipeline-index">1</span>

          <div>
            <strong>Planner 规划</strong>
            <p>读取需求内容并选择需要执行的工具。</p>
          </div>
        </div>

        <div class="pipeline-line"></div>

        <div class="pipeline-item">
          <span class="pipeline-index">2</span>

          <div>
            <strong>Tool Registry 执行</strong>
            <p>按计划执行完整性、歧义和优先级检查。</p>
          </div>
        </div>

        <div class="pipeline-line"></div>

        <div class="pipeline-item">
          <span class="pipeline-index">3</span>

          <div>
            <strong>报告生成</strong>
            <p>整合工具结果并生成最终分析报告。</p>
          </div>
        </div>

        <div class="pipeline-line"></div>

        <div class="pipeline-item">
          <span class="pipeline-index">4</span>

          <div>
            <strong>历史与缓存</strong>
            <p>保存分析记录，并复用未变化需求的结果。</p>
          </div>
        </div>
      </div>

      <div class="tool-box">
        <span>当前注册工具</span>

        <div>
          <el-tag effect="plain">完整性检查</el-tag>
          <el-tag effect="plain">歧义检测</el-tag>
          <el-tag effect="plain">优先级建议</el-tag>
        </div>
      </div>
    </aside>
  </section>

  <section class="panel result-panel">
    <div class="panel-heading">
      <div>
        <h3>最近分析结果</h3>
        <p>展示当前需求最近一次保存的分析摘要。</p>
      </div>

      <el-tag
        v-if="selectedAnalysis"
        type="success"
        effect="light"
        round
      >
        已保存
      </el-tag>
    </div>

    <div
      v-if="selectedAnalysis"
      class="result-content"
    >
      <section class="result-metrics">
        <article>
          <span>整体结果</span>
          <strong>
            {{
              selectedAnalysis.passed
                ? '检查通过'
                : '需要改进'
            }}
          </strong>
        </article>

        <article>
          <span>建议优先级</span>
          <strong>
            {{
              getPriorityLabel(
                selectedAnalysis.suggested_priority,
              )
            }}
          </strong>
        </article>

        <article>
          <span>计划工具数</span>
          <strong>
            {{
              selectedAnalysis.planned_tools?.length ?? 0
            }}
          </strong>
        </article>

        <article>
          <span>发现问题数</span>
          <strong>
            {{ selectedAnalysis.issues?.length ?? 0 }}
          </strong>
        </article>
      </section>

      <section class="result-section">
        <h4>执行工具</h4>

        <div class="tool-tags">
          <el-tag
            v-for="tool in selectedAnalysis.planned_tools ?? []"
            :key="tool"
            effect="plain"
          >
            {{ getToolLabel(tool) }}
          </el-tag>
        </div>
      </section>

      <section class="result-section">
        <h4>最终报告</h4>

        <div class="final-report">
          {{
            selectedAnalysis.final_report ??
            '暂无最终报告内容'
          }}
        </div>
      </section>
    </div>

    <el-empty
      v-else
      description="当前需求还没有分析结果"
      :image-size="90"
    />
  </section>
</template>

<style scoped>
.page-heading {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 24px;
  margin-bottom: 16px;
}

.page-heading h2 {
  margin: 0;
  color: #1d2129;
  font-size: 22px;
  font-weight: 600;
}

.page-heading p {
  margin: 7px 0 0;
  color: #86909c;
  font-size: 13px;
}

.summary-strip {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  margin-bottom: 16px;
  border: 1px solid #e5e6eb;
  background: white;
}

.summary-strip article {
  padding: 17px 20px;
  border-right: 1px solid #e5e6eb;
}

.summary-strip article:last-child {
  border-right: 0;
}

.summary-strip span {
  color: #86909c;
  font-size: 12px;
}

.summary-strip strong {
  display: block;
  margin-top: 8px;
  color: #1d2129;
  font-size: 24px;
  font-weight: 600;
}

.summary-strip .status-text {
  color: #165dff;
  font-size: 18px;
}

.workspace-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 360px;
  gap: 16px;
  margin-bottom: 16px;
}

.panel {
  overflow: hidden;
  border: 1px solid #e5e6eb;
  border-radius: 4px;
  background: white;
}

.panel-heading {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  padding: 16px 18px;
  border-bottom: 1px solid #f2f3f5;
}

.panel-heading h3 {
  margin: 0;
  color: #1d2129;
  font-size: 15px;
  font-weight: 600;
}

.panel-heading p {
  margin: 6px 0 0;
  color: #86909c;
  font-size: 11px;
}

.requirement-selector {
  padding: 18px;
  border-bottom: 1px solid #f2f3f5;
}

.requirement-select {
  width: 100%;
}

.requirement-detail {
  padding: 20px;
}

.requirement-title {
  display: grid;
  grid-template-columns: 42px minmax(0, 1fr) auto;
  align-items: center;
  gap: 12px;
}

.requirement-avatar {
  width: 42px;
  height: 42px;
  display: grid;
  place-items: center;
  border-radius: 4px;
  background: #e8f3ff;
  color: #165dff;
  font-size: 14px;
  font-weight: 600;
}

.requirement-title h4 {
  margin: 0;
  color: #1d2129;
  font-size: 16px;
}

.requirement-title span {
  display: block;
  margin-top: 5px;
  color: #86909c;
  font-family: Consolas, monospace;
  font-size: 10px;
}

.requirement-content {
  min-height: 120px;
  margin-top: 18px;
  padding: 16px;
  border: 1px solid #e5e6eb;
  background: #f7f8fa;
  color: #4e5969;
  font-size: 13px;
  line-height: 1.8;
  white-space: pre-wrap;
  word-break: break-word;
}

.requirement-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 24px;
  margin-top: 16px;
  color: #86909c;
  font-size: 11px;
}

.requirement-meta strong {
  color: #ff7d00;
}

.requirement-meta strong.analyzed {
  color: #00b42a;
}

.requirement-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 20px;
}

.pipeline-list {
  padding: 20px;
}

.pipeline-item {
  display: flex;
  gap: 12px;
}

.pipeline-index {
  width: 28px;
  height: 28px;
  display: grid;
  place-items: center;
  flex-shrink: 0;
  border-radius: 3px;
  background: #e8f3ff;
  color: #165dff;
  font-size: 11px;
  font-weight: 600;
}

.pipeline-item strong {
  color: #1d2129;
  font-size: 12px;
}

.pipeline-item p {
  margin: 5px 0 0;
  color: #86909c;
  font-size: 10px;
  line-height: 1.6;
}

.pipeline-line {
  width: 1px;
  height: 24px;
  margin: 5px 0 5px 14px;
  background: #e5e6eb;
}

.tool-box {
  margin: 0 18px 18px;
  padding: 14px;
  background: #f7f8fa;
}

.tool-box > span {
  display: block;
  margin-bottom: 10px;
  color: #4e5969;
  font-size: 11px;
}

.tool-box > div {
  display: flex;
  flex-wrap: wrap;
  gap: 7px;
}

.result-panel {
  min-height: 300px;
}

.result-content {
  padding: 18px;
}

.result-metrics {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
}

.result-metrics article {
  padding: 14px;
  border: 1px solid #e5e6eb;
  background: #f7f8fa;
}

.result-metrics span {
  color: #86909c;
  font-size: 11px;
}

.result-metrics strong {
  display: block;
  margin-top: 7px;
  color: #1d2129;
  font-size: 16px;
}

.result-section {
  margin-top: 20px;
  padding-top: 18px;
  border-top: 1px solid #f2f3f5;
}

.result-section h4 {
  margin: 0 0 12px;
  color: #1d2129;
  font-size: 13px;
}

.tool-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.final-report {
  padding: 16px;
  border: 1px solid #dbe7ff;
  background: #f4f8ff;
  color: #4e5969;
  font-size: 12px;
  line-height: 1.8;
  white-space: pre-wrap;
  word-break: break-word;
}

@media (max-width: 1250px) {
  .workspace-grid {
    grid-template-columns: 1fr;
  }

  .summary-strip {
    grid-template-columns: repeat(2, 1fr);
  }

  .summary-strip article:nth-child(2) {
    border-right: 0;
  }

  .summary-strip article:nth-child(-n + 2) {
    border-bottom: 1px solid #e5e6eb;
  }

  .result-metrics {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
