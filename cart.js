/* Paititi — tiny localStorage cart shared by the store pages and header badge.
 * Items: { id, name, priceCents, qty, meta? } — validated server-side at checkout. */
(function () {
  const KEY = 'pt-cart';
  const read = () => {
    try { return JSON.parse(localStorage.getItem(KEY) || '[]'); } catch (e) { return []; }
  };
  const write = (items) => {
    localStorage.setItem(KEY, JSON.stringify(items));
    const count = items.reduce((s, i) => s + (i.qty || 1), 0);
    window.dispatchEvent(new CustomEvent('pt-cart-changed', { detail: { count, items } }));
  };
  window.PtCart = {
    get: read,
    count: () => read().reduce((s, i) => s + (i.qty || 1), 0),
    add(item) {
      const items = read();
      const existing = items.find((i) => i.id === item.id);
      if (existing) existing.qty = (existing.qty || 1) + (item.qty || 1);
      else items.push({ qty: 1, ...item });
      write(items);
    },
    setQty(id, qty) {
      let items = read();
      if (qty <= 0) items = items.filter((i) => i.id !== id);
      else items.forEach((i) => { if (i.id === id) i.qty = qty; });
      write(items);
    },
    remove(id) { write(read().filter((i) => i.id !== id)); },
    clear() { write([]); },
    async checkout() {
      const items = read().map((i) => ({ id: i.id, qty: i.qty, amount: i.amount, frequency: i.frequency, variantId: i.variantId }));
      const res = await fetch('/api/checkout', {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify({ items }),
      });
      const data = await res.json().catch(() => ({}));
      if (res.ok && data.url) { location.href = data.url; return; }
      throw new Error(data.error || 'Checkout failed');
    },
  };
})();
