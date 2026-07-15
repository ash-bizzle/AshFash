import { useState, useEffect } from 'react';
import { getFilters } from '../api';

export default function FilterSidebar({ filters, onChange }) {
  const [available, setAvailable] = useState({ genders: [], price_range: {}, brands: [] });

  useEffect(() => {
    getFilters().then((res) => setAvailable(res.data)).catch(() => {});
  }, []);

  const set = (key, value) => onChange({ ...filters, [key]: value, page: 1 });
  const clear = () => onChange({ page: 1, sort: 'newest' });

  return (
    <aside style={styles.sidebar}>
      <div style={styles.header}>
        <h2 style={styles.title}>Filters</h2>
        <button style={styles.clearBtn} onClick={clear}>Clear all</button>
      </div>

      <Section label="Gender">
        {['women', 'men', 'unisex', 'kids'].map((g) => (
          <label key={g} style={styles.option}>
            <input
              type="radio"
              name="gender"
              checked={filters.gender === g}
              onChange={() => set('gender', g)}
            />
            {g.charAt(0).toUpperCase() + g.slice(1)}
          </label>
        ))}
      </Section>

      <Section label="Sort by">
        {[['newest', 'Newest'], ['price_asc', 'Price: Low to High'], ['price_desc', 'Price: High to Low']].map(([val, label]) => (
          <label key={val} style={styles.option}>
            <input
              type="radio"
              name="sort"
              checked={(filters.sort || 'newest') === val}
              onChange={() => set('sort', val)}
            />
            {label}
          </label>
        ))}
      </Section>

      <Section label="Price Range">
        <div style={styles.priceRow}>
          <input
            type="number"
            placeholder="Min"
            value={filters.min_price || ''}
            onChange={(e) => set('min_price', e.target.value)}
            style={styles.priceInput}
          />
          <span>—</span>
          <input
            type="number"
            placeholder="Max"
            value={filters.max_price || ''}
            onChange={(e) => set('max_price', e.target.value)}
            style={styles.priceInput}
          />
        </div>
      </Section>
    </aside>
  );
}

function Section({ label, children }) {
  return (
    <div style={{ marginBottom: 24 }}>
      <h3 style={{ fontSize: 13, fontWeight: 600, textTransform: 'uppercase', letterSpacing: 1, marginBottom: 12, color: '#444' }}>
        {label}
      </h3>
      {children}
    </div>
  );
}

const styles = {
  sidebar: {
    width: 220,
    flexShrink: 0,
    padding: '0 24px 0 0',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 24,
  },
  title: { fontSize: 18, fontWeight: 700, margin: 0 },
  clearBtn: {
    background: 'none',
    border: 'none',
    fontSize: 12,
    color: '#888',
    cursor: 'pointer',
    textDecoration: 'underline',
  },
  option: {
    display: 'flex',
    alignItems: 'center',
    gap: 8,
    marginBottom: 8,
    fontSize: 14,
    cursor: 'pointer',
  },
  priceRow: { display: 'flex', alignItems: 'center', gap: 8 },
  priceInput: {
    width: 70,
    padding: '6px 8px',
    border: '1px solid #ddd',
    borderRadius: 4,
    fontSize: 13,
  },
};
