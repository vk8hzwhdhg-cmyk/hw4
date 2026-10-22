import { Link } from 'react-router-dom'

export default function NotFound() {
  return (
    <div className="container section">
      <h1 className="page-title">Page not found</h1>
      <p className="page-sub">This page wandered off campus.</p>
      <Link to="/" className="btn">Back to Home</Link>
    </div>
  )
}
