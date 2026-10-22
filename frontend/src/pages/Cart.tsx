import { useEffect, useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { formatDate, formatPrice, store, type CartQuote } from '../api'
import { useCart } from '../CartContext'

export default function Cart() {
  const cart = useCart()
  const [quote, setQuote] = useState<CartQuote | null>(null)
  const [error, setError] = useState('')
  const [checkout, setCheckout] = useState(false)
  // Discount code (e.g. Boola1234): remembered in this browser, always checked by the server.
  const [code, setCode] = useState(() => localStorage.getItem('cc_discount') ?? '')
  const [codeInput, setCodeInput] = useState(code)

  // Re-price the cart from the server whenever it (or the code) changes.
  useEffect(() => {
    setError('')
    if (cart.items.length === 0) {
      setQuote({ lines: [], item_count: 0, subtotal: 0 })
      return
    }
    store.quote(cart.items, code || undefined).then(setQuote).catch(() => setError("We couldn't load your cart. Is the backend running?"))
  }, [cart.items, code])

  const applyCode = (e: FormEvent) => {
    e.preventDefault()
    const c = codeInput.trim()
    setCode(c)
    if (c) localStorage.setItem('cc_discount', c)
    else localStorage.removeItem('cc_discount')
  }
  const removeCode = () => {
    setCode('')
    setCodeInput('')
    localStorage.removeItem('cc_discount')
  }

  if (error) return <div className="container section"><p className="notice error">{error}</p></div>
  if (!quote) return <div className="container section"><p className="notice">Loading your cart…</p></div>

  if (quote.lines.length === 0)
    return (
      <div className="container section cart">
        <h1 className="page-title">Your Cart</h1>
        <p className="page-sub">Your cart is empty.</p>
        <Link to="/products" className="btn">Shop Official Yale Merch</Link>
      </div>
    )

  return (
    <div className="container section cart">
      <h1 className="page-title">Your Cart</h1>
      <p className="page-sub">{quote.item_count} {quote.item_count === 1 ? 'item' : 'items'} · prices and stock checked just now</p>
      <div className="cart-layout">
        <ul className="cart-lines">
          {quote.lines.map((l) => (
            <li key={`${l.product_id}-${l.size}`} className={`cart-line ${l.status}`}>
              {l.image_url && <Link to={`/products/${l.product_id}`}><img src={l.image_url} alt="" /></Link>}
              <div className="cart-line-info">
                <Link to={`/products/${l.product_id}`} className="cart-line-name">{l.name ?? l.product_id}</Link>
                <span className="cart-line-meta">Size {l.size}{l.price !== null && <> · {formatPrice(l.price)} each</>}</span>
                {l.message && <span className="cart-line-warn">{l.message}</span>}
                <div className="cart-line-actions">
                  {l.status !== 'sold_out' && l.status !== 'unavailable' && (
                    <label>
                      Qty{' '}
                      <select value={l.quantity} aria-label={`Quantity for ${l.name}`}
                              onChange={(e) => cart.setQuantity(l.product_id, l.size, Number(e.target.value))}>
                        {Array.from({ length: Math.min(10, l.available) }, (_, i) => i + 1).map((n) => <option key={n} value={n}>{n}</option>)}
                      </select>
                    </label>
                  )}
                  <button className="link-button" onClick={() => cart.remove(l.product_id, l.size)}>Remove</button>
                </div>
              </div>
              <span className="cart-line-total">{formatPrice(l.line_total)}</span>
            </li>
          ))}
        </ul>

        <aside className="cart-summary">
          <h2>Order Summary</h2>
          <p className="cart-row"><span>Subtotal</span><strong>{formatPrice(quote.subtotal)}</strong></p>
          <form className="discount-form" onSubmit={applyCode}>
            <label htmlFor="discount-code">Discount code</label>
            <div className="discount-row">
              <input id="discount-code" value={codeInput} placeholder="Boola1234" maxLength={30}
                     onChange={(e) => setCodeInput(e.target.value)} autoComplete="off" />
              <button className="btn btn-small" type="submit">Apply</button>
            </div>
          </form>
          {quote.discount && (
            <p className="cart-row discount-applied">
              <span>
                {quote.discount.code} ({quote.discount.percent_off}% off)
                <button className="link-button" onClick={removeCode}>Remove</button>
                <small>Expires {formatDate(quote.discount.expires_at)}</small>
              </span>
              <strong>−{formatPrice(quote.discount.amount)}</strong>
            </p>
          )}
          {quote.discount_error && <p className="discount-error" role="alert">{quote.discount_error}</p>}
          <p className="cart-row cart-total"><span>Total</span><strong>{formatPrice(quote.total ?? quote.subtotal)}</strong></p>
          <p className="cart-small">Taxes and pickup or shipping options are shown at checkout.</p>
          <button className="btn btn-block" disabled={quote.item_count === 0} onClick={() => setCheckout(true)}>
            Checkout
          </button>
          {checkout && (
            <p className="notice" role="status">
              Online checkout isn't connected yet in this demo store, so no payment is taken. To buy these
              items, visit us at 57 Broadway, New Haven, or ask Bulldog for help.
            </p>
          )}
          <Link to="/products" className="link-arrow">← Continue shopping</Link>
        </aside>
      </div>
    </div>
  )
}
