import { useCallback, useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api, formatPrice, type ProductDetail } from '../api'
import { useCart } from '../CartContext'
import { openBulldog } from '../chatEvents'
import NotifyMe from '../components/NotifyMe'
import SizeGuide from '../components/SizeGuide'

export default function ProductPage() {
  const { productId = '' } = useParams()
  const [product, setProduct] = useState<ProductDetail | null>(null)
  const [error, setError] = useState('')
  const [size, setSize] = useState('')
  const [qty, setQty] = useState(1)
  const [added, setAdded] = useState('')
  const [showGuide, setShowGuide] = useState(false)
  const closeGuide = useCallback(() => setShowGuide(false), [])
  const cart = useCart()

  useEffect(() => {
    setProduct(null)
    setError('')
    setSize('')
    setQty(1)
    setAdded('')
    api
      .product(productId)
      .then(setProduct)
      .catch((e: Error) =>
        setError(e.message === 'Not found' ? "We couldn't find that product." : "We couldn't load this product."),
      )
  }, [productId])

  if (error)
    return (
      <div className="container section">
        <p className="notice error">{error}</p>
        <Link to="/products" className="link-arrow">← Back to products</Link>
      </div>
    )
  if (!product) return <div className="container section"><p className="notice">Loading…</p></div>

  const selected = product.sizes.find((s) => s.size === size)
  const soldOut = product.total_stock === 0
  const selectedSoldOut = selected?.status === 'sold out'
  const maxQty = selected ? Math.min(10, selected.quantity) : 1

  const addToCart = () => {
    if (!selected || selectedSoldOut) return
    cart.add(product.product_id, selected.size, qty)
    setAdded(`Added ${qty} × ${product.name} (${selected.size}) to your cart.`)
  }

  return (
    <div className="container section">
      <nav className="breadcrumb" aria-label="Breadcrumb">
        <Link to="/">Home</Link> / <Link to="/products">Products</Link> /{' '}
        <Link to={`/products?category=${encodeURIComponent(product.category)}`}>{product.category}</Link>
      </nav>

      <div className="pdp">
        <div className="pdp-image">
          <img src={product.image_url} alt={product.name} />
        </div>

        <div className="pdp-info">
          <span className="card-category">{product.category}</span>
          <h1 className="pdp-title">{product.name}</h1>
          <p className="pdp-price">{formatPrice(product.price)}</p>

          <p className="pdp-desc">{product.description}</p>

          {product.colors.length > 0 && (
            <p className="pdp-colors">
              <strong>Colors:</strong> {product.colors.join(', ')}
            </p>
          )}

          <fieldset className="sizes">
            <legend>
              Size{selected && <>: <strong>{selected.size}</strong></>}
              <button type="button" className="link-button size-guide-link" onClick={() => setShowGuide(true)}>
                📏 Size guide
              </button>
            </legend>
            <div className="size-grid">
              {product.sizes.map((s) => (
                <button
                  key={s.size}
                  type="button"
                  className={`size ${size === s.size ? 'active' : ''} ${s.status === 'sold out' ? 'sold-out' : ''}`}
                  aria-pressed={size === s.size}
                  title={s.status === 'sold out' ? 'Sold out: select to get a restock email' : `${s.quantity} in stock`}
                  onClick={() => {
                    setSize(s.size)
                    setQty(1)
                    setAdded('')
                  }}
                >
                  {s.size}
                </button>
              ))}
            </div>
          </fieldset>

          <p className={`stock ${selected ? selected.status.replace(' ', '-') : ''}`} aria-live="polite">
            {soldOut
              ? 'Sold out in all sizes.'
              : !selected
                ? 'Select a size to see availability.'
                : selectedSoldOut
                  ? `Sold out in ${selected.size}.`
                  : selected.status === 'low stock'
                  ? `Only ${selected.quantity} left in ${selected.size}. Order soon!`
                  : `In stock in ${selected.size}.`}
          </p>

          {selected && selectedSoldOut && <NotifyMe key={selected.size} productId={product.product_id} size={selected.size} />}

          {selected && !selectedSoldOut && (
            <label className="qty">
              Quantity
              <select value={qty} onChange={(e) => setQty(Number(e.target.value))}>
                {Array.from({ length: maxQty }, (_, i) => i + 1).map((n) => <option key={n} value={n}>{n}</option>)}
              </select>
            </label>
          )}
          <button className="btn btn-block" disabled={!selected || selectedSoldOut} onClick={addToCart}>
            {soldOut ? 'Sold Out' : !selected ? 'Select a Size' : selectedSoldOut ? `Sold Out in ${selected.size}` : 'Add to Cart'}
          </button>
          {added && (
            <p className="added" role="status">
              ✓ {added} <Link to="/cart">View cart →</Link>
            </p>
          )}
          <button type="button" className="btn btn-block btn-outline ask-bulldog" onClick={openBulldog}>
            🐶 Ask Bulldog about this item
          </button>
          <p className="pdp-note">Sizes, colors, stock or similar styles. Bulldog knows which item you're viewing.</p>

          <table className="stock-table">
            <caption>Availability by size</caption>
            <tbody>
              {product.sizes.map((s) => (
                <tr key={s.size}>
                  <th scope="row">{s.size}</th>
                  <td className={s.status.replace(' ', '-')}>
                    {s.status === 'sold out' ? 'Sold out' : s.status === 'low stock' ? `Low stock (${s.quantity})` : 'In stock'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
      {showGuide && <SizeGuide category={product.category} onClose={closeGuide} />}
    </div>
  )
}
