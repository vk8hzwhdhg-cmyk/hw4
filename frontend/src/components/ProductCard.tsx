import { Link } from 'react-router-dom'
import { formatPrice, type CardData } from '../api'

// One card used everywhere; every card opens the single-item page.
export default function ProductCard({ product }: { product: CardData }) {
  return (
    <Link to={`/products/${product.product_id}`} className="card">
      <div className="card-image">
        <img src={product.image_url} alt={product.name} loading="lazy" />
        {!product.in_stock && <span className="badge">Sold out</span>}
      </div>
      <div className="card-body">
        <span className="card-category">{product.category}</span>
        <h3 className="card-title">{product.name}</h3>
        <p className="card-desc">{product.short_description}</p>
        <span className="card-price">{formatPrice(product.price)}</span>
      </div>
    </Link>
  )
}
