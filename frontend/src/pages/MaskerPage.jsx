import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { getMaskerPages, maskPage, IMAGE_BASE_URL } from '../api/client.js';
import { useAuth } from '../context/AuthContext.jsx';

const MEDIUM_LABEL  = { english_medium: 'English Medium', kannada_medium: 'Kannada Medium' };
const CLASS_LABEL   = { class_8: 'Class 8', class_9: 'Class 9', class_10: 'Class 10' };
const SUBJECT_LABEL = { english: 'English', kannada: 'Kannada', science: 'Science', social_science: 'Social Science', maths: 'Maths' };

// Draw boxes over student name / roll number. Burned in black by the backend so
// annotators never see identifying information. The raw original stays admin-only.
export default function MaskerPage() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const [queue,   setQueue]   = useState([]);
  const [loading, setLoading] = useState(true);
  const [active,  setActive]  = useState(null);   // page being masked
  const [regions, setRegions] = useState([]);     // committed [{x,y,w,h}] normalised 0..1
  const [draft,   setDraft]   = useState(null);   // in-progress rectangle
  const [saving,  setSaving]  = useState(false);
  const [error,   setError]   = useState('');

  const startRef = useRef(null);
  const boxRef   = useRef(null);

  useEffect(() => { load(); }, []);

  async function load() {
    setLoading(true);
    try {
      const q = await getMaskerPages();
      setQueue(q);
      setActive((prev) => (prev && q.some((p) => p.page_name === prev.page_name)) ? prev : (q[0] || null));
    } catch {
      setError('Failed to load the masking queue.');
    } finally {
      setLoading(false);
    }
  }

  function selectPage(p) {
    setActive(p);
    setRegions([]);
    setDraft(null);
    setError('');
  }

  function relPoint(e) {
    const rect = boxRef.current.getBoundingClientRect();
    const x = (e.clientX - rect.left) / rect.width;
    const y = (e.clientY - rect.top) / rect.height;
    return { x: Math.max(0, Math.min(1, x)), y: Math.max(0, Math.min(1, y)) };
  }

  function onDown(e) {
    if (!active) return;
    e.preventDefault();
    startRef.current = relPoint(e);
    setDraft({ ...startRef.current, w: 0, h: 0 });
  }

  function onMove(e) {
    if (!startRef.current) return;
    const cur = relPoint(e);
    const s = startRef.current;
    setDraft({
      x: Math.min(s.x, cur.x), y: Math.min(s.y, cur.y),
      w: Math.abs(cur.x - s.x), h: Math.abs(cur.y - s.y),
    });
  }

  function onUp() {
    if (draft && draft.w > 0.005 && draft.h > 0.005) {
      setRegions((prev) => [...prev, draft]);
    }
    setDraft(null);
    startRef.current = null;
  }

  function removeRegion(i) {
    setRegions((prev) => prev.filter((_, idx) => idx !== i));
  }

  async function submit(noPii) {
    if (!active) return;
    setSaving(true);
    setError('');
    try {
      await maskPage(active.page_name, noPii ? [] : regions);
      const rest = queue.filter((p) => p.page_name !== active.page_name);
      setQueue(rest);
      setActive(rest[0] || null);
      setRegions([]);
      setDraft(null);
    } catch (e) {
      setError(e.response?.data?.detail || 'Failed to save.');
    } finally {
      setSaving(false);
    }
  }

  const tags = active
    ? [MEDIUM_LABEL[active.medium], CLASS_LABEL[active.cls], SUBJECT_LABEL[active.subject]].filter(Boolean)
    : [];

  return (
    <div style={{ minHeight: '100vh', backgroundColor: '#f5f6f8' }}>
      {/* Header */}
      <div style={S.header}>
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: '18px', fontWeight: 700, color: '#1a1a1a' }}>Mask identifiers</div>
          <div style={{ fontSize: '12px', color: '#aaa', marginTop: '2px' }}>
            {user?.username} · {queue.length} page{queue.length !== 1 ? 's' : ''} awaiting masking
          </div>
        </div>
        <button onClick={() => { logout(); navigate('/login'); }} style={S.outlineBtn}>Sign out</button>
      </div>

      <div style={S.body}>
        {/* Queue */}
        <div style={S.queue}>
          <div style={S.queueTitle}>Queue</div>
          {loading ? (
            <p style={S.muted}>Loading…</p>
          ) : queue.length === 0 ? (
            <p style={S.muted}>All caught up — nothing to mask.</p>
          ) : (
            queue.map((p) => (
              <button
                key={p.page_name}
                onClick={() => selectPage(p)}
                style={{ ...S.queueItem, ...(active?.page_name === p.page_name ? S.queueItemOn : {}) }}
                title={p.page_name}
              >
                {p.page_name}
              </button>
            ))
          )}
        </div>

        {/* Workspace */}
        <div style={S.work}>
          {!active ? (
            <div style={S.empty}>
              {loading ? 'Loading…' : 'No page selected. The queue is empty.'}
            </div>
          ) : (
            <>
              <div style={S.workHead}>
                <div>
                  <div style={{ fontWeight: 600, fontSize: '14px' }}>{active.page_name}</div>
                  <div style={{ display: 'flex', gap: '4px', marginTop: '4px' }}>
                    {tags.map((t) => <span key={t} style={S.tag}>{t}</span>)}
                  </div>
                </div>
                <div style={{ fontSize: '12px', color: '#888' }}>
                  {regions.length} box{regions.length !== 1 ? 'es' : ''} drawn
                </div>
              </div>

              <p style={S.hint}>
                Drag boxes over the student's <b>name</b> and <b>roll number</b>. They are burned out in black
                before any annotator sees the page. If there is no identifying information, click
                “No identifiers”.
              </p>

              {/* Canvas */}
              <div
                ref={boxRef}
                style={S.canvas}
                onMouseDown={onDown}
                onMouseMove={onMove}
                onMouseUp={onUp}
                onMouseLeave={onUp}
              >
                <img
                  src={`${IMAGE_BASE_URL}/${active.image_path}`}
                  alt={active.page_name}
                  draggable={false}
                  style={S.img}
                />
                {regions.map((r, i) => (
                  <div key={i} style={{ ...S.region, left: `${r.x * 100}%`, top: `${r.y * 100}%`, width: `${r.w * 100}%`, height: `${r.h * 100}%` }}>
                    <button onClick={(e) => { e.stopPropagation(); removeRegion(i); }} style={S.regionDel}>×</button>
                  </div>
                ))}
                {draft && (
                  <div style={{ ...S.draft, left: `${draft.x * 100}%`, top: `${draft.y * 100}%`, width: `${draft.w * 100}%`, height: `${draft.h * 100}%` }} />
                )}
              </div>

              {error && <p style={{ color: '#c62828', fontSize: '13px', marginTop: '10px' }}>{error}</p>}

              <div style={S.actions}>
                <button onClick={() => setRegions([])} disabled={saving || regions.length === 0} style={S.clearBtn}>
                  Clear boxes
                </button>
                <div style={{ flex: 1 }} />
                <button onClick={() => submit(true)} disabled={saving} style={S.noPiiBtn}>
                  No identifiers
                </button>
                <button onClick={() => submit(false)} disabled={saving || regions.length === 0} style={S.maskBtn}>
                  {saving ? 'Saving…' : 'Mask & mark done'}
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

const S = {
  header: {
    display: 'flex', alignItems: 'center', padding: '18px 28px',
    backgroundColor: '#fff', borderBottom: '1px solid #e4e4e4',
  },
  outlineBtn: {
    background: 'none', border: '1px solid #ddd', borderRadius: '6px',
    padding: '5px 12px', cursor: 'pointer', fontSize: '13px', color: '#555',
  },
  body: { display: 'flex', gap: '16px', padding: '20px 28px', maxWidth: '1200px', margin: '0 auto', alignItems: 'flex-start' },
  queue: {
    width: '240px', flexShrink: 0, backgroundColor: '#fff', border: '1px solid #e8e8e8',
    borderRadius: '10px', padding: '14px', maxHeight: '80vh', overflowY: 'auto',
  },
  queueTitle: { fontSize: '13px', fontWeight: 600, color: '#333', marginBottom: '10px' },
  queueItem: {
    display: 'block', width: '100%', textAlign: 'left', padding: '7px 9px', marginBottom: '4px',
    fontSize: '12px', border: '1px solid #eee', borderRadius: '6px', cursor: 'pointer',
    backgroundColor: '#fafafa', color: '#444', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
  },
  queueItemOn: { backgroundColor: '#e8eaf6', borderColor: '#7986cb', color: '#283593', fontWeight: 600 },
  work: { flex: 1, backgroundColor: '#fff', border: '1px solid #e8e8e8', borderRadius: '10px', padding: '20px' },
  workHead: { display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: '8px' },
  empty: { color: '#bbb', fontSize: '14px', textAlign: 'center', padding: '60px 0' },
  hint: { fontSize: '12px', color: '#777', backgroundColor: '#f7f7fb', borderRadius: '6px', padding: '8px 10px', margin: '0 0 14px' },
  canvas: {
    position: 'relative', display: 'inline-block', lineHeight: 0,
    border: '1px solid #ddd', borderRadius: '4px', cursor: 'crosshair', userSelect: 'none',
    maxWidth: '100%',
  },
  img: { display: 'block', maxWidth: '100%', maxHeight: '70vh', width: 'auto', height: 'auto' },
  region: { position: 'absolute', backgroundColor: 'rgba(0,0,0,0.78)', border: '1px solid #000' },
  regionDel: {
    position: 'absolute', top: '-10px', right: '-10px', width: '20px', height: '20px',
    borderRadius: '50%', border: 'none', backgroundColor: '#e53935', color: '#fff',
    fontSize: '13px', lineHeight: '20px', cursor: 'pointer', padding: 0,
  },
  draft: { position: 'absolute', backgroundColor: 'rgba(0,0,0,0.30)', border: '1px dashed #000' },
  actions: { display: 'flex', alignItems: 'center', gap: '10px', marginTop: '16px' },
  clearBtn: {
    padding: '8px 14px', fontSize: '13px', border: '1px solid #ddd', borderRadius: '6px',
    background: '#fff', color: '#666', cursor: 'pointer',
  },
  noPiiBtn: {
    padding: '8px 16px', fontSize: '13px', border: '1px solid #bbb', borderRadius: '6px',
    background: '#fff', color: '#444', cursor: 'pointer', fontWeight: 600,
  },
  maskBtn: {
    padding: '8px 18px', fontSize: '13px', border: 'none', borderRadius: '6px',
    background: '#3f51b5', color: '#fff', cursor: 'pointer', fontWeight: 600,
  },
  muted: { color: '#bbb', fontSize: '13px', margin: 0 },
  tag: { fontSize: '11px', backgroundColor: '#f0f0f0', color: '#555', padding: '2px 7px', borderRadius: '8px' },
};
