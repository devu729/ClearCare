import { useState } from 'react'
import { useAuth } from '../lib/AuthContext'
import DenialTracer  from '../components/DenialTracer'
import AppealDrafter from '../components/AppealDrafter'

const NAV = [
  { id: 'home',           icon: '🏠', label: 'My Portal'         },
  { id: 'explain-denial', icon: '🔍', label: 'Explain My Denial'  },
  { id: 'appeal-letter',  icon: '✍️', label: 'Write My Appeal'   },
]

export default function PatientDashboard() {
  const { user, signOut } = useAuth()
  const [tab, setTab] = useState('home')

  return (
    <>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=DM+Mono:wght@300;400;500&display=swap');
        *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
        body { background: #f0f9ff; }

        .pd-shell {
          min-height: 100vh;
          display: grid;
          grid-template-rows: 64px 1fr;
          grid-template-columns: 230px 1fr;
          background: #f0f9ff;
          font-family: 'Outfit', sans-serif;
        }
        .pd-nav {
          grid-column: 1 / -1;
          display: flex; align-items: center; justify-content: space-between;
          padding: 0 28px; background: #fff;
          border-bottom: 1px solid #bae6fd;
          box-shadow: 0 1px 8px rgba(14,165,233,0.08);
          position: sticky; top: 0; z-index: 200;
        }
        .pd-brand { display: flex; align-items: center; gap: 10px; }
        .pd-brand-mark {
          width: 34px; height: 34px;
          background: linear-gradient(135deg, #0284c7, #38bdf8);
          border-radius: 8px; display: flex; align-items: center;
          justify-content: center; font-size: 16px;
          box-shadow: 0 2px 8px rgba(14,165,233,0.3);
        }
        .pd-brand-name { font-size: 18px; font-weight: 800; color: #0f172a; letter-spacing: -0.01em; }
        .pd-brand-name span { color: #0ea5e9; }
        .pd-nav-right { display: flex; align-items: center; gap: 14px; }
        .pd-badge { background: #e0f2fe; color: #0369a1; font-size: 11px; font-weight: 600; padding: 4px 10px; border-radius: 6px; }
        .pd-email { font-size: 13px; color: #64748b; }
        .pd-signout {
          padding: 7px 16px; border: 1.5px solid #fecaca; background: #fff;
          color: #dc2626; border-radius: 7px; font-family: 'Outfit', sans-serif;
          font-size: 13px; font-weight: 500; cursor: pointer; transition: all 0.2s;
        }
        .pd-signout:hover { background: #fef2f2; }

        .pd-sidebar {
          background: #fff; border-right: 1px solid #e0f2fe;
          padding: 20px 0; overflow-y: auto;
          position: sticky; top: 64px; height: calc(100vh - 64px);
        }
        .pd-sidebar-section { font-size: 10px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.12em; color: #cbd5e1; padding: 0 20px; margin: 16px 0 8px; }
        .pd-nav-item { display: flex; align-items: center; gap: 10px; padding: 10px 20px; cursor: pointer; transition: all 0.15s; border-left: 3px solid transparent; margin: 1px 0; }
        .pd-nav-item:hover { background: #f0f9ff; }
        .pd-nav-item.active { background: #f0f9ff; border-left-color: #0ea5e9; }
        .pd-nav-icon { font-size: 16px; width: 20px; text-align: center; flex-shrink: 0; }
        .pd-nav-label { font-size: 14px; color: #475569; }
        .pd-nav-item.active .pd-nav-label { color: #0284c7; font-weight: 600; }

        .pd-main { padding: 36px 48px; overflow-y: auto; }

        .pd-banner {
          background: linear-gradient(135deg, #0369a1 0%, #0ea5e9 60%, #38bdf8 100%);
          border-radius: 16px; padding: 36px 40px; margin-bottom: 28px;
          color: #fff; position: relative; overflow: hidden;
        }
        .pd-banner::after {
          content: '🏥'; font-size: 80px; position: absolute; right: 32px;
          top: 50%; transform: translateY(-50%); opacity: 0.15;
        }
        .pd-banner-title { font-size: 22px; font-weight: 800; margin-bottom: 8px; letter-spacing: -0.01em; }
        .pd-banner-sub { font-size: 14px; opacity: 0.85; line-height: 1.7; max-width: 440px; }

        .pd-cards { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 24px; }
        .pd-card {
          background: #fff; border: 1.5px solid #e0f2fe; border-radius: 14px;
          padding: 24px; cursor: pointer; transition: all 0.2s;
          box-shadow: 0 2px 8px rgba(14,165,233,0.06);
        }
        .pd-card:hover { border-color: #7dd3fc; transform: translateY(-2px); box-shadow: 0 6px 20px rgba(14,165,233,0.12); }
        .pd-card-icon { font-size: 28px; margin-bottom: 14px; display: block; }
        .pd-card-title { font-size: 16px; font-weight: 700; color: #0f172a; margin-bottom: 6px; }
        .pd-card-desc { font-size: 13px; color: #64748b; line-height: 1.7; }
        .pd-card-cta { display: inline-flex; align-items: center; gap: 6px; margin-top: 14px; font-size: 13px; font-weight: 600; color: #0ea5e9; }

        .pd-rights { background: #fff; border: 1px solid #e0f2fe; border-radius: 12px; padding: 24px; box-shadow: 0 2px 8px rgba(14,165,233,0.05); }
        .pd-rights-title { font-size: 15px; font-weight: 700; color: #0f172a; margin-bottom: 16px; }
        .pd-rights-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
        .pd-right-item { display: flex; gap: 8px; font-size: 13px; color: #475569; line-height: 1.5; }
        .pd-right-check { color: #0ea5e9; flex-shrink: 0; font-weight: 700; }

        @media (max-width: 768px) {
          .pd-shell { grid-template-columns: 1fr; }
          .pd-sidebar { display: none; }
          .pd-cards { grid-template-columns: 1fr; }
          .pd-rights-grid { grid-template-columns: 1fr; }
          .pd-main { padding: 24px 20px; }
        }
      `}</style>

      <div className="pd-shell">
        <header className="pd-nav">
          <div className="pd-brand">
            <div className="pd-brand-mark">🏥</div>
            <div className="pd-brand-name">Clear<span>Care</span></div>
          </div>
          <div className="pd-nav-right">
            <span className="pd-badge">Patient</span>
            <span className="pd-email">{user?.email}</span>
            <button className="pd-signout" onClick={signOut}>Sign Out</button>
          </div>
        </header>

        <aside className="pd-sidebar">
          <div className="pd-sidebar-section">My Tools</div>
          {NAV.map(item => (
            <div key={item.id} className={`pd-nav-item ${tab === item.id ? 'active' : ''}`}
              onClick={() => setTab(item.id)}>
              <span className="pd-nav-icon">{item.icon}</span>
              <span className="pd-nav-label">{item.label}</span>
            </div>
          ))}
        </aside>

        <main className="pd-main">
          {tab === 'home' && (
            <>
              <div className="pd-banner">
                <div className="pd-banner-title">You deserve to understand every decision made about your healthcare.</div>
                <div className="pd-banner-sub">ClearCare reads your denial letters, finds the exact rule that triggered the decision, and explains it in plain English — along with your rights and how to appeal.</div>
              </div>
              <div className="pd-cards">
                {[
                  { tab:'explain-denial', icon:'🔍', title:'Explain My Denial',  desc:"Upload your denial letter. We find the exact policy rule and explain what it means in plain English.", cta:'Get explanation →' },
                  { tab:'appeal-letter',  icon:'✍️', title:'Write My Appeal',    desc:'Get a pre-written appeal letter based on your specific denial reason. Just review and send.', cta:'Draft letter →' },
                ].map(c => (
                  <div className="pd-card" key={c.tab} onClick={() => setTab(c.tab)}>
                    <span className="pd-card-icon">{c.icon}</span>
                    <div className="pd-card-title">{c.title}</div>
                    <div className="pd-card-desc">{c.desc}</div>
                    <div className="pd-card-cta">{c.cta}</div>
                  </div>
                ))}
              </div>
              <div className="pd-rights">
                <div className="pd-rights-title">🏛️ Your Patient Rights</div>
                <div className="pd-rights-grid">
                  {[
                    'Right to an explanation for any denial',
                    'Right to appeal any insurance decision',
                    'Right to an independent external review',
                    'Right to continue care during appeal',
                    'Right to a written denial notice',
                    'Appeal deadlines are typically 30–180 days',
                  ].map(r => (
                    <div className="pd-right-item" key={r}>
                      <span className="pd-right-check">✓</span><span>{r}</span>
                    </div>
                  ))}
                </div>
              </div>
            </>
          )}
          {tab === 'explain-denial' && <DenialTracer userRole="patient" />}
          {tab === 'appeal-letter'  && <AppealDrafter />}
        </main>
      </div>
    </>
  )
}
