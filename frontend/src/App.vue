<script setup>
import { computed, nextTick, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'

import {
  analyzeRequirement as requestRequirementAnalysis,
  createRequirement as requestCreateRequirement,
  listRequirementAnalyses,
  listRequirements,
  removeRequirement,
  updateRequirement as requestUpdateRequirement,
} from './api/requirements'
import { getSystemHealth } from './api/system'
const route = useRoute()
const router = useRouter()

const requirements = ref([])
const loading = ref(false)
const backendHealthy = ref(false)

const activeMenu = computed(() => route.name ?? 'requirements')
const createDialogVisible = ref(false)
const createSubmitting = ref(false)
const createFormRef = ref()

const editDialogVisible = ref(false)
const editSubmitting = ref(false)
const editFormRef = ref()
const deletingRequirementId = ref(null)

const detailDrawerVisible = ref(false)
const selectedRequirement = ref(null)

const analysisDialogVisible = ref(false)
const analysisLoading = ref(false)
const analysisError = ref('')
const analysisResult = ref(null)
const analysisRequirement = ref(null)
const analyzingRequirementId = ref(null)
const analysisResultsByRequirement = ref({})
const analysisViewMode = ref('live')

const historyLoading = ref(false)
const historyRecords = ref([])
const selectedHistoryRequirementId = ref(null)

const createForm = reactive({
  title: '',
  content: '',
  priority: 2,
})

const editForm = reactive({
  id: null,
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

const pageMeta = {
  dashboard: {
    title: '工作台',
    breadcrumb: '工作空间 / 工作台',
  },
  requirements: {
    title: '需求管理',
    breadcrumb: '工作空间 / 需求管理',
  },
  analysis: {
    title: '智能分析',
    breadcrumb: '工作空间 / 智能分析',
  },
  history: {
    title: '分析历史',
    breadcrumb: '工作空间 / 分析历史',
  },
  settings: {
    title: '系统设置',
    breadcrumb: '系统 / 系统设置',
  },
}

const currentPageTitle = computed(() => {
  return pageMeta[activeMenu.value]?.title ?? 'ReqFlow Agent'
})

const currentBreadcrumb = computed(() => {
  return (
    pageMeta[activeMenu.value]?.breadcrumb ??
    '工作空间'
  )
})

const selectedHistoryRequirement = computed(() => {
  return requirements.value.find(
    (item) => item.id === selectedHistoryRequirementId.value,
  )
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

function formatList(items) {
  if (!items || items.length === 0) {
    return '无'
  }

  return items.join('、')
}

function formatDateTime(value) {
  if (!value) {
    return '--'
  }

  return value.replace('T', ' ').slice(0, 19)
}

async function loadRequirementHistory(requirementId) {
  if (!requirementId) {
    historyRecords.value = []
    return
  }

  historyLoading.value = true

  try {
    historyRecords.value = await listRequirementAnalyses(
      requirementId,
      {
        limit: 100,
        offset: 0,
      },
    )
  } catch (error) {
    historyRecords.value = []
    ElMessage.error('分析历史加载失败，请检查后端服务。')
    console.error(error)
  } finally {
    historyLoading.value = false
  }
}

async function prepareHistoryPage() {
  const firstAnalyzedRequirement = requirements.value.find(
    (item) => analysisResultsByRequirement.value[item.id],
  )

  const fallbackRequirement = requirements.value[0]

  selectedHistoryRequirementId.value =
    selectedHistoryRequirementId.value ??
    firstAnalyzedRequirement?.id ??
    fallbackRequirement?.id ??
    null

  await loadRequirementHistory(
    selectedHistoryRequirementId.value,
  )
}

async function handleMenuSelect(index) {
  if (index === activeMenu.value) {
    return
  }

  await router.push({
    name: index,
  })

  if (index === 'history') {
    await prepareHistoryPage()
  }
}

async function handleHistoryRequirementChange(requirementId) {
  await loadRequirementHistory(requirementId)
}

function openHistoryRecord(record) {
  const requirement = requirements.value.find(
    (item) => item.id === record.requirement_id,
  )

  analysisRequirement.value =
    requirement ??
    {
      id: record.requirement_id,
      title: '历史需求',
    }

  analysisResult.value = record
  analysisError.value = ''
  analysisViewMode.value = 'history'
  analysisDialogVisible.value = true
}

async function loadLatestAnalysisStatuses(requirementItems) {
  const historyEntries = await Promise.all(
    requirementItems.map(async (requirement) => {
      try {
        const history = await listRequirementAnalyses(
          requirement.id,
          {
            limit: 1,
            offset: 0,
          },
        )

        return [requirement.id, history[0] ?? null]
      } catch (error) {
        console.error(
          `加载需求 ${requirement.id} 的分析状态失败：`,
          error,
        )

        return [requirement.id, null]
      }
    }),
  )

  analysisResultsByRequirement.value = Object.fromEntries(
    historyEntries.filter(([, analysis]) => analysis !== null),
  )
}

async function loadData() {
  loading.value = true

  try {
    const [healthData, requirementsData] = await Promise.all([
      getSystemHealth(),
      listRequirements({
        limit: 100,
        offset: 0,
      }),
    ])

    backendHealthy.value = healthData.status === 'ok'
    requirements.value = requirementsData

    await loadLatestAnalysisStatuses(requirementsData)
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

function openDetailDrawer(requirement) {
  selectedRequirement.value = requirement
  detailDrawerVisible.value = true
}

async function openEditDialog(requirement) {
  editForm.id = requirement.id
  editForm.title = requirement.title
  editForm.content = requirement.content
  editForm.priority = requirement.priority

  detailDrawerVisible.value = false
  editDialogVisible.value = true

  await nextTick()
  editFormRef.value?.clearValidate()
}

async function submitRequirementEdit() {
  if (!editFormRef.value || editForm.id === null) {
    return
  }

  const formValid = await editFormRef.value
    .validate()
    .catch(() => false)

  if (!formValid) {
    return
  }

  editSubmitting.value = true

  try {
    const updatedRequirement = await requestUpdateRequirement(
      editForm.id,
      {
        title: editForm.title.trim(),
        content: editForm.content.trim(),
        priority: editForm.priority,
      },
    )

    requirements.value = requirements.value.map((item) =>
      item.id === updatedRequirement.id
        ? updatedRequirement
        : item,
    )

    selectedRequirement.value = updatedRequirement

    const updatedAnalysisStatuses = {
      ...analysisResultsByRequirement.value,
    }

    delete updatedAnalysisStatuses[updatedRequirement.id]
    analysisResultsByRequirement.value =
      updatedAnalysisStatuses

    editDialogVisible.value = false
    detailDrawerVisible.value = true

    ElMessage.success('需求更新成功，请重新执行 Agent 分析')
  } catch (error) {
    ElMessage.error('需求更新失败，请检查填写内容和后端服务。')
    console.error(error)
  } finally {
    editSubmitting.value = false
  }
}

async function deleteRequirement(requirement) {
  try {
    await ElMessageBox.confirm(
      `确定删除“${requirement.title}”吗？该需求的分析历史和缓存也会一起删除，此操作无法撤销。`,
      '删除需求',
      {
        confirmButtonText: '确认删除',
        cancelButtonText: '取消',
        type: 'warning',
        confirmButtonClass: 'danger-confirm-button',
      },
    )
  } catch {
    return
  }

  deletingRequirementId.value = requirement.id

  try {
    await removeRequirement(requirement.id)

    requirements.value = requirements.value.filter(
      (item) => item.id !== requirement.id,
    )

    const updatedAnalysisStatuses = {
      ...analysisResultsByRequirement.value,
    }
    delete updatedAnalysisStatuses[requirement.id]
    analysisResultsByRequirement.value =
      updatedAnalysisStatuses

    if (
      selectedHistoryRequirementId.value ===
      requirement.id
    ) {
      selectedHistoryRequirementId.value =
        requirements.value[0]?.id ?? null

      await loadRequirementHistory(
        selectedHistoryRequirementId.value,
      )
    }

    selectedRequirement.value = null
    detailDrawerVisible.value = false
    editDialogVisible.value = false

    ElMessage.success('需求删除成功')
  } catch (error) {
    ElMessage.error('需求删除失败，请检查后端服务。')
    console.error(error)
  } finally {
    deletingRequirementId.value = null
  }
}

async function runAnalysis(requirement) {
  analysisRequirement.value = requirement
  analysisViewMode.value = 'live'
  analysisResult.value = null
  analysisError.value = ''
  analysisDialogVisible.value = true
  detailDrawerVisible.value = false
  analysisLoading.value = true
  analyzingRequirementId.value = requirement.id

  try {
    const result = await requestRequirementAnalysis(
      requirement.id,
    )

    analysisResult.value = result
    analysisResultsByRequirement.value = {
      ...analysisResultsByRequirement.value,
      [requirement.id]: result,
    }

    if (result.cache_hit) {
      ElMessage.success('已读取缓存中的分析结果')
    } else {
      ElMessage.success('Agent 分析完成')
    }
  } catch (error) {
    analysisError.value =
      'Agent 分析失败，请检查后端服务和模型配置。'
    ElMessage.error(analysisError.value)
    console.error(error)
  } finally {
    analysisLoading.value = false
    analyzingRequirementId.value = null
  }
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
    await requestCreateRequirement({
      title: createForm.title.trim(),
      content: createForm.content.trim(),
      priority: createForm.priority,
    })

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

onMounted(async () => {
  await loadData()

  if (route.name === 'history') {
    await prepareHistoryPage()
  }
})
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
        class="sidebar-menu"
        :default-active="activeMenu"
        @select="handleMenuSelect"
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
          <p class="breadcrumb">{{ currentBreadcrumb }}</p>
          <h1>{{ currentPageTitle }}</h1>
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
        <RouterView v-slot="{ Component, route: currentRoute }">
          <component
            :is="Component"
            v-if="currentRoute.name === 'requirements'"
            :requirements="requirements"
            :loading="loading"
            :backend-healthy="backendHealthy"
            :analysis-results-by-requirement="
              analysisResultsByRequirement
            "
            :analyzing-requirement-id="
              analyzingRequirementId
            "
            @open-create="openCreateDialog"
            @refresh="loadData"
            @open-detail="openDetailDrawer"
            @analyze="runAnalysis"
            @pending="showPendingMessage"
          />

          <component
            :is="Component"
            v-else-if="currentRoute.name === 'history'"
            v-model:selected-requirement-id="
              selectedHistoryRequirementId
            "
            :requirements="requirements"
            :history-records="historyRecords"
            :history-loading="historyLoading"
            @refresh="
              loadRequirementHistory(
                selectedHistoryRequirementId,
              )
            "
            @change="handleHistoryRequirementChange"
            @open-record="openHistoryRecord"
          />

          <component
            :is="Component"
            v-else-if="currentRoute.name === 'dashboard'"
            :requirements="requirements"
            :backend-healthy="backendHealthy"
            :analysis-results-by-requirement="
              analysisResultsByRequirement
            "
            :analyzing-requirement-id="
              analyzingRequirementId
            "
            @open-create="openCreateDialog"
            @open-detail="openDetailDrawer"
            @analyze="runAnalysis"
          />

          <component
            :is="Component"
            v-else
          />
        </RouterView>
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

    <el-dialog
      v-model="editDialogVisible"
      title="编辑软件需求"
      width="580px"
      :close-on-click-modal="false"
      destroy-on-close
    >
      <el-form
        ref="editFormRef"
        :model="editForm"
        :rules="createRules"
        label-position="top"
      >
        <el-form-item
          label="需求标题"
          prop="title"
        >
          <el-input
            v-model="editForm.title"
            maxlength="100"
            show-word-limit
            placeholder="请输入需求标题"
          />
        </el-form-item>

        <el-form-item
          label="需求内容"
          prop="content"
        >
          <el-input
            v-model="editForm.content"
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
            v-model="editForm.priority"
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

        <el-alert
          title="修改标题、内容或优先级后，需要重新执行 Agent 分析。已有分析历史会继续保留。"
          type="warning"
          show-icon
          :closable="false"
        />
      </el-form>

      <template #footer>
        <el-button
          :disabled="editSubmitting"
          @click="
            editDialogVisible = false;
            detailDrawerVisible = true
          "
        >
          取消
        </el-button>

        <el-button
          type="primary"
          :loading="editSubmitting"
          @click="submitRequirementEdit"
        >
          保存修改
        </el-button>
      </template>
    </el-dialog>

    <el-drawer
      v-model="detailDrawerVisible"
      title="需求详情"
      size="520px"
      destroy-on-close
    >
      <div
        v-if="selectedRequirement"
        class="detail-drawer"
      >
        <div class="detail-heading">
          <div class="detail-avatar">
            {{ selectedRequirement.title.slice(0, 1) }}
          </div>

          <div>
            <h3>{{ selectedRequirement.title }}</h3>

            <span class="detail-code">
              REQ-{{ String(selectedRequirement.id).padStart(4, '0') }}
            </span>
          </div>
        </div>

        <el-divider />

        <section class="detail-section">
          <span class="detail-label">需求优先级</span>

          <el-tag
            :type="getPriorityType(selectedRequirement.priority)"
            effect="light"
            round
          >
            {{ getPriorityLabel(selectedRequirement.priority) }}
          </el-tag>
        </section>

        <section class="detail-section detail-content-section">
          <span class="detail-label">需求内容</span>

          <div class="detail-content">
            {{ selectedRequirement.content }}
          </div>
        </section>

        <section class="detail-section">
          <span class="detail-label">当前分析状态</span>

          <span
            class="analysis-status"
            :class="{
              completed:
                analysisResultsByRequirement[
                  selectedRequirement.id
                ],
            }"
          >
            <span></span>
            {{
              analysisResultsByRequirement[
                selectedRequirement.id
              ]
                ? '已分析'
                : '待分析'
            }}
          </span>
        </section>

        <div class="detail-actions">
          <el-button
            type="danger"
            plain
            :loading="
              deletingRequirementId === selectedRequirement.id
            "
            @click="deleteRequirement(selectedRequirement)"
          >
            <el-icon><Delete /></el-icon>
            删除需求
          </el-button>

          <div class="detail-actions-right">
            <el-button @click="detailDrawerVisible = false">
              关闭
            </el-button>

            <el-button
              @click="openEditDialog(selectedRequirement)"
            >
              <el-icon><Edit /></el-icon>
              编辑需求
            </el-button>

            <el-button
              type="primary"
            :loading="
              analyzingRequirementId === selectedRequirement.id
            "
            @click="runAnalysis(selectedRequirement)"
          >
              <el-icon><MagicStick /></el-icon>
              启动 Agent 分析
            </el-button>
          </div>
        </div>
      </div>
    </el-drawer>

    <el-dialog
      v-model="analysisDialogVisible"
      title="Agent 分析结果"
      width="900px"
      :close-on-click-modal="false"
      destroy-on-close
    >
      <div class="analysis-dialog">
        <div
          v-if="analysisRequirement"
          class="analysis-requirement-heading"
        >
          <div>
            <span>当前需求</span>
            <h3>{{ analysisRequirement.title }}</h3>
          </div>

          <span class="detail-code">
            REQ-{{
              String(analysisRequirement.id).padStart(4, '0')
            }}
          </span>
        </div>

        <div
          v-if="analysisLoading"
          class="analysis-loading"
        >
          <el-icon class="is-loading"><Loading /></el-icon>
          <strong>Agent 正在分析需求</strong>
          <p>
            正在规划工具、执行检查并生成最终报告，请稍候。
          </p>
        </div>

        <el-alert
          v-else-if="analysisError"
          :title="analysisError"
          type="error"
          show-icon
          :closable="false"
        />

        <div
          v-else-if="analysisResult"
          class="analysis-result"
        >
          <div class="analysis-badges">
            <el-tag
              :type="analysisResult.passed ? 'success' : 'warning'"
              effect="light"
              round
            >
              {{
                analysisResult.passed
                  ? '整体检查通过'
                  : '发现待改进项'
              }}
            </el-tag>

            <el-tag
              :type="
                analysisViewMode === 'history'
                  ? 'info'
                  : analysisResult.cache_hit
                    ? 'info'
                    : 'primary'
              "
              effect="plain"
              round
            >
              {{
                analysisViewMode === 'history'
                  ? '历史分析记录'
                  : analysisResult.cache_hit
                    ? '缓存命中'
                    : '本次实时分析'
              }}
            </el-tag>

            <el-tag
              v-if="analysisResult.llm_fallback_used"
              type="warning"
              effect="plain"
              round
            >
              已启用模型降级
            </el-tag>
          </div>

          <section class="analysis-overview">
            <article>
              <span>当前优先级</span>
              <strong>
                {{
                  getPriorityLabel(
                    analysisResult.current_priority,
                  )
                }}
              </strong>
            </article>

            <article>
              <span>建议优先级</span>
              <strong>
                {{
                  getPriorityLabel(
                    analysisResult.suggested_priority,
                  )
                }}
              </strong>
            </article>

            <article>
              <span>计划工具数</span>
              <strong>
                {{ analysisResult.planned_tools.length }}
              </strong>
            </article>

            <article>
              <span>发现问题数</span>
              <strong>{{ analysisResult.issues.length }}</strong>
            </article>
          </section>

          <section class="analysis-section">
            <div class="analysis-section-heading">
              <h4>Agent 执行计划</h4>
              <span>Planner 选择的分析工具</span>
            </div>

            <div class="planned-tools">
              <el-tag
                v-for="tool in analysisResult.planned_tools"
                :key="tool"
                effect="plain"
              >
                {{ getToolLabel(tool) }}
              </el-tag>
            </div>
          </section>

          <section class="analysis-section">
            <div class="analysis-section-heading">
              <h4>工具执行结果</h4>
              <span>每个工具返回的结构化检查结果</span>
            </div>

            <div class="tool-result-grid">
              <article
                v-if="analysisResult.tool_results.completeness"
                class="tool-result-card"
              >
                <div class="tool-result-title">
                  <el-icon><CircleCheckFilled /></el-icon>
                  <strong>完整性检查</strong>
                </div>

                <p>
                  状态：
                  {{
                    analysisResult.tool_results.completeness
                      .passed
                      ? '通过'
                      : '未通过'
                  }}
                </p>

                <p>
                  缺失字段：
                  {{
                    formatList(
                      analysisResult.tool_results.completeness
                        .missing_fields,
                    )
                  }}
                </p>
              </article>

              <article
                v-if="analysisResult.tool_results.ambiguity"
                class="tool-result-card"
              >
                <div class="tool-result-title">
                  <el-icon><Search /></el-icon>
                  <strong>歧义检测</strong>
                </div>

                <p>
                  状态：
                  {{
                    analysisResult.tool_results.ambiguity.passed
                      ? '通过'
                      : '发现歧义'
                  }}
                </p>

                <p>
                  命中词语：
                  {{
                    formatList(
                      analysisResult.tool_results.ambiguity
                        .matched_terms,
                    )
                  }}
                </p>
              </article>

              <article
                v-if="analysisResult.tool_results.priority"
                class="tool-result-card"
              >
                <div class="tool-result-title">
                  <el-icon><WarningFilled /></el-icon>
                  <strong>优先级建议</strong>
                </div>

                <p>
                  建议：
                  {{
                    getPriorityLabel(
                      analysisResult.tool_results.priority
                        .suggested_priority,
                    )
                  }}
                </p>

                <p>
                  原因：
                  {{
                    analysisResult.tool_results.priority.reason
                  }}
                </p>
              </article>
            </div>
          </section>

          <section class="analysis-section">
            <div class="analysis-section-heading">
              <h4>发现的问题</h4>
              <span>需要进一步完善的需求内容</span>
            </div>

            <el-empty
              v-if="analysisResult.issues.length === 0"
              description="未发现明显问题"
              :image-size="70"
            />

            <ul v-else class="issue-list">
              <li
                v-for="issue in analysisResult.issues"
                :key="issue"
              >
                <el-icon><WarningFilled /></el-icon>
                <span>{{ issue }}</span>
              </li>
            </ul>
          </section>

          <section class="analysis-section report-section">
            <div class="analysis-section-heading">
              <h4>最终分析报告</h4>
              <span>模型结合工具结果生成的总结</span>
            </div>

            <div class="final-report">
              {{ analysisResult.final_report }}
            </div>
          </section>

          <el-alert
            v-if="analysisResult.llm_error"
            :title="analysisResult.llm_error"
            type="warning"
            show-icon
            :closable="false"
          />
        </div>
      </div>

      <template #footer>
        <el-button @click="analysisDialogVisible = false">
          关闭
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

.detail-drawer {
  display: flex;
  min-height: calc(100vh - 110px);
  flex-direction: column;
}

.detail-heading {
  display: flex;
  align-items: center;
  gap: 14px;
}

.detail-avatar {
  width: 48px;
  height: 48px;
  display: grid;
  place-items: center;
  flex-shrink: 0;
  border-radius: 12px;
  background: #eef2ff;
  color: #4f46e5;
  font-size: 18px;
  font-weight: 700;
}

.detail-heading h3 {
  margin: 0 0 7px;
  color: #101828;
  font-size: 19px;
}

.detail-code {
  color: #98a2b3;
  font-family: Consolas, monospace;
  font-size: 12px;
}

.detail-section {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  padding: 17px 0;
  border-bottom: 1px solid #eaecf0;
}

.detail-content-section {
  align-items: flex-start;
  flex-direction: column;
}

.detail-label {
  color: #667085;
  font-size: 13px;
  font-weight: 500;
}

.detail-content {
  width: 100%;
  padding: 16px;
  border: 1px solid #eaecf0;
  border-radius: 10px;
  background: #f9fafb;
  color: #344054;
  font-size: 14px;
  line-height: 1.8;
  white-space: pre-wrap;
  word-break: break-word;
}

.detail-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-top: auto;
  padding-top: 24px;
}

.detail-actions-right {
  display: flex;
  align-items: center;
  gap: 10px;
}

:deep(.el-drawer__title) {
  color: #101828;
  font-size: 18px;
  font-weight: 600;
}

.analysis-status.completed {
  color: #067647;
}

.analysis-status.completed span {
  background: #12b76a;
}

.analysis-dialog {
  min-height: 250px;
}

.analysis-requirement-heading {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 20px;
  padding: 2px 0 18px;
  border-bottom: 1px solid #eaecf0;
}

.analysis-requirement-heading span:first-child {
  color: #98a2b3;
  font-size: 12px;
}

.analysis-requirement-heading h3 {
  margin: 7px 0 0;
  color: #101828;
  font-size: 18px;
}

.analysis-loading {
  min-height: 320px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  color: #667085;
  text-align: center;
}

.analysis-loading .el-icon {
  color: #4f46e5;
  font-size: 38px;
}

.analysis-loading strong {
  margin-top: 18px;
  color: #101828;
  font-size: 16px;
}

.analysis-loading p {
  margin: 8px 0 0;
  font-size: 13px;
}

.analysis-badges {
  display: flex;
  flex-wrap: wrap;
  gap: 9px;
  padding: 18px 0;
}

.analysis-overview {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
}

.analysis-overview article {
  padding: 15px;
  border: 1px solid #eaecf0;
  border-radius: 10px;
  background: #f9fafb;
}

.analysis-overview span {
  display: block;
  color: #667085;
  font-size: 12px;
}

.analysis-overview strong {
  display: block;
  margin-top: 8px;
  color: #101828;
  font-size: 17px;
}

.analysis-section {
  margin-top: 22px;
  padding-top: 20px;
  border-top: 1px solid #eaecf0;
}

.analysis-section-heading {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 20px;
  margin-bottom: 14px;
}

.analysis-section-heading h4 {
  margin: 0;
  color: #101828;
  font-size: 15px;
}

.analysis-section-heading span {
  color: #98a2b3;
  font-size: 11px;
}

.planned-tools {
  display: flex;
  flex-wrap: wrap;
  gap: 9px;
}

.tool-result-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

.tool-result-card {
  min-height: 145px;
  padding: 16px;
  border: 1px solid #eaecf0;
  border-radius: 11px;
  background: #ffffff;
}

.tool-result-title {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #344054;
}

.tool-result-title .el-icon {
  color: #4f46e5;
}

.tool-result-card p {
  margin: 12px 0 0;
  color: #667085;
  font-size: 12px;
  line-height: 1.7;
}

.issue-list {
  display: flex;
  flex-direction: column;
  gap: 9px;
  margin: 0;
  padding: 0;
  list-style: none;
}

.issue-list li {
  display: flex;
  align-items: flex-start;
  gap: 9px;
  padding: 12px 14px;
  border-radius: 9px;
  background: #fffaeb;
  color: #7a2e0e;
  font-size: 13px;
  line-height: 1.6;
}

.issue-list .el-icon {
  flex-shrink: 0;
  margin-top: 3px;
  color: #f79009;
}

.report-section {
  padding-bottom: 4px;
}

.final-report {
  padding: 17px;
  border: 1px solid #e0e7ff;
  border-radius: 10px;
  background: #f8f9ff;
  color: #344054;
  font-size: 13px;
  line-height: 1.85;
  white-space: pre-wrap;
  word-break: break-word;
}

:global(.danger-confirm-button) {
  border-color: #d92d20 !important;
  background: #d92d20 !important;
}

:global(.danger-confirm-button:hover) {
  border-color: #b42318 !important;
  background: #b42318 !important;
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