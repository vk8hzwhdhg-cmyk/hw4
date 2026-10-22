import { useEffect, useRef, useState } from 'react'
import { useLocation } from 'react-router-dom'
import { useChatResults } from '../ChatResultsContext'
import ProductCard from './ProductCard'

// "Bulldog's picks": the product matches from the latest chat answer, shown on the page.
// On a single-item page it collapses to a slim bar so the product view stays on top.
export default function ChatResults() {
  const { results, clear } = useChatResults()
  const { pathname } = useLocation()
  const onDetailPage = pathname.startsWith('/products/')
  const [expanded, setExpanded] = useState(true)
  const ref = useRef<HTMLElement>(null)

  // New results: show them and bring them into view.
  useEffect(() => {
    if (!results) return
    setExpanded(true)
    ref.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }, [results])

  // Opening a product collapses the picks; other pages show them.
  useEffect(() => {
    setExpanded(!onDetailPage)
  }, [pathname, onDetailPage])

  if (!results) return null

  if (!expanded)
    return (
      <div className="chat-results-bar">
        <div className="container chat-results-bar-inner">
          <span>🐶 Bulldog's picks: <strong>{results.title}</strong> ({results.products.length})</span>
          <span>
            <button className="link-button" onClick={() => setExpanded(true)}>Show picks</button>
            <button className="link-button" onClick={clear}>Clear</button>
          </span>
        </div>
      </div>
    )

  return (
    <section className="chat-results" ref={ref} aria-label="Bulldog's picks" aria-live="polite">
      <div className="container">
        <div className="chat-results-head">
          <div>
            <p className="eyebrow">🐶 Bulldog's picks · “{results.question}”</p>
            <h2 className="section-title">{results.title}</h2>
          </div>
          <span className="chat-results-actions">
            {onDetailPage && <button className="btn btn-small btn-outline" onClick={() => setExpanded(false)}>Hide</button>}
            <button className="btn btn-small btn-outline" onClick={clear}>Clear</button>
          </span>
        </div>
        <div className="product-grid">
          {results.products.map((p) => <ProductCard key={p.product_id} product={p} />)}
        </div>
      </div>
    </section>
  )
}
