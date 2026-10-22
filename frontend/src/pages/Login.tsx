import { useState, type FormEvent } from 'react'
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../AuthContext'

export default function Login() {
  const { user, login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  // Send shoppers back to the page they came from (set by links that require login).
  const from = (location.state as { from?: string } | null)?.from ?? '/'
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  if (user && !submitting) return <Navigate to={from} replace />

  const onSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    const data = new FormData(e.currentTarget)
    setError('')
    setSubmitting(true)
    try {
      await login(String(data.get('email')), String(data.get('password')))
      navigate(from, { replace: true })
    } catch (err) {
      setError((err as Error).message)
      setSubmitting(false)
    }
  }

  return (
    <div className="container section auth">
      <h1 className="page-title">Log In</h1>
      <p className="page-sub">Welcome back, Bulldog.</p>
      <form className="form" onSubmit={onSubmit}>
        <label>
          Email
          <input type="email" name="email" autoComplete="email" required autoFocus />
        </label>
        <label>
          Password
          <input type="password" name="password" autoComplete="current-password" required />
        </label>
        {error && <p className="notice error" role="alert">{error}</p>}
        <button className="btn btn-block" type="submit" disabled={submitting}>
          {submitting ? 'Logging in…' : 'Log In'}
        </button>
      </form>
      <p className="auth-switch">
        New to Campus Customs? <Link to="/create-account" state={{ from }}>Create an account</Link>
      </p>
    </div>
  )
}
