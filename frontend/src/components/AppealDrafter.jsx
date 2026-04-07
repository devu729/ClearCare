import { useState } from 'react'
import { traceDenial, sendExplanationEmail, createAppealDeadline } from '../lib/agentClient'

export default function AppealDrafter() {
  const [denialText,   setDenialText]   = useState('')
  const [patientName,  setPatientName]  = useState('')
  const [loading,      setLoading]      = useState(false)
  const [letter,       setLetter]       = useState('')
  const [editedLetter, setEditedLetter] = useState('')
  const [deadlineDate, setDeadlineDate] = useState('')
  const [email,        setEmail]        = useState('')
  const [error,        setError]        = useState('')
  const [emailSent,    setEmailSent]    = useState(false)
  const [calSaved,     setCalSaved]     = useState(false)
  const [copyDone,     setCopyDone]     = useState(false)
  const [isEditing,    setIsEditing]    = useState(false)

  const [fields, setFields] = useState({
    date:             new Date().toLocaleDateString('en-US', { year:'numeric', month:'long', day:'numeric' }),
    patient_name:     '',
    member_id:        '',
    claim_number:     '',
    date_of_service:  '',
    provider_name:    '',
    provider_address: '',
    provider_phone:   '',
    insurance_address:'',
  })

  const generate = async () => {
    if (!denialText.trim()) return setError('Please paste a denial reason or letter.')
    setLoading(true); setError(''); setLetter(''); setEditedLetter('')
    setEmailSent(false); setCalSaved(false)
    try {
      const data = await traceDenial({
        query:           denialText,
        generate_appeal: true,
        patient_name:    patientName || fields.patient_name,
        recipient_type:  'insurance',
      })
      const raw = data.appeal_letter || ''
      setLetter(raw)
      setEditedLetter(raw)
      // Always set a deadline — use API response or fall back to 30 days
      setDeadlineDate(data.appeal_deadline || '30 days from denial notice')
      if (patientName) setFields(f => ({ ...f, patient_name: patientName }))
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  const fillPlaceholders = () => {
    let filled = letter
    const replacements = {
      '[DATE]':              fields.date,
      '[PATIENT NAME]':      fields.patient_name,
      '[MEMBER ID]':         fields.member_id,
      '[CLAIM NUMBER]':      fields.claim_number,
      '[DATE OF SERVICE]':   fields.date_of_service,
      '[PROVIDER NAME]':     fields.provider_name,
      '[Provider Address]':  fields.provider_address,
      '[City, State, Zip Code]': fields.provider_address,
      '[Provider Phone Number]': fields.provider_phone,
      '[Insurance Company Address - if known, otherwise general PO Box]': fields.insurance_address,
    }
    Object.entries(replacements).forEach(([k, v]) => {
      if (v) filled = filled.replaceAll(k, v)
    })
    setEditedLetter(filled)
    setIsEditing(false)
  }

  const unfilledCount = (editedLetter.match(/\[.*?\]/g) || []).length

  const copyToClipboard = () => {
    navigator.clipboard.writeText(editedLetter).then(() => {
      setCopyDone(true)
      setTimeout(() => setCopyDone(false), 2000)
    })
  }

  const sendEmail = async () => {
    if (!email) return setError('Enter an email address to send to.')
    setError('')
    try {
      await sendExplanationEmail({
        to:      email,
        subject: 'Your Insurance Appeal Letter — ClearCare',
        body:    editedLetter,
      })
      setEmailSent(true)
    } catch (e) {
      setError(e.message)
    }
  }

  const saveDeadline = async () => {
    if (!deadlineDate) return
    setError('')
    try {
      const result = await createAppealDeadline({
        title: 'Insurance Appeal Deadline',
        date:  deadlineDate,
        notes: `Appeal for: ${fields.patient_name || denialText.slice(0, 80)}`,
      })
      if (result.ics_content) {
        const blob = new Blob([result.ics_content], { type: 'text/calendar' })
        const url  = URL.createObjectURL(blob)
        const a    = document.createElement('a')
        a.href     = url
        a.download = result.filename || 'appeal_deadline.ics'
        document.body.appendChild(a)
        a.click()
        document.body.removeChild(a)
        URL.revokeObjectURL(url)
      }
      setCalSaved(true)
    } catch (e) {
      setError(e.message)
    }
  }

  const fieldDef = [
    { key:'date',             label:'Letter Date',        placeholder:'e.g. March 28, 2026' },
    { key:'patient_name',     label:'Patient Full Name',  placeholder:'e.g. John Smith' },
    { key:'member_id',        label:'Member / Policy ID', placeholder:'e.g. BSH-123456789' },
    { key:'claim_number',     label:'Claim Number',       placeholder:'e.g. CLM-2026-00847' },
    { key:'date_of_service',  label:'Date of Service',    placeholder:'e.g. February 10, 2026' },
    { key:'provider_name',    label:'Provider Name',      placeholder:'e.g. Dr. Sarah Johnson' },
    { key:'provider_address', label:'Provider Address',   placeholder:'e.g. 123 Medical Ave, Houston, TX' },
    { key:'provider_phone',   label:'Provider Phone',     placeholder:'e.g. (713) 555-0100' },
    { key:'insurance_address',label:'Insurance Address',  placeholder:'e.g. P.O. Box 272540, Chico, CA' },
  ]

  return (
    <div className="ad-root">
      <style>{`
        .ad-root { max-width:800px; font-family:'Outfit',sans-serif; }
        .ad-heading { font-size:20px; font-weight:700; color:#0f172a; margin-bottom:4px; }
        .ad-sub { font-size:13px; color:#64748b; margin-bottom:28px; }
        .ad-form { background:#fff; border:1px solid #e0f2fe; border-radius:14px; padding:24px; margin-bottom:20px; box-shadow:0 2px 12px rgba(14,165,233,0.07); }
        .ad-label { font-size:13px; font-weight:500; color:#334155; margin-bottom:6px; display:block; }
        .ad-input { width:100%; padding:11px 14px; border:1.5px solid #e2e8f0; border-radius:8px; font-family:'Outfit',sans-serif; font-size:14px; color:#0f172a; outline:none; transition:all 0.2s; margin-bottom:14px; }
        .ad-input:focus { border-color:#0ea5e9; box-shadow:0 0 0 3px rgba(14,165,233,0.1); }
        textarea.ad-input { resize:vertical; min-height:80px; }
        .ad-btn { padding:11px 28px; background:linear-gradient(135deg,#0284c7,#0ea5e9); border:none; border-radius:8px; color:#fff; font-family:'Outfit',sans-serif; font-size:14px; font-weight:600; cursor:pointer; transition:all 0.2s; box-shadow:0 4px 12px rgba(14,165,233,0.25); }
        .ad-btn:hover:not(:disabled) { transform:translateY(-1px); }
        .ad-btn:disabled { opacity:0.45; cursor:not-allowed; transform:none; }
        .ad-btn-ghost { padding:9px 16px; background:#fff; border:1.5px solid #bae6fd; border-radius:8px; color:#0369a1; font-family:'Outfit',sans-serif; font-size:13px; font-weight:500; cursor:pointer; transition:all 0.2s; white-space:nowrap; }
        .ad-btn-ghost:hover { background:#f0f9ff; border-color:#0ea5e9; }
        .ad-btn-success { background:#f0fdf4 !important; border-color:#bbf7d0 !important; color:#16a34a !important; }
        .ad-btn-warning { padding:9px 16px; background:#fff7ed; border:1.5px solid #fed7aa; border-radius:8px; color:#c2410c; font-family:'Outfit',sans-serif; font-size:13px; font-weight:500; cursor:pointer; white-space:nowrap; }
        .ad-loading { display:flex; align-items:center; gap:10px; padding:16px; background:#f0f9ff; border-radius:10px; font-size:13px; color:#0369a1; margin-bottom:16px; }
        .ad-spinner { width:16px; height:16px; border:2px solid #bae6fd; border-top-color:#0ea5e9; border-radius:50%; animation:spin 0.7s linear infinite; flex-shrink:0; }
        .ad-error { padding:12px 16px; background:#fef2f2; border:1px solid #fecaca; border-radius:8px; font-size:13px; color:#dc2626; margin-bottom:16px; }
        .ad-letter-card { background:#fff; border:1.5px solid #bae6fd; border-radius:14px; overflow:hidden; animation:fadeUp 0.4s ease; box-shadow:0 4px 20px rgba(14,165,233,0.1); }
        .ad-letter-header { background:#f0f9ff; padding:14px 20px; border-bottom:1px solid #bae6fd; display:flex; justify-content:space-between; align-items:center; gap:8px; flex-wrap:wrap; }
        .ad-letter-title { font-size:14px; font-weight:700; color:#0f172a; }
        .ad-header-actions { display:flex; gap:8px; align-items:center; flex-wrap:wrap; }
        .ad-unfilled-badge { display:inline-flex; align-items:center; gap:5px; background:#fff7ed; border:1px solid #fed7aa; border-radius:6px; padding:5px 10px; font-size:11px; color:#c2410c; font-weight:600; }
        .ad-fill-form { padding:20px 24px; background:#fff7ed; border-bottom:1px solid #fed7aa; }
        .ad-fill-title { font-size:13px; font-weight:700; color:#92400e; margin-bottom:4px; }
        .ad-fill-sub { font-size:11px; color:#b45309; margin-bottom:16px; }
        .ad-fill-grid { display:grid; grid-template-columns:1fr 1fr; gap:12px; }
        .ad-fill-field { display:flex; flex-direction:column; gap:4px; }
        .ad-fill-label { font-size:11px; font-weight:600; color:#64748b; text-transform:uppercase; letter-spacing:0.06em; }
        .ad-fill-input { padding:8px 12px; border:1.5px solid #e2e8f0; border-radius:6px; font-family:'Outfit',sans-serif; font-size:13px; color:#0f172a; outline:none; }
        .ad-fill-input:focus { border-color:#f59e0b; }
        .ad-fill-actions { display:flex; gap:8px; margin-top:16px; justify-content:flex-end; }
        .ad-fill-apply { padding:9px 20px; background:linear-gradient(135deg,#d97706,#f59e0b); border:none; border-radius:8px; color:#fff; font-family:'Outfit',sans-serif; font-size:13px; font-weight:600; cursor:pointer; }
        .ad-fill-cancel { padding:9px 16px; background:#fff; border:1.5px solid #e2e8f0; border-radius:8px; color:#64748b; font-family:'Outfit',sans-serif; font-size:13px; cursor:pointer; }
        .ad-letter-body { padding:24px; font-family:'DM Mono',monospace; font-size:12.5px; color:#334155; line-height:1.9; white-space:pre-wrap; max-height:420px; overflow-y:auto; background:#fafeff; }
        .ad-letter-editable { padding:24px; font-family:'DM Mono',monospace; font-size:12.5px; color:#334155; line-height:1.9; width:100%; min-height:420px; border:none; outline:none; background:#fafeff; resize:vertical; }
        .ad-send-section { padding:20px 24px; border-top:1px solid #e0f2fe; background:#f8fafc; }
        .ad-send-title { font-size:11px; font-weight:600; text-transform:uppercase; letter-spacing:0.1em; color:#94a3b8; margin-bottom:14px; }
        .ad-send-row { display:flex; gap:8px; margin-bottom:12px; align-items:center; flex-wrap:wrap; }
        .ad-send-input { flex:1; min-width:200px; padding:10px 14px; border:1.5px solid #e2e8f0; border-radius:8px; font-family:'Outfit',sans-serif; font-size:13px; outline:none; transition:all 0.2s; color:#0f172a; }
        .ad-send-input:focus { border-color:#0ea5e9; }
        .ad-deadline-badge { display:inline-flex; align-items:center; gap:6px; background:#fff7ed; border:1px solid #fed7aa; border-radius:8px; padding:8px 14px; font-size:13px; color:#c2410c; font-weight:500; }
        .ad-ics-hint { font-size:11px; color:#64748b; margin-top:8px; padding:10px 14px; background:#f0f9ff; border-radius:8px; border:1px solid #e0f2fe; line-height:1.7; }
        .ad-ics-hint.success { color:#16a34a; border-color:#bbf7d0; background:#f0fdf4; }
        @keyframes fadeUp { from{opacity:0;transform:translateY(12px)}to{opacity:1;transform:translateY(0)} }
        @keyframes spin { to{transform:rotate(360deg)} }
        @media(max-width:600px){ .ad-fill-grid{grid-template-columns:1fr} }
      `}</style>

      <h2 className="ad-heading">Appeal Drafter</h2>
      <p className="ad-sub">Generate a formal appeal letter to send to the insurance company</p>

      <div className="ad-form">
        <label className="ad-label">Patient name (optional)</label>
        <input className="ad-input" type="text" placeholder="John Smith"
          value={patientName} onChange={e => setPatientName(e.target.value)} />

        <label className="ad-label">Denial reason or letter text</label>
        <textarea className="ad-input" rows={4}
          placeholder="Paste the denial reason, denial code, or full denial letter..."
          value={denialText} onChange={e => setDenialText(e.target.value)} />

        <button className="ad-btn" onClick={generate} disabled={loading || !denialText.trim()}>
          {loading ? 'Generating...' : 'Generate Appeal Letter →'}
        </button>
      </div>

      {loading && (
        <div className="ad-loading">
          <div className="ad-spinner" />
          Tracing denial rule → drafting appeal arguments → writing letter...
        </div>
      )}
      {error && <div className="ad-error">⚠ {error}</div>}

      {editedLetter && (
        <div className="ad-letter-card">
          <div className="ad-letter-header">
            <div>
              <span className="ad-letter-title">🏢 Insurance Appeal Letter</span>
              <div style={{ fontSize:10, color:'#94a3b8', marginTop:2 }}>
                Formal clinical appeal — ready to send to insurance company
              </div>
            </div>
            <div className="ad-header-actions">
              {unfilledCount > 0 && (
                <span className="ad-unfilled-badge">⚠ {unfilledCount} placeholder{unfilledCount > 1 ? 's' : ''}</span>
              )}
              <button className="ad-btn-warning" onClick={() => setIsEditing(!isEditing)}>
                {isEditing ? '👁 Preview' : '✏️ Fill Details'}
              </button>
              <button className={`ad-btn-ghost ${copyDone ? 'ad-btn-success' : ''}`} onClick={copyToClipboard}>
                {copyDone ? '✓ Copied!' : '📋 Copy'}
              </button>
            </div>
          </div>

          {isEditing && (
            <div className="ad-fill-form">
              <div className="ad-fill-title">📝 Fill in your details</div>
              <div className="ad-fill-sub">These replace the [PLACEHOLDERS] in your letter automatically.</div>
              <div className="ad-fill-grid">
                {fieldDef.map(f => (
                  <div className="ad-fill-field" key={f.key}>
                    <label className="ad-fill-label">{f.label}</label>
                    <input className="ad-fill-input" type="text" placeholder={f.placeholder}
                      value={fields[f.key]}
                      onChange={e => setFields(p => ({ ...p, [f.key]: e.target.value }))} />
                  </div>
                ))}
              </div>
              <div className="ad-fill-actions">
                <button className="ad-fill-cancel" onClick={() => setIsEditing(false)}>Cancel</button>
                <button className="ad-fill-apply" onClick={fillPlaceholders}>✓ Apply to Letter</button>
              </div>
            </div>
          )}

          {isEditing
            ? <textarea className="ad-letter-editable" value={editedLetter} onChange={e => setEditedLetter(e.target.value)} />
            : <div className="ad-letter-body">{editedLetter}</div>
          }

          <div className="ad-send-section">
            <div className="ad-send-title">Send & Track</div>

            {unfilledCount > 0 && (
              <div style={{ padding:'10px 14px', background:'#fff7ed', border:'1px solid #fed7aa', borderRadius:8, fontSize:12, color:'#92400e', marginBottom:14 }}>
                ⚠ <strong>{unfilledCount} unfilled placeholder{unfilledCount > 1 ? 's' : ''}</strong> — click ✏️ Fill Details above before sending.
              </div>
            )}

            {/* Email row */}
            <div className="ad-send-row">
              <input className="ad-send-input" type="email"
                placeholder="Insurance company appeals email..."
                value={email} onChange={e => setEmail(e.target.value)} />
              <button className={`ad-btn-ghost ${emailSent ? 'ad-btn-success' : ''}`} onClick={sendEmail}>
                {emailSent ? '✓ Sent!' : '📧 Send Email'}
              </button>
            </div>

            {/* Calendar row — always shows after letter is generated */}
            <div>
              <div className="ad-send-row">
                <div className="ad-deadline-badge">
                  ⏰ Appeal deadline: {deadlineDate}
                </div>
                <button className={`ad-btn-ghost ${calSaved ? 'ad-btn-success' : ''}`} onClick={saveDeadline}>
                  {calSaved ? '✓ Downloaded!' : '📅 Download Calendar File'}
                </button>
              </div>
              {!calSaved && (
                <div className="ad-ics-hint">
                  📎 Downloads a <strong>.ics</strong> file — open to add this deadline to Google Calendar, Outlook, or Apple Calendar. Reminders set 7 days and 1 day before.
                </div>
              )}
              {calSaved && (
                <div className="ad-ics-hint success">
                  ✅ Open the downloaded file to add the appeal deadline to your calendar. Reminders set 7 days and 1 day before.
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
