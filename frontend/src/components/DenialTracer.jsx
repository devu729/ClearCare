import { useState, useEffect } from 'react'
import { traceDenial, listDocuments } from '../lib/agentClient'

export default function DenialTracer({ userRole = 'clinician' }) {
  const [docs,    setDocs]    = useState([])
  const [docId,   setDocId]   = useState('')
  const [input,   setInput]   = useState('')
  const [loading, setLoading] = useState(false)
  const [result,  setResult]  = useState(null)
  const [error,   setError]   = useState('')
  const [view,    setView]    = useState('clinician')

  const isPatient = userRole === 'patient'

  useEffect(() => {
    listDocuments().then(d => {
      const list = d.documents || []
      setDocs(list)
      if (list.length > 0) setDocId(list[0].document_id)
    }).catch(() => {})
  }, [])

  const trace = async () => {
    if (!input.trim()) return setError('Enter a denial code or paste a denial letter.')
    setLoading(true); setError(''); setResult(null)
    try { setResult(await traceDenial({ query: input, document_id: docId || null })) }
    catch (e) { setError(e.message) }
    finally { setLoading(false) }
  }

  const confColor = s => s >= 0.85 ? '#10b981' : s >= 0.65 ? '#f59e0b' : '#ef4444'
  const confLabel = s => s >= 0.85 ? 'High confidence' : s >= 0.65 ? 'Medium — review recommended' : 'Low — manual verification required'

  // Clinician sees all 3 tabs. Patient sees nothing — just the plain explanation directly.
  const tabs = [
    { id: 'clinician', label: '👨‍⚕️ Clinician View' },
    { id: 'patient',   label: '🧑 Patient View'    },
    { id: 'sources',   label: '📄 Source Rules'    },
  ]

  return (
    <div style={{ maxWidth:760 }}>
      <style>{`
        .dt-form { background:#fff; border:1px solid #e0f2fe; border-radius:14px; padding:24px; margin-bottom:24px; box-shadow:0 2px 12px rgba(14,165,233,0.07); }
        .dt-input { width:100%; padding:11px 14px; border:1.5px solid #e2e8f0; border-radius:8px; font-family:'Outfit',sans-serif; font-size:14px; color:#0f172a; outline:none; transition:all 0.2s; resize:vertical; min-height:50px; }
        .dt-input:focus { border-color:#0ea5e9; box-shadow:0 0 0 3px rgba(14,165,233,0.1); }
        .dt-select { padding:11px 14px; border:1.5px solid #e2e8f0; border-radius:8px; font-family:'Outfit',sans-serif; font-size:13px; color:#334155; background:#fff; outline:none; cursor:pointer; width:100%; margin-bottom:14px; }
        .dt-select:focus { border-color:#0ea5e9; }
        .dt-btn { padding:12px 28px; background:linear-gradient(135deg,#0284c7,#0ea5e9); border:none; border-radius:8px; color:#fff; font-family:'Outfit',sans-serif; font-size:14px; font-weight:600; cursor:pointer; white-space:nowrap; transition:all 0.2s; box-shadow:0 4px 12px rgba(14,165,233,0.25); margin-top:12px; }
        .dt-btn:hover:not(:disabled) { transform:translateY(-1px); }
        .dt-btn:disabled { opacity:0.45; cursor:not-allowed; transform:none; }
        .dt-spinner { width:16px; height:16px; border:2px solid #bae6fd; border-top-color:#0ea5e9; border-radius:50%; animation:spin 0.7s linear infinite; }
        .dt-result { background:#fff; border:1.5px solid #bae6fd; border-radius:16px; overflow:hidden; animation:fadeUp 0.4s ease; box-shadow:0 4px 20px rgba(14,165,233,0.1); }
        .dt-header { background:linear-gradient(135deg,#f0f9ff,#e0f2fe); padding:20px 24px; border-bottom:1px solid #bae6fd; }
        .dt-conf-track { flex:1; height:8px; background:#e0f2fe; border-radius:4px; overflow:hidden; }
        .dt-conf-fill { height:100%; border-radius:4px; transition:width 0.8s ease; }
        .dt-source { display:inline-flex; align-items:center; gap:6px; background:#fff; border:1px solid #bae6fd; border-radius:6px; padding:5px 12px; font-size:12px; color:#0369a1; font-family:'DM Mono',monospace; margin-top:12px; }
        .dt-source.unverified { border-color:#fde68a; color:#92400e; background:#fffbeb; }
        .dt-tabs { display:flex; border-bottom:1px solid #e0f2fe; }
        .dt-tab { flex:1; padding:14px; text-align:center; cursor:pointer; font-size:13px; font-weight:500; color:#64748b; border:none; background:#f8fafc; transition:all 0.2s; border-bottom:2px solid transparent; }
        .dt-tab.active { background:#fff; color:#0ea5e9; font-weight:600; border-bottom-color:#0ea5e9; }
        .dt-explain { padding:24px; font-size:14px; color:#334155; line-height:1.8; }
        .dt-action { display:flex; align-items:flex-start; gap:10px; padding:12px 14px; background:#f0f9ff; border:1px solid #bae6fd; border-radius:8px; margin-bottom:8px; font-size:13px; color:#0369a1; }
        .dt-chunk { background:#f8fafc; border:1px solid #e0f2fe; border-radius:8px; padding:12px 14px; margin-bottom:8px; }
        .dt-chunk-tag { font-size:10px; font-family:'DM Mono',monospace; background:#e0f2fe; color:#0369a1; padding:2px 7px; border-radius:4px; margin-right:6px; }
        .dt-warn { margin:0 24px 16px; padding:12px 14px; background:#fffbeb; border:1px solid #fde68a; border-radius:8px; font-size:12px; color:#92400e; display:flex; gap:8px; }
        .dt-patient-badge { display:inline-flex; align-items:center; gap:6px; background:#f0fdf4; border:1px solid #bbf7d0; border-radius:8px; padding:8px 14px; font-size:12px; color:#166534; font-weight:500; margin-bottom:16px; }
        @keyframes fadeUp { from{opacity:0;transform:translateY(12px)}to{opacity:1;transform:translateY(0)} }
        @keyframes spin { to{transform:rotate(360deg)} }
      `}</style>

      <h2 style={{ fontSize:20,fontWeight:700,color:'#0f172a',marginBottom:4 }}>
        {isPatient ? 'Explain My Denial' : 'Denial Tracer'}
      </h2>
      <p style={{ fontSize:13,color:'#64748b',marginBottom:28 }}>
        {isPatient
          ? 'Paste your denial code or letter — get a plain English explanation of what it means and what to do next'
          : 'Enter a denial code or paste a denial letter — find the exact policy rule that triggered it'
        }
      </p>

      <div className="dt-form">
        {/* Clinician only: document selector */}
        {!isPatient && docs.length > 0 && (
          <div style={{ marginBottom:14 }}>
            <label style={{ fontSize:13,fontWeight:500,color:'#334155',display:'block',marginBottom:6 }}>Policy document to search</label>
            <select className="dt-select" value={docId} onChange={e => setDocId(e.target.value)}>
              <option value="">Search all indexed policies</option>
              {docs.map(d => <option key={d.document_id} value={d.document_id}>{d.document_name}</option>)}
            </select>
          </div>
        )}

        <label style={{ fontSize:13,fontWeight:500,color:'#334155',display:'block',marginBottom:6 }}>
          {isPatient
            ? 'Your denial code or letter text'
            : 'Denial code, reason, or paste denial letter'
          }
        </label>
        <textarea className="dt-input" rows={3}
          placeholder={isPatient
            ? 'e.g. "CO-4" or paste your full denial letter from the insurance company...'
            : 'e.g. "CO-4 — The service is inconsistent with the payer policy" or paste full denial letter...'
          }
          value={input} onChange={e => setInput(e.target.value)} />
        <div style={{ fontSize:11,color:'#94a3b8',margin:'6px 0 0' }}>
          {isPatient
            ? 'Find the code on your Explanation of Benefits (EOB) letter from your insurance company'
            : 'Works with CARC/RARC codes, payer denial codes, or plain-text denial letters'
          }
        </div>
        <button className="dt-btn" onClick={trace} disabled={loading || !input.trim()}>
          {loading ? 'Tracing...' : isPatient ? 'Explain My Denial →' : 'Trace Denial →'}
        </button>
      </div>

      {loading && (
        <div style={{ display:'flex',alignItems:'center',gap:10,padding:16,background:'#f0f9ff',borderRadius:10,fontSize:13,color:'#0369a1',marginBottom:16 }}>
          <div className="dt-spinner" />
          {isPatient
            ? 'Finding the policy rule → generating your explanation...'
            : 'Searching indexed rules → matching policy → generating explanations...'
          }
        </div>
      )}
      {error && (
        <div style={{ padding:'12px 16px',background:'#fef2f2',border:'1px solid #fecaca',borderRadius:8,fontSize:13,color:'#dc2626',marginBottom:16 }}>
          ⚠ {error}
        </div>
      )}

      {result && (
        <div className="dt-result">
          <div className="dt-header">
            <div style={{ fontSize:16,fontWeight:700,color:'#0f172a',marginBottom:10 }}>
              {isPatient ? 'Here is what happened' : 'Decision traced to policy rule'}
            </div>
            <div style={{ display:'flex',alignItems:'center',gap:12 }}>
              <div className="dt-conf-track">
                <div className="dt-conf-fill" style={{ width:`${Math.round((result.confidence||0)*100)}%`, background:confColor(result.confidence||0) }} />
              </div>
              <span style={{ fontSize:14,fontWeight:700,color:confColor(result.confidence||0),minWidth:44,textAlign:'right' }}>
                {Math.round((result.confidence||0)*100)}%
              </span>
            </div>
            <div style={{ fontSize:11,color:'#64748b',marginTop:4 }}>{confLabel(result.confidence||0)}</div>
            {result.source_rule && (
              <div className={`dt-source ${result.verified?'':'unverified'}`}>
                {result.verified?'✓':'⚠'} {result.source_rule}{result.page_num ? ` · Page ${result.page_num}` : ''}
              </div>
            )}
          </div>

          {!result.verified && (
            <div className="dt-warn">
              ⚠ <span>Some points could not be verified against the source document. Please manually review before acting.</span>
            </div>
          )}

          {/* PATIENT: no tabs, show explanation directly */}
          {isPatient && (
            <>
              <div className="dt-explain"
                dangerouslySetInnerHTML={{ __html:(result.patient_explanation||'').replace(/\n/g,'<br/>') }} />
              {result.patient_actions?.length > 0 && (
                <div style={{ padding:'0 24px 24px' }}>
                  <div style={{ fontSize:11,fontWeight:600,textTransform:'uppercase',letterSpacing:'0.1em',color:'#94a3b8',marginBottom:12 }}>
                    Your Next Steps
                  </div>
                  {result.patient_actions.map((a,i) => (
                    <div className="dt-action" key={i}><span>{i+1}.</span>{a}</div>
                  ))}
                </div>
              )}
            </>
          )}

          {/* CLINICIAN: show all 3 tabs */}
          {!isPatient && (
            <>
              <div className="dt-tabs">
                {tabs.map(v => (
                  <button key={v.id} className={`dt-tab ${view===v.id?'active':''}`} onClick={() => setView(v.id)}>
                    {v.label}
                  </button>
                ))}
              </div>

              {view === 'clinician' && (
                <>
                  <div className="dt-explain"
                    dangerouslySetInnerHTML={{ __html:(result.clinician_explanation||'').replace(/\n/g,'<br/>') }} />
                  {result.clinician_actions?.length > 0 && (
                    <div style={{ padding:'0 24px 24px' }}>
                      <div style={{ fontSize:11,fontWeight:600,textTransform:'uppercase',letterSpacing:'0.1em',color:'#94a3b8',marginBottom:12 }}>
                        Recommended Actions
                      </div>
                      {result.clinician_actions.map((a,i) => (
                        <div className="dt-action" key={i}><span>→</span>{a}</div>
                      ))}
                    </div>
                  )}
                </>
              )}

              {view === 'patient' && (
                <>
                  <div className="dt-explain"
                    dangerouslySetInnerHTML={{ __html:(result.patient_explanation||'').replace(/\n/g,'<br/>') }} />
                  {result.patient_actions?.length > 0 && (
                    <div style={{ padding:'0 24px 24px' }}>
                      <div style={{ fontSize:11,fontWeight:600,textTransform:'uppercase',letterSpacing:'0.1em',color:'#94a3b8',marginBottom:12 }}>
                        Patient Next Steps
                      </div>
                      {result.patient_actions.map((a,i) => (
                        <div className="dt-action" key={i}><span>{i+1}.</span>{a}</div>
                      ))}
                    </div>
                  )}
                </>
              )}

              {view === 'sources' && (
                <div style={{ padding:'24px' }}>
                  <div style={{ fontSize:11,fontWeight:600,textTransform:'uppercase',letterSpacing:'0.1em',color:'#94a3b8',marginBottom:10 }}>
                    Matched Policy Rules
                  </div>
                  {(result.source_chunks||[]).map((c,i) => (
                    <div className="dt-chunk" key={i}>
                      <div style={{ marginBottom:6 }}>
                        <span className="dt-chunk-tag">Page {c.page_num}</span>
                        <span className="dt-chunk-tag">{c.document_name}</span>
                        <span className="dt-chunk-tag">Match: {Math.round((1-c.distance)*100)}%</span>
                      </div>
                      <div style={{ fontSize:12,color:'#475569',lineHeight:1.7,fontFamily:'DM Mono,monospace' }}>{c.text}</div>
                    </div>
                  ))}
                </div>
              )}
            </>
          )}
        </div>
      )}
    </div>
  )
}
