// API client — all calls go to relative /api paths (Vite proxies to FastAPI).
// The browser never holds an LLM key; the backend owns all AI calls.

async function request(path, options = {}) {
  const res = await fetch(path, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const body = await res.json();
      detail = body.detail || detail;
    } catch (_) {
      /* ignore */
    }
    throw new Error(detail);
  }
  return res.json();
}

export const api = {
  meta: () => request('/api/meta'),
  createSession: (consentGiven = true, locale = 'hi-IN') =>
    request('/api/session', {
      method: 'POST',
      body: JSON.stringify({ consent_given: consentGiven, locale }),
    }),
  turn: (sessionId, userText) =>
    request('/api/conversation/turn', {
      method: 'POST',
      body: JSON.stringify({ session_id: sessionId, user_text: userText }),
    }),
  confirm: (sessionId, userText = null) =>
    request('/api/conversation/confirm', {
      method: 'POST',
      body: JSON.stringify({ session_id: sessionId, user_text: userText }),
    }),
  recommend: (profile) =>
    request('/api/recommend', {
      method: 'POST',
      body: JSON.stringify({ profile }),
    }),
  deleteMyData: (sessionId) =>
    request(`/api/session/${sessionId}`, { method: 'DELETE' }),
};
