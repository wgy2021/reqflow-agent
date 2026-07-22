<template>
  <section class="knowledge-page">
    <div class="knowledge-toolbar">
      <div>
        <h2>知识库管理</h2>
        <p>维护用于 RAG 检索与需求分析的知识文档。</p>
      </div>

      <el-button type="primary">
        新建知识文档
      </el-button>
    </div>

    <el-card shadow="never">
      <el-empty description="知识库数据将在下一步接入" />
    </el-card>
  </section>
</template>

<style scoped>
.knowledge-page {
  display: grid;
  gap: 16px;
}

.knowledge-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
}

.knowledge-toolbar h2 {
  margin: 0;
  color: #172033;
  font-size: 20px;
}

.knowledge-toolbar p {
  margin: 6px 0 0;
  color: #86909c;
  font-size: 13px;
}
</style>