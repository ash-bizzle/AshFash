import { useState, useRef, useEffect } from 'react';
import { askStylist } from '../api';

export default function StylistWidget() {
  const [open, setOpen] = useState(false);
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const scrollRef = useRef(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, loading]);

  const submit = async (e) => {
    e.preventDefault();
    const text = input.trim();
    if (!text || loading) return;

    setMessages((m) => [...m, { role: 'user', text }]);
    setInput('');
    setLoading(true);

    try {
      const res = await askStylist(text);
      setMessages((m) => [...m, {
        role: 'assistant',
        text: res.data.answer,
        products: res.data.products || [],
      }]);
    } catch (err) {
      setMessages((m) => [...m, { role: 'error', text: err.message }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={styles.root}>
      {open && (
        <div style={styles.panel}>
          <div style={styles.header}>
            <span style={styles.headerTitle}>AshFash Stylist</span>
            <button style={styles.closeBtn} onClick={() => setOpen(false)} aria-label="Close">✕</button>
          </div>

          <div style={styles.messages} ref={scrollRef}>
            {messages.length === 0 && (
              <p style={styles.greeting}>
                Hi! Tell me what you&rsquo;re shopping for - an occasion, a budget, a
                colour - and I&rsquo;ll pull some picks from the catalog.
              </p>
            )}

            {messages.map((m, i) => (
              <div key={i} style={bubbleWrapStyle(m.role)}>
                <div style={bubbleStyle(m.role)}>{m.text}</div>
                {m.products && m.products.length > 0 && (
                  <div style={styles.productRow}>
                    {m.products.map((p) => (
                      <a
                        key={p.external_id}
                        href={p.external_url || '#'}
                        target="_blank"
                        rel="noreferrer"
                        style={styles.productChip}
                      >
                        <img
                          src={p.primary_image_url}
                          alt={p.name}
                          style={styles.productImg}
                          onError={(e) => { e.target.src = 'https://via.placeholder.com/80x100?text=%20'; }}
                        />
                        <div style={styles.productInfo}>
                          <span style={styles.productName}>{p.name}</span>
                          <span style={styles.productPrice}>
                            {p.sale_price_amount
                              ? `$${p.sale_price_amount}`
                              : (p.price_amount != null ? `$${p.price_amount}` : '')}
                          </span>
                        </div>
                      </a>
                    ))}
                  </div>
                )}
              </div>
            ))}

            {loading && (
              <div style={bubbleWrapStyle('assistant')}>
                <div style={bubbleStyle('assistant')}>Thinking...</div>
              </div>
            )}
          </div>

          <form onSubmit={submit} style={styles.form}>
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="e.g. something warm for a fall wedding"
              style={styles.input}
              disabled={loading}
              maxLength={1000}
            />
            <button type="submit" style={styles.sendBtn} disabled={loading || !input.trim()}>
              Send
            </button>
          </form>
        </div>
      )}

      <button style={styles.toggleBtn} onClick={() => setOpen((o) => !o)}>
        {open ? '✕' : '💬 Ask our stylist'}
      </button>
    </div>
  );
}

function bubbleWrapStyle(role) {
  return {
    display: 'flex',
    flexDirection: 'column',
    alignItems: role === 'user' ? 'flex-end' : 'flex-start',
    marginBottom: 12,
  };
}

function bubbleStyle(role) {
  const base = {
    maxWidth: '85%',
    padding: '10px 14px',
    borderRadius: 14,
    fontSize: 14,
    lineHeight: 1.4,
    whiteSpace: 'pre-wrap',
  };
  if (role === 'user') {
    return { ...base, background: '#222', color: '#fff', borderBottomRightRadius: 4 };
  }
  if (role === 'error') {
    return { ...base, background: '#fdecea', color: '#c62828', borderBottomLeftRadius: 4 };
  }
  return { ...base, background: '#f1f1f1', color: '#222', borderBottomLeftRadius: 4 };
}

const styles = {
  root: {
    position: 'fixed',
    bottom: 20,
    right: 20,
    zIndex: 1000,
    fontFamily: 'sans-serif',
  },
  toggleBtn: {
    marginTop: 12,
    float: 'right',
    padding: '12px 18px',
    background: '#222',
    color: '#fff',
    border: 'none',
    borderRadius: 24,
    fontSize: 14,
    fontWeight: 600,
    cursor: 'pointer',
    boxShadow: '0 4px 12px rgba(0,0,0,0.2)',
  },
  panel: {
    width: 360,
    height: 480,
    background: '#fff',
    borderRadius: 12,
    boxShadow: '0 8px 30px rgba(0,0,0,0.2)',
    display: 'flex',
    flexDirection: 'column',
    overflow: 'hidden',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '14px 16px',
    borderBottom: '1px solid #eee',
    background: '#fafafa',
  },
  headerTitle: { fontSize: 15, fontWeight: 700 },
  closeBtn: {
    background: 'none',
    border: 'none',
    fontSize: 16,
    cursor: 'pointer',
    color: '#888',
  },
  messages: {
    flex: 1,
    overflowY: 'auto',
    padding: '16px',
  },
  greeting: {
    fontSize: 14,
    color: '#666',
    lineHeight: 1.5,
  },
  productRow: {
    display: 'flex',
    gap: 8,
    overflowX: 'auto',
    maxWidth: '100%',
    paddingBottom: 4,
  },
  productChip: {
    display: 'flex',
    flexDirection: 'column',
    width: 90,
    flexShrink: 0,
    textDecoration: 'none',
    color: '#222',
    border: '1px solid #eee',
    borderRadius: 8,
    overflow: 'hidden',
    background: '#fff',
  },
  productImg: {
    width: '100%',
    height: 100,
    objectFit: 'cover',
    background: '#f5f5f5',
  },
  productInfo: { padding: '6px 6px' },
  productName: {
    display: '-webkit-box',
    fontSize: 11,
    lineHeight: 1.3,
    overflow: 'hidden',
    textOverflow: 'ellipsis',
    WebkitLineClamp: 2,
    WebkitBoxOrient: 'vertical',
  },
  productPrice: { display: 'block', fontSize: 11, fontWeight: 700, marginTop: 2 },
  form: {
    display: 'flex',
    gap: 8,
    padding: 12,
    borderTop: '1px solid #eee',
  },
  input: {
    flex: 1,
    padding: '10px 12px',
    fontSize: 13,
    border: '1px solid #ddd',
    borderRadius: 6,
    outline: 'none',
  },
  sendBtn: {
    padding: '10px 16px',
    background: '#222',
    color: '#fff',
    border: 'none',
    borderRadius: 6,
    fontSize: 13,
    cursor: 'pointer',
  },
};
