import { useState, type ReactNode } from 'react'

const BANNER = '/hero/yale-bulldog-blue-banner.webp' // from yalebulldogblue.com; git-ignored

// Home hero. Like the real site: the full lifestyle banner (it already carries the
// YALE BULLDOG BLUE logo), with the headline and buttons in a band below it.
// A fresh GitHub clone has no banner, so it falls back to the original navy hero
// (Yale-blue background with the headline in white).
export default function HeroImage({ children }: { children: ReactNode }) {
  const [hasBanner, setHasBanner] = useState(true)

  if (hasBanner)
    return (
      <section className="hero-banner" aria-label="Yale Bulldog Blue">
        <img
          className="hero-banner-img"
          src={BANNER}
          width={2000}
          height={791}
          alt="Smiling students walking on campus in Yale T-shirts and sweatshirts. Yale Bulldog Blue, officially licensed merchandise."
          onError={() => setHasBanner(false)}
        />
        <div className="hero-intro">
          <div className="container hero-intro-inner">{children}</div>
        </div>
      </section>
    )

  return (
    <section className="hero">
      <div className="container hero-inner">{children}</div>
    </section>
  )
}
