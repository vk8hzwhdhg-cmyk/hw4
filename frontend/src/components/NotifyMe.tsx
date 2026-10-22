import { useState, type FormEvent } from 'react'
import { store } from '../api'
import { useAuth } from '../AuthContext'

// "Notify me when back in stock" for a sold-out size.
export default function NotifyMe({ productId, size }: { productId: string; size: string }) {
  const { user } = useAuth()
  const [email, setEmail] = useState('')
  const [done, setDone] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  const submit = async (e: FormEvent) => {
    e.preventDefault()
    setBusy(true)
    setError('')
    try {
      await store.notifyMe(productId, size, user ? undefined : email)
      setDone(`We'll email ${user ? user.email : email} when ${size} is back in stock.`)
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setBusy(false)
    }
  }

  if (done) return <p className="notify notify-done" role="status">✓ {done}</p>
  return (
    <form className="notify" onSubmit={submit}>
      <p className="notify-title">🔔 Sold out in {size}. Get an email when it's back.</p>
      <div className="notify-row">
        {!user && (
          <input type="email" required placeholder="Your email" value={email} aria-label="Email for restock alert"
                 onChange={(e) => setEmail(e.target.value)} />
        )}
        <button className="btn btn-small" type="submit" disabled={busy}>
          {user ? `Notify me at ${user.email}` : 'Notify me'}
        </button>
      </div>
      {error && <p className="notice error" role="alert">{error}</p>}
    </form>
  )
}
