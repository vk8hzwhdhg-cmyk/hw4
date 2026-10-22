import { useState, type FormEvent } from 'react'
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../AuthContext'

export default function CreateAccount() {
  const { user, register } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const from = (location.state as { from?: string } | null)?.from ?? '/'
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  if (user && !submitting) return <Navigate to={from} replace />

  const onSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    const data = new FormData(e.currentTarget)
    const field = (name: string) => String(data.get(name) ?? '')
    if (field('password') !== field('confirm_password')) {
      setError('Passwords do not match.')
      return
    }
    setError('')
    setSubmitting(true)
    try {
      await register({
        first_name: field('first_name'),
        last_name: field('last_name'),
        email: field('email'),
        password: field('password'),
        confirm_password: field('confirm_password'),
      })
      navigate(from, { replace: true })
    } catch (err) {
      setError((err as Error).message)
      setSubmitting(false)
    }
  }

  return (
    <div className="container section auth">
      <h1 className="page-title">Create Account</h1>
      <p className="page-sub">Join the Campus Customs family.</p>
      <form className="form" onSubmit={onSubmit}>
        <div className="form-row">
          <label>
            First name
            <input name="first_name" autoComplete="given-name" maxLength={50} required autoFocus />
          </label>
          <label>
            Last name
            <input name="last_name" autoComplete="family-name" maxLength={50} required />
          </label>
        </div>
        <label>
          Email
          <input type="email" name="email" autoComplete="email" required />
        </label>
        <label>
          Password
          <input type="password" name="password" autoComplete="new-password" minLength={8} maxLength={128} required />
          <span className="hint">At least 8 characters.</span>
        </label>
        <label>
          Confirm password
          <input type="password" name="confirm_password" autoComplete="new-password" minLength={8} maxLength={128} required />
        </label>
        {error && <p className="notice error" role="alert">{error}</p>}
        <button className="btn btn-block" type="submit" disabled={submitting}>
          {submitting ? 'Creating account…' : 'Create Account'}
        </button>
      </form>
      <p className="auth-switch">
        Already have an account? <Link to="/login" state={{ from }}>Log in</Link>
      </p>
    </div>
  )
}
