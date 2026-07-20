<script setup>
import { onMounted, ref } from 'vue'

const backendStatus = ref('正在检查后端连接...')
const backendHealthy = ref(false)

async function checkBackend() {
  backendStatus.value = '正在检查后端连接...'
  backendHealthy.value = false

  try {
    const response = await fetch('/api/health')

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`)
    }

    const data = await response.json()

    if (data.status === 'ok') {
      backendHealthy.value = true
      backendStatus.value = `后端连接正常：${data.service}`
    } else {
      backendStatus.value = '后端返回了异常状态'
    }
  } catch (error) {
    backendStatus.value = '后端连接失败，请检查 Docker 容器'
    console.error('检查后端失败：', error)
  }
}

onMounted(checkBackend)
</script>

<template>
  <main class="page">
    <section class="hero">
      <p class="label">AI REQUIREMENT ANALYSIS</p>

      <h1>ReqFlow Agent</h1>

      <p class="description">
        面向软件需求场景的智能分析平台
      </p>

      <div
        class="status-card"
        :class="{ healthy: backendHealthy }"
      >
        <span class="status-dot"></span>

        <div>
          <strong>系统状态</strong>
          <p>{{ backendStatus }}</p>
        </div>
      </div>

      <button type="button" @click="checkBackend">
        重新检查
      </button>
    </section>
  </main>
</template>

<style scoped>
* {
  box-sizing: border-box;
}

.page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 32px;
  background:
    radial-gradient(circle at top left, #e0e7ff, transparent 35%),
    #f7f8fc;
  font-family:
    Inter, "Microsoft YaHei", Arial, sans-serif;
}

.hero {
  width: 100%;
  max-width: 720px;
  padding: 56px;
  border: 1px solid #e5e7eb;
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.92);
  box-shadow: 0 24px 70px rgba(15, 23, 42, 0.1);
}

.label {
  margin: 0 0 14px;
  color: #4f46e5;
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 2px;
}

h1 {
  margin: 0;
  color: #111827;
  font-size: 52px;
  line-height: 1.1;
}

.description {
  margin: 20px 0 36px;
  color: #6b7280;
  font-size: 18px;
}

.status-card {
  display: flex;
  gap: 16px;
  align-items: flex-start;
  padding: 20px;
  border: 1px solid #fecaca;
  border-radius: 14px;
  background: #fff7f7;
}

.status-card.healthy {
  border-color: #bbf7d0;
  background: #f0fdf4;
}

.status-dot {
  width: 12px;
  height: 12px;
  margin-top: 5px;
  flex-shrink: 0;
  border-radius: 50%;
  background: #ef4444;
}

.healthy .status-dot {
  background: #22c55e;
}

.status-card strong {
  color: #111827;
}

.status-card p {
  margin: 6px 0 0;
  color: #6b7280;
}

button {
  margin-top: 24px;
  padding: 12px 20px;
  border: 0;
  border-radius: 10px;
  background: #4f46e5;
  color: white;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
}

button:hover {
  background: #4338ca;
}
</style>