const REQUIREMENTS_API = '/api/requirements'

async function requestJson(url, options = {}) {
  const response = await fetch(url, options)

  if (!response.ok) {
    let detail = ''

    try {
      const errorData = await response.json()

      if (typeof errorData.detail === 'string') {
        detail = errorData.detail
      }
    } catch {
      // 后端没有返回 JSON 错误体时，保留 HTTP 状态码。
    }

    const detailMessage = detail ? `：${detail}` : ''

    throw new Error(
      `接口请求失败（HTTP ${response.status}）${detailMessage}`,
    )
  }

  if (response.status === 204) {
    return null
  }

  return response.json()
}

export function listRequirements({
  limit = 100,
  offset = 0,
  priority = null,
} = {}) {
  const query = new URLSearchParams({
    limit: String(limit),
    offset: String(offset),
  })

  if (priority !== null) {
    query.set('priority', String(priority))
  }

  return requestJson(`${REQUIREMENTS_API}?${query.toString()}`)
}

export function createRequirement(payload) {
  return requestJson(REQUIREMENTS_API, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  })
}

export function updateRequirement(requirementId, payload) {
  return requestJson(
    `${REQUIREMENTS_API}/${requirementId}`,
    {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    },
  )
}

export function removeRequirement(requirementId) {
  return requestJson(
    `${REQUIREMENTS_API}/${requirementId}`,
    {
      method: 'DELETE',
    },
  )
}

export function analyzeRequirement(
  requirementId,
  { forceRefresh = false } = {},
) {
  const query = new URLSearchParams()

  if (forceRefresh) {
    query.set('force_refresh', 'true')
  }

  const queryString = query.toString()
  const url = queryString
    ? `${REQUIREMENTS_API}/${requirementId}/analyze?${queryString}`
    : `${REQUIREMENTS_API}/${requirementId}/analyze`

  return requestJson(url, {
    method: 'POST',
  })
}

export function listRequirementAnalyses(
  requirementId,
  {
    limit = 20,
    offset = 0,
  } = {},
) {
  const query = new URLSearchParams({
    limit: String(limit),
    offset: String(offset),
  })

  return requestJson(
    `${REQUIREMENTS_API}/${requirementId}/analyses?${query.toString()}`,
  )
}
