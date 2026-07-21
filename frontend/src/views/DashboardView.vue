<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'

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
  'open-create',
  'open-detail',
  'analyze',
])

const router = useRouter()

const analyzedCount = computed(() => {
  return props.requirements.filter(
    (item) => props.analysisResultsByRequirement[item.id],
  ).length
})

const pendingCount = computed(() => {
  return props.requirements.length - analyzedCount.value
})

const highPriorityCount = computed(() => {
  return props.requirements.filter(
    (item) => item.priority === 1,
  ).length
})

const analysisProgress = computed(() => {
  if (props.requirements.length === 0) {
    return 0
  }

  return Math.round(
    (analyzedCount.value / props.requirements.length) * 100,
  )
})

const recentRequirements = computed(() => {
  return [...props.requirements]
    .sort((left, right) => right.id - left.id)
    .slice(0, 6)
})

const priorityStats = computed(() => {
  const total = props.requirements.length || 1

  return [
    {
      label: '高优先级',
      count: props.requirements.filter(
        (item) => item.priority === 1,
      ).length,
      type: 'danger',
      className: 'high',
    },
    {
      label: '中优先级',
      count: props.requirements.filter(
        (item) => item.priority === 2,
      ).length,
      type: 'warning',
      className: 'medium',
    },
    {
      label: '低优先级',
      count: props.requirements.filter(
        (item) => item.priority === 3,
      ).length,
      type: 'success',
      className: 'low',
    },
  ].map((item) => ({
    ...item,
    percentage: Math.round((item.count / total) * 100),
  }))
})

const systemRows = computed(() => [
  {
    name: 'FastAPI 服务',
    description: '需求 CRUD、分析与历史查询接口',
    status: props.backendHealthy ? '在线' : '异常',
    healthy: props.backendHealthy,
  },
  {
    name: 'Agent 工具链',
    description: '完整性检查、歧义检测、优先级建议',
    status: '3 个工具',
    healthy: true,
  },
  {
    name: '分析覆盖率',
    description: '已完成分析的需求占比',
    status: `${analysisProgress.value}%`,
    healthy: analysisProgress.value > 0,
  },
  {
    name: '分析历史',
    description: '已保存分析结果的需求数量',
    status: `${analyzedCount.value} 条`,
    healthy: true,
  },
])

function goTo(routeName) {
  router.push({
    name: routeName,
  })
}

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
</script>

<template>
  <section class="page-heading">
    <div>
      <h2>工作台</h2>
      <p>
        查看需求处理进度、Agent 执行状态与系统运行情况。
      </p>
    </div>

    <div class="heading-actions">
      <el-button @click="goTo('history')">
        <el-icon><Clock /></el-icon>
        分析历史
      </el-button>

      <el-button
        type="primary"
        @click="emit('open-create')"
      >
        <el-icon><Plus /></el-icon>
        新建需求
      </el-button>
    </div>
  </section>

  <section class="summary-panel">
    <article class="summary-item">
      <span>需求总数</span>
      <strong>{{ requirements.length }}</strong>
      <p>当前纳管需求</p>
    </article>

    <article class="summary-item">
      <span>已完成分析</span>
      <strong>{{ analyzedCount }}</strong>
      <p>已生成分析报告</p>
    </article>

    <article class="summary-item">
      <span>待分析需求</span>
      <strong>{{ pendingCount }}</strong>
      <p>等待 Agent 执行</p>
    </article>

    <article class="summary-item">
      <span>高优先级需求</span>
      <strong>{{ highPriorityCount }}</strong>
      <p>建议优先处理</p>
    </article>

    <article class="summary-item">
      <span>后端服务</span>
      <strong
        class="service-value"
        :class="{ unhealthy: !backendHealthy }"
      >
        {{ backendHealthy ? '运行正常' : '连接异常' }}
      </strong>
      <p>FastAPI 健康检查</p>
    </article>
  </section>

  <section class="analytics-grid">
    <article class="panel coverage-panel">
      <div class="panel-heading">
        <div>
          <h3>分析进度</h3>
          <p>当前全部需求的 Agent 分析覆盖情况</p>
        </div>

        <el-button
          link
          type="primary"
          @click="goTo('analysis')"
        >
          进入智能分析
          <el-icon><ArrowRight /></el-icon>
        </el-button>
      </div>

      <div class="coverage-content">
        <div class="coverage-number">
          <strong>{{ analysisProgress }}%</strong>
          <span>分析覆盖率</span>
        </div>

        <div class="coverage-detail">
          <div class="coverage-meta">
            <span>
              已分析 {{ analyzedCount }}
            </span>

            <span>
              待分析 {{ pendingCount }}
            </span>
          </div>

          <el-progress
            :percentage="analysisProgress"
            :stroke-width="12"
            :show-text="false"
          />

          <div class="coverage-legend">
            <span>
              <i class="legend-dot analyzed"></i>
              已生成报告
            </span>

            <span>
              <i class="legend-dot pending"></i>
              待执行或需重新分析
            </span>
          </div>
        </div>
      </div>
    </article>

    <article class="panel priority-panel">
      <div class="panel-heading">
        <div>
          <h3>优先级分布</h3>
          <p>按当前需求优先级统计</p>
        </div>

        <span class="panel-total">
          共 {{ requirements.length }} 条
        </span>
      </div>

      <div class="priority-list">
        <div
          v-for="item in priorityStats"
          :key="item.label"
          class="priority-row"
        >
          <div class="priority-row-heading">
            <span>{{ item.label }}</span>
            <strong>{{ item.count }}</strong>
          </div>

          <div class="priority-track">
            <div
              class="priority-fill"
              :class="item.className"
              :style="{
                width: `${item.percentage}%`,
              }"
            ></div>
          </div>

          <span class="priority-percentage">
            {{ item.percentage }}%
          </span>
        </div>
      </div>
    </article>

    <article class="panel agent-panel">
      <div class="panel-heading">
        <div>
          <h3>Agent 运行概览</h3>
          <p>当前执行链路与工具注册状态</p>
        </div>

        <el-tag
          :type="backendHealthy ? 'success' : 'danger'"
          effect="light"
          round
        >
          {{ backendHealthy ? '可用' : '异常' }}
        </el-tag>
      </div>

      <div class="agent-flow">
        <div class="flow-step">
          <span class="flow-index">1</span>

          <div>
            <strong>Planner 规划</strong>
            <p>根据需求内容选择分析工具</p>
          </div>
        </div>

        <div class="flow-arrow">
          <el-icon><Right /></el-icon>
        </div>

        <div class="flow-step">
          <span class="flow-index">2</span>

          <div>
            <strong>Tool Registry</strong>
            <p>执行完整性、歧义和优先级检查</p>
          </div>
        </div>

        <div class="flow-arrow">
          <el-icon><Right /></el-icon>
        </div>

        <div class="flow-step">
          <span class="flow-index">3</span>

          <div>
            <strong>报告与持久化</strong>
            <p>生成报告并写入分析历史</p>
          </div>
        </div>
      </div>

      <div class="tool-tags">
        <el-tag effect="plain">完整性检查</el-tag>
        <el-tag effect="plain">歧义检测</el-tag>
        <el-tag effect="plain">优先级建议</el-tag>
      </div>
    </article>
  </section>

  <section class="content-grid">
    <article class="panel recent-panel">
      <div class="panel-heading">
        <div>
          <h3>最近需求</h3>
          <p>按需求编号倒序展示最近记录</p>
        </div>

        <el-button
          link
          type="primary"
          @click="goTo('requirements')"
        >
          查看全部
          <el-icon><ArrowRight /></el-icon>
        </el-button>
      </div>

      <el-table
        :data="recentRequirements"
        row-key="id"
        empty-text="暂无需求数据"
        class="recent-table"
      >
        <el-table-column
          label="需求名称"
          min-width="260"
        >
          <template #default="{ row }">
            <div class="requirement-cell">
              <div class="requirement-avatar">
                {{ row.title.slice(0, 1) }}
              </div>

              <div class="requirement-copy">
                <strong>{{ row.title }}</strong>
                <span>
                  REQ-{{ String(row.id).padStart(4, '0') }}
                </span>
              </div>
            </div>
          </template>
        </el-table-column>

        <el-table-column
          label="优先级"
          width="120"
        >
          <template #default="{ row }">
            <el-tag
              :type="getPriorityType(row.priority)"
              effect="light"
              round
            >
              {{ getPriorityLabel(row.priority) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column
          label="分析状态"
          width="120"
        >
          <template #default="{ row }">
            <span
              class="analysis-status"
              :class="{
                completed:
                  analysisResultsByRequirement[row.id],
              }"
            >
              <span></span>
              {{
                analysisResultsByRequirement[row.id]
                  ? '已分析'
                  : '待分析'
              }}
            </span>
          </template>
        </el-table-column>

        <el-table-column
          label="操作"
          width="170"
          fixed="right"
        >
          <template #default="{ row }">
            <el-button
              link
              type="primary"
              @click="emit('open-detail', row)"
            >
              查看
            </el-button>

            <el-button
              link
              type="primary"
              :loading="analyzingRequirementId === row.id"
              @click="emit('analyze', row)"
            >
              分析
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </article>

    <aside class="side-column">
      <article class="panel system-panel">
        <div class="panel-heading">
          <div>
            <h3>系统状态</h3>
            <p>核心服务运行概览</p>
          </div>

          <el-button
            link
            type="primary"
            @click="goTo('settings')"
          >
            系统设置
          </el-button>
        </div>

        <div class="system-list">
          <div
            v-for="row in systemRows"
            :key="row.name"
            class="system-row"
          >
            <div>
              <strong>{{ row.name }}</strong>
              <p>{{ row.description }}</p>
            </div>

            <span
              class="system-status"
              :class="{ error: !row.healthy }"
            >
              {{ row.status }}
            </span>
          </div>
        </div>
      </article>

      <article class="panel quick-panel">
        <div class="panel-heading">
          <div>
            <h3>快捷入口</h3>
            <p>常用业务操作</p>
          </div>
        </div>

        <div class="quick-actions">
          <button @click="emit('open-create')">
            <el-icon><Plus /></el-icon>
            <span>
              <strong>新建需求</strong>
              <small>录入新的业务需求</small>
            </span>
            <el-icon><ArrowRight /></el-icon>
          </button>

          <button @click="goTo('analysis')">
            <el-icon><MagicStick /></el-icon>
            <span>
              <strong>智能分析</strong>
              <small>执行 Agent 工具链</small>
            </span>
            <el-icon><ArrowRight /></el-icon>
          </button>

          <button @click="goTo('history')">
            <el-icon><Clock /></el-icon>
            <span>
              <strong>分析历史</strong>
              <small>查看历次分析报告</small>
            </span>
            <el-icon><ArrowRight /></el-icon>
          </button>
        </div>
      </article>
    </aside>
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

.heading-actions {
  display: flex;
  gap: 8px;
}

.summary-panel {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  margin-bottom: 16px;
  border: 1px solid #e5e6eb;
  background: #ffffff;
}

.summary-item {
  min-width: 0;
  padding: 18px 20px;
  border-right: 1px solid #e5e6eb;
}

.summary-item:last-child {
  border-right: 0;
}

.summary-item span {
  color: #86909c;
  font-size: 12px;
}

.summary-item strong {
  display: block;
  margin-top: 8px;
  color: #1d2129;
  font-size: 26px;
  font-weight: 600;
  line-height: 1;
}

.summary-item p {
  margin: 8px 0 0;
  color: #c2c7d0;
  font-size: 11px;
}

.summary-item .service-value {
  color: #00b42a;
  font-size: 18px;
}

.summary-item .service-value.unhealthy {
  color: #f53f3f;
}

.analytics-grid {
  display: grid;
  grid-template-columns:
    minmax(0, 1.15fr)
    minmax(280px, 0.85fr)
    minmax(330px, 1fr);
  gap: 16px;
  margin-bottom: 16px;
}

.content-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 340px;
  gap: 16px;
  align-items: start;
}

.panel {
  overflow: hidden;
  border: 1px solid #e5e6eb;
  border-radius: 4px;
  background: #ffffff;
}

.panel-heading {
  min-height: 64px;
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

.panel-total {
  color: #86909c;
  font-size: 11px;
}

.coverage-content {
  display: grid;
  grid-template-columns: 130px minmax(0, 1fr);
  align-items: center;
  gap: 24px;
  min-height: 170px;
  padding: 22px;
}

.coverage-number {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  height: 118px;
  border-right: 1px solid #f2f3f5;
}

.coverage-number strong {
  color: #165dff;
  font-size: 36px;
  font-weight: 600;
}

.coverage-number span {
  margin-top: 7px;
  color: #86909c;
  font-size: 11px;
}

.coverage-meta {
  display: flex;
  justify-content: space-between;
  margin-bottom: 12px;
  color: #4e5969;
  font-size: 12px;
}

.coverage-legend {
  display: flex;
  flex-wrap: wrap;
  gap: 18px;
  margin-top: 15px;
  color: #86909c;
  font-size: 10px;
}

.coverage-legend span {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.legend-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
}

.legend-dot.analyzed {
  background: #165dff;
}

.legend-dot.pending {
  background: #ff7d00;
}

.priority-list {
  display: flex;
  justify-content: center;
  flex-direction: column;
  gap: 17px;
  min-height: 170px;
  padding: 20px;
}

.priority-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 38px;
  column-gap: 12px;
}

.priority-row-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 7px;
  color: #4e5969;
  font-size: 11px;
}

.priority-row-heading strong {
  color: #1d2129;
}

.priority-track {
  height: 7px;
  overflow: hidden;
  border-radius: 2px;
  background: #f2f3f5;
}

.priority-fill {
  height: 100%;
  min-width: 3px;
}

.priority-fill.high {
  background: #f53f3f;
}

.priority-fill.medium {
  background: #ff7d00;
}

.priority-fill.low {
  background: #00b42a;
}

.priority-percentage {
  align-self: end;
  color: #86909c;
  font-size: 10px;
  text-align: right;
}

.agent-flow {
  min-height: 145px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 20px 14px 10px;
}

.flow-step {
  min-width: 0;
  display: flex;
  align-items: flex-start;
  gap: 9px;
}

.flow-index {
  width: 27px;
  height: 27px;
  display: grid;
  place-items: center;
  flex-shrink: 0;
  border-radius: 2px;
  background: #e8f3ff;
  color: #165dff;
  font-size: 10px;
  font-weight: 600;
}

.flow-step strong {
  display: block;
  color: #1d2129;
  font-size: 11px;
  white-space: nowrap;
}

.flow-step p {
  max-width: 130px;
  margin: 5px 0 0;
  color: #86909c;
  font-size: 9px;
  line-height: 1.5;
}

.flow-arrow {
  color: #c9cdd4;
  font-size: 13px;
}

.tool-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 7px;
  padding: 0 18px 18px;
}

.recent-panel {
  min-height: 412px;
}

.recent-table {
  width: 100%;
}

:deep(.el-table th.el-table__cell) {
  height: 44px;
  background: #f7f8fa;
  color: #4e5969;
  font-size: 12px;
  font-weight: 500;
}

:deep(.el-table td.el-table__cell) {
  padding: 13px 0;
}

.requirement-cell {
  display: flex;
  align-items: center;
  gap: 10px;
}

.requirement-avatar {
  width: 34px;
  height: 34px;
  display: grid;
  place-items: center;
  flex-shrink: 0;
  border-radius: 3px;
  background: #e8f3ff;
  color: #165dff;
  font-size: 12px;
  font-weight: 600;
}

.requirement-copy strong {
  display: block;
  color: #1d2129;
  font-size: 12px;
  font-weight: 500;
}

.requirement-copy span {
  display: block;
  margin-top: 4px;
  color: #86909c;
  font-family: Consolas, monospace;
  font-size: 10px;
}

.analysis-status {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: #86909c;
  font-size: 11px;
}

.analysis-status > span {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #ff7d00;
}

.analysis-status.completed {
  color: #00b42a;
}

.analysis-status.completed > span {
  background: #00b42a;
}

.side-column {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.system-list {
  padding: 2px 18px 12px;
}

.system-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 14px 0;
  border-bottom: 1px solid #f2f3f5;
}

.system-row:last-child {
  border-bottom: 0;
}

.system-row strong {
  color: #1d2129;
  font-size: 11px;
  font-weight: 500;
}

.system-row p {
  margin: 5px 0 0;
  color: #86909c;
  font-size: 9px;
}

.system-status {
  flex-shrink: 0;
  color: #00b42a;
  font-size: 10px;
}

.system-status.error {
  color: #f53f3f;
}

.quick-actions {
  display: flex;
  flex-direction: column;
  padding: 2px 14px 12px;
}

.quick-actions button {
  display: grid;
  grid-template-columns: 28px minmax(0, 1fr) 16px;
  align-items: center;
  gap: 10px;
  padding: 13px 6px;
  border: 0;
  border-bottom: 1px solid #f2f3f5;
  background: transparent;
  color: inherit;
  text-align: left;
  cursor: pointer;
}

.quick-actions button:last-child {
  border-bottom: 0;
}

.quick-actions button:hover {
  background: #f7f8fa;
}

.quick-actions button > .el-icon:first-child {
  color: #165dff;
  font-size: 17px;
}

.quick-actions button > .el-icon:last-child {
  color: #c9cdd4;
}

.quick-actions strong {
  display: block;
  color: #1d2129;
  font-size: 11px;
  font-weight: 500;
}

.quick-actions small {
  display: block;
  margin-top: 4px;
  color: #86909c;
  font-size: 9px;
}

@media (max-width: 1350px) {
  .summary-panel {
    grid-template-columns: repeat(3, 1fr);
  }

  .summary-item:nth-child(3) {
    border-right: 0;
  }

  .summary-item:nth-child(-n + 3) {
    border-bottom: 1px solid #e5e6eb;
  }

  .analytics-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .agent-panel {
    grid-column: 1 / -1;
  }

  .content-grid {
    grid-template-columns: 1fr;
  }

  .side-column {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
