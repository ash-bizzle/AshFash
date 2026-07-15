# Phia Interview Prep — Backend Feature Questions

## Context
1-hour feature-oriented interview using Python, Flask, and PyMySQL.

**Tables already in the DB:**
- `products (id, external_id, name, brand, price_amount, sale_price_amount, gender, colour, category_id, is_active)`
- `categories (id, external_id, name, slug, parent_id, gender)`
- `product_images (id, product_id, image_url, is_primary, display_order)`
- `product_sizes (id, product_id, size_label, is_available)`

**Existing endpoints:** `GET /products`, `GET /products/search`, `GET /products/<id>`, `GET /categories`, `GET /filters`

**The route pattern — memorise this:**
```python
conn = get_db()
with conn.cursor() as cursor:
    cursor.execute("SELECT * FROM products WHERE id = %s", (product_id,))
    row = cursor.fetchone()  # returns a dict
```

---

## Questions (each ~20-30 min)

---

### 1. On-sale products endpoint
**Prompt:** "Add an endpoint that returns only products currently on sale."

```python
# GET /products/on-sale
cursor.execute(
    "SELECT * FROM products WHERE is_active = 1 AND sale_price_amount IS NOT NULL ORDER BY sale_price_amount ASC"
)
```
Register this route **before** `GET /products/<id>` in the file.

---

### 2. New arrivals endpoint
**Prompt:** "Add an endpoint that returns products added in the last 7 days."

```python
# GET /products/new-arrivals
cursor.execute(
    "SELECT * FROM products WHERE is_active = 1 AND created_at >= NOW() - INTERVAL 7 DAY ORDER BY created_at DESC"
)
```

---

### 3. Random product endpoint
**Prompt:** "Add an endpoint that returns one random product."

```python
# GET /products/random
cursor.execute(
    "SELECT * FROM products WHERE is_active = 1 ORDER BY RAND() LIMIT 1"
)
row = cursor.fetchone()
if not row:
    return error_response('No products found', 404)
return success_response(row)
```

---

### 4. Deactivate a product (Admin)
**Prompt:** "Add an admin endpoint to deactivate a product so it stops appearing in listings."

```python
# PATCH /admin/products/<external_id>
cursor.execute("SELECT id FROM products WHERE external_id = %s", (external_id,))
if not cursor.fetchone():
    return error_response('Not found', 404)

cursor.execute("UPDATE products SET is_active = 0 WHERE external_id = %s", (external_id,))
conn.commit()
return success_response({'deactivated': external_id})
```
Check the `X-Admin-Key` header first — the pattern already exists in `admin.py`.

---

### 5. View count tracking
**Prompt:** "Track how many times each product is viewed."

**Step 1** — add the column:
```sql
ALTER TABLE products ADD COLUMN view_count INT NOT NULL DEFAULT 0;
```

**Step 2** — increment on each detail request (modify `GET /products/<id>`):
```python
cursor.execute(
    "UPDATE products SET view_count = view_count + 1 WHERE external_id = %s",
    (external_id,)
)
conn.commit()
```

**Step 3** — new endpoint:
```python
# GET /products/trending
cursor.execute(
    "SELECT * FROM products WHERE is_active = 1 ORDER BY view_count DESC LIMIT 10"
)
```
Route ordering: `/products/trending` must come before `/products/<id>`.

---

### 6. Product count per category
**Prompt:** "Update the categories endpoint to include how many active products each category has."

```python
# Modify GET /categories — add a COUNT to the query
cursor.execute("""
    SELECT c.*, COUNT(p.id) as product_count
    FROM categories c
    LEFT JOIN products p ON p.category_id = c.id AND p.is_active = 1
    WHERE c.is_active = 1
    GROUP BY c.id
    ORDER BY c.display_order
""")
```

---

### 7. Search a specific field
**Prompt:** "Add an endpoint to search products by brand name."

```python
# GET /products/by-brand?brand=Uniqlo
brand = request.args.get('brand', '').strip()
if not brand:
    return error_response('brand param required', 400)

cursor.execute(
    "SELECT * FROM products WHERE is_active = 1 AND brand LIKE %s ORDER BY name",
    (f'%{brand}%',)
)
```

---

### 8. Similar products
**Prompt:** "Add an endpoint that returns products in the same category as a given product."

```python
# GET /products/<external_id>/similar
cursor.execute("SELECT id, category_id FROM products WHERE external_id = %s", (external_id,))
product = cursor.fetchone()
if not product:
    return error_response('Not found', 404)

cursor.execute(
    "SELECT * FROM products WHERE category_id = %s AND id != %s AND is_active = 1 ORDER BY created_at DESC LIMIT 8",
    (product['category_id'], product['id'])
)
```

---

## Key Patterns to Know Cold

**Always use parameterised queries:**
```python
cursor.execute("SELECT * FROM products WHERE id = %s", (product_id,))  # correct
cursor.execute(f"SELECT * FROM products WHERE id = {product_id}")       # never — SQL injection
```

**Commit after writes, not reads:**
```python
cursor.execute("UPDATE products SET is_active = 0 WHERE id = %s", (id,))
conn.commit()
```

**Get the ID of a new row:**
```python
cursor.execute("INSERT INTO table (...) VALUES (%s)", (...))
new_id = cursor.lastrowid
```

**Return 404 before doing work:**
```python
cursor.execute("SELECT id FROM products WHERE external_id = %s", (external_id,))
if not cursor.fetchone():
    return error_response('Not found', 404)
```

**Validate input before touching the DB:**
```python
data = request.get_json(silent=True) or {}
if not data.get('name'):
    return error_response('name is required', 400)
```

**Route ordering — static before dynamic:**
```python
@bp.get('/products/trending')   # must come first
@bp.get('/products/<id>')       # otherwise Flask matches "trending" as an id
```

---

## 1-Hour Time Budget

| Task | Time |
|------|------|
| Read existing code — route pattern, DB helper, response format | 10 min |
| Write the route + SQL | 20 min |
| `ALTER TABLE` if needed | 5 min |
| Test with curl | 10 min |
| Edge cases (404, missing params, empty results) | 15 min |

---

## Tiered Practice Set (Easy / Medium / Hard)

Questions 1-8 above are already partly solved in the codebase (`sale_items`, `recent`, `random` exist in `products.py`). These are fresh, on parts of the app that aren't built yet, tiered by real difficulty. Try to solve each one yourself before checking the Solutions section below.

### Easy (10-15 min each — single table, one condition)

**1. Missing-image report**
`GET /products/missing-images` — active products with no primary image.

**2. Distinct brand list**
`GET /brands` — simpler cousin of `/filters` (`app/routes/filters.py:36`), one query.

**3. Direct child categories**
`GET /categories/<external_id>/children` — one-hop self-referential lookup on `categories.parent_id`.

---

### Medium (20-25 min — pagination, aggregation, or a write)

**4. Paginate `GET /products`**
`success_response` already accepts a `meta` dict (`app/utils/response.py:4`) but nothing populates it. Add `page`/`per_page` query params and a `meta` block with total/total_pages.

**5. Wire up `view_count` (it already exists in the schema, unused!)**
The `products` table has a `view_count` column (`app/db_schema.sql:35`) that no route touches. Increment it in `GET /products/<external_id>` and add `GET /products/trending` sorted by it. Watch your route ordering.

**6. Add a size to a product (write + duplicate check)**
`POST /admin/products/<external_id>/sizes` with body `{"size_label": "M"}` — protect with the admin key, prevent duplicate sizes, insert and commit.

---

### Hard (25-30 min — transactions, concurrency, or debugging real code)

**7. Bulk restock in one transaction**
`POST /admin/products/<external_id>/restock` with body `{"sizes": [{"size_label": "M", "is_available": true}, ...]}`. Update multiple `product_sizes` rows atomically — if any size_label doesn't belong to the product, roll back the whole batch.

**8. Recommendation query without N+1**
`GET /products/<external_id>/recommended` — same category, shares at least one available size, price within ±20%, excluding itself, single query (no per-size Python loop calling the DB).

**9. Debug your own code — the search-miss fallback race**
Look at `search_products()` in `app/routes/products.py:77-100`: on a zero-result search it synchronously calls the external API *inside* the request handler before responding. What breaks in production, and how would you fix it?

---

### Solutions

**1. Missing-image report**
```python
cursor.execute("SELECT * FROM products WHERE is_active = 1 AND primary_image_url IS NULL")
```

**2. Distinct brand list**
```python
cursor.execute("SELECT DISTINCT brand FROM products WHERE is_active = 1 AND brand IS NOT NULL ORDER BY brand")
return success_response([r['brand'] for r in cursor.fetchall()])
```

**3. Direct child categories**
```python
cursor.execute("SELECT id FROM categories WHERE external_id = %s", (external_id,))
parent = cursor.fetchone()
if not parent: return error_response('Category not found', 404)
cursor.execute("SELECT * FROM categories WHERE parent_id = %s AND is_active = 1 ORDER BY display_order", (parent['id'],))
```

**4. Paginate `GET /products`**
```python
page = max(int(request.args.get('page', 1)), 1)
per_page = min(int(request.args.get('per_page', 20)), 100)
cursor.execute(f"SELECT COUNT(*) as total FROM products p WHERE {where}", params)
total = cursor.fetchone()['total']
cursor.execute(f"... ORDER BY {sort_clause} LIMIT %s OFFSET %s", params + [per_page, (page-1)*per_page])
meta = {'page': page, 'per_page': per_page, 'total': total, 'total_pages': -(-total // per_page)}
```

**5. Wire up `view_count`**
Increment on detail fetch:
```python
cursor.execute("UPDATE products SET view_count = view_count + 1 WHERE external_id = %s", (external_id,))
conn.commit()
```
Trending endpoint (register before `/products/<external_id>`):
```python
cursor.execute("SELECT * FROM products WHERE is_active = 1 ORDER BY view_count DESC LIMIT 10")
```

**6. Add a size to a product**
```python
cursor.execute("SELECT id FROM products WHERE external_id = %s", (external_id,))
product = cursor.fetchone()
if not product: return error_response('Product not found', 404)

cursor.execute(
    "SELECT id FROM product_sizes WHERE product_id = %s AND size_label = %s",
    (product['id'], size_label)
)
if cursor.fetchone():
    return error_response('Size already exists', 400)

cursor.execute(
    "INSERT INTO product_sizes (product_id, size_label, is_available) VALUES (%s, %s, 1)",
    (product['id'], size_label)
)
conn.commit()
return success_response({'id': cursor.lastrowid, 'size_label': size_label})
```

**7. Bulk restock in one transaction**
```python
cursor.execute("SELECT id FROM products WHERE external_id = %s", (external_id,))
product = cursor.fetchone()
if not product: return error_response('Product not found', 404)

try:
    for size in data['sizes']:
        cursor.execute(
            "SELECT id FROM product_sizes WHERE product_id = %s AND size_label = %s",
            (product['id'], size['size_label'])
        )
        row = cursor.fetchone()
        if not row:
            raise ValueError(f"Unknown size_label: {size['size_label']}")
        cursor.execute(
            "UPDATE product_sizes SET is_available = %s WHERE id = %s",
            (size['is_available'], row['id'])
        )
    conn.commit()
except ValueError as e:
    conn.rollback()
    return error_response(str(e), 400)

return success_response({'updated': len(data['sizes'])})
```

**8. Recommendation query without N+1**
```python
cursor.execute("SELECT id, category_id, price_amount FROM products WHERE external_id = %s", (external_id,))
product = cursor.fetchone()
if not product: return error_response('Product not found', 404)

low = float(product['price_amount']) * 0.8
high = float(product['price_amount']) * 1.2

cursor.execute(
    '''SELECT p.* FROM products p
       WHERE p.is_active = 1
       AND p.category_id = %s
       AND p.id != %s
       AND p.price_amount BETWEEN %s AND %s
       AND EXISTS (
           SELECT 1 FROM product_sizes ps1
           JOIN product_sizes ps2 ON ps1.size_label = ps2.size_label
           WHERE ps1.product_id = p.id AND ps1.is_available = 1
           AND ps2.product_id = %s AND ps2.is_available = 1
       )
       LIMIT 8''',
    (product['category_id'], product['id'], low, high, product['id'])
)
```

**9. Debug the search-miss fallback race**
What breaks: the request thread blocks on a slow external call; two concurrent requests for the same missing query both fire the API and both burn quota since there's no lock; an API failure becomes a swallowed `logging.warning` and the user silently gets an empty result.
How to fix it: move the cache-fill to a background job/queue instead of doing it inline, or take a short-lived lock keyed on the query string so only one request fills the cache. Then decide whether the *first* request should wait for the fill or just return empty and let a retry benefit from the now-cached data.

This last one is the strongest "hard" question — interviewers love pointing at code you wrote and asking "what's wrong here," and it's sitting in your file already.
