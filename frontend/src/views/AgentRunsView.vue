<script setup>
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

      <el-button type="primary">
        <el-icon><Refresh /></el-icon>
        刷新记录
      </el-button>
    </div>

    <el-card shadow="never" class="placeholder-card">
      <el-empty description="运行记录列表将在下一步接入">
        <template #image>
          <div class="empty-mark">
            <el-icon><Operation /></el-icon>
          </div>
        </template>
      </el-empty>
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
