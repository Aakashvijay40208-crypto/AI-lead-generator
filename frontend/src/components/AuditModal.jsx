import React, { useState } from 'react';
import { X, Mail, Phone, Globe, Shield, ShieldCheck, Gauge, Copy, Check, ExternalLink, Calendar, MessageSquare, Laptop, Smartphone } from 'lucide-react';

export default function AuditModal({ leadId, onClose, backendUrl }) {
  const [lead, setLead] = React.useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('audit'); // 'audit' | 'screenshots'
  const [copied, setCopied] = useState(false);

  React.useEffect(() => {
    async function fetchLeadDetails() {
      try {
        const response = await fetch(`${backendUrl}/api/leads/${leadId}`);
        if (response.ok) {
          const data = await response.json();
          setLead(data);
        }
      } catch (err) {
        console.error("Error fetching lead detail:", err);
      } finally {
        setLoading(false);
      }
    }
    if (leadId) fetchLeadDetails();
  }, [leadId]);

  if (loading) {
    return (
      <div style={modalOverlayStyle}>
        <div className="glass-panel" style={{ width: '400px', display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '40px', gap: '16px' }}>
          <div style={{ border: '3px solid rgba(255,255,255,0.1)', borderTop: '3px solid var(--primary)', borderRadius: '50%', width: '40px', height: '40px', animation: 'spin 1s linear infinite' }} />
          <span style={{ fontSize: '14px', color: 'var(--text-secondary)' }}>Gathering lead intelligence...</span>
        </div>
        <style>{`@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }`}</style>
      </div>
    );
  }

  if (!lead) return null;

  const audit = lead.audit_reports || {};
  const scores = lead.lead_scores || {};
  const contacts = lead.contacts || {};
  const seo = audit.seo || {};
  const ux = audit.ux || {};
  const tech = audit.tech_detected || {};
  const socials = contacts.socialLinks || {};

  const handleCopyPitch = () => {
    if (lead.lead_scores?.recommended_services) {
      // In mock mode or real mode we fetch the AI report custom pitch
      const pitch = lead.lead_scores?.personalized_pitch || `Hi there,\n\nI was looking up services and came across ${lead.name}...`;
      navigator.clipboard.writeText(pitch);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const getProblemLabel = (key) => {
    const labels = {
      no_website: "No Website",
      poor_seo: "Poor SEO optimization",
      poor_performance: "Poor speed performance",
      old_website: "Outdated website (> 5 years old)",
      missing_ssl: "Missing SSL connection",
      missing_whatsapp: "No WhatsApp CTA",
      missing_booking: "No Online booking",
      poor_mobile_experience: "Not mobile friendly",
      outdated_design: "Legacy design",
      broken_contact_form: "Broken contact form"
    };
    return labels[key] || key;
  };

  return (
    <div style={modalOverlayStyle}>
      <div className="glass-panel animate-fade-in audit-modal-content" style={modalContentStyle}>
        
        {/* Modal Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', borderBottom: '1px solid var(--border-light)', paddingBottom: '16px', marginBottom: '20px' }}>
          <div>
            <h2 style={{ fontSize: '22px', fontWeight: 800, fontFamily: 'var(--font-display)' }}>
              {lead.name}
            </h2>
            <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginTop: '4px' }}>
              {lead.address}
            </p>
          </div>
          <button onClick={onClose} style={closeBtnStyle}>
            <X size={18} />
          </button>
        </div>

        {/* Modal Scrollable Body */}
        <div style={modalBodyStyle} className="audit-modal-body">
          
          {/* Left Column: Tech Audits & Info */}
          <div style={{ flex: '1.2', display: 'flex', flexDirection: 'column', gap: '20px', minWidth: '280px' }}>
            
            {/* Tabs selector */}
            <div style={{ display: 'flex', gap: '10px', borderBottom: '1px solid var(--border-light)', paddingBottom: '10px' }}>
              <button 
                onClick={() => setActiveTab('audit')} 
                style={activeTab === 'audit' ? tabActiveStyle : tabInactiveStyle}
              >
                Presence & Audit Logs
              </button>
              <button 
                onClick={() => setActiveTab('screenshots')} 
                style={activeTab === 'screenshots' ? tabActiveStyle : tabInactiveStyle}
                disabled={!lead.website}
              >
                Visual Mockups
              </button>
            </div>

            {activeTab === 'audit' ? (
              <>
                {/* Contact profiles */}
                <div style={cardStyle}>
                  <h4 style={cardHeaderStyle}>Contact Channels</h4>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', marginTop: '12px' }}>
                    <div style={contactRowStyle}>
                      <Phone size={14} style={{ color: 'var(--primary)' }} />
                      <span style={{ fontSize: '13px' }}>{lead.phone_number || "No Phone available"}</span>
                    </div>
                    <div style={contactRowStyle}>
                      <Mail size={14} style={{ color: 'var(--primary)' }} />
                      <span style={{ fontSize: '13px', wordBreak: 'break-word' }}>
                        {contacts.emails?.length > 0 ? contacts.emails.join(", ") : "No emails found"}
                      </span>
                    </div>
                    <div style={contactRowStyle}>
                      <Globe size={14} style={{ color: 'var(--primary)' }} />
                      <span style={{ fontSize: '13px', wordBreak: 'break-word' }}>
                        {lead.website ? (
                          <a href={lead.website} target="_blank" rel="noopener noreferrer" style={{ color: 'var(--accent)', textDecoration: 'none' }}>
                            {lead.website} <ExternalLink size={10} style={{ display: 'inline' }} />
                          </a>
                        ) : "No Website"}
                      </span>
                    </div>
                    {/* Socials badges */}
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', marginTop: '8px' }}>
                      {Object.entries(socials).map(([platform, link]) => {
                        if (!link) return null;
                        return (
                          <a 
                            key={platform} 
                            href={link} 
                            target="_blank" 
                            rel="noopener noreferrer"
                            style={socialBadgeStyle}
                          >
                            {platform}
                          </a>
                        );
                      })}
                    </div>
                  </div>
                </div>

                {/* Playwright Core Audit details */}
                <div style={cardStyle}>
                  <h4 style={cardHeaderStyle}>Playwright Website Audit</h4>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))', gap: '16px', marginTop: '12px' }}>
                    <div style={auditStatStyle}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                        {audit.is_https ? (
                          <ShieldCheck size={16} style={{ color: 'var(--success)' }} />
                        ) : (
                          <Shield size={16} style={{ color: 'var(--error)' }} />
                        )}
                        <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Security SSL</span>
                      </div>
                      <span style={{ fontSize: '14px', fontWeight: 700, marginTop: '4px' }}>
                        {audit.is_https ? "HTTPS Secure" : "HTTP Insecure"}
                      </span>
                    </div>

                    <div style={auditStatStyle}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                        <Gauge size={16} style={{ color: audit.response_time_ms > 3000 ? 'var(--error)' : 'var(--success)' }} />
                        <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Response Time</span>
                      </div>
                      <span style={{ fontSize: '14px', fontWeight: 700, marginTop: '4px' }}>
                        {lead.website ? `${audit.response_time_ms || 0} ms` : "N/A"}
                      </span>
                    </div>
                  </div>

                  {/* SEO Details */}
                  {lead.website && (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginTop: '16px', borderTop: '1px solid var(--border-light)', paddingTop: '12px' }}>
                      <div style={{ fontSize: '12px', wordBreak: 'break-word' }}>
                        <strong style={{ color: 'var(--text-secondary)' }}>SEO Title:</strong>{" "}
                        <span style={{ color: seo.title ? 'var(--text-primary)' : 'var(--error)' }}>
                          {seo.title || "[Missing SEO Title Tag]"}
                        </span>
                      </div>
                      <div style={{ fontSize: '12px', wordBreak: 'break-word' }}>
                        <strong style={{ color: 'var(--text-secondary)' }}>Meta Description:</strong>{" "}
                        <span style={{ color: seo.description ? 'var(--text-primary)' : 'var(--error)' }}>
                          {seo.description || "[Missing Meta Description]"}
                        </span>
                      </div>
                      <div style={{ fontSize: '12px', wordBreak: 'break-word' }}>
                        <strong style={{ color: 'var(--text-secondary)' }}>H1 Headers:</strong>{" "}
                        <span style={{ color: seo.h1Hierarchy?.length ? 'var(--text-primary)' : 'var(--warning)' }}>
                          {seo.h1Hierarchy?.length ? seo.h1Hierarchy.join(" | ") : "[No H1 Tags Found]"}
                        </span>
                      </div>
                    </div>
                  )}
                </div>

                {/* Tech discovery check lists */}
                <div style={cardStyle}>
                  <h4 style={cardHeaderStyle}>Technology & Features Detected</h4>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))', gap: '10px', marginTop: '12px' }}>
                    {Object.entries(tech).map(([key, val]) => (
                      <div 
                        key={key} 
                        style={{ 
                          display: 'flex', 
                          alignItems: 'center', 
                          gap: '6px',
                          background: 'rgba(255, 255, 255, 0.02)',
                          padding: '6px 10px',
                          borderRadius: '6px',
                          border: '1px solid var(--border-light)'
                        }}
                      >
                        <span style={{
                          width: '8px',
                          height: '8px',
                          borderRadius: '50%',
                          background: val ? 'var(--success)' : 'rgba(255, 255, 255, 0.1)'
                        }} />
                        <span style={{ fontSize: '11px', textTransform: 'capitalize' }}>
                          {key.replace(/([A-Z])/g, ' $1').trim()}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              </>
            ) : (
              /* Visual screenshot slides */
              <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                {audit.screenshots?.desktopUrl ? (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                    <div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '13px', fontWeight: 600, marginBottom: '6px' }}>
                        <Laptop size={14} /> Desktop Screenshot
                      </div>
                      <div style={imgContainerStyle}>
                        <img 
                          src={`${backendUrl}${audit.screenshots.desktopUrl}`} 
                          alt="Desktop Website View" 
                          style={{ width: '100%', height: 'auto', display: 'block', borderRadius: '4px' }}
                        />
                      </div>
                    </div>

                    <div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '13px', fontWeight: 600, marginBottom: '6px' }}>
                        <Smartphone size={14} /> Mobile Screenshot
                      </div>
                      <div style={{ ...imgContainerStyle, maxWidth: '280px', margin: '0 auto' }}>
                        <img 
                          src={`${backendUrl}${audit.screenshots.mobileUrl}`} 
                          alt="Mobile Website View" 
                          style={{ width: '100%', height: 'auto', display: 'block', borderRadius: '4px' }}
                        />
                      </div>
                    </div>
                  </div>
                ) : (
                  <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-secondary)' }}>
                    No visual screenshots available for this lead.
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Right Column: Lead Score & Audit Gaps */}
          <div style={{ flex: '1', display: 'flex', flexDirection: 'column', gap: '20px', minWidth: '280px', borderLeft: '1px solid var(--border-light)', paddingLeft: '20px' }} className="audit-modal-right-col">

            
            {/* Score circle & Website Status */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
              <div style={{
                background: 'var(--primary-gradient)',
                color: '#fff',
                width: '64px',
                height: '64px',
                borderRadius: '50%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '22px',
                fontWeight: 800,
                fontFamily: 'var(--font-display)',
                boxShadow: '0 0 15px rgba(99, 102, 241, 0.4)'
              }}>
                {scores.score}
              </div>
              <div>
                <span style={{ fontSize: '11px', color: 'var(--text-secondary)', textTransform: 'uppercase', fontWeight: 600 }}>
                  Lead Score & Priority
                </span>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '4px' }}>
                  <span className={`badge-priority ${scores.priority?.toLowerCase()}`} style={{ fontSize: '13px', padding: '6px 12px' }}>
                    {scores.priority} OPPORTUNITY
                  </span>
                </div>
              </div>
            </div>

            {/* Website Status card */}
            <div style={cardStyle}>
              <h4 style={cardHeaderStyle}>Website Availability</h4>
              <div style={{ marginTop: '8px' }}>
                <span style={{
                  display: 'inline-block',
                  padding: '6px 14px',
                  borderRadius: '20px',
                  fontSize: '12px',
                  fontWeight: 700,
                  background: lead.website ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)',
                  color: lead.website ? 'var(--success)' : 'var(--error)',
                  border: `1px solid ${lead.website ? 'rgba(16, 185, 129, 0.3)' : 'rgba(239, 68, 68, 0.3)'}`
                }}>
                  {lead.website ? "Website Available" : "No Website"}
                </span>
              </div>
            </div>

            {/* Audit gaps checklist */}
            <div style={cardStyle}>
              <h4 style={cardHeaderStyle}>Audit Gaps Identified</h4>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginTop: '12px' }}>
                {scores.failed_checks?.map((chk) => (
                  <div key={chk} style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '13px', color: 'var(--text-primary)' }}>
                    <span style={{ display: 'inline-block', width: '6px', height: '6px', background: 'var(--error)', borderRadius: '50%' }} />
                    <span>{chk}</span>
                  </div>
                ))}
                {(!scores.failed_checks || scores.failed_checks.length === 0) && (
                  <div style={{ fontSize: '12px', color: 'var(--success)' }}>✓ No presence flaws detected.</div>
                )}
              </div>
            </div>

            {/* Recommended services */}
            <div style={cardStyle}>
              <h4 style={cardHeaderStyle}>Recommended Services</h4>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginTop: '12px' }}>
                {scores.recommended_services?.map((svc) => (
                  <span 
                    key={svc} 
                    style={{ 
                      fontSize: '11px', 
                      background: 'rgba(99, 102, 241, 0.1)', 
                      border: '1px solid rgba(99, 102, 241, 0.25)', 
                      color: '#A5B4FC',
                      padding: '4px 10px',
                      borderRadius: '12px',
                      fontWeight: 600
                    }}
                  >
                    {svc}
                  </span>
                ))}
              </div>
            </div>
            
          </div>
        </div>

      </div>
    </div>
  );
}


// Inline Styles
const modalOverlayStyle = {
  position: 'fixed',
  top: 0,
  left: 0,
  right: 0,
  bottom: 0,
  background: 'rgba(5, 7, 18, 0.75)',
  backdropFilter: 'blur(8px)',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  zIndex: 1000,
  padding: '20px'
};

const modalContentStyle = {
  width: '100%',
  maxWidth: '920px',
  maxHeight: '90vh',
  display: 'flex',
  flexDirection: 'column',
  padding: '24px 30px',
  overflow: 'hidden'
};

const closeBtnStyle = {
  background: 'none',
  border: 'none',
  color: 'var(--text-secondary)',
  cursor: 'pointer',
  padding: '4px',
  borderRadius: '50%',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  transition: 'background 0.2s',
  '&:hover': {
    background: 'rgba(255,255,255,0.05)'
  }
};

const modalBodyStyle = {
  display: 'flex',
  flexWrap: 'wrap',
  gap: '24px',
  overflowY: 'auto',
  paddingRight: '6px'
};

const tabActiveStyle = {
  background: 'none',
  border: 'none',
  borderBottom: '2px solid var(--primary)',
  color: 'var(--text-primary)',
  padding: '6px 12px',
  fontWeight: 600,
  fontSize: '13px',
  cursor: 'pointer'
};

const tabInactiveStyle = {
  background: 'none',
  border: 'none',
  color: 'var(--text-muted)',
  padding: '6px 12px',
  fontSize: '13px',
  cursor: 'pointer'
};

const cardStyle = {
  background: 'rgba(255, 255, 255, 0.015)',
  border: '1px solid var(--border-light)',
  borderRadius: '10px',
  padding: '14px 18px'
};

const cardHeaderStyle = {
  fontSize: '13px',
  fontWeight: 700,
  textTransform: 'uppercase',
  letterSpacing: '0.05em',
  color: 'var(--text-secondary)'
};

const contactRowStyle = {
  display: 'flex',
  alignItems: 'center',
  gap: '8px',
  color: 'var(--text-primary)'
};

const socialBadgeStyle = {
  fontSize: '10px',
  textTransform: 'capitalize',
  background: 'rgba(255, 255, 255, 0.04)',
  border: '1px solid var(--border-light)',
  borderRadius: '4px',
  padding: '2px 6px',
  color: 'var(--text-secondary)',
  textDecoration: 'none',
  display: 'inline-block'
};

const auditStatStyle = {
  background: 'rgba(255, 255, 255, 0.01)',
  border: '1px solid var(--border-light)',
  borderRadius: '8px',
  padding: '10px',
  display: 'flex',
  flexDirection: 'column'
};

const imgContainerStyle = {
  width: '100%',
  border: '1px solid var(--border-light)',
  borderRadius: '6px',
  overflow: 'hidden',
  background: 'var(--bg-space)'
};

const textareaStyle = {
  width: '100%',
  height: '160px',
  flexGrow: 1,
  background: 'var(--bg-input)',
  border: '1px solid var(--border-light)',
  borderRadius: '8px',
  color: 'var(--text-primary)',
  padding: '10px 12px',
  fontSize: '12.5px',
  fontFamily: 'monospace',
  lineHeight: '1.5',
  resize: 'none',
  outline: 'none',
  marginTop: '8px'
};
