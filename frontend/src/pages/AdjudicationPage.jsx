import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  getAdjudicationView, getPageBoxes, createBox, submitPage,
  normalizeBox, IMAGE_BASE_URL,
} from '../api/client.js';
import { useAuth } from '../context/AuthContext.jsx';

const TIER_COLOR = { 1: '#1e88e5', 2: '#43a047' };

export default function AdjudicationPage() {
  const { pageName } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();

  const [data,    setData]    = useState(null);
  const [myBoxes, setMyBoxes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error,   setError]   = useState('');
  const [busy,    setBusy]    = useState(false);

  const isAdjudicator = user?.role === 'annotator';

  useEffect(() => { load(); }, [pageName]);

  async function load() {
    setLoading(true);
    setError('');
    try {
      const view = await getAdjudicationView(pageName);
      setData(view);
      if (isAdjudicator) setMyBoxes(await getPageBoxes(pageName));
    } catch (e) {
      setError(e.response?.data?.detail || 'Failed to load comparison.');
    } finally {
      setLoading(false);
    }
  }

  async function copyTier(tier) {
    const tierData = data.tiers.find(t => t.tier === tier);
    if (!tierData || busy) return;
    if (myBoxes.length > 0 &&
        !window.confirm(`Your draft already has ${myBoxes.length} box(es). Copying will add ${tierData.boxes.length} more on top, not replace them. Continue?`)) {
      return;
    }
    setBusy(true);
    try {
      const idMap = {};
      const roots    = tierData.boxes.filter(b => !b.parent_id);
      const children = tierData.boxes.filter(b => b.parent_id);
      for (const b of [...roots, ...children]) {
        const created = await createBox(pageName, {
          coordinates:    b.coordinates,
          parent_id:      b.parent_id ? (idMap[b.parent_id] ?? null) : null,
          tag_category:   b.tag_category,
          tag_attributes: b.tag_attributes,
          content_text:   b.content_text,
          reading_order:  b.reading_order,
          confidence:     b.confidence,
        });
        idMap[b.id] = created.id;
      }
      setMyBoxes(await getPageBoxes(pageName));
    } catch (e) {
      alert(e.response?.data?.detail || 'Failed to copy boxes.');
    } finally {
      setBusy(false);
    }
  }

  async function handleSubmit() {
    if (busy) return;
    setBusy(true);
    try {
      await submitPage(pageName);
      navigate('/annotator');
    } catch (e) {
      alert(e.response?.data?.detail || 'Failed to submit.');
    } finally {
      setBusy(false);
    }
  }

  if (loading) return <Centered>Loading…</Centered>;
  if (error)   return <Centered>{error}</Centered>;
  if (!data)   return null;

  if (data.area !== 'needs_adjudication') {
    return (
      <Centered>
        This page is no longer awaiting adjudication (status: {data.area}).
        <div style={{ marginTop: '12px' }}>
          <button onClick={() => navigate('/annotator')} style={S.outlineBtn}>← Back to My Work</button>
        </div>
      </Centered>
    );
  }

  const imageUrl = `${IMAGE_BASE_URL}/${data.image_path}`;

  return (
    <div style={{ minHeight: '100vh', backgroundColor: '#f5f6f8' }}>
      <div style={{ padding: '28px', maxWidth: '1100px', margin: '0 auto' }}>

        <div style={{ display: 'flex', alignItems: 'center', marginBottom: '20px', paddingBottom: '16px', borderBottom: '1px solid #e4e4e4' }}>
          <button onClick={() => navigate(-1)} style={S.outlineBtn}>← Back</button>
          <div style={{ fontSize: '18px', fontWeight: 700, color: '#1a1a1a', margin: '0 0 0 14px', flex: 1 }}>
            Adjudicate: {data.page_name}
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: data.tiers.length > 1 ? '1fr 1fr' : '1fr', gap: '16px', marginBottom: '16px' }}>
          {data.tiers.map(t => (
            <TierColumn key={t.tier} tier={t} imageUrl={imageUrl}
              onCopy={isAdjudicator ? () => copyTier(t.tier) : null} busy={busy} />
          ))}
        </div>

        {isAdjudicator && (
          <div style={S.card}>
            <div style={S.cardTitle}>Your draft (tier-3)</div>
            <p style={S.muted}>
              {myBoxes.length === 0
                ? 'No boxes yet — copy one side above, or build your own from scratch.'
                : `${myBoxes.length} box${myBoxes.length !== 1 ? 'es' : ''} ready.`}
            </p>
            <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
              <button onClick={() => navigate(`/annotate/${encodeURIComponent(pageName)}`)} style={S.annotateBtn}>
                Edit my draft
              </button>
              <button
                onClick={handleSubmit}
                disabled={busy || myBoxes.length === 0}
                style={{ ...S.submitBtn, opacity: myBoxes.length === 0 ? 0.5 : 1 }}
              >
                {busy ? '…' : 'Submit as final'}
              </button>
            </div>
          </div>
        )}

      </div>
    </div>
  );
}

function TierColumn({ tier, imageUrl, onCopy, busy }) {
  const sortedBoxes = [...tier.boxes].sort((a, b) => (a.reading_order ?? 0) - (b.reading_order ?? 0));
  const color = TIER_COLOR[tier.tier] || '#888';

  return (
    <div style={S.card}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
        <div>
          <span style={{ ...S.tierBadge, backgroundColor: `${color}1a`, color }}>Tier {tier.tier}</span>
          <span style={{ fontSize: '13px', fontWeight: 600, color: '#333', marginLeft: '8px' }}>{tier.annotator}</span>
        </div>
        {onCopy && (
          <button onClick={onCopy} disabled={busy} style={{ ...S.copyBtn, border: `1px solid ${color}`, color }}>
            Copy into my draft →
          </button>
        )}
      </div>

      <div style={{ position: 'relative', width: '100%', border: '1px solid #e0e0e0', borderRadius: '6px', overflow: 'hidden' }}>
        <img src={imageUrl} alt={tier.annotator} style={{ width: '100%', display: 'block' }} />
        {sortedBoxes.map(b => <BoxOverlay key={b.id} box={b} color={color} />)}
      </div>

      <div style={{ marginTop: '10px', maxHeight: '260px', overflowY: 'auto', border: '1px solid #eee', borderRadius: '6px' }}>
        {sortedBoxes.length === 0 ? (
          <p style={{ ...S.muted, padding: '10px' }}>No boxes.</p>
        ) : sortedBoxes.map((b, i) => (
          <div key={b.id} style={{ padding: '7px 10px', borderBottom: i < sortedBoxes.length - 1 ? '1px solid #f5f5f5' : 'none' }}>
            <span style={{ fontSize: '10px', fontWeight: 600, color, marginRight: '6px' }}>
              {b.tag_category || 'untagged'}
            </span>
            <span style={{ fontSize: '12px', color: '#444' }}>{b.content_text || '—'}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function BoxOverlay({ box, color }) {
  const nb = normalizeBox(box);
  let left, top, width, height;

  if (nb.polygon_points) {
    let pts;
    try { pts = JSON.parse(nb.polygon_points); } catch { pts = []; }
    if (!pts.length) return null;
    const xs = pts.map(p => p[0]), ys = pts.map(p => p[1]);
    left = Math.min(...xs); top = Math.min(...ys);
    width = Math.max(...xs) - left; height = Math.max(...ys) - top;
  } else {
    ({ x: left, y: top, width, height } = nb);
  }

  return (
    <div style={{
      position: 'absolute',
      left: `${left * 100}%`, top: `${top * 100}%`,
      width: `${width * 100}%`, height: `${height * 100}%`,
      border: `2px solid ${color}`, backgroundColor: `${color}22`,
      boxSizing: 'border-box', pointerEvents: 'none',
      transform: nb.rotation ? `rotate(${nb.rotation}deg)` : undefined,
      transformOrigin: 'center center',
    }} />
  );
}

function Centered({ children }) {
  return (
    <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', backgroundColor: '#f5f6f8' }}>
      <div style={{ color: '#666', fontSize: '14px', textAlign: 'center' }}>{children}</div>
    </div>
  );
}

const S = {
  outlineBtn: {
    background: 'none', border: '1px solid #ddd', borderRadius: '6px',
    padding: '5px 12px', cursor: 'pointer', fontSize: '13px', color: '#555',
  },
  card: {
    backgroundColor: '#fff', borderRadius: '10px', padding: '16px 18px',
    border: '1px solid #e8e8e8',
  },
  cardTitle: { fontSize: '14px', fontWeight: 600, color: '#333', margin: '0 0 8px' },
  muted: { color: '#bbb', fontSize: '13px', margin: '0 0 10px' },
  tierBadge: {
    fontSize: '11px', fontWeight: 700, padding: '3px 9px', borderRadius: '10px',
  },
  copyBtn: {
    padding: '5px 12px', backgroundColor: '#fff',
    borderRadius: '5px', cursor: 'pointer', fontSize: '12px', fontWeight: 600,
  },
  annotateBtn: {
    padding: '7px 16px', backgroundColor: '#3f51b5', color: '#fff',
    border: 'none', borderRadius: '6px', cursor: 'pointer', fontSize: '13px', fontWeight: 600,
  },
  submitBtn: {
    padding: '7px 16px', backgroundColor: '#2e7d32', color: '#fff',
    border: 'none', borderRadius: '6px', cursor: 'pointer', fontSize: '13px', fontWeight: 600,
  },
};
