import { useState } from 'react'
import { Link, NavLink, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../AuthContext'
import { useCart } from '../CartContext'

const MAIN_LINKS = [
  { to: '/', label: 'Home', end: true },
  { to: '/products', label: 'Products' },
  { to: '/about', label: 'About Us' },
]

export default function NavBar() {
  const [open, setOpen] = useState(false)
  const close = () => setOpen(false)
  const { user, loading, logout } = useAuth()
  const { count } = useCart()
  const { pathname } = useLocation()
  const navigate = useNavigate()
  // After logging in, return to this page (but never back to an auth page).
  const from = pathname === '/login' || pathname === '/create-account' ? '/' : pathname

  const onLogout = async () => {
    close()
    await logout()
    navigate('/')
  }

  return (
    <header className="site-header">
      <nav className="nav container" aria-label="Main">
        <Link to="/" className="brand" onClick={close}>
          <span className="brand-mark">Y</span>
          <span className="brand-text">
            <span className="brand-name">Campus Customs</span>
            <span className="brand-sub">Yale Bulldog Blue</span>
          </span>
        </Link>

        <button
          className="nav-toggle"
          aria-expanded={open}
          aria-controls="nav-links"
          onClick={() => setOpen(!open)}
        >
          {open ? 'Close' : 'Menu'}
        </button>

        <div id="nav-links" className={`nav-links ${open ? 'open' : ''}`}>
          <ul className="nav-main">
            {MAIN_LINKS.map((l) => (
              <li key={l.to}>
                <NavLink to={l.to} end={l.end} onClick={close}>
                  {l.label}
                </NavLink>
              </li>
            ))}
          </ul>
          <ul className="nav-account">
            <li>
              <NavLink to="/cart" onClick={close} aria-label={`Cart, ${count} items`}>
                🛒 Cart{count > 0 && <span className="cart-count">{count}</span>}
              </NavLink>
            </li>
            {loading ? null : user ? (
              <>
                <li>
                  <NavLink to="/account" className="nav-greeting" onClick={close} title="My Account">
                    Hi, {user.first_name}
                  </NavLink>
                </li>
                <li>
                  <button className="btn btn-small btn-nav" onClick={onLogout}>
                    Log Out
                  </button>
                </li>
              </>
            ) : (
              <>
                <li>
                  <NavLink to="/login" state={{ from }} onClick={close}>Log In</NavLink>
                </li>
                <li>
                  <NavLink to="/create-account" state={{ from }} className="btn btn-small" onClick={close}>
                    Create Account
                  </NavLink>
                </li>
              </>
            )}
          </ul>
        </div>
      </nav>
    </header>
  )
}
