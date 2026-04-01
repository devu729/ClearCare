import { useState } from 'react'
import { useAuth } from '../lib/AuthContext'
import PolicyParser  from '../components/PolicyParser'
import DenialTracer  from '../components/DenialTracer'
import AppealDrafter from '../components/AppealDrafter'
import AuditLog      from '../components/AuditLog'

const NAV = [
  { id: 'overview',       icon: '◈',  label: 'Overview'       },
  { id: 'policy-parser',  icon: '📄', label: 'Policy Parser'  },
  { id: 'denial-tracer',  icon: '🔍', label: 'Denial Tracer'  },
  { id: 'appeal-drafter', icon: '✍️', label: 'Appeal Drafter' },
  { id: 'audit-log',      icon: '🛡️', label: 'Audit Log'      },
]

const CARDS = [
  { tab: 'policy-parser',  icon: '📄', title: 'Policy Parser',   desc: 'Upload insurance PDFs. Rules extracted, PHI-stripped, indexed to ChromaDB.',     tag: '✓ Live',    live: true  },
  { tab: 'denial-tracer',  icon: '🔍', title: 'Denial Tracer',   desc: 'Enter denial code → exact policy rule match → clinician & patient explanation.', tag: '✓ Live',    live: true  },
  { tab: 'appeal-drafter', icon: '✍️', title: 'Appeal Drafter',  desc: 'Auto-generate appeal letters. Send via email. Track deadline in Calendar.',      tag: '✓ Live',    live: true  },
  { tab: null,              icon: '🔔', title: 'Slack Alerts',    desc: 'Urgent denial alerts to Slack by severity. Clinicians get pinged instantly.',    tag: 'MCP',       live: false },
  { tab: null,              icon: '📅', title: 'Calendar Track',  desc: 'Appeal deadlines auto-created in Google Calendar with reminders.',               tag: 'MCP',       live: false },
  { tab: 'audit-log',      icon: '🛡️', title: 'Audit Log',       desc: 'Every action logged. Full HIPAA compliance trail — no PHI in logs.',             tag: '✓ Live',    live: true  },
]

export default function ClinicianDashboard() {
  const { user, signOut } = useAuth()
  const [tab, setTab] = useState('overview')

  return (
    <>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=DM+Mono:wght@300;400;500&display=swap');
        *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
        body { background: #f0f9ff; }

        .cd-shell {
          min-height: 100vh;
          display: grid;
          grid-template-rows: 64px 1fr;
          grid-template-columns: 230px 1fr;
          background: #f0f9ff;
          font-family: 'Outfit', sans-serif;
        }
        .cd-nav {
          grid-column: 1 / -1;
          display: flex; align-items: center; justify-content: space-between;
          padding: 0 28px; background: #fff;
          border-bottom: 1px solid #e0f2fe;
          box-shadow: 0 1px 8px rgba(14,165,233,0.08);
          position: sticky; top: 0; z-index: 200;
        }
        .cd-brand { display: flex; align-items: center; gap: 10px; }
        .cd-brand-mark {
          width: 34px; height: 34px;
          background: linear-gradient(135deg, #0284c7, #38bdf8);
          border-radius: 8px; display: flex; align-items: center;
          justify-content: center; font-size: 16px;
          box-shadow: 0 2px 8px rgba(14,165,233,0.3);
        }
        .cd-brand-name { font-size: 18px; font-weight: 800; color: #0f172a; letter-spacing: -0.01em; }
        .cd-brand-name span { color: #0ea5e9; }
        .cd-nav-right { display: flex; align-items: center; gap: 14px; }
        .cd-badge { background: #e0f2fe; color: #0369a1; font-size: 11px; font-weight: 600; padding: 4px 10px; border-radius: 6px; }
        .cd-user-email { font-size: 13px; color: #64748b; }
        .cd-signout {
          padding: 7px 16px; border: 1.5px solid #fecaca; background: #fff;
          color: #dc2626; border-radius: 7px; font-family: 'Outfit', sans-serif;
          font-size: 13px; font-weight: 500; cursor: pointer; transition: all 0.2s;
        }
        .cd-signout:hover { background: #fef2f2; }

        .cd-sidebar {
          background: #fff; border-right: 1px solid #e0f2fe;
          padding: 20px 0; overflow-y: auto;
          position: sticky; top: 64px; height: calc(100vh - 64px);
        }
        .cd-sidebar-section {
          font-size: 10px; font-weight: 600; text-transform: uppercase;
          letter-spacing: 0.12em; color: #cbd5e1; padding: 0 20px; margin: 16px 0 8px;
        }
        .cd-nav-item {
          display: flex; align-items: center; gap: 10px;
          padding: 10px 20px; cursor: pointer; transition: all 0.15s;
          border-left: 3px solid transparent; margin: 1px 0;
        }
        .cd-nav-item:hover { background: #f0f9ff; }
        .cd-nav-item.active { background: #f0f9ff; border-left-color: #0ea5e9; }
        .cd-nav-icon { font-size: 16px; width: 20px; text-align: center; flex-shrink: 0; }
        .cd-nav-label { font-size: 14px; color: #475569; }
        .cd-nav-item.active .cd-nav-label { color: #0284c7; font-weight: 600; }
        .cd-sidebar-divider { height: 1px; background: #f0f9ff; margin: 12px 16px; }
        .cd-mcp-tag {
          font-size: 8px; background: #dcfce7; color: #166534;
          padding: 2px 6px; border-radius: 4px; font-weight: 600; margin-left: auto;
        }

        .cd-main { padding: 36px 48px; overflow-y: auto; }
        .cd-ov-title { font-size: 26px; font-weight: 700; color: #0f172a; letter-spacing: -0.01em; margin-bottom: 4px; }
        .cd-ov-title span { color: #0ea5e9; }
        .cd-ov-sub { font-size: 14px; color: #64748b; margin-bottom: 28px; }
        .cd-ov-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }
        .cd-ov-card {
          background: #fff; border: 1.5px solid #e0f2fe; border-radius: 14px;
          padding: 22px; cursor: pointer; transition: all 0.2s;
          box-shadow: 0 2px 8px rgba(14,165,233,0.06);
        }
        .cd-ov-card:hover { border-color: #7dd3fc; transform: translateY(-2px); box-shadow: 0 6px 18px rgba(14,165,233,0.12); }
        .cd-ov-card.no-click { cursor: default; opacity: 0.7; }
        .cd-ov-card.no-click:hover { transform: none; }
        .cd-ov-icon { font-size: 24px; margin-bottom: 12px; }
        .cd-ov-card-title { font-size: 15px; font-weight: 700; color: #0f172a; margin-bottom: 6px; }
        .cd-ov-card-desc { font-size: 12px; color: #64748b; line-height: 1.7; }
        .cd-ov-tag {
          display: inline-block; margin-top: 12px;
          font-size: 10px; font-weight: 600; text-transform: uppercase;
          letter-spacing: 0.08em; padding: 3px 9px; border-radius: 5px;
        }
        .tag-live { background: #dcfce7; color: #166534; }
        .tag-mcp  { background: #e0f2fe; color: #0369a1; }

        @media (max-width: 1024px) { .cd-ov-grid { grid-template-columns: repeat(2, 1fr); } }
        @media (max-width: 768px) {
          .cd-shell { grid-template-columns: 1fr; }
          .cd-sidebar { display: none; }
          .cd-main { padding: 24px 20px; }
          .cd-ov-grid { grid-template-columns: 1fr; }
        }
      `}</style>

      <div className="cd-shell">
        <header className="cd-nav">
          <div className="cd-brand">
            <div className="cd-brand-mark">🏥</div>
            <div className="cd-brand-name">Clear<span>Care</span></div>
          </div>
          <div className="cd-nav-right">
            <span className="cd-badge">Clinician</span>
            <span className="cd-user-email">{user?.email}</span>
            <button className="cd-signout" onClick={signOut}>Sign Out</button>
          </div>
        </header>

        <aside className="cd-sidebar">
          <div className="cd-sidebar-section">Workspace</div>
          {NAV.map(item => (
            <div key={item.id}
              className={`cd-nav-item ${tab === item.id ? 'active' : ''}`}
              onClick={() => setTab(item.id)}>
              <span className="cd-nav-icon">{item.icon}</span>
              <span className="cd-nav-label">{item.label}</span>
            </div>
          ))}
          <div className="cd-sidebar-divider" />
          <div className="cd-sidebar-section">Communication</div>
          {[{icon:'📧',label:'Gmail'},{icon:'📅',label:'Google Calendar'}].map(m => (
            <div key={m.label} className="cd-nav-item" style={{cursor:'default'}}>
              <span className="cd-nav-icon">{m.icon}</span>
              <span className="cd-nav-label" style={{fontSize:13,color:'#94a3b8'}}>{m.label}</span>
              <span className="cd-mcp-tag">ON</span>
            </div>
          ))}
        </aside>

        <main className="cd-main">
          {tab === 'overview' && (
            <>
              <h1 className="cd-ov-title">Clinician <span>Dashboard</span></h1>
              <p className="cd-ov-sub">All agents are live — select one to get started</p>
              <div className="cd-ov-grid">
                {CARDS.map(card => (
                  <div key={card.title}
                    className={`cd-ov-card ${!card.live ? 'no-click' : ''}`}
                    onClick={() => card.tab && setTab(card.tab)}>
                    <div className="cd-ov-icon">{card.icon}</div>
                    <div className="cd-ov-card-title">{card.title}</div>
                    <div className="cd-ov-card-desc">{card.desc}</div>
                    <span className={`cd-ov-tag ${card.live ? 'tag-live' : 'tag-mcp'}`}>{card.tag}</span>
                  </div>
                ))}
              </div>
            </>
          )}
          {tab === 'policy-parser'  && <PolicyParser />}
          {tab === 'denial-tracer'  && <DenialTracer userRole="clinician" />}
          {tab === 'appeal-drafter' && <AppealDrafter />}
          {tab === 'audit-log'      && <AuditLog />}
        </main>
      </div>
    </>
  )
}
