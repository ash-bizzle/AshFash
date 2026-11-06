"""Stylist agent: lets Claude answer open-ended styling requests by searching
the AshFash catalog itself, rather than us hand-coding the query logic.

Claude is given three tools - search_catalog, get_product_details and
get_available_filters - and decides on its own how many times to call each
one (e.g. check what colours/prices exist, search, narrow down, search again)
before writing a final recommendation. We only ever hand it real rows from
MySQL; it cannot invent products.
"""
import json
import re

import anthropic
from anthropic import beta_tool
from flask import current_app

from app.db import get_db

STYLIST_SYSTEM_PROMPT = """You are AshFash's personal stylist.

Rules:
- Only recommend products returned by search_catalog or get_product_details. \
Never invent a product, price, colour, or external_id.
- If you're unsure what brands, colours, or price ranges exist in the catalog, \
call get_available_filters before searching, so you don't waste searches on \
terms that don't exist.
- If a search comes back empty, try again with broader or different keywords \
before giving up.
- When you recommend a product, name it and include its external_id in \
parentheses, e.g. "Floral Midi Dress (prod-001)", and mention its price.
- Keep the final answer short: a friendly sentence or two, then a bulleted list \
of picks.
- If nothing in the catalog fits the request, say so honestly rather than \
making something up.
"""

MAX_RESULTS_PER_SEARCH = 10


def run_stylist_session(user_message):
    """Run one stylist turn and return {'answer': str, 'products': [...]}."""
    client = anthropic.Anthropic(api_key=current_app.config['ANTHROPIC_API_KEY'])

    # Every product Claude looked at (via either tool) during this turn,
    # keyed by external_id so the frontend can render product cards for
    # whatever it actually found - not just what it mentions in prose.
    seen_products = {}

    @beta_tool
    def search_catalog(query: str = '', gender: str = '', colour: str = '', max_price: float = 0) -> str:
        """Search the AshFash product catalog and return matching products.

        Args:
            query: Free-text keywords to match against product name, brand,
                and description (e.g. "linen shirt"). Leave blank to browse by
                filters only.
            gender: Restrict to "women", "men", "kids", or "unisex". Leave
                blank for any.
            colour: Restrict to products of roughly this colour (e.g. "black").
            max_price: Only return products at or below this price. Use 0 for
                no limit.
        """
        conditions = ['p.is_active = 1']
        params = []

        if query:
            like = f'%{query}%'
            conditions.append('(p.name LIKE %s OR p.brand LIKE %s OR p.description LIKE %s)')
            params += [like, like, like]
        if gender:
            conditions.append("p.gender IN (%s, 'unisex')")
            params.append(gender)
        if colour:
            conditions.append('p.colour LIKE %s')
            params.append(f'%{colour}%')
        if max_price and max_price > 0:
            conditions.append('COALESCE(p.sale_price_amount, p.price_amount) <= %s')
            params.append(max_price)

        where = ' AND '.join(conditions)
        conn = get_db()
        with conn.cursor() as cursor:
            cursor.execute(
                f'''SELECT p.external_id, p.name, p.brand, p.primary_image_url,
                           p.external_url, p.price_amount, p.price_currency,
                           p.sale_price_amount, p.gender, p.colour
                    FROM products p
                    WHERE {where}
                    ORDER BY p.created_at DESC
                    LIMIT {MAX_RESULTS_PER_SEARCH}''',
                tuple(params)
            )
            rows = cursor.fetchall()

        results = [_serialize_product(r) for r in rows]
        for r in results:
            seen_products[r['external_id']] = r

        if not results:
            return json.dumps({'message': 'No products matched. Try broader or different keywords.'})
        return json.dumps(results)

    @beta_tool
    def get_product_details(external_id: str) -> str:
        """Look up full details (including available sizes) for one product.

        Args:
            external_id: The product's external_id, as returned by search_catalog.
        """
        conn = get_db()
        with conn.cursor() as cursor:
            cursor.execute(
                'SELECT * FROM products WHERE external_id = %s AND is_active = 1',
                (external_id,)
            )
            product = cursor.fetchone()
            if not product:
                return json.dumps({'error': f'No active product with external_id "{external_id}"'})

            cursor.execute(
                'SELECT size_label, is_available FROM product_sizes WHERE product_id = %s',
                (product['id'],)
            )
            sizes = cursor.fetchall()

        data = _serialize_product(product)
        data['sizes'] = [s['size_label'] for s in sizes if s['is_available']]
        seen_products[data['external_id']] = data
        return json.dumps(data)

    @beta_tool
    def get_available_filters() -> str:
        """Return the brands, colours, genders, and price range currently in
        the catalog, so you know what's realistic to search for."""
        conn = get_db()
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT DISTINCT brand FROM products WHERE is_active = 1 AND brand IS NOT NULL ORDER BY brand"
            )
            brands = [r['brand'] for r in cursor.fetchall()]

            cursor.execute(
                "SELECT DISTINCT colour FROM products WHERE is_active = 1 AND colour IS NOT NULL ORDER BY colour"
            )
            colours = [r['colour'] for r in cursor.fetchall()]

            cursor.execute(
                "SELECT DISTINCT gender FROM products WHERE is_active = 1 AND gender IS NOT NULL"
            )
            genders = [r['gender'] for r in cursor.fetchall()]

            cursor.execute(
                "SELECT MIN(price_amount) AS min_price, MAX(price_amount) AS max_price FROM products WHERE is_active = 1"
            )
            price_row = cursor.fetchone()

        return json.dumps({
            'brands': brands,
            'colours': colours,
            'genders': genders,
            'price_range': {
                'min': float(price_row['min_price']) if price_row['min_price'] is not None else None,
                'max': float(price_row['max_price']) if price_row['max_price'] is not None else None,
            },
        })

    runner = client.beta.messages.tool_runner(
        model=current_app.config['STYLIST_MODEL'],
        max_tokens=2048,
        # Caps how many tool-call rounds Claude can make in one request - without
        # this, an unusual request could loop indefinitely (each round is a billed
        # API call). "No limit by default" per the SDK, so this must be set explicitly.
        max_iterations=current_app.config['STYLIST_MAX_ITERATIONS'],
        system=STYLIST_SYSTEM_PROMPT,
        tools=[search_catalog, get_product_details, get_available_filters],
        messages=[{'role': 'user', 'content': user_message}],
    )

    final_message = None
    for message in runner:
        final_message = message

    answer = ''
    if final_message is not None:
        answer = ''.join(b.text for b in final_message.content if b.type == 'text').strip()

    if not answer:
        # Either the iteration cap was hit while Claude was still mid-search
        # (stop_reason != "end_turn" and the last turn was tool calls, not
        # text), or it refused, or something else left no text to show.
        # Fall back to a deterministic summary of whatever was actually
        # found, instead of returning an empty answer.
        stop_reason = getattr(final_message, 'stop_reason', None)
        answer = _fallback_answer(seen_products, stop_reason)

    return {
        'answer': answer,
        'products': _cited_products(answer, seen_products),
    }


def _cited_products(answer, seen_products):
    """Only the products the final answer actually recommends - not every
    product a search happened to turn up along the way.

    The system prompt tells Claude to cite picks as "Name (external_id)",
    so pull external_ids out of parentheses, in the order they're first
    mentioned, and look each one up in what the tools actually returned.
    """
    cited = []
    cited_ids = set()
    for match in re.finditer(r'\(([^()]+)\)', answer):
        ext_id = match.group(1).strip()
        if ext_id in seen_products and ext_id not in cited_ids:
            cited_ids.add(ext_id)
            cited.append(seen_products[ext_id])

    if cited:
        return cited
    # Claude didn't cite anything in the expected format (e.g. a refusal, or
    # it just described things in prose) - show everything it looked at
    # rather than nothing.
    return list(seen_products.values())


def _fallback_answer(seen_products, stop_reason):
    if stop_reason == 'refusal':
        return "I'm not able to help with that request."

    products = list(seen_products.values())
    if not products:
        return (
            "I wasn't able to put together a recommendation for that - try rephrasing "
            "with more specific details (a price range, colour, or category helps)."
        )

    picks = ', '.join(f"{p['name']} ({p['external_id']})" for p in products[:5])
    return (
        f"I ran out of search steps before finishing a full recommendation, but here's "
        f"what I found that might work: {picks}."
    )


def _serialize_product(row):
    return {
        'external_id': row['external_id'],
        'name': row['name'],
        'brand': row.get('brand'),
        'primary_image_url': row.get('primary_image_url'),
        'external_url': row.get('external_url'),
        'price_amount': float(row['price_amount']) if row.get('price_amount') is not None else None,
        'price_currency': row.get('price_currency'),
        'sale_price_amount': float(row['sale_price_amount']) if row.get('sale_price_amount') is not None else None,
        'gender': row.get('gender'),
        'colour': row.get('colour'),
    }
