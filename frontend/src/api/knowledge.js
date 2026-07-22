const KNOWLEDGE_API = '/api/knowledge'

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
      // 后端未返回 JSON 时，仅显示 HTTP 状态码。
    }

    const detailMessage = detail ? `：${detail}` : ''

    throw new Error(
      `知识库接口请求失败（HTTP ${response.status}）${detailMessage}`,
    )
  }

  return response.json()
}

export function listKnowledgeDocuments({
  limit = 100,
  offset = 0,
} = {}) {
  const query = new URLSearchParams({
    limit: String(limit),
    offset: String(offset),
  })

  return requestJson(
    `${KNOWLEDGE_API}/documents?${query.toString()}`,
  )
}

export function createKnowledgeDocument({
  title,
  content,
  source,
}) {
  return requestJson(
    `${KNOWLEDGE_API}/documents`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        title: title.trim(),
        content: content.trim(),
        source: source.trim() || null,
      }),
    },
  )
}