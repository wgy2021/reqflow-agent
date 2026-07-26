const AGENT_RUNS_API = '/api/agent/runs'

async function requestJson(url, options = {}) {
  const response = await fetch(url, options)

  if (!response.ok) {
    let detail = ''

    try {
      const errorData = await response.json()
      detail = errorData.detail ?? ''
    } catch {
      // 后端未返回 JSON 时，保留 HTTP 状态码。
    }

    const detailMessage = detail
      ? `：${detail}`
      : ''

    throw new Error(
      `获取 Agent 运行记录失败（HTTP ${response.status}）${detailMessage}`,
    )
  }

  return response.json()
}

export function listAgentRuns(requirementId = null) {
  const url = requirementId === null
    ? AGENT_RUNS_API
    : `${AGENT_RUNS_API}?requirement_id=${encodeURIComponent(requirementId)}`

  return requestJson(url)
}

export function resolveAgentApproval(runId, approved) {
  const encodedRunId = encodeURIComponent(runId)

  return requestJson(
    `${AGENT_RUNS_API}/${encodedRunId}/approval`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        approved,
      }),
    },
  )
}
export function createAgentRun(
  message,
  maxSteps = 5,
  requirementId = null,
) {
  return requestJson(AGENT_RUNS_API, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      message,
      max_steps: maxSteps,
      requirement_id: requirementId,
    }),
  })
}