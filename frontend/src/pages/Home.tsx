import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api, toCard, type Category, type ProductSummary } from '../api'
import ProductCard from '../components/ProductCard'
import HeroImage from '../components/HeroImage'

const FEATURED = [
  'champion-reverse-weave-hoodie',
  'yale-sports-hoodie-diving',
  'district-vit-crewneck-vintage-bulldog',
  'big-yale-tri-blend-t-shirt',
]

export default function Home() {
  const [categories, setCategories] = useState<Category[]>([])
  const [colleges, setColleges] = useState<ProductSummary[]>([])
  const [featured, setFeatured] = useState<ProductSummary[]>([])

  useEffect(() => {
    api.categories().then(setCategories).catch(() => setCategories([]))
    api.products({ q: 'College Crewneck' }).then((p) => setColleges(p.slice(0, 4))).catch(() => {})
    api
      .products()
      .then((all) => {
        const picks = all.filter((p) => FEATURED.some((id) => p.product_id.startsWith(id)))
        setFeatured((picks.length >= 4 ? picks : all).slice(0, 4))
      })
      .catch(() => {})
  }, [])

  return (
    <>
      <HeroImage>
          <p className="eyebrow">Yale Bulldog Blue by Campus Customs</p>
          <h1>Bring Tradition with you wherever you go.</h1>
          <p className="hero-sub">Official Yale Merch.</p>
          <div className="hero-actions">
            <Link to="/products" className="btn btn-light">Shop All Products</Link>
            <Link to="/about" className="btn btn-outline-light">Our Story</Link>
          </div>
        </HeroImage>

      <section className="container section">
        <h2 className="section-title">Shop Comfy Layers</h2>
        <div className="category-grid">
          {categories.map((c) => (
            <Link
              key={c.category}
              to={`/products?category=${encodeURIComponent(c.category)}`}
              className="category-tile"
            >
              <span className="category-name">{c.category}</span>
              <span className="category-count">{c.count} styles</span>
            </Link>
          ))}
        </div>
      </section>

      <section className="container section">
        <div className="section-head">
          <h2 className="section-title">Big Spirit, Big Yale</h2>
          <Link to="/products" className="link-arrow">View all →</Link>
        </div>
        <div className="product-grid">
          {featured.map((p) => <ProductCard key={p.product_id} product={toCard(p)} />)}
        </div>
      </section>

      <section className="band">
        <div className="container section">
          <div className="section-head">
            <h2 className="section-title">Show your residential college pride!</h2>
            <Link to="/products?collection=Colleges" className="link-arrow">All colleges →</Link>
          </div>
          <div className="product-grid">
            {colleges.map((p) => <ProductCard key={p.product_id} product={toCard(p)} />)}
          </div>
        </div>
      </section>
    </>
  )
}
