import { useState, useEffect } from 'react'
import { getAuditLog } from '../lib/agentClient'

const COLORS = {
  login:                  { bg:'#f0fdf4', border:'#bbf7d0', color:'#166534', icon:'🔐' },
  logout:                 { bg:'#f8fafc', border:'#e2e8f0', color:'#475569', icon:'🚪' },
  pdf_upload:             { bg:'#f0f9ff', border:'#bae6fd', color:'#0369a1', icon:'📄' },
  policy_parse_complete:  { bg:'#f0fdf4', border:'#bbf7d0', color:'#166534', icon:'✅' },
  policy_parse_failed:    { bg:'#fef2f2', border:'#fecaca', color:'#dc2626', icon:'❌' },
  denial_trace:           { bg:'#faf5ff', border:'#e9d5ff', color:'#7c3aed', icon:'🔍' },
  appeal_draft:           { bg:'#fff7ed', border:'#fed7aa', color:'#c2410c', icon:'✍️' },
  email_sent:             { bg:'#f0f9ff', border:'#bae6fd', color:'#0369a1', icon:'📧' },
  calendar_event_created: { bg:'#f0f9ff', border:'#bae6fd', color:'#0369a1', icon:'📅' },
}

export default function AuditLog() {
  const [logs,    setLogs]    = useState([])
  const [loading, setLoading] = useState(true)
  const [error,   setError]   = useState('')

  useEffect(() => {
    getAuditLog()
      .then(d => setLogs(d.logs || []))
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  const fmt = iso => {
    if (!iso) return '—'
    return new Date(iso).toLocaleString('en-US', { month:'short', day:'numeric', hour:'2-digit', minute:'2-digit' })
  }

  return (
    <div style={{ maxWidth:760 }}>
      <h2 style={{ fontSize:20,fontWeight:700,color:'#0f172a',marginBottom:4 }}>Audit Log</h2>
      <p style={{ fontSize:13,color:'#64748b',marginBottom:8 }}>Every action logged with timestamp — required for HIPAA compliance</p>
      <span style={{ display:'inline-flex',alignItems:'center',gap:6,background:'#f0fdf4',border:'1px solid #bbf7d0',borderRadius:6,padding:'5px 12px',fontSize:11,color:'#166534',fontWeight:500,marginBottom:24 }}>
        🛡 HIPAA-compliant audit trail · No PHI stored in logs
      </span>

      {loading && <div style={{ padding:40,textAlign:'center',color:'#94a3b8',fontSize:13 }}>Loading audit log...</div>}
      {error   && <div style={{ padding:'12px 16px',background:'#fef2f2',border:'1px solid #fecaca',borderRadius:8,fontSize:13,color:'#dc2626' }}>⚠ {error}</div>}
      {!loading && !error && logs.length === 0 && (
        <div style={{ padding:40,textAlign:'center',color:'#94a3b8',fontSize:13,border:'2px dashed #e0f2fe',borderRadius:10 }}>
          No audit entries yet. Actions will appear here as you use ClearCare.
        </div>
      )}
      {logs.map((log, i) => {
        const c = COLORS[log.action] || { bg:'#f8fafc', border:'#e2e8f0', color:'#475569', icon:'⚡' }
        return (
          <div key={i} style={{ display:'grid',gridTemplateColumns:'36px 1fr auto',alignItems:'start',gap:12,padding:'14px 16px',background:'#fff',border:'1px solid #e0f2fe',borderRadius:10,marginBottom:8,boxShadow:'0 1px 4px rgba(14,165,233,0.05)' }}>
            <div style={{ width:36,height:36,borderRadius:8,display:'flex',alignItems:'center',justifyContent:'center',fontSize:16,background:c.bg,border:`1px solid ${c.border}`,flexShrink:0 }}>
              {c.icon}
            </div>
            <div>
              <div style={{ fontSize:13,fontWeight:600,color:c.color,fontFamily:'DM Mono,monospace' }}>{log.action}</div>
              {log.resource && <div style={{ fontSize:12,color:'#64748b',marginTop:2 }}>{log.resource}</div>}
            </div>
            <div style={{ fontSize:11,color:'#94a3b8',fontFamily:'DM Mono,monospace',whiteSpace:'nowrap' }}>{fmt(log.created_at)}</div>
          </div>
        )
      })}
    </div>
  )
}
