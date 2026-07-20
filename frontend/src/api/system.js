const SYSTEM_API = '/api'

async function requestJson(url, options = {}) {
  const response = await fetch(url, options)

  if (!response.ok) {
    throw new Error(
      `系统接口请求失败（HTTP ${response.status}）`,
    )
  }

  return response.json()
}

export function getSystemHealth() {
  return requestJson(`${SYSTEM_API}/health`)
}
