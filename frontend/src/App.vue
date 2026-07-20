<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'

const requirements = ref([])
const loading = ref(false)
const backendHealthy = ref(false)

const keyword = ref('')
const priorityFilter = ref(null)
const activeMenu = ref('requirements')
const createDialogVisible = ref(false)
const createSubmitting = ref(false)
const createFormRef = ref()

const createForm = reactive({
  title: '',
  content: '',
  priority: 2,
})

const createRules = {
  title: [
    {
      required: true,
      message: '请输入需求标题',
      trigger: 'blur',
    },
    {
      min: 1,
      max: 100,
      message: '标题长度不能超过 100 个字符',
      trigger: 'blur',
    },
  ],
  content: [
    {
      required: true,
      message: '请输入需求内容',
      trigger: 'blur',
    },
    {
      min: 1,
      max: 5000,
      message: '需求内容不能超过 5000 个字符',
      trigger: 'blur',
    },
  ],
  priority: [
    {
      required: true,
      message: '请选择需求优先级',
      trigger: 'change',
    },
  ],
}

const filteredRequirements = computed(() => {
  return requirements.value.filter((item) => {
    const normalizedKeyword = keyword.value.trim().toLowerCase()

    const matchesKeyword =
      normalizedKeyword === '' ||
      item.title.toLowerCase().includes(normalizedKeyword) ||
      item.content.toLowerCase().includes(normalizedKeyword)

    const matchesPriority =
      priorityFilter.value === null ||
      item.priority === priorityFilter.value

    return matchesKeyword && matchesPriority
  })
})

const highPriorityCount = computed(() => {
  return requirements.value.filter((item) => item.priority === 1).length
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

async function loadData() {
  loading.value = true

  try {
    const [healthResponse, requirementsResponse] = await Promise.all([
      fetch('/api/health'),
      fetch('/api/requirements?limit=100&offset=0'),
    ])

    if (!healthResponse.ok || !requirementsResponse.ok) {
      throw new Error('后端接口返回异常')
    }

    const healthData = await healthResponse.json()
    const requirementsData = await requirementsResponse.json()

    backendHealthy.value = healthData.status === 'ok'
    requirements.value = requirementsData
  } catch (error) {
    backendHealthy.value = false

    ElMessage.error('数据加载失败，请检查后端容器是否正常运行。')
    console.error(error)
  } finally {
    loading.value = false
  }
}

function showPendingMessage(featureName) {
  ElMessage.info(`${featureName}将在下一步接入。`)
}

function resetCreateForm() {
  createForm.title = ''
  createForm.content = ''
  createForm.priority = 2

  createFormRef.value?.clearValidate()
}

function openCreateDialog() {
  resetCreateForm()
  createDialogVisible.value = true
}

async function submitRequirement() {
  if (!createFormRef.value) {
    return
  }

  const formValid = await createFormRef.value
    .validate()
    .catch(() => false)

  if (!formValid) {
    return
  }

  createSubmitting.value = true

  try {
    const response = await fetch('/api/requirements', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        title: createForm.title.trim(),
        content: createForm.content.trim(),
        priority: createForm.priority,
      }),
    })

    if (!response.ok) {
      throw new Error(`创建需求失败：HTTP ${response.status}`)
    }

    createDialogVisible.value = false

    ElMessage.success('需求创建成功')

    await loadData()
  } catch (error) {
    ElMessage.error('需求创建失败，请检查填写内容和后端服务。')
    console.error(error)
  } finally {
    createSubmitting.value = false
  }
}

onMounted(loadData)
</script>

<template>
  <el-container class="app-shell">
    <el-aside width="236px" class="sidebar">
      <div class="brand">
        <div class="brand-logo">R</div>

        <div class="brand-content">
          <strong>ReqFlow</strong>
          <span>Requirement Agent</span>
        </div>
      </div>

      <el-menu
        v-model="activeMenu"
        class="sidebar-menu"
        default-active="requirements"
      >
        <p class="menu-group-title">工作空间</p>

        <el-menu-item index="dashboard">
          <el-icon><Grid /></el-icon>
          <span>工作台</span>
        </el-menu-item>

        <el-menu-item index="requirements">
          <el-icon><Document /></el-icon>
          <span>需求管理</span>
        </el-menu-item>

        <el-menu-item index="analysis">
          <el-icon><MagicStick /></el-icon>
          <span>智能分析</span>
        </el-menu-item>

        <el-menu-item index="history">
          <el-icon><Clock /></el-icon>
          <span>分析历史</span>
        </el-menu-item>

        <p class="menu-group-title second-group">系统</p>

        <el-menu-item index="settings">
          <el-icon><Setting /></el-icon>
          <span>系统设置</span>
        </el-menu-item>
      </el-menu>

      <div class="sidebar-status">
        <span
          class="status-dot"
          :class="{ online: backendHealthy }"
        ></span>

        <div>
          <strong>
            {{ backendHealthy ? '服务运行正常' : '服务连接异常' }}
          </strong>

          <span>FastAPI Backend</span>
        </div>
      </div>
    </el-aside>

    <el-container class="workspace">
      <el-header class="topbar">
        <div>
          <p class="breadcrumb">工作空间 / 需求管理</p>
          <h1>需求管理</h1>
        </div>

        <div class="topbar-actions">
          <div class="service-status">
            <span
              class="service-dot"
              :class="{ online: backendHealthy }"
            ></span>

            {{ backendHealthy ? '系统正常' : '系统异常' }}
          </div>

          <el-button circle @click="loadData">
            <el-icon><Refresh /></el-icon>
          </el-button>

          <div class="avatar">WG</div>
        </div>
      </el-header>

      <el-main class="main-content">
        <section class="page-heading">
          <div>
            <h2>软件需求列表</h2>

            <p>
              统一管理软件需求，并通过 Agent 完成完整性、歧义和优先级分析。
            </p>
          </div>

          <el-button
            type="primary"
            size="large"
            @click="openCreateDialog"
          >
            <el-icon><Plus /></el-icon>
            新建需求
          </el-button>
        </section>

        <section class="metrics">
          <article class="metric-card">
            <div class="metric-icon blue">
              <el-icon><Document /></el-icon>
            </div>

            <div>
              <span>需求总数</span>
              <strong>{{ requirements.length }}</strong>
              <p>当前系统中的全部需求</p>
            </div>
          </article>

          <article class="metric-card">
            <div class="metric-icon orange">
              <el-icon><WarningFilled /></el-icon>
            </div>

            <div>
              <span>高优先级需求</span>
              <strong>{{ highPriorityCount }}</strong>
              <p>需要优先处理的需求</p>
            </div>
          </article>

          <article class="metric-card">
            <div class="metric-icon green">
              <el-icon><Connection /></el-icon>
            </div>

            <div>
              <span>后端服务</span>

              <strong class="text-value">
                {{ backendHealthy ? '运行正常' : '连接异常' }}
              </strong>

              <p>FastAPI 健康检查结果</p>
            </div>
          </article>
        </section>

        <section class="content-grid">
          <article class="table-panel">
            <div class="panel-toolbar">
              <div>
                <h3>需求列表</h3>
                <p>共 {{ filteredRequirements.length }} 条记录</p>
              </div>

              <div class="filters">
                <el-input
                  v-model="keyword"
                  clearable
                  placeholder="搜索需求标题或内容"
                  class="search-input"
                >
                  <template #prefix>
                    <el-icon><Search /></el-icon>
                  </template>
                </el-input>

                <el-select
                  v-model="priorityFilter"
                  clearable
                  placeholder="全部优先级"
                  class="priority-select"
                >
                  <el-option
                    label="高优先级"
                    :value="1"
                  />

                  <el-option
                    label="中优先级"
                    :value="2"
                  />

                  <el-option
                    label="低优先级"
                    :value="3"
                  />
                </el-select>

                <el-button @click="loadData">
                  <el-icon><Refresh /></el-icon>
                  刷新
                </el-button>
              </div>
            </div>

            <el-table
              v-loading="loading"
              :data="filteredRequirements"
              row-key="id"
              class="requirements-table"
              empty-text="暂无需求数据"
            >
              <el-table-column
                label="需求信息"
                min-width="330"
              >
                <template #default="{ row }">
                  <div class="requirement-cell">
                    <div class="requirement-avatar">
                      {{ row.title.slice(0, 1) }}
                    </div>

                    <div class="requirement-text">
                      <strong>{{ row.title }}</strong>
                      <p>{{ row.content }}</p>
                    </div>
                  </div>
                </template>
              </el-table-column>

              <el-table-column
                label="需求编号"
                width="135"
              >
                <template #default="{ row }">
                  <span class="requirement-code">
                    REQ-{{ String(row.id).padStart(4, '0') }}
                  </span>
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
                label="分析状态"
                width="125"
              >
                <template #default>
                  <span class="analysis-status">
                    <span></span>
                    待分析
                  </span>
                </template>
              </el-table-column>

              <el-table-column
                label="操作"
                width="180"
                fixed="right"
              >
                <template #default>
                  <el-button
                    link
                    type="primary"
                    @click="showPendingMessage('需求详情')"
                  >
                    <el-icon><View /></el-icon>
                    查看
                  </el-button>

                  <el-button
                    link
                    type="primary"
                    @click="showPendingMessage('Agent 分析')"
                  >
                    <el-icon><MagicStick /></el-icon>
                    分析
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
          </article>

          <aside class="agent-panel">
            <div class="agent-heading">
              <div class="agent-logo">
                <el-icon><MagicStick /></el-icon>
              </div>

              <div>
                <h3>Agent 分析流程</h3>
                <p>当前已配置 3 个分析工具</p>
              </div>
            </div>

            <div class="agent-steps">
              <div class="agent-step">
                <div class="step-number">1</div>

                <div>
                  <strong>选择分析工具</strong>
                  <p>Planner 根据需求内容制定工具执行计划。</p>
                </div>
              </div>

              <div class="step-line"></div>

              <div class="agent-step">
                <div class="step-number">2</div>

                <div>
                  <strong>执行需求检查</strong>
                  <p>依次完成完整性、歧义和优先级分析。</p>
                </div>
              </div>

              <div class="step-line"></div>

              <div class="agent-step">
                <div class="step-number">3</div>

                <div>
                  <strong>生成分析报告</strong>
                  <p>汇总工具结果并输出结构化最终报告。</p>
                </div>
              </div>
            </div>

            <div class="tool-list">
              <div class="tool-item">
                <el-icon><CircleCheckFilled /></el-icon>
                完整性检查
              </div>

              <div class="tool-item">
                <el-icon><CircleCheckFilled /></el-icon>
                歧义检测
              </div>

              <div class="tool-item">
                <el-icon><CircleCheckFilled /></el-icon>
                优先级建议
              </div>
            </div>

            <el-button
              type="primary"
              class="start-button"
              @click="showPendingMessage('批量 Agent 分析')"
            >
              启动 Agent 分析
              <el-icon><ArrowRight /></el-icon>
            </el-button>
          </aside>
        </section>
      </el-main>
    </el-container>

    <el-dialog
      v-model="createDialogVisible"
      title="新建软件需求"
      width="580px"
      :close-on-click-modal="false"
      destroy-on-close
    >
      <el-form
        ref="createFormRef"
        :model="createForm"
        :rules="createRules"
        label-position="top"
      >
        <el-form-item
          label="需求标题"
          prop="title"
        >
          <el-input
            v-model="createForm.title"
            maxlength="100"
            show-word-limit
            placeholder="例如：用户登录失败提示"
          />
        </el-form-item>

        <el-form-item
          label="需求内容"
          prop="content"
        >
          <el-input
            v-model="createForm.content"
            type="textarea"
            :rows="6"
            maxlength="5000"
            show-word-limit
            resize="none"
            placeholder="请描述使用场景、用户行为、系统响应和限制条件"
          />
        </el-form-item>

        <el-form-item
          label="需求优先级"
          prop="priority"
        >
          <el-select
            v-model="createForm.priority"
            class="dialog-priority-select"
          >
            <el-option
              label="高优先级"
              :value="1"
            />

            <el-option
              label="中优先级"
              :value="2"
            />

            <el-option
              label="低优先级"
              :value="3"
            />
          </el-select>
        </el-form-item>

        <div class="form-notice">
          <el-icon><InfoFilled /></el-icon>

          <span>
            创建完成后，可以在需求列表中启动 Agent 分析。
          </span>
        </div>
      </el-form>

      <template #footer>
        <el-button
          :disabled="createSubmitting"
          @click="createDialogVisible = false"
        >
          取消
        </el-button>

        <el-button
          type="primary"
          :loading="createSubmitting"
          @click="submitRequirement"
        >
          创建需求
        </el-button>
      </template>
    </el-dialog>
  </el-container>
</template>

<style scoped>
:global(*) {
  box-sizing: border-box;
}

:global(body) {
  margin: 0;
  min-width: 1024px;
  background: #f5f7fa;
  color: #1d2939;
  font-family:
    Inter, "Microsoft YaHei", "PingFang SC", Arial, sans-serif;
}

:global(button),
:global(input) {
  font-family: inherit;
}

.app-shell {
  min-height: 100vh;
}

.sidebar {
  position: fixed;
  inset: 0 auto 0 0;
  z-index: 20;
  display: flex;
  flex-direction: column;
  padding: 24px 14px 18px;
  border-right: 1px solid #e8eaed;
  background: #ffffff;
}

.brand {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 0 10px 28px;
}

.brand-logo {
  width: 40px;
  height: 40px;
  display: grid;
  place-items: center;
  border-radius: 11px;
  background: #4f46e5;
  color: white;
  font-size: 19px;
  font-weight: 800;
  box-shadow: 0 7px 16px rgba(79, 70, 229, 0.25);
}

.brand-content {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.brand-content strong {
  color: #172033;
  font-size: 17px;
}

.brand-content span {
  color: #98a2b3;
  font-size: 10px;
  letter-spacing: 0.7px;
  text-transform: uppercase;
}

.sidebar-menu {
  border-right: 0;
}

.menu-group-title {
  margin: 5px 15px 8px;
  color: #98a2b3;
  font-size: 11px;
  font-weight: 600;
}

.second-group {
  margin-top: 25px;
}

:deep(.el-menu-item) {
  height: 44px;
  margin-bottom: 5px;
  border-radius: 9px;
  color: #667085;
  font-size: 14px;
}

:deep(.el-menu-item .el-icon) {
  font-size: 17px;
}

:deep(.el-menu-item:hover) {
  background: #f6f7fb;
  color: #344054;
}

:deep(.el-menu-item.is-active) {
  background: #eef2ff;
  color: #4f46e5;
  font-weight: 600;
}

.sidebar-status {
  display: flex;
  align-items: center;
  gap: 11px;
  margin-top: auto;
  padding: 14px;
  border: 1px solid #e8eaed;
  border-radius: 11px;
  background: #fafbfc;
}

.status-dot,
.service-dot {
  width: 8px;
  height: 8px;
  flex-shrink: 0;
  border-radius: 50%;
  background: #f04438;
}

.status-dot.online,
.service-dot.online {
  background: #12b76a;
}

.sidebar-status div {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.sidebar-status strong {
  color: #344054;
  font-size: 12px;
}

.sidebar-status span {
  color: #98a2b3;
  font-size: 10px;
}

.workspace {
  min-height: 100vh;
  margin-left: 236px;
}

.topbar {
  height: 82px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 32px;
  border-bottom: 1px solid #e8eaed;
  background: rgba(255, 255, 255, 0.94);
}

.breadcrumb {
  margin: 0 0 6px;
  color: #98a2b3;
  font-size: 12px;
}

.topbar h1 {
  margin: 0;
  color: #101828;
  font-size: 21px;
}

.topbar-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.service-status {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border: 1px solid #e8eaed;
  border-radius: 999px;
  background: white;
  color: #475467;
  font-size: 12px;
  font-weight: 500;
}

.avatar {
  width: 38px;
  height: 38px;
  display: grid;
  place-items: center;
  border-radius: 10px;
  background: #4f46e5;
  color: white;
  font-size: 12px;
  font-weight: 700;
}

.main-content {
  width: 100%;
  max-width: 1680px;
  margin: 0 auto;
  padding: 32px 36px 48px;
}

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

.metrics {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 18px;
  margin-bottom: 20px;
}

.metric-card {
  display: flex;
  gap: 15px;
  padding: 20px;
  border: 1px solid #eaecf0;
  border-radius: 13px;
  background: white;
  box-shadow: 0 1px 3px rgba(16, 24, 40, 0.03);
}

.metric-icon {
  width: 42px;
  height: 42px;
  display: grid;
  place-items: center;
  flex-shrink: 0;
  border-radius: 11px;
  font-size: 19px;
}

.metric-icon.blue {
  background: #eef2ff;
  color: #4f46e5;
}

.metric-icon.orange {
  background: #fff4ed;
  color: #f79009;
}

.metric-icon.green {
  background: #ecfdf3;
  color: #12b76a;
}

.metric-card div:last-child {
  display: flex;
  flex-direction: column;
}

.metric-card span {
  color: #667085;
  font-size: 13px;
}

.metric-card strong {
  margin-top: 5px;
  color: #101828;
  font-size: 26px;
  line-height: 1.1;
}

.metric-card .text-value {
  margin-top: 8px;
  font-size: 20px;
}

.metric-card p {
  margin: 7px 0 0;
  color: #98a2b3;
  font-size: 12px;
}

.content-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 360px;
  gap: 22px;
  align-items: stretch;
}

.table-panel,
.agent-panel {
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

.filters {
  display: flex;
  gap: 10px;
}

.search-input {
  width: 245px;
}

.priority-select {
  width: 145px;
}

.requirements-table {
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

.requirement-cell {
  display: flex;
  align-items: center;
  gap: 12px;
}

.requirement-avatar {
  width: 40px;
  height: 40px;
  display: grid;
  place-items: center;
  flex-shrink: 0;
  border-radius: 10px;
  background: #eef2ff;
  color: #4f46e5;
  font-size: 14px;
  font-weight: 700;
}

.requirement-text {
  min-width: 0;
}

.requirement-text strong {
  display: block;
  overflow: hidden;
  color: #344054;
  font-size: 14px;
  font-weight: 600;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.requirement-text p {
  max-width: 520px;
  margin: 6px 0 0;
  overflow: hidden;
  color: #98a2b3;
  font-size: 13px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.requirement-code {
  color: #667085;
  font-family: Consolas, monospace;
  font-size: 12px;
}

.analysis-status {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  color: #667085;
  font-size: 12px;
}

.analysis-status span {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #f79009;
}

.agent-panel {
  padding: 22px;
}

.agent-heading {
  display: flex;
  align-items: center;
  gap: 12px;
  padding-bottom: 20px;
  border-bottom: 1px solid #eaecf0;
}

.agent-logo {
  width: 42px;
  height: 42px;
  display: grid;
  place-items: center;
  border-radius: 11px;
  background: #4f46e5;
  color: white;
  font-size: 19px;
}

.agent-heading h3 {
  margin: 0;
  color: #101828;
  font-size: 17px;
}

.agent-heading p {
  margin: 5px 0 0;
  color: #98a2b3;
  font-size: 12px;
}

.agent-steps {
  padding: 22px 0;
}

.agent-step {
  display: flex;
  gap: 12px;
}

.step-number {
  width: 27px;
  height: 27px;
  display: grid;
  place-items: center;
  flex-shrink: 0;
  border-radius: 50%;
  background: #eef2ff;
  color: #4f46e5;
  font-size: 12px;
  font-weight: 700;
}

.agent-step strong {
  color: #344054;
  font-size: 14px;
}

.agent-step p {
  margin: 7px 0 0;
  color: #7f899a;
  font-size: 12px;
  line-height: 1.7;
}

.step-line {
  width: 1px;
  height: 27px;
  margin: 4px 0 4px 13px;
  background: #eaecf0;
}

.tool-list {
  display: flex;
  flex-direction: column;
  gap: 9px;
  padding: 15px;
  border-radius: 10px;
  background: #f9fafb;
}

.tool-item {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #475467;
  font-size: 12px;
}

.tool-item .el-icon {
  color: #12b76a;
}

.start-button {
  width: 100%;
  margin-top: 18px;
}

.dialog-priority-select {
  width: 100%;
}

.form-notice {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 14px;
  border-radius: 9px;
  background: #f8fafc;
  color: #667085;
  font-size: 12px;
}

.form-notice .el-icon {
  flex-shrink: 0;
  color: #4f46e5;
  font-size: 16px;
}

:deep(.el-dialog) {
  border-radius: 14px;
}

:deep(.el-dialog__title) {
  color: #101828;
  font-size: 18px;
  font-weight: 600;
}

:deep(.el-form-item__label) {
  color: #344054;
  font-weight: 500;
}

@media (max-width: 1250px) {
  .content-grid {
    grid-template-columns: 1fr;
  }

  .agent-panel {
    width: 100%;
  }

  .filters {
    flex-wrap: wrap;
    justify-content: flex-end;
  }
}
</style>