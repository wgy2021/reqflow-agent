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
  systemInfo: {
    type: Object,
    default: null,
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
  return Math.max(
    props.requirements.length - analyzedCount.value,
    0,
  )
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

const toolCount = computed(() => {
  return props.systemInfo?.tool_count ?? 3
})

const databaseLabel = computed(() => {
  const value = props.systemInfo?.database_type ?? 'sqlite'

  return value.toLowerCase() === 'sqlite'
    ? 'SQLite'
    : value
})

const kpiItems = computed(() => [
  {
    label: '需求总数',
    value: props.requirements.length,
    description: '全部纳管需求',
    icon: 'Document',
    tone: 'blue',
  },
  {
    label: '已分析需求',
    value: analyzedCount.value,
    description: '已完成 Agent 分析',
    icon: 'CircleCheck',
    tone: 'green',
  },
  {
    label: '待分析需求',
    value: pendingCount.value,
    description: '等待进入分析流程',
    icon: 'Timer',
    tone: 'amber',
  },
  {
    label: '分析覆盖率',
    value: `${analysisProgress.value}%`,
    description: '已分析需求占比',
    icon: 'TrendCharts',
    tone: 'blue',
  },
])

const serviceItems = computed(() => [
  {
    name: 'FastAPI 服务',
    description: `ReqFlow Agent ${props.systemInfo?.version ?? '0.1.0'}`,
    status: props.backendHealthy ? '运行正常' : '连接异常',
    icon: 'Connection',
    tone: 'blue',
    healthy: props.backendHealthy,
  },
  {
    name: `${databaseLabel.value} 数据库`,
    description: 'SQLAlchemy + Alembic',
    status: props.backendHealthy ? '可访问' : '待检查',
    icon: 'Coin',
    tone: 'slate',
    healthy: props.backendHealthy,
  },
  {
    name: 'Agent 工具注册中心',
    description: `已注册 ${toolCount.value} 个工具`,
    status: props.backendHealthy ? '正常' : '待检查',
    icon: 'Cpu',
    tone: 'amber',
    healthy: props.backendHealthy,
  },
  {
    name: '分析历史',
    description: `${analyzedCount.value} 条需求已有记录`,
    status: '可用',
    icon: 'DataAnalysis',
    tone: 'green',
    healthy: true,
  },
])

const systemInfoRows = computed(() => [
  ['环境', props.systemInfo?.environment ?? 'development'],
  ['LLM Provider', props.systemInfo?.llm_provider ?? '未获取'],
  ['服务版本', props.systemInfo?.version ?? '0.1.0'],
  ['数据库类型', databaseLabel.value],
  ['Agent 工具', `${toolCount.value} 个`],
  ['缓存版本', props.systemInfo?.cache_version ?? 'v1'],
])

const toolMetadata = {
  ambiguity_check: {
    label: '歧义检测',
    icon: 'Search',
  },
  completeness_check: {
    label: '完整性检查',
    icon: 'DocumentChecked',
  },
  priority_suggestion: {
    label: '优先级建议',
    icon: 'Flag',
  },
}

const toolItems = computed(() => {
  const names = props.systemInfo?.tools ?? [
    'ambiguity_check',
    'completeness_check',
    'priority_suggestion',
  ]

  return names.map((name) => ({
    name,
    label: toolMetadata[name]?.label ?? name,
    icon: toolMetadata[name]?.icon ?? 'Tools',
  }))
})

function goTo(routeName) {
  router.push({
    name: routeName,
  })
}

function hasAnalysis(requirementId) {
  return Boolean(
    props.analysisResultsByRequirement[requirementId],
  )
}

function formatRequirementCode(id) {
  return `REQ-${String(id).padStart(4, '0')}`
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
  <div class="dashboard-page">
    <section class="kpi-grid">
      <article
        v-for="item in kpiItems"
        :key="item.label"
        class="kpi-card"
      >
        <div
          class="kpi-icon"
          :class="item.tone"
        >
          <el-icon>
            <component :is="item.icon" />
          </el-icon>
        </div>

        <div class="kpi-copy">
          <span>{{ item.label }}</span>
          <strong>{{ item.value }}</strong>
          <p>{{ item.description }}</p>
        </div>
      </article>
    </section>

    <section class="dashboard-grid">
      <main class="main-column">
        <article class="panel service-panel">
          <div class="panel-heading">
            <div>
              <h3>运行状态</h3>
              <p>核心服务与基础设施状态概览</p>
            </div>

            <span
              class="panel-health"
              :class="{ error: !backendHealthy }"
            >
              <i></i>
              {{ backendHealthy ? '系统可用' : '服务异常' }}
            </span>
          </div>

          <div class="service-grid">
            <div
              v-for="item in serviceItems"
              :key="item.name"
              class="service-card"
            >
              <div
                class="service-icon"
                :class="item.tone"
              >
                <el-icon>
                  <component :is="item.icon" />
                </el-icon>
              </div>

              <div class="service-copy">
                <strong>{{ item.name }}</strong>
                <span>{{ item.description }}</span>
              </div>

              <div
                class="service-status"
                :class="{ error: !item.healthy }"
              >
                <i></i>
                {{ item.status }}
              </div>
            </div>
          </div>
        </article>

        <article class="panel quick-panel">
          <div class="panel-heading">
            <div>
              <h3>快捷操作</h3>
              <p>常用业务功能快速入口</p>
            </div>
          </div>

          <div class="quick-grid">
            <button @click="emit('open-create')">
              <span class="quick-icon blue">
                <el-icon><Plus /></el-icon>
              </span>
              <span>
                <strong>新建需求</strong>
                <small>录入新的软件需求</small>
              </span>
              <el-icon><ArrowRight /></el-icon>
            </button>

            <button @click="goTo('analysis')">
              <span class="quick-icon amber">
                <el-icon><MagicStick /></el-icon>
              </span>
              <span>
                <strong>智能分析</strong>
                <small>执行 Agent 工具链</small>
              </span>
              <el-icon><ArrowRight /></el-icon>
            </button>

            <button @click="goTo('history')">
              <span class="quick-icon green">
                <el-icon><Clock /></el-icon>
              </span>
              <span>
                <strong>分析历史</strong>
                <small>查看历次分析报告</small>
              </span>
              <el-icon><ArrowRight /></el-icon>
            </button>

            <button @click="goTo('settings')">
              <span class="quick-icon slate">
                <el-icon><Setting /></el-icon>
              </span>
              <span>
                <strong>系统设置</strong>
                <small>查看系统运行配置</small>
              </span>
              <el-icon><ArrowRight /></el-icon>
            </button>
          </div>
        </article>

        <article class="panel recent-panel">
          <div class="panel-heading recent-heading">
            <div>
              <h3>最近分析记录</h3>
              <p>按需求编号倒序展示最近记录</p>
            </div>

            <el-button
              link
              type="primary"
              @click="goTo('history')"
            >
              查看全部
              <el-icon><ArrowRight /></el-icon>
            </el-button>
          </div>

          <el-table
            :data="recentRequirements"
            row-key="id"
            class="recent-table"
            empty-text="暂无需求数据"
          >
            <el-table-column
              label="需求标题"
              min-width="280"
            >
              <template #default="{ row }">
                <div class="requirement-cell">
                  <div class="requirement-avatar">
                    {{ row.title.slice(0, 1) }}
                  </div>

                  <div>
                    <strong>{{ row.title }}</strong>
                    <span>{{ formatRequirementCode(row.id) }}</span>
                  </div>
                </div>
              </template>
            </el-table-column>

            <el-table-column
              label="优先级"
              width="125"
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
              label="工具数量"
              width="100"
              align="center"
            >
              <template #default="{ row }">
                {{ hasAnalysis(row.id) ? toolCount : 0 }}
              </template>
            </el-table-column>

            <el-table-column
              label="状态"
              width="115"
            >
              <template #default="{ row }">
                <span
                  class="analysis-status"
                  :class="{
                    completed: hasAnalysis(row.id),
                  }"
                >
                  <i></i>
                  {{
                    hasAnalysis(row.id)
                      ? '分析完成'
                      : '待分析'
                  }}
                </span>
              </template>
            </el-table-column>

            <el-table-column
              label="操作"
              width="175"
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
                  :loading="
                    analyzingRequirementId === row.id
                  "
                  @click="emit('analyze', row)"
                >
                  {{
                    hasAnalysis(row.id)
                      ? '重新分析'
                      : '分析'
                  }}
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </article>
      </main>

      <aside class="side-column">
        <article class="panel info-panel">
          <div class="panel-heading">
            <div>
              <h3>系统信息</h3>
              <p>运行环境与后端配置</p>
            </div>
          </div>

          <div class="info-list">
            <div
              v-for="row in systemInfoRows"
              :key="row[0]"
            >
              <span>{{ row[0] }}</span>
              <strong>{{ row[1] }}</strong>
            </div>
          </div>
        </article>

        <article class="panel tools-panel">
          <div class="panel-heading">
            <div>
              <h3>Agent 工具</h3>
              <p>后端已注册的分析工具</p>
            </div>

            <span class="count-tag">
              {{ toolItems.length }} 个工具
            </span>
          </div>

          <div class="tool-list">
            <div
              v-for="item in toolItems"
              :key="item.name"
              class="tool-item"
            >
              <div class="tool-icon">
                <el-icon>
                  <component :is="item.icon" />
                </el-icon>
              </div>

              <div class="tool-copy">
                <strong>{{ item.label }}</strong>
                <span>{{ item.name }}</span>
              </div>

              <span class="registered-tag">
                已启用
              </span>
            </div>
          </div>
        </article>
      </aside>
    </section>
  </div>
</template>

<style scoped>
.dashboard-page {
  width: 100%;
  color: var(--rf-text-primary);
}

.page-heading {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 24px;
  margin-bottom: 18px;
}

.page-kicker {
  display: block;
  margin-bottom: 5px;
  color: var(--rf-primary);
  font-size: 9px;
  font-weight: 750;
  letter-spacing: 0.12em;
}

.page-heading h2 {
  margin: 0;
  color: #172033;
  font-size: 24px;
  font-weight: 680;
  letter-spacing: -0.025em;
}

.page-heading p {
  margin: 7px 0 0;
  color: var(--rf-text-secondary);
  font-size: 12px;
}

.page-actions {
  display: flex;
  gap: 8px;
}

.kpi-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px;
  margin-bottom: 16px;
}

.kpi-card {
  min-width: 0;
  min-height: 92px;
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 18px 20px;
  border: 1px solid var(--rf-border);
  border-radius: var(--rf-radius-medium);
  background: var(--rf-bg-card);
  box-shadow: var(--rf-shadow-card);
}

.kpi-icon,
.service-icon,
.quick-icon,
.tool-icon {
  display: grid;
  place-items: center;
  flex-shrink: 0;
  border-radius: 7px;
}

.kpi-icon {
  width: 42px;
  height: 42px;
  color: var(--rf-primary);
  background: var(--rf-primary-light);
  font-size: 19px;
}

.kpi-icon.green {
  color: var(--rf-success);
  background: var(--rf-success-bg);
}

.kpi-icon.amber {
  color: var(--rf-warning);
  background: var(--rf-warning-bg);
}

.kpi-copy {
  min-width: 0;
}

.kpi-copy span {
  display: block;
  color: var(--rf-text-secondary);
  font-size: 11px;
}

.kpi-copy strong {
  display: block;
  margin-top: 5px;
  color: #172033;
  font-size: 25px;
  font-weight: 680;
  line-height: 1;
}

.kpi-copy p {
  margin: 7px 0 0;
  color: var(--rf-text-tertiary);
  font-size: 10px;
}

.dashboard-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 330px;
  gap: 16px;
  align-items: start;
}

.main-column,
.side-column {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.panel {
  overflow: hidden;
  border: 1px solid var(--rf-border);
  border-radius: var(--rf-radius-medium);
  background: var(--rf-bg-card);
  box-shadow: var(--rf-shadow-card);
}

.panel-heading {
  min-height: 70px;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 14px;
  padding: 17px 18px;
  border-bottom: 1px solid var(--rf-border-light);
}

.panel-heading h3 {
  margin: 0;
  color: #172033;
  font-size: 14px;
  font-weight: 670;
}

.panel-heading p {
  margin: 5px 0 0;
  color: var(--rf-text-tertiary);
  font-size: 10px;
}

.panel-health {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 5px 8px;
  border-radius: 999px;
  color: var(--rf-success);
  background: var(--rf-success-bg);
  font-size: 9px;
  font-weight: 650;
  white-space: nowrap;
}

.panel-health i,
.service-status i,
.analysis-status i {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
}

.panel-health.error,
.service-status.error {
  color: var(--rf-danger);
  background: var(--rf-danger-bg);
}

.service-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.service-card {
  min-height: 104px;
  display: grid;
  grid-template-columns: 42px minmax(0, 1fr) auto;
  align-items: center;
  gap: 12px;
  padding: 20px 18px;
  border-right: 1px solid var(--rf-border-light);
  border-bottom: 1px solid var(--rf-border-light);
}

.service-card:nth-child(2n) {
  border-right: 0;
}

.service-card:nth-last-child(-n + 2) {
  border-bottom: 0;
}

.service-icon {
  width: 40px;
  height: 40px;
  color: var(--rf-primary);
  background: var(--rf-primary-light);
  font-size: 18px;
}

.service-icon.green {
  color: var(--rf-success);
  background: var(--rf-success-bg);
}

.service-icon.amber {
  color: var(--rf-warning);
  background: var(--rf-warning-bg);
}

.service-icon.slate {
  color: #475854;
  background: #F1F3F0;
}

.service-copy {
  min-width: 0;
}

.service-copy strong {
  display: block;
  color: #344541;
  font-size: 12px;
  font-weight: 650;
}

.service-copy span {
  display: block;
  margin-top: 5px;
  overflow: hidden;
  color: var(--rf-text-tertiary);
  font-size: 9px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.service-status {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  color: var(--rf-success);
  font-size: 9px;
  font-weight: 650;
  white-space: nowrap;
}

.quick-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
  padding: 16px;
}

.quick-grid button {
  min-width: 0;
  min-height: 82px;
  display: grid;
  grid-template-columns: 38px minmax(0, 1fr) 15px;
  align-items: center;
  gap: 11px;
  padding: 14px;
  border: 1px solid var(--rf-border);
  border-radius: 7px;
  color: inherit;
  background: #ffffff;
  font: inherit;
  text-align: left;
  cursor: pointer;
  transition:
    border-color 0.15s ease,
    box-shadow 0.15s ease,
    transform 0.15s ease;
}

.quick-grid button:hover {
  border-color: #99D9D2;
  box-shadow: 0 5px 14px rgb(16 24 40 / 6%);
  transform: translateY(-1px);
}

.quick-icon {
  width: 38px;
  height: 38px;
  color: var(--rf-primary);
  background: var(--rf-primary-light);
  font-size: 17px;
}

.quick-icon.green {
  color: var(--rf-success);
  background: var(--rf-success-bg);
}

.quick-icon.amber {
  color: var(--rf-warning);
  background: var(--rf-warning-bg);
}

.quick-icon.slate {
  color: #475854;
  background: #F1F3F0;
}

.quick-grid button > span:nth-child(2) {
  min-width: 0;
}

.quick-grid strong {
  display: block;
  overflow: hidden;
  color: #344541;
  font-size: 11px;
  font-weight: 650;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.quick-grid small {
  display: block;
  overflow: hidden;
  margin-top: 5px;
  color: var(--rf-text-tertiary);
  font-size: 9px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.quick-grid button > .el-icon {
  color: var(--rf-text-tertiary);
  font-size: 12px;
}

.recent-panel {
  min-height: 330px;
}

.recent-table {
  width: 100%;
}

:deep(.recent-table .el-table__inner-wrapper::before) {
  display: none;
}

:deep(.recent-table th.el-table__cell) {
  height: 46px;
  background: var(--rf-bg-subtle);
  color: var(--rf-text-secondary);
  font-size: 10px;
  font-weight: 650;
}

:deep(.recent-table td.el-table__cell) {
  padding: 14px 0;
  border-bottom-color: var(--rf-border-light);
}

:deep(.recent-table .el-table__row:hover > td.el-table__cell) {
  background: #FAFBF9;
}

.requirement-cell {
  display: flex;
  align-items: center;
  gap: 11px;
}

.requirement-avatar {
  width: 34px;
  height: 34px;
  display: grid;
  place-items: center;
  flex-shrink: 0;
  border-radius: 6px;
  color: var(--rf-primary);
  background: var(--rf-primary-light);
  font-size: 11px;
  font-weight: 750;
}

.requirement-cell strong {
  display: block;
  color: #344541;
  font-size: 11px;
  font-weight: 650;
}

.requirement-cell span {
  display: block;
  margin-top: 4px;
  color: var(--rf-text-tertiary);
  font-family: Consolas, monospace;
  font-size: 9px;
}

.analysis-status {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: var(--rf-warning);
  font-size: 10px;
  white-space: nowrap;
}

.analysis-status.completed {
  color: var(--rf-success);
}

.info-list {
  padding: 8px 18px 13px;
}

.info-list > div {
  min-height: 43px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  border-bottom: 1px solid var(--rf-border-light);
}

.info-list > div:last-child {
  border-bottom: 0;
}

.info-list span {
  color: var(--rf-text-secondary);
  font-size: 10px;
}

.info-list strong {
  overflow: hidden;
  color: #344541;
  font-size: 10px;
  font-weight: 650;
  text-align: right;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.count-tag {
  padding: 5px 8px;
  border-radius: 999px;
  color: var(--rf-text-secondary);
  background: var(--rf-bg-subtle);
  font-size: 9px;
  white-space: nowrap;
}

.tool-list {
  padding: 5px 16px 12px;
}

.tool-item {
  min-height: 72px;
  display: grid;
  grid-template-columns: 36px minmax(0, 1fr) auto;
  align-items: center;
  gap: 11px;
  border-bottom: 1px solid var(--rf-border-light);
}

.tool-item:last-child {
  border-bottom: 0;
}

.tool-icon {
  width: 34px;
  height: 34px;
  color: var(--rf-primary);
  background: var(--rf-primary-light);
  font-size: 15px;
}

.tool-copy {
  min-width: 0;
}

.tool-copy strong {
  display: block;
  color: #344541;
  font-size: 11px;
  font-weight: 650;
}

.tool-copy span {
  display: block;
  margin-top: 4px;
  overflow: hidden;
  color: var(--rf-text-tertiary);
  font-family: Consolas, monospace;
  font-size: 8px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.registered-tag {
  padding: 4px 7px;
  border-radius: 999px;
  color: var(--rf-success);
  background: var(--rf-success-bg);
  font-size: 8px;
  font-weight: 650;
  white-space: nowrap;
}

@media (max-width: 1280px) {
  .dashboard-grid {
    grid-template-columns: 1fr;
  }

  .side-column {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 980px) {
  .kpi-grid,
  .quick-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .side-column {
    grid-template-columns: 1fr;
  }
}

/* Reference-image scale overrides */
.kpi-grid {
  gap: 18px;
  margin-bottom: 20px;
}

.kpi-card {
  min-height: 114px;
  gap: 18px;
  padding: 22px 24px;
  border-radius: 10px;
  box-shadow:
    0 1px 2px rgb(16 24 40 / 4%),
    0 5px 16px rgb(16 24 40 / 5%);
}

.kpi-icon {
  width: 52px;
  height: 52px;
  font-size: 24px;
}

.kpi-copy span {
  font-size: 14px;
}

.kpi-copy strong {
  font-size: 29px;
}

.kpi-copy p {
  font-size: 12px;
}

.dashboard-grid {
  grid-template-columns: minmax(0, 1fr) 368px;
  gap: 20px;
}

.main-column,
.side-column {
  gap: 18px;
}

.panel {
  border-radius: 10px;
  box-shadow:
    0 1px 2px rgb(16 24 40 / 4%),
    0 5px 16px rgb(16 24 40 / 5%);
}

.panel-heading {
  min-height: 78px;
  padding: 20px;
}

.panel-heading h3 {
  font-size: 18px;
}

.panel-heading p {
  margin-top: 6px;
  font-size: 12px;
}

.panel-health {
  padding: 6px 10px;
  font-size: 11px;
}

.service-card {
  min-height: 116px;
  grid-template-columns: 48px minmax(0, 1fr) auto;
  gap: 15px;
  padding: 22px 20px;
}

.service-icon {
  width: 46px;
  height: 46px;
  font-size: 21px;
}

.service-copy strong {
  font-size: 15px;
}

.service-copy span {
  margin-top: 6px;
  font-size: 11px;
}

.service-status {
  font-size: 11px;
}

.quick-grid {
  gap: 14px;
  padding: 18px;
}

.quick-grid button {
  min-height: 94px;
  grid-template-columns: 44px minmax(0, 1fr) 16px;
  gap: 13px;
  padding: 17px;
}

.quick-icon {
  width: 44px;
  height: 44px;
  font-size: 20px;
}

.quick-grid strong {
  font-size: 14px;
}

.quick-grid small {
  margin-top: 6px;
  font-size: 11px;
}

.recent-panel {
  min-height: 360px;
}

:deep(.recent-table th.el-table__cell) {
  height: 52px;
  font-size: 12px;
}

:deep(.recent-table td.el-table__cell) {
  padding: 17px 0;
}

.requirement-avatar {
  width: 40px;
  height: 40px;
  font-size: 13px;
}

.requirement-cell strong {
  font-size: 13px;
}

.requirement-cell span {
  font-size: 10px;
}

.analysis-status {
  font-size: 12px;
}

.info-list > div {
  min-height: 50px;
}

.info-list span,
.info-list strong {
  font-size: 12px;
}

.tool-item {
  min-height: 84px;
  grid-template-columns: 42px minmax(0, 1fr) auto;
}

.tool-icon {
  width: 40px;
  height: 40px;
  font-size: 18px;
}

.tool-copy strong {
  font-size: 14px;
}

.tool-copy span {
  font-size: 10px;
}

.registered-tag,
.count-tag {
  font-size: 10px;
}


/* Graphite + deep teal trial palette */
.kpi-icon.indigo,
.service-icon.violet,
.quick-icon.violet {
  color: #0F766E;
  background: #F0FDFA;
}

.quick-grid button:hover {
  border-color: #9BCFC8;
  background: #F4F9F7;
}

.requirement-avatar,
.quick-icon,
.tool-icon {
  color: #0F766E;
  background: #F0FDFA;
}

</style>
