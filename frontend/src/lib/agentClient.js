import { supabase } from './supabaseClient'

const BASE = import.meta.env.VITE_BACKEND_URL
if (!BASE) throw new Error('Missing VITE_BACKEND_URL in .env')

async function getToken() {
  const { data: { session } } = await supabase.auth.getSession()
  if (!session?.access_token) throw new Error('Not authenticated')
  return session.access_token
}

async function authFetch(path, opts = {}) {
  const t = await getToken()
  const res = await fetch(`${BASE}${path}`, {
    ...opts,
    headers: { Authorization: `Bearer ${t}`, ...opts.headers },
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Request failed' }))
    throw new Error(err.detail || `HTTP ${res.status}`)
  }
  return res.json()
}

// ── Policy Parser ──────────────────────────────────────────────────────────
export async function uploadPolicyPDF(file, onProgress) {
  const t = await getToken()
  const form = new FormData()
  form.append('file', file)
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest()
    xhr.upload.addEventListener('progress', e => {
      if (e.lengthComputable && onProgress) onProgress(Math.round(e.loaded / e.total * 100))
    })
    xhr.addEventListener('load', () => {
      if (xhr.status >= 200 && xhr.status < 300) resolve(JSON.parse(xhr.responseText))
      else {
        try { reject(new Error(JSON.parse(xhr.responseText).detail)) }
        catch { reject(new Error(`Upload failed: ${xhr.status}`)) }
      }
    })
    xhr.addEventListener('error', () => reject(new Error('Network error')))
    xhr.open('POST', `${BASE}/api/policy/upload`)
    xhr.setRequestHeader('Authorization', `Bearer ${t}`)
    xhr.send(form)
  })
}

export const listDocuments = () => authFetch('/api/policy/documents')

// ── Decision Tracer ────────────────────────────────────────────────────────
export const traceDenial = (payload) =>
  authFetch('/api/trace/denial', {
    method:  'POST',
    headers: { 'Content-Type': 'application/json' },
    body:    JSON.stringify(payload),
  })

// ── MCP ───────────────────────────────────────────────────────────────────
export const sendExplanationEmail = (payload) =>
  authFetch('/api/mcp/email', {
    method:  'POST',
    headers: { 'Content-Type': 'application/json' },
    body:    JSON.stringify(payload),
  })

export const createAppealDeadline = (payload) =>
  authFetch('/api/mcp/calendar', {
    method:  'POST',
    headers: { 'Content-Type': 'application/json' },
    body:    JSON.stringify(payload),
  })

// ── Audit ─────────────────────────────────────────────────────────────────
export const getAuditLog = () => authFetch('/api/audit/logs')

// ── Evals ─────────────────────────────────────────────────────────────────
export const runEval = (payload) =>
  authFetch('/api/evals/run', {
    method:  'POST',
    headers: { 'Content-Type': 'application/json' },
    body:    JSON.stringify(payload),
  })

// ── Health ────────────────────────────────────────────────────────────────
export const checkHealth = () => fetch(`${BASE}/health`).then(r => r.json())
