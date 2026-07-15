import { useState } from 'react';
import useProducts from '../hooks/useProducts';
import ProductCard from '../components/ProductCard';
import FilterSidebar from '../components/FilterSidebar';
import SearchBar from '../components/SearchBar';

export default function Home() {
  const [filters, setFilters] = useState({ sort: 'newest' });

  const { products, loading, error } = useProducts(filters);

  const handleSearch = (q) => setFilters((f) => ({ ...f, q }));

  return (
    <div style={styles.page}>
      <header style={styles.header}>
        <h1 style={styles.logo}>AshFash</h1>
        <SearchBar value={filters.q || ''} onSearch={handleSearch} />
      </header>

      <div style={styles.body}>
        <FilterSidebar filters={filters} onChange={setFilters} />

        <main style={styles.main}>
          <div style={styles.resultsBar}>
            <p style={styles.count}>
              {loading ? 'Loading...' : `${products.length} product${products.length !== 1 ? 's' : ''}`}
              {filters.q && ` for "${filters.q}"`}
            </p>
          </div>

          {error && <p style={styles.error}>{error}</p>}

          {!loading && products.length === 0 && !error && (
            <p style={styles.empty}>No products found. Try different filters.</p>
          )}

          <div style={styles.grid}>
            {products.map((p) => (
              <ProductCard key={p.id} product={p} />
            ))}
          </div>

        </main>
      </div>
    </div>
  );
}

const styles = {
  page: { minHeight: '100vh', background: '#f8f8f8', fontFamily: 'sans-serif' },
  header: {
    display: 'flex',
    alignItems: 'center',
    gap: 32,
    padding: '16px 40px',
    background: '#fff',
    borderBottom: '1px solid #eee',
    position: 'sticky',
    top: 0,
    zIndex: 10,
  },
  logo: { fontSize: 24, fontWeight: 800, margin: 0, letterSpacing: -1 },
  body: { display: 'flex', padding: '32px 40px', gap: 32, maxWidth: 1400, margin: '0 auto' },
  main: { flex: 1, minWidth: 0 },
  resultsBar: { marginBottom: 16 },
  count: { fontSize: 14, color: '#666', margin: 0 },
  grid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))',
    gap: 20,
  },
  error: { color: '#e53935', fontSize: 14 },
  empty: { color: '#888', fontSize: 14, textAlign: 'center', marginTop: 60 },
};
