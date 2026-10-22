import { useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { api, toCard, type Category, type Collection, type ProductSummary } from '../api'
import ProductCard from '../components/ProductCard'

const PRICE_RANGES: Record<string, [number, number]> = {
  'under-40': [0, 39.99],
  '40-60': [40, 60],
  '60-80': [60.01, 80],
  '80-plus': [80.01, Infinity],
}
const PRICE_LABELS: Record<string, string> = {
  '': 'Any price', 'under-40': 'Under $40', '40-60': '$40 – $60', '60-80': '$60 – $80', '80-plus': 'Over $80',
}
const SORTS: Record<string, string> = {
  '': 'Featured', 'price-asc': 'Price: low to high', 'price-desc': 'Price: high to low', 'name': 'Name: A to Z',
}

export default function Products() {
  const [params, setParams] = useSearchParams()
  const category = params.get('category') ?? ''
  const q = params.get('q') ?? ''
  const collection = params.get('collection') ?? ''
  const sort = params.get('sort') ?? ''
  const price = params.get('price') ?? ''
  const inStock = params.get('instock') === '1'
  const [search, setSearch] = useState(q)
  const [categories, setCategories] = useState<Category[]>([])
  const [collections, setCollections] = useState<Collection[]>([])
  const [products, setProducts] = useState<ProductSummary[] | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    api.categories().then(setCategories).catch(() => {})
    api.collections().then(setCollections).catch(() => {})
  }, [])

  useEffect(() => setSearch(q), [q])

  useEffect(() => {
    setProducts(null)
    setError('')
    api
      .products({ category, q, collection })
      .then(setProducts)
      .catch(() => setError("We couldn't load products. Is the backend running?"))
  }, [category, q, collection])

  const update = (next: Record<string, string>) => {
    const merged = { category, q, collection, sort, price, instock: inStock ? '1' : '', ...next }
    setParams(Object.fromEntries(Object.entries(merged).filter(([, v]) => v)))
  }

  // Sort and price / stock filters run in the browser on the loaded list (102 items max).
  const shown = useMemo(() => {
    if (!products) return null
    let list = products
    if (price && PRICE_RANGES[price]) {
      const [lo, hi] = PRICE_RANGES[price]
      list = list.filter((p) => p.price >= lo && p.price <= hi)
    }
    if (inStock) list = list.filter((p) => p.total_stock > 0)
    const sorted = [...list]
    if (sort === 'price-asc') sorted.sort((a, b) => a.price - b.price || a.name.localeCompare(b.name))
    if (sort === 'price-desc') sorted.sort((a, b) => b.price - a.price || a.name.localeCompare(b.name))
    if (sort === 'name') sorted.sort((a, b) => a.name.localeCompare(b.name))
    return sorted
  }, [products, price, inStock, sort])
  const anyFilter = Boolean(category || collection || q || price || inStock)

  return (
    <div className="container section">
      <h1 className="page-title">
        {[collection, category].filter(Boolean).join(' · ') || 'All Products'}
      </h1>
      <p className="page-sub">Casual comfort, classic Bulldog pride.</p>

      <div className="filters">
        <div className="filter-rows">
        <div className="chips" role="group" aria-label="Category">
          <button className={`chip ${!category ? 'active' : ''}`} onClick={() => update({ category: '' })}>
            All
          </button>
          {categories.map((c) => (
            <button
              key={c.category}
              className={`chip ${category === c.category ? 'active' : ''}`}
              onClick={() => update({ category: c.category })}
            >
              {c.category}
            </button>
          ))}
        </div>
        <div className="chips" role="group" aria-label="Collection">
          <span className="chips-label">Shop by:</span>
          {collections.map((c) => (
            <button
              key={c.collection}
              className={`chip chip-collection ${collection === c.collection ? 'active' : ''}`}
              aria-pressed={collection === c.collection}
              title={collection === c.collection ? 'Click again to remove this filter' : undefined}
              onClick={() => update({ collection: collection === c.collection ? '' : c.collection })}
            >
              {c.collection} <span className="chip-count">{c.count}</span>
            </button>
          ))}
        </div>
        </div>
        <form
          className="search"
          role="search"
          onSubmit={(e) => {
            e.preventDefault()
            update({ q: search.trim() })
          }}
        >
          <input
            type="search"
            placeholder="Search (e.g. Saybrook, tennis, navy)"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            aria-label="Search products"
          />
          <button className="btn btn-small" type="submit">Search</button>
        </form>
      </div>

      <div className="sort-bar">
        <label>
          Sort by{' '}
          <select value={sort} onChange={(e) => update({ sort: e.target.value })}>
            {Object.entries(SORTS).map(([v, l]) => <option key={v} value={v}>{l}</option>)}
          </select>
        </label>
        <label>
          Price{' '}
          <select value={price} onChange={(e) => update({ price: e.target.value })}>
            {Object.entries(PRICE_LABELS).map(([v, l]) => <option key={v} value={v}>{l}</option>)}
          </select>
        </label>
        <label className="check">
          <input type="checkbox" checked={inStock} onChange={(e) => update({ instock: e.target.checked ? '1' : '' })} />
          In stock only
        </label>
      </div>

      {error && <p className="notice error">{error}</p>}
      {!error && products === null && <p className="notice">Loading products…</p>}
      {shown && (
        <>
          <p className="result-count">
            {shown.length} {shown.length === 1 ? 'product' : 'products'}
            {q && <> matching “{q}”</>}
            {anyFilter && (
              <button className="link-button" onClick={() => setParams({})}>Clear filters</button>
            )}
          </p>
          {shown.length === 0 ? (
            <p className="notice">
              {q || price || inStock
                ? 'No products match these filters.'
                : `We don't have any ${collection && category ? `${category.toLowerCase()} in ${collection}` : (category || collection).toLowerCase()} right now.`}{' '}
              <button className="link-button" onClick={() => (q || price || inStock ? setParams({}) : update({ category: '' }))}>
                {!(q || price || inStock) && collection && category ? `See all ${collection}` : 'See all products'}
              </button>
            </p>
          ) : (
            <div className="product-grid">
              {shown.map((p) => <ProductCard key={p.product_id} product={toCard(p)} />)}
            </div>
          )}
        </>
      )}
    </div>
  )
}
