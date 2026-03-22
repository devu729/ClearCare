import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { supabase } from '../lib/supabaseClient'

const VALID_ORG_CODES = (import.meta.env.VITE_CLINICIAN_ORG_CODES || 'DEMO2024').split(',')

export default function Login() {
  const navigate = useNavigate()
  const [tab,      setTab]      = useState('login')
  const [role,     setRole]     = useState('patient')
  const [email,    setEmail]    = useState('')
  const [password, setPassword] = useState('')
  const [orgCode,  setOrgCode]  = useState('')
  const [error,    setError]    = useState('')
  const [info,     setInfo]     = useState('')
  const [loading,  setLoading]  = useState(false)

  const validate = () => {
    if (!email || !password)  return 'Email and password are required.'
    if (password.length < 8)  return 'Password must be at least 8 characters.'
    if (tab === 'signup' && role === 'clinician' && !orgCode)
      return 'Clinicians must enter an organization code.'
    if (tab === 'signup' && role === 'clinician' &&
        !VALID_ORG_CODES.includes(orgCode.trim().toUpperCase()))
      return 'Invalid organization code. Contact your administrator.'
    return null
  }

  const handleSubmit = async () => {
    setError(''); setInfo('')
    const ve = validate()
    if (ve) return setError(ve)
    setLoading(true)
    try {
      if (tab === 'login') {
        const { data, error: e } = await supabase.auth.signInWithPassword({ email, password })
        if (e) throw e
        navigate(data.user.user_metadata?.role === 'clinician' ? '/clinician' : '/patient', { replace: true })
      } else {
        const { error: e } = await supabase.auth.signUp({
          email, password,
          options: { data: { role }, emailRedirectTo: `${window.location.origin}/login` }
        })
        if (e) throw e
        setInfo('Check your email to confirm your account, then sign in.')
        setTab('login')
      }
    } catch (err) {
      setError(err.message || 'Something went wrong.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&display=swap');
        .lp { min-height:100vh; display:grid; grid-template-columns:1fr 1fr; font-family:'Outfit',sans-serif; background:#f0f9ff; }
        .lp-hero { background:linear-gradient(145deg,#0369a1 0%,#0ea5e9 50%,#38bdf8 100%); padding:56px 60px; display:flex; flex-direction:column; justify-content:space-between; position:relative; overflow:hidden; }
        .lp-hero::after { content:''; position:absolute; width:400px; height:400px; background:radial-gradient(circle,rgba(255,255,255,0.12) 0%,transparent 70%); bottom:-100px; right:-100px; border-radius:50%; }
        .lp-grid { position:absolute; inset:0; background-image:radial-gradient(rgba(255,255,255,0.08) 1px,transparent 1px); background-size:32px 32px; pointer-events:none; }
        .lp-brand { position:relative; display:flex; align-items:center; gap:12px; animation:fadeUp 0.5s ease; }
        .lp-brand-mark { width:40px; height:40px; background:rgba(255,255,255,0.2); border-radius:10px; display:flex; align-items:center; justify-content:center; font-size:20px; border:1px solid rgba(255,255,255,0.3); }
        .lp-brand-name { font-size:20px; font-weight:800; color:#fff; letter-spacing:-0.01em; }
        .lp-brand-name span { font-weight:300; opacity:0.8; }
        .lp-body { position:relative; animation:fadeUp 0.5s 0.1s ease both; }
        .lp-tag { display:inline-block; background:rgba(255,255,255,0.15); border:1px solid rgba(255,255,255,0.25); color:#fff; font-size:11px; letter-spacing:0.12em; text-transform:uppercase; padding:5px 14px; border-radius:20px; margin-bottom:24px; }
        .lp-h1 { font-size:clamp(32px,3.2vw,48px); font-weight:800; color:#fff; line-height:1.1; letter-spacing:-0.02em; margin-bottom:20px; }
        .lp-sub { font-size:15px; color:rgba(255,255,255,0.75); line-height:1.8; max-width:380px; }
        .lp-stats { position:relative; display:grid; grid-template-columns:repeat(3,1fr); gap:1px; background:rgba(255,255,255,0.15); border-radius:12px; overflow:hidden; animation:fadeUp 0.5s 0.2s ease both; }
        .lp-stat { background:rgba(255,255,255,0.1); padding:18px 14px; text-align:center; }
        .lp-stat-num { font-size:22px; font-weight:800; color:#fff; display:block; }
        .lp-stat-lbl { font-size:10px; color:rgba(255,255,255,0.6); letter-spacing:0.08em; margin-top:2px; display:block; }
        .lp-right { display:flex; align-items:center; justify-content:center; padding:48px 56px; background:#fff; }
        .lp-card { width:100%; max-width:400px; }
        .lp-heading { font-size:26px; font-weight:700; color:#0f172a; margin-bottom:4px; letter-spacing:-0.01em; }
        .lp-subheading { font-size:14px; color:#64748b; margin-bottom:32px; }
        .lp-tabs { display:grid; grid-template-columns:1fr 1fr; background:#f0f9ff; border-radius:10px; padding:4px; margin-bottom:28px; }
        .lp-tab { padding:9px; text-align:center; cursor:pointer; font-size:13px; font-weight:500; color:#64748b; border-radius:7px; border:none; background:none; font-family:'Outfit',sans-serif; transition:all 0.2s; }
        .lp-tab.active { background:#fff; color:#0ea5e9; font-weight:600; box-shadow:0 1px 6px rgba(14,165,233,0.15); }
        .role-grid { display:grid; grid-template-columns:1fr 1fr; gap:10px; margin-bottom:22px; }
        .role-card { padding:14px 12px; border:1.5px solid #e2e8f0; border-radius:10px; cursor:pointer; background:#fff; transition:all 0.2s; text-align:left; }
        .role-card:hover { border-color:#7dd3fc; background:#f0f9ff; }
        .role-card.active { border-color:#0ea5e9; background:#f0f9ff; }
        .role-icon { font-size:20px; margin-bottom:6px; display:block; }
        .role-name { font-size:13px; font-weight:600; color:#0f172a; display:block; }
        .role-card.active .role-name { color:#0ea5e9; }
        .role-desc { font-size:11px; color:#94a3b8; margin-top:2px; display:block; }
        .lp-field { margin-bottom:16px; }
        .lp-label { display:block; font-size:13px; font-weight:500; color:#334155; margin-bottom:6px; }
        .lp-input { width:100%; padding:11px 14px; border:1.5px solid #e2e8f0; border-radius:8px; font-family:'Outfit',sans-serif; font-size:14px; color:#0f172a; outline:none; transition:all 0.2s; }
        .lp-input:focus { border-color:#0ea5e9; box-shadow:0 0 0 3px rgba(14,165,233,0.12); }
        .lp-input::placeholder { color:#cbd5e1; }
        .msg-error { background:#fef2f2; border:1px solid #fecaca; color:#dc2626; border-radius:8px; padding:11px 14px; font-size:13px; margin-bottom:16px; line-height:1.5; }
        .msg-info  { background:#f0fdf4; border:1px solid #bbf7d0; color:#16a34a;  border-radius:8px; padding:11px 14px; font-size:13px; margin-bottom:16px; line-height:1.5; }
        .lp-btn { width:100%; padding:13px; background:linear-gradient(135deg,#0284c7,#0ea5e9); border:none; border-radius:10px; color:#fff; font-family:'Outfit',sans-serif; font-size:15px; font-weight:600; cursor:pointer; transition:all 0.2s; box-shadow:0 4px 14px rgba(14,165,233,0.3); }
        .lp-btn:hover:not(:disabled) { transform:translateY(-1px); box-shadow:0 6px 20px rgba(14,165,233,0.4); }
        .lp-btn:disabled { opacity:0.5; cursor:not-allowed; transform:none; }
        .lp-footer { text-align:center; margin-top:20px; font-size:13px; color:#64748b; }
        .lp-footer button { background:none; border:none; color:#0ea5e9; font-family:'Outfit',sans-serif; font-size:13px; font-weight:600; cursor:pointer; margin-left:4px; }
        .lp-footer button:hover { text-decoration:underline; }
        .lp-security { display:flex; align-items:center; gap:7px; margin-top:20px; padding:10px 14px; background:#f0f9ff; border-radius:8px; font-size:11px; color:#0369a1; }
        @media (max-width:768px) { .lp { grid-template-columns:1fr; } .lp-hero { display:none; } .lp-right { padding:32px 24px; } }
        @keyframes fadeUp { from { opacity:0; transform:translateY(16px); } to { opacity:1; transform:translateY(0); } }
      `}</style>

      <div className="lp">
        <div className="lp-hero">
          <div className="lp-grid" />
          <div className="lp-brand">
            <div className="lp-brand-mark">🏥</div>
            <div className="lp-brand-name">Clear<span>Care</span></div>
          </div>
          <div className="lp-body">
            <span className="lp-tag">Healthcare Decision Intelligence</span>
            <h1 className="lp-h1">Every decision.<br />Explained.<br />Trusted.</h1>
            <p className="lp-sub">ClearCare reads insurance policy documents, traces denial decisions to their exact source rule, and explains them — to clinicians and patients alike.</p>
          </div>
          <div className="lp-stats">
            {[['$262B','Lost to denials/yr'],['79%','Patients never use AI'],['95%','AI pilots fail']].map(([n,l]) => (
              <div className="lp-stat" key={l}><span className="lp-stat-num">{n}</span><span className="lp-stat-lbl">{l}</span></div>
            ))}
          </div>
        </div>

        <div className="lp-right">
          <div className="lp-card">
            <h2 className="lp-heading">{tab === 'login' ? 'Welcome back' : 'Create account'}</h2>
            <p className="lp-subheading">{tab === 'login' ? 'Sign in to your secure ClearCare workspace' : 'Select your role to get started'}</p>

            <div className="lp-tabs">
              {['login','signup'].map(t => (
                <button key={t} className={`lp-tab ${tab===t?'active':''}`}
                  onClick={() => { setTab(t); setError(''); setInfo('') }}>
                  {t === 'login' ? 'Sign In' : 'Sign Up'}
                </button>
              ))}
            </div>

            {tab === 'signup' && (
              <div className="role-grid">
                {[{id:'patient',icon:'🧑',name:'Patient',desc:'Understand my bills & rights'},
                  {id:'clinician',icon:'👨‍⚕️',name:'Clinician',desc:'Trace denials & take action'}].map(r => (
                  <div key={r.id} className={`role-card ${role===r.id?'active':''}`} onClick={() => setRole(r.id)}>
                    <span className="role-icon">{r.icon}</span>
                    <span className="role-name">{r.name}</span>
                    <span className="role-desc">{r.desc}</span>
                  </div>
                ))}
              </div>
            )}

            {error && <div className="msg-error">⚠ {error}</div>}
            {info  && <div className="msg-info">✓ {info}</div>}

            <div className="lp-field">
              <label className="lp-label">Email address</label>
              <input className="lp-input" type="email" placeholder="you@hospital.org"
                value={email} onChange={e => setEmail(e.target.value)}
                onKeyDown={e => e.key==='Enter' && handleSubmit()} autoComplete="email" />
            </div>
            <div className="lp-field">
              <label className="lp-label">Password</label>
              <input className="lp-input" type="password" placeholder="Minimum 8 characters"
                value={password} onChange={e => setPassword(e.target.value)}
                onKeyDown={e => e.key==='Enter' && handleSubmit()}
                autoComplete={tab==='login'?'current-password':'new-password'} />
            </div>
            {tab === 'signup' && role === 'clinician' && (
              <div className="lp-field">
                <label className="lp-label">Organization Code</label>
                <input className="lp-input" type="text" placeholder="Provided by your admin (try: DEMO2024)"
                  value={orgCode} onChange={e => setOrgCode(e.target.value)} autoComplete="off" />
              </div>
            )}

            <button className="lp-btn" onClick={handleSubmit} disabled={loading}>
              {loading ? 'Please wait...' : tab==='login' ? 'Sign In Securely' : 'Create Account'}
            </button>

            <div className="lp-footer">
              {tab==='login' ? "Don't have an account?" : 'Already have an account?'}
              <button onClick={() => { setTab(tab==='login'?'signup':'login'); setError(''); setInfo('') }}>
                {tab==='login' ? 'Sign Up' : 'Sign In'}
              </button>
            </div>
            <div className="lp-security">🔒 PHI-protected · TLS encrypted · Session expires in 15 min</div>
          </div>
        </div>
      </div>
    </>
  )
}
