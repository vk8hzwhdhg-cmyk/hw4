import { useState } from 'react'
import { Link } from 'react-router-dom'

const ADDRESS = '57 Broadway, New Haven, CT 06511'
const q = encodeURIComponent(ADDRESS)
// Keyless Google Maps embed, plus "open in…" links for the shopper's preferred app.
const MAP_EMBED = `https://www.google.com/maps?q=${q}&z=16&output=embed`
const MAP_LINKS = [
  { label: 'Google Maps', href: `https://www.google.com/maps/search/?api=1&query=${q}` },
  { label: 'Apple Maps', href: `https://maps.apple.com/?address=${q}&q=${encodeURIComponent('Yale Bulldog Blue by Campus Customs')}` },
  { label: 'Waze', href: `https://waze.com/ul?q=${q}&navigate=yes` },
]

export default function About() {
  const [copied, setCopied] = useState(false)
  const copyAddress = async () => {
    try {
      await navigator.clipboard.writeText(ADDRESS)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      window.prompt('Copy the address:', ADDRESS)
    }
  }

  return (
    <>
      <section className="hero hero-short">
        <div className="container hero-inner">
          <p className="eyebrow">About Us</p>
          <h1>Part of the Yale fabric.</h1>
        </div>
      </section>

      <div className="container section about">
        <div className="about-copy">
          <p className="lead">Family-owned and operated for over 50 years.</p>
          <p>
            We're part of the Yale fabric and produce on site for quick turnarounds while supporting
            the local community. We've got you covered for all of your Yale merch needs.
          </p>
          <p>
            Reach out if you have any questions or would like to create a Campus Custom idea with us.
          </p>
          <Link to="/products" className="btn">Shop Official Yale Merch</Link>
        </div>

        <aside className="about-card">
          <h2>Come Visit Us!</h2>
          <p>
            Yale Bulldog Blue by Campus Customs
            <br />
            57 Broadway
            <br />
            New Haven, CT 06511
          </p>
          <iframe
            className="about-map"
            title="Map to Yale Bulldog Blue by Campus Customs, 57 Broadway, New Haven"
            src={MAP_EMBED}
            loading="lazy"
            referrerPolicy="no-referrer-when-downgrade"
          />
          <p className="map-open-label">Open directions in:</p>
          <div className="map-links">
            {MAP_LINKS.map((m) => (
              <a key={m.label} className="btn btn-small btn-outline" href={m.href} target="_blank" rel="noopener noreferrer">
                {m.label}
              </a>
            ))}
            <button type="button" className="btn btn-small btn-outline" onClick={copyAddress}>
              {copied ? 'Copied ✓' : 'Copy address'}
            </button>
          </div>
          <p className="map-hint">Using another app? Copy the address and paste it in.</p>
        </aside>
      </div>
    </>
  )
}
