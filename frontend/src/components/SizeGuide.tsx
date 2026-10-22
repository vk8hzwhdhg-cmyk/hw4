import { useEffect, useState } from 'react'
import { store, type SizeGuide as Guide } from '../api'

const SIZES = ['XS', 'S', 'M', 'L', 'XL', 'XXL']

// Size guide dialog. Shows the chart for this product's category first.
export default function SizeGuide({ category, onClose }: { category: string; onClose: () => void }) {
  const [guide, setGuide] = useState<Guide | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    store.sizeGuide().then(setGuide).catch(() => setError("We couldn't load the size guide."))
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && onClose()
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])

  const charts = guide
    ? Object.values(guide.charts).sort((a, b) => Number(b.applies_to.includes(category)) - Number(a.applies_to.includes(category)))
    : []

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal" role="dialog" aria-modal="true" aria-label="Size guide" onClick={(e) => e.stopPropagation()}>
        <button className="modal-close" aria-label="Close size guide" onClick={onClose}>×</button>
        <h2>Size Guide</h2>
        {error && <p className="notice error">{error}</p>}
        {guide && (
          <>
            <p className="guide-note">{guide.fit_note}</p>
            {charts.map((c) => (
              <div key={c.label} className="guide-chart">
                <h3>{c.label}{c.applies_to.includes(category) && <span className="guide-badge">This item</span>}</h3>
                <table className="guide-table">
                  <thead>
                    <tr><th>Size</th>{c.columns.map((col) => <th key={col}>{col} (in)</th>)}<th>Fits chest (in)</th></tr>
                  </thead>
                  <tbody>
                    {SIZES.map((s) => (
                      <tr key={s}>
                        <th scope="row">{s}</th>
                        {c.sizes[s] ? c.sizes[s]!.map((v, i) => <td key={i}>{v}</td>) : <td colSpan={c.columns.length} className="muted">Not published</td>}
                        <td>{guide.body_chest_inches[s] ?? '—'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ))}
            <p className="guide-note"><strong>How to measure:</strong> {guide.how_to_measure}</p>
            <p className="guide-small">{guide.note}</p>
          </>
        )}
      </div>
    </div>
  )
}
