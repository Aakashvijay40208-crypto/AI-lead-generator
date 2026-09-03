import React, { useState, useEffect } from 'react';
import { useAuth } from './context/AuthContext';
import DashboardStats from './components/DashboardStats';
import SearchPanel from './components/SearchPanel';
import LeadsGrid from './components/LeadsGrid';
import AuditModal from './components/AuditModal';
import { LogOut, ShieldAlert, Cpu, Sparkles, LogIn, Lock, Mail } from 'lucide-react';
import './styles/theme.css';

// We run the Flask server locally on port 5000 (default)
const BACKEND_URL = "http://localhost:5000";

function AppContent() {
  const { user, loginWithGoogle, loginWithEmail, logout, isDemoMode } = useAuth();
  
  // Dashboard & Leads states
  const [leads, setLeads] = useState([]);
  const [stats, setStats] = useState({
    leadsGenerated: 0,
    hotLeads: 0,
    averageLeadScore: 0,
    websitesWithoutWebsite: 0,
    analyzedBusinesses: 0
  });
  const [apiStatus, setApiStatus] = useState({});
  const [selectedLeadId, setSelectedLeadId] = useState(null);
  const [currentSearchId, setCurrentSearchId] = useState(null);
  
  // Filtering & Sorting states
  const [filters, setFilters] = useState({
    city: '',
    website: '',
    leadScore: '',
    rating: ''
  });
  const [sortBy, setSortBy] = useState('-score');

  // Login Form State
  const [emailInput, setEmailInput] = useState('');
  const [passwordInput, setPasswordInput] = useState('');
  const [loginError, setLoginError] = useState('');
  const [loginLoading, setLoginLoading] = useState(false);

  // Reload data from backend
  const refreshData = async () => {
    try {
      // 1. Fetch leads
      const params = new URLSearchParams();
      Object.entries(filters).forEach(([k, v]) => {
        if (v) params.append(k, v);
      });
      if (sortBy) params.append('sort_by', sortBy);
      if (currentSearchId) params.append('search_id', currentSearchId);
      
      const leadsRes = await fetch(`${BACKEND_URL}/api/leads?${params.toString()}`);
      if (leadsRes.ok) {
        const leadsData = await leadsRes.json();
        setLeads(leadsData);
      }

      // 2. Fetch stats
      const statsRes = await fetch(`${BACKEND_URL}/api/stats`);
      if (statsRes.ok) {
        const statsData = await statsRes.json();
        setStats(statsData);
      }

      // 3. Fetch API status
      const apiRes = await fetch(`${BACKEND_URL}/api/api-status`);
      if (apiRes.ok) {
        const apiData = await apiRes.json();
        setApiStatus(apiData);
      }
    } catch (e) {
      console.error("Failed to load dashboard data:", e);
    }
  };

  // Reload when filters/sorting change
  useEffect(() => {
    if (user) {
      refreshData();
    }
  }, [filters, sortBy, user, currentSearchId]);

  // Handle email login
  const handleEmailLogin = async (e) => {
    e.preventDefault();
    setLoginError('');
    setLoginLoading(true);
    const { data, error } = await loginWithEmail(emailInput, passwordInput);
    setLoginLoading(false);
    if (error) {
      setLoginError(error.message || "Invalid email or password");
    }
  };

  // Unauthenticated: Render Login view
  if (!user) {
    return (
      <div style={loginContainerStyle}>
        <div className="glass-panel animate-fade-in" style={loginCardStyle}>
          {/* Logo */}
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '8px', marginBottom: '24px' }}>
            <div style={logoIconStyle} className="pulse-glow">
              <Cpu size={32} style={{ color: 'var(--primary)' }} />
            </div>
            <h1 style={{ fontSize: '24px', fontWeight: 800, fontFamily: 'var(--font-display)', marginTop: '12px' }}>
              OXIS Lead Intelligence
            </h1>
            <p style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
              B2B Digital Audit & Scraper Platform
            </p>
          </div>

          {isDemoMode && (
            <div style={demoBannerStyle}>
              <Sparkles size={14} style={{ color: 'var(--accent)' }} />
              <span>Running in local Simulation mode (Supabase keys not set)</span>
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleEmailLogin} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div>
              <label className="form-label">Email Address</label>
              <div style={{ position: 'relative' }}>
                <Mail size={16} style={inputIconStyle} />
                <input 
                  type="email" 
                  className="form-input" 
                  placeholder="agent@oxis.com" 
                  value={emailInput}
                  onChange={(e) => setEmailInput(e.target.value)}
                  style={{ paddingLeft: '40px' }}
                  required
                />
              </div>
            </div>

            <div>
              <label className="form-label">Password</label>
              <div style={{ position: 'relative' }}>
                <Lock size={16} style={inputIconStyle} />
                <input 
                  type="password" 
                  className="form-input" 
                  placeholder="••••••••" 
                  value={passwordInput}
                  onChange={(e) => setPasswordInput(e.target.value)}
                  style={{ paddingLeft: '40px' }}
                  required
                />
              </div>
            </div>

            {loginError && (
              <div style={loginErrorStyle}>
                <ShieldAlert size={14} />
                <span>{loginError}</span>
              </div>
            )}

            <button 
              type="submit" 
              className="btn-primary" 
              style={{ width: '100%', justifyContent: 'center', padding: '14px' }}
              disabled={loginLoading}
            >
              <LogIn size={16} />
              {loginLoading ? "Signing in..." : "Sign In to Platform"}
            </button>
          </form>

          {/* Google OAuth Button */}
          <div style={dividerStyle}>
            <span style={{ background: 'var(--bg-deep)', padding: '0 10px', color: 'var(--text-muted)', fontSize: '11px', textTransform: 'uppercase' }}>
              Or
            </span>
          </div>

          <button 
            onClick={loginWithGoogle} 
            className="btn-secondary" 
            style={{ width: '100%', justifyContent: 'center', padding: '12px', border: '1px solid rgba(99,102,241,0.2)' }}
          >
            <svg style={{ width: '16px', height: '16px', marginRight: '8px' }} viewBox="0 0 24 24">
              <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
              <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
              <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z" />
              <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z" />
            </svg>
            Sign In with Google
          </button>
        </div>
      </div>
    );
  }

  // Authenticated: Render Dashboard
  return (
    <div style={dashboardShellStyle}>
      {/* Header bar */}
      <header style={headerStyle}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div style={{ background: 'var(--primary-gradient)', padding: '8px', borderRadius: '8px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Cpu size={20} style={{ color: '#fff' }} />
          </div>
          <div>
            <h2 style={{ fontSize: '16px', fontWeight: 800, fontFamily: 'var(--font-display)' }}>
              OXIS Lead Intelligence
            </h2>
            <span style={{ fontSize: '10px', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 700, letterSpacing: '0.05em' }}>
              B2B transformation Engine
            </span>
          </div>
        </div>

        {/* User bar */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <img 
              src={user.user_metadata?.avatar_url || `https://api.dicebear.com/7.x/initials/svg?seed=${user.email}`} 
              alt="Avatar" 
              style={{ width: '32px', height: '32px', borderRadius: '50%', border: '1px solid var(--border-light)' }}
            />
            <div style={{ display: 'none', mdBlock: 'block' }}>
              <div style={{ fontSize: '13px', fontWeight: 600 }}>
                {user.user_metadata?.full_name || user.email.split('@')[0]}
              </div>
              <div style={{ fontSize: '10px', color: 'var(--text-muted)' }}>
                {user.email}
              </div>
            </div>
          </div>
          <button onClick={logout} className="btn-secondary" style={{ padding: '8px 12px', fontSize: '12px' }}>
            <LogOut size={12} />
            Logout
          </button>
        </div>
      </header>

      {/* Main Grid dashboard */}
      <main style={mainContentStyle}>
        <div style={{ display: 'grid', gridTemplateColumns: '1.4fr 1fr', gap: '24px', alignItems: 'start', flexWrap: 'wrap' }}>
          {/* Left panel: Search Form */}
          <SearchPanel 
            onSearchComplete={(sId) => setCurrentSearchId(sId)} 
            onSearchStart={() => {
              setLeads([]);
              setCurrentSearchId(null);
            }}
            backendUrl={BACKEND_URL} 
          />
          
          {/* Right panel: Aggregated metrics */}
          <DashboardStats stats={stats} apiStatus={apiStatus} />
        </div>

        {/* Data leads grid */}
        <div style={{ marginTop: '24px' }}>
          <h3 style={{ fontSize: '18px', fontWeight: 700, fontFamily: 'var(--font-display)', marginBottom: '16px' }}>
            Collected Leads Pipeline
          </h3>
          <LeadsGrid 
            leads={leads} 
            filters={filters} 
            setFilters={setFilters} 
            sortBy={sortBy} 
            setSortBy={setSortBy} 
            onSelectLead={setSelectedLeadId}
            backendUrl={BACKEND_URL}
          />
        </div>
      </main>

      {/* Detail Audit Modal overlay */}
      {selectedLeadId && (
        <AuditModal 
          leadId={selectedLeadId} 
          onClose={() => setSelectedLeadId(null)} 
          backendUrl={BACKEND_URL}
        />
      )}
    </div>
  );
}

// Global wrap to apply auth provider
export default function App() {
  return (
    <div className="App">
      <AppContent />
    </div>
  );
}

// Inline layouts styles
const loginContainerStyle = {
  display: 'flex',
  minHeight: '100vh',
  alignItems: 'center',
  justifyContent: 'center',
  padding: '20px',
  background: 'radial-gradient(circle at center, #0F1229 0%, var(--bg-space) 100%)'
};

const loginCardStyle = {
  width: '100%',
  maxWidth: '400px',
  padding: '30px',
  background: 'rgba(18, 23, 49, 0.85)',
  border: '1px solid rgba(255, 255, 255, 0.08)'
};

const logoIconStyle = {
  background: 'rgba(99, 102, 241, 0.08)',
  border: '1px solid var(--border-glow)',
  borderRadius: '16px',
  width: '64px',
  height: '64px',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center'
};

const demoBannerStyle = {
  display: 'flex',
  alignItems: 'center',
  gap: '8px',
  background: 'rgba(6, 182, 212, 0.08)',
  border: '1px solid rgba(6, 182, 212, 0.15)',
  borderRadius: '8px',
  padding: '10px 14px',
  fontSize: '12px',
  color: '#A5F3FC',
  marginBottom: '20px',
  lineHeight: '1.4'
};

const inputIconStyle = {
  position: 'absolute',
  top: '50%',
  left: '14px',
  transform: 'translateY(-50%)',
  color: 'var(--text-muted)'
};

const loginErrorStyle = {
  display: 'flex',
  alignItems: 'center',
  gap: '8px',
  color: 'var(--error)',
  fontSize: '12px',
  background: 'rgba(239, 68, 68, 0.05)',
  border: '1px solid rgba(239, 68, 68, 0.15)',
  padding: '8px 12px',
  borderRadius: '6px'
};

const dividerStyle = {
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  margin: '16px 0',
  position: 'relative',
  borderBottom: '1px solid var(--border-light)'
};

const dashboardShellStyle = {
  minHeight: '100vh',
  display: 'flex',
  flexDirection: 'column'
};

const headerStyle = {
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'space-between',
  padding: '16px 30px',
  borderBottom: '1px solid var(--border-light)',
  background: 'rgba(18, 23, 49, 0.45)',
  backdropFilter: 'var(--panel-blur)'
};

const mainContentStyle = {
  flexGrow: 1,
  padding: '30px',
  maxWidth: '1200px',
  width: '100%',
  margin: '0 auto',
  display: 'flex',
  flexDirection: 'column',
  gap: '24px'
};
