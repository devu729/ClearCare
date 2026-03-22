import { useState, useRef, useCallback, useEffect } from 'react'
import { uploadPolicyPDF, listDocuments } from '../lib/agentClient'

const S = { IDLE:'idle', UPLOADING:'uploading', PARSING:'parsing', DONE:'done', ERROR:'error' }

export default function PolicyParser() {
  const [status,   setStatus]   = useState(S.IDLE)
  const [progress, setProgress] = useState(0)
  const [result,   setResult]   = useState(null)
  const [error,    setError]    = useState('')
  const [docs,     setDocs]     = useState([])
  const [dragOver, setDragOver] = useState(false)
  const [file,     setFile]     = useState(null)
  const inputRef = useRef()

  useEffect(() => {
    listDocuments().then(d => setDocs(d.documents || [])).catch(() => {})
  }, [])

  const pickFile = useCallback((f) => {
    if (!f) return
    if (f.type !== 'application/pdf') return setError('Only PDF files accepted.')
    if (f.size > 20 * 1024 * 1024)   return setError('Max file size is 20MB.')
    setError(''); setFile(f); setStatus(S.IDLE); setResult(null)
  }, [])

  const reset = () => { setFile(null); setStatus(S.IDLE); setProgress(0); setResult(null); setError('') }

  const upload = async () => {
    if (!file) return
    setStatus(S.UPLOADING); setProgress(0); setError(''); setResult(null)
    try {
      const data = await uploadPolicyPDF(file, p => {
        setProgress(p)
        if (p === 100) setStatus(S.PARSING)
      })
      setResult(data); setStatus(S.DONE)
      listDocuments().then(d => setDocs(d.documents || []))
    } catch (e) { setError(e.message); setStatus(S.ERROR) }
  }

  const busy = status === S.UPLOADING || status === S.PARSING

  return (
    <div style={{ maxWidth: 700 }}>
      <style>{`
        .pp-zone { border:2px dashed #bae6fd; border-radius:14px; padding:48px 32px; text-align:center; cursor:pointer; transition:all 0.2s; background:#fff; }
        .pp-zone:hover,.pp-zone.drag { border-color:#0ea5e9; background:#f0f9ff; }
        .pp-zone.has-file { border-style:solid; border-color:#38bdf8; }
        .pp-pill { display:inline-flex; align-items:center; gap:8px; margin-top:14px; padding:8px 16px; background:#e0f2fe; border-radius:20px; font-size:13px; color:#0369a1; font-weight:500; }
        .pp-rm { background:none; border:none; cursor:pointer; color:#7dd3fc; font-size:15px; line-height:1; }
        .pp-rm:hover { color:#ef4444; }
        .pp-btn { padding:11px 28px; background:linear-gradient(135deg,#0284c7,#0ea5e9); border:none; border-radius:8px; color:#fff; font-family:'Outfit',sans-serif; font-size:14px; font-weight:600; cursor:pointer; transition:all 0.2s; box-shadow:0 4px 12px rgba(14,165,233,0.25); }
        .pp-btn:hover:not(:disabled) { transform:translateY(-1px); }
        .pp-btn:disabled { opacity:0.45; cursor:not-allowed; transform:none; }
        .pp-ghost { padding:11px 20px; background:#fff; border:1.5px solid #bae6fd; border-radius:8px; color:#0ea5e9; font-family:'Outfit',sans-serif; font-size:14px; cursor:pointer; transition:all 0.2s; }
        .pp-ghost:hover { border-color:#0ea5e9; background:#f0f9ff; }
        .pp-bar-track { height:6px; background:#e0f2fe; border-radius:3px; overflow:hidden; }
        .pp-bar-fill { height:100%; background:linear-gradient(90deg,#0284c7,#38bdf8); border-radius:3px; transition:width 0.3s; }
        .pp-spinner { width:12px; height:12px; border:2px solid #bae6fd; border-top-color:#0ea5e9; border-radius:50%; animation:spin 0.7s linear infinite; }
        .pp-result { margin-top:24px; padding:24px; background:linear-gradient(135deg,#f0fdf4,#f0f9ff); border:1.5px solid #bbf7d0; border-radius:14px; animation:fadeUp 0.4s ease; }
        .pp-stats { display:grid; grid-template-columns:repeat(3,1fr); gap:10px; margin-bottom:18px; }
        .pp-stat { background:#fff; border:1px solid #e0f2fe; border-radius:10px; padding:14px; text-align:center; }
        .pp-stat-num { font-size:24px; font-weight:800; color:#0ea5e9; display:block; }
        .pp-stat-lbl { font-size:10px; color:#94a3b8; text-transform:uppercase; letter-spacing:0.06em; display:block; margin-top:2px; }
        .pp-sample { background:#fff; border:1px solid #e0f2fe; border-radius:8px; padding:12px 14px; font-size:12px; color:#475569; line-height:1.7; margin-bottom:8px; font-family:'DM Mono',monospace; }
        .pp-doc-row { display:flex; align-items:center; gap:12px; padding:12px 16px; background:#fff; border:1px solid #e0f2fe; border-radius:8px; margin-bottom:8px; transition:border-color 0.2s; }
        .pp-doc-row:hover { border-color:#7dd3fc; }
        .pp-empty { padding:28px; text-align:center; font-size:13px; color:#94a3b8; border:2px dashed #e0f2fe; border-radius:10px; }
        input[type="file"] { display:none; }
        @keyframes fadeUp { from{opacity:0;transform:translateY(12px)}to{opacity:1;transform:translateY(0)} }
        @keyframes spin { to{transform:rotate(360deg)} }
      `}</style>

      <h2 style={{ fontSize:20,fontWeight:700,color:'#0f172a',marginBottom:4 }}>Policy Parser</h2>
      <p style={{ fontSize:13,color:'#64748b',marginBottom:28 }}>Upload insurance PDFs · Rules are extracted, PHI-stripped, and indexed locally</p>

      <div className={`pp-zone ${dragOver?'drag':''} ${file?'has-file':''}`}
        onClick={() => !file && inputRef.current?.click()}
        onDragOver={e => { e.preventDefault(); setDragOver(true) }}
        onDragLeave={() => setDragOver(false)}
        onDrop={e => { e.preventDefault(); setDragOver(false); pickFile(e.dataTransfer.files[0]) }}>
        <input ref={inputRef} type="file" accept="application/pdf"
          onChange={e => pickFile(e.target.files[0])} />
        {!file ? (
          <>
            <div style={{ fontSize:40,marginBottom:14 }}>📄</div>
            <div style={{ fontSize:16,fontWeight:600,color:'#0f172a',marginBottom:6 }}>Drop insurance policy PDF here</div>
            <div style={{ fontSize:13,color:'#94a3b8' }}>or click to browse · PDF only · max 20MB</div>
          </>
        ) : (
          <>
            <div style={{ fontSize:40,marginBottom:14 }}>📋</div>
            <div style={{ fontSize:16,fontWeight:600,color:'#0f172a',marginBottom:6 }}>Ready to index</div>
            <div className="pp-pill">
              📄 {file.name}
              <span style={{ color:'#7dd3fc',fontSize:11 }}>({(file.size/1024/1024).toFixed(1)}MB)</span>
              <button className="pp-rm" onClick={e => { e.stopPropagation(); reset() }}>✕</button>
            </div>
          </>
        )}
      </div>

      <div style={{ display:'flex',gap:10,marginTop:18 }}>
        <button className="pp-btn" onClick={upload} disabled={!file||busy}>{busy?'Processing...':'Index Policy'}</button>
        {file && !busy && <button className="pp-ghost" onClick={reset}>Clear</button>}
      </div>

      {busy && (
        <div style={{ marginTop:20 }}>
          <div style={{ display:'flex',justifyContent:'space-between',fontSize:12,color:'#64748b',marginBottom:7 }}>
            <span>{status===S.UPLOADING?'Uploading PDF...':'Extracting & indexing rules...'}</span>
            <span>{progress}%</span>
          </div>
          <div className="pp-bar-track"><div className="pp-bar-fill" style={{ width:`${progress}%` }} /></div>
          <div style={{ display:'flex',alignItems:'center',gap:8,marginTop:10,fontSize:12,color:'#0369a1' }}>
            <div className="pp-spinner" />
            {status===S.UPLOADING?'Uploading...':'Stripping PHI → chunking → embedding → ChromaDB...'}
          </div>
        </div>
      )}

      {error && <div style={{ marginTop:14,padding:'12px 16px',background:'#fef2f2',border:'1px solid #fecaca',borderRadius:8,fontSize:13,color:'#dc2626' }}>⚠ {error}</div>}

      {status===S.DONE && result && (
        <div className="pp-result">
          <div style={{ display:'flex',alignItems:'center',gap:12,marginBottom:18 }}>
            <span style={{ fontSize:24 }}>✅</span>
            <div>
              <div style={{ fontSize:15,fontWeight:700,color:'#166534' }}>Policy indexed successfully</div>
              <div style={{ fontSize:12,color:'#64748b',marginTop:2 }}>{result.message}</div>
            </div>
          </div>
          <div className="pp-stats">
            {[['total_pages','Pages read'],['total_chunks','Text chunks'],['rule_chunks','Rules indexed']].map(([k,l]) => (
              <div className="pp-stat" key={k}><span className="pp-stat-num">{result[k]}</span><span className="pp-stat-lbl">{l}</span></div>
            ))}
          </div>
          {result.sample_rules?.length > 0 && (
            <>
              <div style={{ fontSize:11,fontWeight:600,textTransform:'uppercase',letterSpacing:'0.08em',color:'#64748b',marginBottom:8 }}>Sample extracted rules</div>
              {result.sample_rules.slice(0,2).map((r,i) => (
                <div className="pp-sample" key={i}>{r.slice(0,280)}{r.length>280?'...':''}</div>
              ))}
            </>
          )}
          <div style={{ fontSize:11,color:'#94a3b8',marginTop:10,fontFamily:'DM Mono,monospace' }}>
            Document ID: <strong style={{ color:'#0369a1' }}>{result.document_id}</strong> · use in Denial Tracer
          </div>
        </div>
      )}

      <div style={{ marginTop:36 }}>
        <div style={{ display:'flex',alignItems:'center',gap:8,marginBottom:14 }}>
          <span style={{ fontSize:14,fontWeight:600,color:'#334155' }}>Indexed Policies</span>
          <span style={{ background:'#e0f2fe',color:'#0369a1',fontSize:11,fontWeight:600,padding:'2px 8px',borderRadius:10 }}>{docs.length}</span>
        </div>
        {docs.length===0
          ? <div className="pp-empty">No policies indexed yet. Upload your first PDF above.</div>
          : docs.map(d => (
            <div className="pp-doc-row" key={d.document_id}>
              <span style={{ fontSize:18 }}>📋</span>
              <span style={{ fontSize:13,color:'#334155',fontWeight:500,flex:1 }}>{d.document_name}</span>
              <span style={{ fontSize:10,color:'#94a3b8',fontFamily:'DM Mono,monospace',background:'#f0f9ff',padding:'3px 8px',borderRadius:4 }}>{d.document_id}</span>
            </div>
          ))}
      </div>
    </div>
  )
}
