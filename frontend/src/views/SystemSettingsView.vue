<script setup>
import { computed } from 'vue'

const props = defineProps({
  backendHealthy: {
    type: Boolean,
    default: false,
  },
  systemInfo: {
    type: Object,
    default: null,
  },
  requirements: {
    type: Array,
    default: () => [],
  },
  analysisResultsByRequirement: {
    type: Object,
    default: () => ({}),
  },
})

const analyzedCount = computed(() => {
  return props.requirements.filter(
    (item) => props.analysisResultsByRequirement[item.id],
  ).length
})

const pendingCount = computed(() => {
  return props.requirements.length - analyzedCount.value
})

const coverageRate = computed(() => {
  if (props.requirements.length === 0) {
    return 0
  }

  return Math.round(
    (analyzedCount.value / props.requirements.length) * 100,
  )
})

const providerLabel = computed(() => {
  return props.systemInfo?.llm_provider ?? '未获取'
})

const modelLabel = computed(() => {
  return props.systemInfo?.llm_model ?? '未配置'
})

const environmentLabel = computed(() => {
  return props.systemInfo?.environment ?? '未获取'
})

const serviceVersion = computed(() => {
  return props.systemInfo?.version ?? '--'
})

const databaseLabel = computed(() => {
  const databaseType =
    props.systemInfo?.database_type ?? '未获取'

  return databaseType === 'sqlite'
    ? 'SQLite'
    : databaseType
})

const cacheVersion = computed(() => {
  return props.systemInfo?.cache_version ?? '--'
})

const registeredToolCount = computed(() => {
  return props.systemInfo?.tool_count ?? 0
})

const serviceItems = computed(() => [
  {
    name: 'FastAPI 服务',
    description: `ReqFlow Agent ${serviceVersion.value}`,
    status: props.backendHealthy ? '运行正常' : '连接异常',
    healthy: props.backendHealthy,
    icon: 'api',
  },
  {
    name: `${databaseLabel.value} 数据库`,
    description: '通过 SQLAlchemy 与 Alembic 管理数据结构',
    status: props.backendHealthy ? '可访问' : '待检查',
    healthy: props.backendHealthy,
    icon: 'database',
  },
  {
    name: 'Agent 工具注册中心',
    description: '由后端 Tool Registry 返回真实注册信息',
    status: `${registeredToolCount.value} 个工具`,
    healthy: props.backendHealthy,
    icon: 'tools',
  },
  {
    name: '分析历史',
    description: '保存每次 Agent 分析结果与最终报告',
    status: `${analyzedCount.value} 条需求`,
    healthy: true,
    icon: 'history',
  },
])

const toolMetadata = {
  completeness_check: {
    label: '完整性检查',
    description: '检查标题、内容和优先级等必要字段。',
  },
  ambiguity_check: {
    label: '歧义检测',
    description: '识别模糊词、范围不清和验收条件缺失。',
  },
  priority_suggestion: {
    label: '优先级建议',
    description: '根据需求影响范围建议处理优先级。',
  },
}

const toolItems = computed(() => {
  const toolNames = props.systemInfo?.tools ?? []

  return toolNames.map((name) => ({
    name,
    label: toolMetadata[name]?.label ?? name,
    description:
      toolMetadata[name]?.description ??
      '由后端 Tool Registry 注册的 Agent 工具。',
  }))
})

</script>

<template>
  <section class="page-heading">
    <div>
      <h2>系统设置</h2>
      <p>
        查看服务状态、模型接入方式、工具注册与部署配置。
      </p>
    </div>

    <el-tag
      :type="backendHealthy ? 'success' : 'danger'"
      effect="light"
      round
    >
      {{ backendHealthy ? '系统运行正常' : '系统连接异常' }}
    </el-tag>
  </section>

  <section class="summary-panel">
    <article>
      <span>需求总数</span>
      <strong>{{ requirements.length }}</strong>
      <p>当前数据库中的需求记录</p>
    </article>

    <article>
      <span>已分析需求</span>
      <strong>{{ analyzedCount }}</strong>
      <p>已保存最近分析结果</p>
    </article>

    <article>
      <span>待分析需求</span>
      <strong>{{ pendingCount }}</strong>
      <p>等待执行 Agent 工作流</p>
    </article>

    <article>
      <span>分析覆盖率</span>
      <strong>{{ coverageRate }}%</strong>
      <p>已分析需求占全部需求比例</p>
    </article>
  </section>

  <section class="settings-grid">
    <article class="panel service-panel">
      <div class="panel-heading">
        <div>
          <h3>运行状态</h3>
          <p>核心服务与基础设施状态概览。</p>
        </div>
      </div>

      <div class="service-list">
        <div
          v-for="item in serviceItems"
          :key="item.name"
          class="service-row"
        >
          <div
            class="service-icon"
            :class="item.icon"
          >
            <el-icon v-if="item.icon === 'api'">
              <Connection />
            </el-icon>

            <el-icon v-else-if="item.icon === 'database'">
              <Coin />
            </el-icon>

            <el-icon v-else-if="item.icon === 'tools'">
              <Tools />
            </el-icon>

            <el-icon v-else>
              <Clock />
            </el-icon>
          </div>

          <div class="service-copy">
            <strong>{{ item.name }}</strong>
            <p>{{ item.description }}</p>
          </div>

          <span
            class="service-status"
            :class="{ error: !item.healthy }"
          >
            <i></i>
            {{ item.status }}
          </span>
        </div>
      </div>
    </article>

    <article class="panel model-panel">
      <div class="panel-heading">
        <div>
          <h3>模型接入</h3>
          <p>当前项目使用兼容 OpenAI 接口协议的模型客户端。</p>
        </div>

        <el-tag
          type="info"
          effect="plain"
        >
          后端环境变量
        </el-tag>
      </div>

      <div class="config-list">
        <div class="config-row">
          <span>LLM Provider</span>
          <strong>{{ providerLabel }}</strong>
        </div>

        <div class="config-row">
          <span>模型名称</span>
          <strong>{{ modelLabel }}</strong>
        </div>

        <div class="config-row">
          <span>运行环境</span>
          <strong>{{ environmentLabel }}</strong>
        </div>

        <div class="config-row">
          <span>服务版本</span>
          <strong>{{ serviceVersion }}</strong>
        </div>

        <div class="config-row">
          <span>异常策略</span>
          <strong>真实模型失败后自动降级</strong>
        </div>
      </div>

      <el-alert
        title="API Key 仅保存在后端环境变量中，前端不会读取或展示密钥。"
        type="success"
        show-icon
        :closable="false"
      />
    </article>

    <article class="panel tools-panel">
      <div class="panel-heading">
        <div>
          <h3>Agent 工具注册</h3>
          <p>Planner 可根据需求内容选择下列工具。</p>
        </div>

        <span class="panel-count">
          {{ toolItems.length }} 个工具
        </span>
      </div>

      <div class="tool-list">
        <div
          v-for="tool in toolItems"
          :key="tool.name"
          class="tool-row"
        >
          <div class="tool-icon">
            <el-icon><MagicStick /></el-icon>
          </div>

          <div>
            <strong>{{ tool.label }}</strong>
            <code>{{ tool.name }}</code>
            <p>{{ tool.description }}</p>
          </div>

          <el-tag
            type="success"
            effect="light"
            round
          >
            已注册
          </el-tag>
        </div>
      </div>
    </article>

    <article class="panel cache-panel">
      <div class="panel-heading">
        <div>
          <h3>缓存与历史</h3>
          <p>减少重复模型调用并保存可追溯结果。</p>
        </div>
      </div>

      <div class="feature-list">
        <div class="feature-row">
          <el-icon><Lock /></el-icon>

          <div>
            <strong>
              内容指纹缓存（{{ cacheVersion }}）
            </strong>
            <p>
              根据标题、内容、优先级和版本生成 SHA-256 指纹。
            </p>
          </div>
        </div>

        <div class="feature-row">
          <el-icon><RefreshRight /></el-icon>

          <div>
            <strong>自动失效</strong>
            <p>
              需求内容发生修改后，旧缓存不会继续命中。
            </p>
          </div>
        </div>

        <div class="feature-row">
          <el-icon><Timer /></el-icon>

          <div>
            <strong>强制刷新</strong>
            <p>
              支持跳过缓存，重新执行 Planner 和工具链。
            </p>
          </div>
        </div>

        <div class="feature-row">
          <el-icon><DocumentCopy /></el-icon>

          <div>
            <strong>分析历史</strong>
            <p>
              每次分析结果持久化保存，支持分页查看。
            </p>
          </div>
        </div>
      </div>
    </article>

    <article class="panel deployment-panel">
      <div class="panel-heading">
        <div>
          <h3>部署信息</h3>
          <p>项目当前支持的运行与交付方式。</p>
        </div>
      </div>

      <div class="deployment-grid">
        <div>
          <span>后端框架</span>
          <strong>FastAPI</strong>
        </div>

        <div>
          <span>前端框架</span>
          <strong>Vue 3 + Vite</strong>
        </div>

        <div>
          <span>数据库</span>
          <strong>{{ databaseLabel }} + Alembic</strong>
        </div>

        <div>
          <span>容器化</span>
          <strong>Docker Compose</strong>
        </div>

        <div>
          <span>缓存版本</span>
          <strong>{{ cacheVersion }}</strong>
        </div>

        <div>
          <span>持续集成</span>
          <strong>GitHub Actions</strong>
        </div>
      </div>
    </article>

    <article class="panel security-panel">
      <div class="panel-heading">
        <div>
          <h3>安全说明</h3>
          <p>当前项目已经采用的基础安全措施。</p>
        </div>
      </div>

      <ul class="security-list">
        <li>
          <el-icon><CircleCheckFilled /></el-icon>
          <span>.env 与数据库文件不会提交到 Git 仓库</span>
        </li>

        <li>
          <el-icon><CircleCheckFilled /></el-icon>
          <span>测试环境固定使用 FakeLLM，不调用真实 API</span>
        </li>

        <li>
          <el-icon><CircleCheckFilled /></el-icon>
          <span>容器默认使用 FakeLLM，避免意外产生费用</span>
        </li>

        <li>
          <el-icon><CircleCheckFilled /></el-icon>
          <span>删除需求时同步清理缓存和分析历史</span>
        </li>
      </ul>
    </article>
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

.summary-panel {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  margin-bottom: 16px;
  border: 1px solid #e5e6eb;
  background: white;
}

.summary-panel article {
  padding: 18px 20px;
  border-right: 1px solid #e5e6eb;
}

.summary-panel article:last-child {
  border-right: 0;
}

.summary-panel span {
  color: #86909c;
  font-size: 12px;
}

.summary-panel strong {
  display: block;
  margin-top: 8px;
  color: #1d2129;
  font-size: 24px;
  font-weight: 600;
}

.summary-panel p {
  margin: 7px 0 0;
  color: #c2c7d0;
  font-size: 10px;
}

.settings-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
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

.panel-count {
  color: #86909c;
  font-size: 11px;
}

.service-panel,
.tools-panel,
.deployment-panel {
  grid-column: 1 / -1;
}

.service-list {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
}

.service-row {
  display: grid;
  grid-template-columns: 40px minmax(0, 1fr) auto;
  align-items: center;
  gap: 12px;
  padding: 18px;
  border-right: 1px solid #f2f3f5;
  border-bottom: 1px solid #f2f3f5;
}

.service-row:nth-child(2n) {
  border-right: 0;
}

.service-row:nth-last-child(-n + 2) {
  border-bottom: 0;
}

.service-icon {
  width: 40px;
  height: 40px;
  display: grid;
  place-items: center;
  border-radius: 4px;
  background: #e8f3ff;
  color: #165dff;
  font-size: 18px;
}

.service-icon.database {
  background: #f2f3ff;
  color: #722ed1;
}

.service-icon.tools {
  background: #fff7e8;
  color: #ff7d00;
}

.service-icon.history {
  background: #e8ffea;
  color: #00b42a;
}

.service-copy strong {
  color: #1d2129;
  font-size: 12px;
  font-weight: 500;
}

.service-copy p {
  margin: 5px 0 0;
  color: #86909c;
  font-size: 10px;
}

.service-status {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: #00b42a;
  font-size: 10px;
}

.service-status i {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #00b42a;
}

.service-status.error {
  color: #f53f3f;
}

.service-status.error i {
  background: #f53f3f;
}

.config-list {
  padding: 4px 18px 12px;
}

.config-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  padding: 14px 0;
  border-bottom: 1px solid #f2f3f5;
}

.config-row span {
  color: #86909c;
  font-size: 11px;
}

.config-row strong {
  color: #1d2129;
  font-size: 11px;
  font-weight: 500;
}

.model-panel :deep(.el-alert) {
  margin: 0 18px 18px;
}

.tool-list {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
}

.tool-row {
  display: grid;
  grid-template-columns: 38px minmax(0, 1fr) auto;
  align-items: flex-start;
  gap: 11px;
  padding: 18px;
  border-right: 1px solid #f2f3f5;
}

.tool-row:last-child {
  border-right: 0;
}

.tool-icon {
  width: 38px;
  height: 38px;
  display: grid;
  place-items: center;
  border-radius: 4px;
  background: #e8f3ff;
  color: #165dff;
}

.tool-row strong {
  display: block;
  color: #1d2129;
  font-size: 12px;
  font-weight: 500;
}

.tool-row code {
  display: block;
  margin-top: 5px;
  color: #165dff;
  font-size: 9px;
}

.tool-row p {
  margin: 7px 0 0;
  color: #86909c;
  font-size: 10px;
  line-height: 1.6;
}

.feature-list {
  padding: 3px 18px 12px;
}

.feature-row {
  display: flex;
  gap: 12px;
  padding: 14px 0;
  border-bottom: 1px solid #f2f3f5;
}

.feature-row:last-child {
  border-bottom: 0;
}

.feature-row > .el-icon {
  margin-top: 2px;
  color: #165dff;
  font-size: 17px;
}

.feature-row strong {
  color: #1d2129;
  font-size: 11px;
  font-weight: 500;
}

.feature-row p {
  margin: 5px 0 0;
  color: #86909c;
  font-size: 10px;
  line-height: 1.6;
}

.deployment-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
}

.deployment-grid div {
  padding: 18px;
  border-right: 1px solid #f2f3f5;
  border-bottom: 1px solid #f2f3f5;
}

.deployment-grid div:nth-child(3n) {
  border-right: 0;
}

.deployment-grid div:nth-last-child(-n + 3) {
  border-bottom: 0;
}

.deployment-grid span {
  color: #86909c;
  font-size: 10px;
}

.deployment-grid strong {
  display: block;
  margin-top: 7px;
  color: #1d2129;
  font-size: 13px;
}

.security-list {
  display: flex;
  flex-direction: column;
  gap: 13px;
  margin: 0;
  padding: 18px;
  list-style: none;
}

.security-list li {
  display: flex;
  align-items: flex-start;
  gap: 9px;
  color: #4e5969;
  font-size: 11px;
  line-height: 1.6;
}

.security-list .el-icon {
  flex-shrink: 0;
  margin-top: 2px;
  color: #00b42a;
}

@media (max-width: 1250px) {
  .summary-panel {
    grid-template-columns: repeat(2, 1fr);
  }

  .summary-panel article:nth-child(2) {
    border-right: 0;
  }

  .summary-panel article:nth-child(-n + 2) {
    border-bottom: 1px solid #e5e6eb;
  }

  .settings-grid {
    grid-template-columns: 1fr;
  }

  .service-panel,
  .tools-panel,
  .deployment-panel {
    grid-column: auto;
  }

  .service-list,
  .tool-list,
  .deployment-grid {
    grid-template-columns: 1fr;
  }

  .service-row,
  .tool-row,
  .deployment-grid div {
    border-right: 0;
    border-bottom: 1px solid #f2f3f5;
  }
}
</style>
