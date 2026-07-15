export default function ProductCard({ product }) {
  return (
    <div style={styles.card}>
      <div style={styles.imageWrapper}>
        <img
          src={product.primary_image_url}
          alt={product.name}
          style={styles.image}
          onError={(e) => { e.target.src = 'https://via.placeholder.com/300x400?text=No+Image'; }}
        />
      </div>
      <div style={styles.info}>
        <p style={styles.gender}>{product.gender}</p>
        <h3 style={styles.name}>{product.name}</h3>
        <div style={styles.priceRow}>
          {product.sale_price_amount ? (
            <>
              <span style={styles.salePrice}>${product.sale_price_amount}</span>
              <span style={styles.originalPrice}>${product.price_amount}</span>
            </>
          ) : (
            <span style={styles.price}>${product.price_amount}</span>
          )}
        </div>
      </div>
    </div>
  );
}

const styles = {
  card: {
    background: '#fff',
    borderRadius: 8,
    overflow: 'hidden',
    boxShadow: '0 1px 4px rgba(0,0,0,0.08)',
    transition: 'transform 0.2s',
    cursor: 'pointer',
  },
  imageWrapper: {
    width: '100%',
    aspectRatio: '3/4',
    overflow: 'hidden',
    background: '#f5f5f5',
  },
  image: {
    width: '100%',
    height: '100%',
    objectFit: 'cover',
  },
  info: {
    padding: '12px',
  },
  gender: {
    fontSize: 11,
    textTransform: 'uppercase',
    color: '#999',
    margin: '0 0 4px',
    letterSpacing: 1,
  },
  name: {
    fontSize: 14,
    fontWeight: 500,
    margin: '0 0 8px',
    color: '#222',
    lineHeight: 1.3,
    display: '-webkit-box',
    WebkitLineClamp: 2,
    WebkitBoxOrient: 'vertical',
    overflow: 'hidden',
  },
  priceRow: { display: 'flex', gap: 8, alignItems: 'center' },
  price: { fontSize: 15, fontWeight: 600, color: '#222' },
  salePrice: { fontSize: 15, fontWeight: 600, color: '#e53935' },
  originalPrice: { fontSize: 13, color: '#999', textDecoration: 'line-through' },
};
