import React, { useState } from 'react';
import { Download, ArrowUpDown, ChevronLeft, ChevronRight, Eye, ShieldAlert, Check } from 'lucide-react';

export default function LeadsGrid({ leads, filters, setFilters, sortBy, setSortBy, onSelectLead, backendUrl }) {
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 8;

  // Sorting Handler
  const handleSort = (field) => {
    if (sortBy === field) {
      setSortBy(`-${field}`); // toggle reverse
    } else {
      setSortBy(field);
    }
    setCurrentPage(1);
  };

  // Filter Handlers
  const handleFilterChange = (key, value) => {
    setFilters(prev => ({ ...prev, [key]: value }));
    setCurrentPage(1);
  };

  // Pagination Math
  const totalItems = leads.length;
  const totalPages = Math.ceil(totalItems / itemsPerPage) || 1;
  const startIndex = (currentPage - 1) * itemsPerPage;
  const paginatedLeads = leads.slice(startIndex, startIndex + itemsPerPage);

  const handleExport = () => {
    // Construct query parameters
    const params = new URLSearchParams();
    Object.entries(filters).forEach(([k, v]) => {
      if (v) params.append(k, v);
    });
    if (sortBy) params.append('sort_by', sortBy);

    // Redirect to download file
    window.open(`${backendUrl}/api/export?${params.toString()}`);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      
      {/* Filtering Toolbar */}
      <div className="glass-panel" style={{ padding: '16px 20px' }}>
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))',
          gap: '12px',
          alignItems: 'end'
        }}>
          <div>
            <label className="form-label">Filter by City</label>
            <input 
              type="text" 
              className="form-input" 
              placeholder="e.g. Austin"
              value={filters.city || ''}
              onChange={(e) => handleFilterChange('city', e.target.value)}
              style={{ padding: '8px 12px' }}
            />
          </div>
          <div>
            <label className="form-label">Website</label>
            <select 
              className="form-input"
              value={filters.website || ''}
              onChange={(e) => handleFilterChange('website', e.target.value)}
              style={{ padding: '8px 12px' }}
            >
              <option value="">All</option>
              <option value="yes">Has Website</option>
              <option value="no">No Website</option>
            </select>
          </div>
          <div>
            <label className="form-label">Priority</label>
            <select 
              className="form-input"
              value={filters.leadScore || ''}
              onChange={(e) => handleFilterChange('leadScore', e.target.value)}
              style={{ padding: '8px 12px' }}
            >
              <option value="">All</option>
              <option value="HOT">Hot Leads</option>
              <option value="MEDIUM">Medium Leads</option>
              <option value="LOW">Low Leads</option>
            </select>
          </div>
          <div>
            <label className="form-label">Min Google Rating</label>
            <select 
              className="form-input"
              value={filters.rating || ''}
              onChange={(e) => handleFilterChange('rating', e.target.value)}
              style={{ padding: '8px 12px' }}
            >
              <option value="">All</option>
              <option value="4.5">4.5★ & Up</option>
              <option value="4.0">4.0★ & Up</option>
              <option value="3.5">3.5★ & Up</option>
              <option value="3.0">3.0★ & Up</option>
            </select>
          </div>
          
          <button 
            onClick={handleExport}
            className="btn-secondary" 
            style={{ 
              padding: '10px 16px', 
              fontSize: '13px', 
              justifyContent: 'center', 
              fontFamily: 'var(--font-display)',
              borderColor: 'rgba(99, 102, 241, 0.25)' 
            }}
          >
            <Download size={14} />
            Export styled Excel
          </button>
        </div>
      </div>

      {/* Grid Panel */}
      <div className="glass-panel" style={{ overflow: 'hidden', padding: 0 }}>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
            <thead>
              <tr style={{ 
                borderBottom: '1px solid var(--border-light)',
                background: 'rgba(255, 255, 255, 0.01)'
              }}>
                <th 
                  onClick={() => handleSort('name')}
                  style={{ padding: '16px 20px', fontSize: '12px', color: 'var(--text-secondary)', cursor: 'pointer', userSelect: 'none' }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    Business Name <ArrowUpDown size={12} />
                  </div>
                </th>
                <th style={{ padding: '16px 20px', fontSize: '12px', color: 'var(--text-secondary)' }}>Address</th>
                <th 
                  onClick={() => handleSort('rating')}
                  style={{ padding: '16px 20px', fontSize: '12px', color: 'var(--text-secondary)', cursor: 'pointer', userSelect: 'none' }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    Google Review <ArrowUpDown size={12} />
                  </div>
                </th>
                <th style={{ padding: '16px 20px', fontSize: '12px', color: 'var(--text-secondary)' }}>Website</th>
                <th 
                  onClick={() => handleSort('score')}
                  style={{ padding: '16px 20px', fontSize: '12px', color: 'var(--text-secondary)', cursor: 'pointer', userSelect: 'none' }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    Score <ArrowUpDown size={12} />
                  </div>
                </th>
                <th style={{ padding: '16px 20px', fontSize: '12px', color: 'var(--text-secondary)' }}>Priority</th>
                <th style={{ padding: '16px 20px', fontSize: '12px', color: 'var(--text-secondary)', textAlign: 'right' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {paginatedLeads.length > 0 ? (
                paginatedLeads.map((lead, i) => {
                  const rating = lead.google_rating || 0;
                  const reviewCount = lead.review_count || 0;
                  const website = lead.website || '';
                  const score = lead.lead_scores?.score ?? 0;
                  const priority = lead.lead_scores?.priority ?? 'LOW';
                  const failed = lead.lead_scores?.failed_checks || [];
                  
                  return (
                    <tr 
                      key={lead.place_id} 
                      style={{ 
                        borderBottom: i === paginatedLeads.length - 1 ? 'none' : '1px solid var(--border-light)',
                        transition: 'background 0.2s ease',
                      }}
                      className="table-row-hover"
                    >
                      <td style={{ padding: '16px 20px' }}>
                        <div style={{ fontWeight: 600, fontSize: '14px' }}>{lead.name}</div>
                        <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '2px' }}>
                          ID: {lead.place_id.substring(0, 15)}...
                        </div>
                      </td>
                      <td style={{ padding: '16px 20px', fontSize: '13px', color: 'var(--text-secondary)', maxWidth: '200px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                        {lead.address}
                      </td>
                      <td style={{ padding: '16px 20px', fontSize: '13px' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                          <span style={{ color: 'var(--warning)', fontWeight: 700 }}>{rating.toFixed(1)}</span>
                          <span style={{ color: 'var(--text-muted)', fontSize: '11px' }}>({reviewCount})</span>
                        </div>
                      </td>
                      <td style={{ padding: '16px 20px', fontSize: '13px' }}>
                        {website ? (
                          <a 
                            href={website} 
                            target="_blank" 
                            rel="noopener noreferrer" 
                            style={{ color: 'var(--accent)', textDecoration: 'none' }}
                          >
                            Link
                          </a>
                        ) : (
                          <span style={{ color: 'var(--text-muted)' }}>None</span>
                        )}
                      </td>
                      <td style={{ padding: '16px 20px', fontWeight: 800, fontSize: '15px' }}>
                        {score}
                      </td>
                      <td style={{ padding: '16px 20px' }}>
                        <span className={`badge-priority ${priority.toLowerCase()}`}>
                          {priority}
                        </span>
                      </td>
                      <td style={{ padding: '16px 20px', textAlign: 'right' }}>
                        <button 
                          onClick={() => onSelectLead(lead.place_id)}
                          className="btn-secondary" 
                          style={{ padding: '6px 12px', fontSize: '12px' }}
                        >
                          <Eye size={12} />
                          Analyze
                        </button>
                      </td>
                    </tr>
                  );
                })
              ) : (
                <tr>
                  <td colSpan={7} style={{ padding: '40px', textAlign: 'center', color: 'var(--text-secondary)' }}>
                    No leads found. Launch a search above to generate new prospects.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination Bar */}
        {totalPages > 1 && (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '16px 20px',
            borderTop: '1px solid var(--border-light)',
            background: 'rgba(255, 255, 255, 0.01)'
          }}>
            <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
              Showing {startIndex + 1}-{Math.min(startIndex + itemsPerPage, totalItems)} of {totalItems} leads
            </span>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <button 
                onClick={() => setCurrentPage(prev => Math.max(prev - 1, 1))}
                disabled={currentPage === 1}
                className="btn-secondary"
                style={{ padding: '6px 10px' }}
              >
                <ChevronLeft size={16} />
              </button>
              <span style={{ fontSize: '13px', fontWeight: 600 }}>{currentPage} of {totalPages}</span>
              <button 
                onClick={() => setCurrentPage(prev => Math.min(prev + 1, totalPages))}
                disabled={currentPage === totalPages}
                className="btn-secondary"
                style={{ padding: '6px 10px' }}
              >
                <ChevronRight size={16} />
              </button>
            </div>
          </div>
        )}
      </div>
      
      {/* Dynamic Styling Hack for Table hover (since vanilla CSS is used without tailwind) */}
      <style dangerouslySetInnerHTML={{__html: `
        .table-row-hover:hover {
          background: rgba(255, 255, 255, 0.03);
        }
      `}} />
    </div>
  );
}
