import { useEffect, useState } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import { chatHistory, clearChatHistory, formatDate, store, type AccountSummary, type HistoryMessage } from '../api'
import { useAuth } from '../AuthContext'
import { useChatResults } from '../ChatResultsContext'
import { openBulldog } from '../chatEvents'

export default function Account() {
  const { user, loading, logout } = useAuth()
  const { clear: clearResults } = useChatResults()
  const navigate = useNavigate()
  const [account, setAccount] = useState<AccountSummary | null>(null)
  const [history, setHistory] = useState<HistoryMessage[]>([])
  const [error, setError] = useState('')

  useEffect(() => {
    if (!user) return
    store.account().then(setAccount).catch(() => setError("We couldn't load your account."))
    chatHistory().then((h) => setHistory(h.messages)).catch(() => {})
  }, [user])

  if (loading) return <div className="container section"><p className="notice">Loading…</p></div>
  if (!user) return <Navigate to="/login" replace state={{ from: '/account' }} />

  const removeAlert = async (id: number) => {
    await store.deleteAlert(id).catch(() => {})
    setAccount((a) => a && { ...a, restock_alerts: a.restock_alerts.filter((r) => r.id !== id) })
  }
  const clearChat = async () => {
    if (!window.confirm("Delete your saved chat with Bulldog? This removes it from your account and can't be undone.")) return
    await clearChatHistory().catch(() => {})
    setHistory([])
    clearResults()
    setAccount((a) => a && { ...a, saved_messages: 0 })
    window.location.reload() // so the chat widget forgets the cleared messages too
  }
  const signOut = async () => {
    navigate('/') // leave first, so this page doesn't redirect to Log In
    await logout()
  }

  return (
    <div className="container section account">
      <h1 className="page-title">My Account</h1>
      <p className="page-sub">Welcome back, {user.first_name}.</p>
      {error && <p className="notice error">{error}</p>}

      <div className="account-grid">
        <section className="account-card">
          <h2>Profile</h2>
          <dl>
            <dt>Name</dt><dd>{user.first_name} {user.last_name}</dd>
            <dt>Email</dt><dd>{user.email}</dd>
            {account && <><dt>Member since</dt><dd>{new Date(account.member_since.replace(' ', 'T') + 'Z').toLocaleDateString()}</dd></>}
          </dl>
          <button className="btn btn-outline btn-small" onClick={signOut}>Sign Out</button>
        </section>

        <section className="account-card">
          <h2>Restock alerts</h2>
          {!account ? <p className="muted">Loading…</p> : account.restock_alerts.length === 0 ? (
            <p className="muted">No alerts. On a product page, select a sold-out size and click <em>Notify me</em>.</p>
          ) : (
            <ul className="alert-list">
              {account.restock_alerts.map((a) => (
                <li key={a.id}>
                  <Link to={`/products/${a.product_id}`}>{a.product_name}</Link> · size {a.size}
                  <button className="link-button" onClick={() => removeAlert(a.id)}>Cancel</button>
                </li>
              ))}
            </ul>
          )}
        </section>

        <section className="account-card">
          <h2>Bulldog discount</h2>
          {!account ? <p className="muted">Loading…</p> : !account.discount ? (
            <p className="muted">No code yet. Say <strong>"Boola Boola"</strong> to Bulldog in the chat to unlock one (once a year).</p>
          ) : (
            <p>
              <strong className="discount-code">{account.discount.code}</strong> · {account.discount.percent_off}% off ·{' '}
              {account.discount.status === 'active'
                ? <>valid until {formatDate(account.discount.expires_at)} · <Link to="/cart">use it in your cart</Link></>
                : account.discount.status === 'expired' ? <>expired {formatDate(account.discount.expires_at)}</> : 'used'}
            </p>
          )}
        </section>

        <section className="account-card account-chat">
          <h2>Chat history with Bulldog</h2>
          <p className="muted">Chats are auto saved for 30 days (up to 200 messages).</p>
          {history.length === 0 ? (
            <p className="muted">No saved chats. <button className="link-button" onClick={openBulldog}>Ask Bulldog something</button></p>
          ) : (
            <>
              <ol className="history-list">
                {history.map((m, i) => (
                  <li key={i} className={m.role}>
                    <span className="history-who">{m.role === 'user' ? 'You' : 'Bulldog'}</span>
                    <span className="history-text">{m.content.replace(/\*\*/g, '')}</span>
                  </li>
                ))}
              </ol>
              <button className="btn btn-outline btn-small" onClick={clearChat}>Clear Chat History</button>
            </>
          )}
        </section>
      </div>
    </div>
  )
}
