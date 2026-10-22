import { Link } from 'react-router-dom'

export default function Footer() {
  return (
    <footer className="site-footer">
      <div className="container footer-grid">
        <div>
          <h3>Come Visit Us!</h3>
          <p>
            57 Broadway
            <br />
            New Haven, CT 06511
          </p>
        </div>
        <div>
          <h3>Shop</h3>
          <ul>
            <li><Link to="/products">All Products</Link></li>
            <li><Link to="/products?category=Hoodies">Hoodies</Link></li>
            <li><Link to="/products?category=Crewnecks">Crewnecks</Link></li>
            <li><Link to="/products?category=T-Shirts">T-Shirts</Link></li>
          </ul>
        </div>
        <div>
          <h3>Campus Customs</h3>
          <ul>
            <li><Link to="/about">About Us</Link></li>
            <li><Link to="/login">Log In</Link></li>
            <li><Link to="/create-account">Create Account</Link></li>
          </ul>
        </div>
      </div>
      <p className="container copyright">
        © {new Date().getFullYear()} Yale Bulldog Blue by Campus Customs. Officially Licensed
        Merchandise.
      </p>
    </footer>
  )
}
