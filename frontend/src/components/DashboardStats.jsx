import React from 'react';
import { Target, Flame, BarChart3, Globe2, KeyRound, CheckCircle2, ShieldAlert } from 'lucide-react';

export default function DashboardStats({ stats, apiStatus }) {
  const cards = [
    {
      title: "Leads Generated",
      value: stats.leadsGenerated || 0,
      sub: "Total discovered",
      icon: Target,
      color: "var(--accent)"
    },
    {
      title: "Hot Opportunities",
      value: stats.hotLeads || 0,
      sub: "Score >= 80 (Urgent)",
      icon: Flame,
      color: "var(--error)"
    },
    {
      title: "Avg Lead Score",
      value: `${stats.averageLeadScore || 0}/100`,
      sub: "Overall prospect value",
      icon: BarChart3,
      color: "var(--primary)"
    },
    {
      title: "No Website Gaps",
      value: stats.websitesWithoutWebsite || 0,
      sub: "Immediate redesign leads",
      icon: Globe2,
      color: "var(--warning)"
    }
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Stat Cards Grid */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
        gap: '20px'
      }}>
        {cards.map((c, i) => {
          const Icon = c.icon;
          return (
            <div 
              key={i} 
              className="glass-panel animate-fade-in"
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '20px',
                animationDelay: `${i * 0.05}s`
              }}
            >
              <div>
                <span style={{ fontSize: '12px', color: 'var(--text-secondary)', fontWeight: 600, textTransform: 'uppercase' }}>
                  {c.title}
                </span>
                <h3 style={{ fontSize: '28px', margin: '8px 0 4px 0', fontFamily: 'var(--font-display)', fontWeight: 800 }}>
                  {c.value}
                </h3>
                <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                  {c.sub}
                </span>
              </div>
              <div style={{
                background: `rgba(255, 255, 255, 0.03)`,
                border: `1px solid rgba(255, 255, 255, 0.05)`,
                borderRadius: '12px',
                padding: '12px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: c.color
              }}>
                <Icon size={24} />
              </div>
            </div>
          );
        })}
      </div>

      {/* API Key Health & Rotation Indicator */}
      <div className="glass-panel animate-fade-in" style={{ padding: '16px 20px', animationDelay: '0.2s' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
          <KeyRound size={16} style={{ color: 'var(--primary)' }} />
          <span style={{ fontSize: '13px', fontWeight: 600, fontFamily: 'var(--font-display)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            API Key Rotation & Quota Monitor
          </span>
        </div>
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: '16px'
        }}>
          {Object.entries(apiStatus || {}).map(([provider, details]) => {
            const isHealthy = details.status === "Healthy";
            return (
              <div 
                key={provider} 
                style={{
                  background: 'rgba(255, 255, 255, 0.02)',
                  border: '1px solid var(--border-light)',
                  borderRadius: '8px',
                  padding: '10px 14px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between'
                }}
              >
                <div>
                  <span style={{ fontSize: '13px', fontWeight: 700, textTransform: 'capitalize' }}>
                    {provider}
                  </span>
                  <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '2px' }}>
                    Active Keys: {details.active_keys}/{details.total_keys} | Calls: {details.total_calls}
                  </div>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  {isHealthy ? (
                    <CheckCircle2 size={14} style={{ color: 'var(--success)' }} />
                  ) : (
                    <ShieldAlert size={14} style={{ color: 'var(--warning)' }} />
                  )}
                  <span style={{ 
                    fontSize: '11px', 
                    fontWeight: 600, 
                    color: isHealthy ? 'var(--success)' : 'var(--warning)' 
                  }}>
                    {details.status}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
