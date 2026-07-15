const BASE_URL = 'http://localhost:5000/api/v1';

async function apiFetch(path, params = {}) {
  const url = new URL(`${BASE_URL}${path}`);
  Object.entries(params).forEach(([k, v]) => {
    if (v !== '' && v !== null && v !== undefined) url.searchParams.set(k, v);
  });
  const res = await fetch(url.toString());
  const text = await res.text();
  if (!text) throw new Error(`Empty response from ${path} (status ${res.status})`);
  let json;
  try {
    json = JSON.parse(text);
  } catch {
    throw new Error(`Non-JSON response from ${path}: ${text.slice(0, 100)}`);
  }
  if (!json.success) throw new Error(json.error || 'API error');
  return json;
}

export const getProducts = (params) => apiFetch('/products', params);
export const searchProducts = (q, params) => apiFetch('/products/search', { q, ...params });
export const getProduct = (id) => apiFetch(`/products/${id}`);
export const getCategories = () => apiFetch('/categories');
export const getFilters = (params) => apiFetch('/filters', params);
