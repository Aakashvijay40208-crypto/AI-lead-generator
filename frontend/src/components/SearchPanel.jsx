import React, { useState, useEffect } from 'react';
import { Search, Loader2, Play, AlertCircle, RefreshCw } from 'lucide-react';

export default function SearchPanel({ onSearchComplete, onSearchStart, backendUrl }) {
  const [category, setCategory] = useState('Dentists');
  const [city, setCity] = useState('Austin');
  const [area, setArea] = useState('Downtown');
  const [radius, setRadius] = useState(5);
  const [limit, setLimit] = useState(5);
  
  const [loading, setLoading] = useState(false);
  const [searchId, setSearchId] = useState(null);
  const [progress, setProgress] = useState(0);
  const [total, setTotal] = useState(0);
  const [statusMsg, setStatusMsg] = useState('');
  const [error, setError] = useState('');

  // Polling for search progress
  useEffect(() => {
    if (!searchId || !loading) return;

    const interval = setInterval(async () => {
      try {
        const response = await fetch(`${backendUrl}/api/search/status/${searchId}`);
        if (!response.ok) throw new Error("Failed to fetch task status.");
        
        const data = await response.json();
        setProgress(data.progress || 0);
        setTotal(data.total || 0);
        setStatusMsg(data.current_lead || 'Running pipeline...');

        if (data.status === 'completed') {
          setLoading(false);
          setSearchId(null);
          clearInterval(interval);
          if (data.total === 0) {
            setError(data.current_lead || 'No leads found for this query (Quota exceeded or no results).');
          } else {
            onSearchComplete(searchId); // Trigger refresh on parent
          }
        } else if (data.status === 'failed') {
          setLoading(false);
          setSearchId(null);
          setError(data.current_lead || 'Search pipeline failed.');
          clearInterval(interval);
          onSearchComplete(searchId);
        }
      } catch (err) {
        console.error("Polling error:", err);
      }
    }, 1500);

    return () => clearInterval(interval);
  }, [searchId, loading]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!category || !city) {
      setError("Category and City are required.");
      return;
    }
    
    setError('');
    setLoading(true);
    setProgress(0);
    setTotal(0);
    setStatusMsg('Initializing B2B prospecting scan...');
    if (onSearchStart) onSearchStart();

    try {
      const response = await fetch(`${backendUrl}/api/search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ category, city, area, radius, limit })
      });

      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.error || "Failed to trigger search.");
      }

      const data = await response.json();
      setSearchId(data.search_id);
    } catch (err) {
      setError(err.message);
      setLoading(false);
    }
  };

  const percent = total > 0 ? Math.round((progress / total) * 100) : 0;

  return (
    <div className="glass-panel" style={{ padding: '24px' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '20px' }}>
        <Search size={18} style={{ color: 'var(--primary)' }} />
        <h2 style={{ fontSize: '18px', fontWeight: 700, fontFamily: 'var(--font-display)' }}>
          Discover B2B Leads
        </h2>
      </div>

      {!loading ? (
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '16px' }}>
            <div>
              <label className="form-label">Business Category</label>
              <input 
                type="text" 
                className="form-input" 
                placeholder="e.g. Dentists, Restaurants" 
                value={category} 
                onChange={(e) => setCategory(e.target.value)} 
              />
            </div>
            <div>
              <label className="form-label">City</label>
              <input 
                type="text" 
                className="form-input" 
                placeholder="e.g. Austin" 
                value={city} 
                onChange={(e) => setCity(e.target.value)} 
              />
            </div>
            <div>
              <label className="form-label">Area (Optional)</label>
              <input 
                type="text" 
                className="form-input" 
                placeholder="e.g. Downtown" 
                value={area} 
                onChange={(e) => setArea(e.target.value)} 
              />
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
              <div>
                <label className="form-label">Radius (mi)</label>
                <select 
                  className="form-input" 
                  value={radius} 
                  onChange={(e) => setRadius(Number(e.target.value))}
                >
                  <option value={1}>1 mi</option>
                  <option value={5}>5 mi</option>
                  <option value={10}>10 mi</option>
                  <option value={20}>20 mi</option>
                </select>
              </div>
              <div>
                <label className="form-label">Max Results</label>
                <select 
                  className="form-input" 
                  value={limit} 
                  onChange={(e) => setLimit(Number(e.target.value))}
                >
                  <option value={3}>3</option>
                  <option value={5}>5</option>
                  <option value={10}>10</option>
                  <option value={20}>20</option>
                </select>
              </div>
            </div>
          </div>

          {error && (
            <div style={{ 
              display: 'flex', 
              alignItems: 'center', 
              gap: '8px', 
              color: 'var(--error)', 
              fontSize: '13px',
              background: 'rgba(239, 68, 68, 0.08)',
              border: '1px solid rgba(239, 68, 68, 0.15)',
              padding: '10px 14px',
              borderRadius: '8px'
            }}>
              <AlertCircle size={16} />
              <span>{error}</span>
            </div>
          )}

          <button 
            type="submit" 
            className="btn-primary btn-search-submit" 
            style={{ alignSelf: 'flex-end', marginTop: '4px' }}
          >
            <Play size={14} fill="currentColor" />
            Launch Prospect Scan
          </button>

        </form>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', padding: '10px 0' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Loader2 size={16} className="pulse-glow" style={{ animation: 'spin 1.5s linear infinite', color: 'var(--primary)' }} />
              <span style={{ fontSize: '14px', fontWeight: 600 }}>Scanning & Auditing leads...</span>
            </div>
            <span style={{ fontSize: '13px', fontWeight: 700, color: 'var(--primary)' }}>{percent}%</span>
          </div>
          
          {/* Progress Bar */}
          <div style={{ 
            width: '100%', 
            height: '8px', 
            background: 'rgba(255, 255, 255, 0.05)', 
            borderRadius: '4px',
            overflow: 'hidden',
            border: '1px solid rgba(255, 255, 255, 0.05)'
          }}>
            <div style={{ 
              width: `${percent}%`, 
              height: '100%', 
              background: 'var(--primary-gradient)', 
              borderRadius: '4px',
              transition: 'width 0.4s ease'
            }} />
          </div>

          <div style={{ 
            fontSize: '12px', 
            color: 'var(--text-secondary)', 
            background: 'rgba(255, 255, 255, 0.02)',
            padding: '10px 14px',
            borderRadius: '8px',
            border: '1px solid var(--border-light)',
            fontFamily: 'monospace'
          }}>
            {statusMsg}
          </div>
        </div>
      )}
    </div>
  );
}
