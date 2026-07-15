import { useState, useEffect, useCallback } from 'react';
import { getProducts, searchProducts } from '../api';

export default function useProducts(filters) {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetch = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const { q, ...rest } = filters;
      const res = q ? await searchProducts(q, rest) : await getProducts(rest);
      setProducts(res.data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [JSON.stringify(filters)]);

  useEffect(() => { fetch(); }, [fetch]);

  return { products, loading, error, refetch: fetch };
}
