import { useEffect, useRef, useState, type FormEvent, type ReactNode } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { chat, chatHistory, clearChatHistory, formatPrice, type ChatProductCard, type ChatTurn,
  type PageContext } from '../api'
import { useAuth } from '../AuthContext'
import { useChatResults } from '../ChatResultsContext'
import { OPEN_BULLDOG } from '../chatEvents'
import BulldogFace, { type BulldogMood } from './BulldogFace'

interface Message extends ChatTurn {
  products?: ChatProductCard[]
  notice?: string // e.g. "We removed a card number from your message"
}

// Quick questions that fit the page the shopper is on.
function quickQuestions(page: PageContext): string[] {
  if (page.product_id)
    return ['Is this in stock in my size?', 'What colors does this come in?', 'Show me similar items']
  if (page.category)
    return [`${page.category} under $60`, `Navy ${page.category.toLowerCase()}`, `Which ${page.category.toLowerCase()} are in stock in M?`]
  return ['Navy hoodies under $70', 'Residential college gear', 'Gifts for a Yale dad']
}

// Renders the small markdown subset the agent uses: **bold**, "- " bullets, line breaks.
function renderMarkdown(text: string): ReactNode {
  const inline = (line: string) =>
    line.split(/(\*\*[^*]+\*\*)/g).map((part, i) =>
      part.startsWith('**') && part.endsWith('**') ? <strong key={i}>{part.slice(2, -2)}</strong> : part,
    )
  const blocks: ReactNode[] = []
  let bullets: string[] = []
  const flush = () => {
    if (bullets.length) blocks.push(<ul key={blocks.length}>{bullets.map((b, i) => <li key={i}>{inline(b)}</li>)}</ul>)
    bullets = []
  }
  for (const line of text.split('\n')) {
    if (/^\s*[-*•]\s+/.test(line)) bullets.push(line.replace(/^\s*[-*•]\s+/, ''))
    else {
      flush()
      if (line.trim()) blocks.push(<p key={blocks.length}>{inline(line)}</p>)
    }
  }
  flush()
  return blocks
}

// Page context for the agent: which product, category or search the shopper is looking at.
function pageContext(pathname: string, search: string): PageContext {
  const params = new URLSearchParams(search)
  const productMatch = pathname.match(/^\/products\/([^/]+)$/)
  return {
    path: pathname,
    product_id: productMatch ? decodeURIComponent(productMatch[1]) : undefined,
    category: params.get('category') ?? undefined,
    search: params.get('q') ?? undefined,
  }
}

export default function ChatWidget() {
  const { user, loading } = useAuth()
  const { show, clear: clearResults } = useChatResults()
  const location = useLocation()
  const [open, setOpen] = useState(false)
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)
  const bodyRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  const launcherRef = useRef<HTMLButtonElement>(null)
  const page = pageContext(location.pathname, location.search)

  // Clicking the bulldog: it randomly winks, barks or licks (and opens/closes the chat).
  const [mood, setMood] = useState<BulldogMood>('idle')
  const moodTimer = useRef<number | undefined>(undefined)
  const BUBBLES: Record<Exclude<BulldogMood, 'idle'>, string> = { wink: '😉', bark: 'Woof! Woof!', lick: '*slurp*' }
  const onLauncherClick = () => {
    const pick = (['wink', 'bark', 'lick'] as const)[Math.floor(Math.random() * 3)]
    setMood(pick)
    window.clearTimeout(moodTimer.current)
    moodTimer.current = window.setTimeout(() => setMood('idle'), 1500)
    setOpen(!open)
  }

  // F1: "Ask Bulldog about this item" (and anything else) can open the chat.
  useEffect(() => {
    const onOpen = () => setOpen(true)
    window.addEventListener(OPEN_BULLDOG, onOpen)
    return () => window.removeEventListener(OPEN_BULLDOG, onOpen)
  }, [])

  // F2: focus the message box on open; Escape closes and returns focus to the Bulldog button
  // (after the panel is gone, since on phones the button is hidden while the chat is open);
  // lock page scroll on phones.
  const returnFocus = useRef(false)
  useEffect(() => {
    if (!open) {
      if (returnFocus.current) launcherRef.current?.focus()
      returnFocus.current = false
      return
    }
    inputRef.current?.focus()
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        returnFocus.current = true
        setOpen(false)
      }
    }
    window.addEventListener('keydown', onKey)
    document.body.classList.add('chat-open')
    return () => {
      window.removeEventListener('keydown', onKey)
      document.body.classList.remove('chat-open')
    }
  }, [open])

  // Logged in: reload saved history from the server. Logged out: start fresh (guests aren't saved).
  const userId = user?.id
  useEffect(() => {
    if (loading) return
    setMessages([])
    if (userId === undefined) return
    let cancelled = false
    chatHistory()
      .then(({ messages: saved }) => {
        if (!cancelled)
          setMessages(saved.map((m) => ({ role: m.role, content: m.content, products: m.products })))
      })
      .catch(() => {})
    return () => {
      cancelled = true
    }
  }, [userId, loading])

  // Clear for everyone: guests' chat only lives in this tab; logged-in history is deleted on the server.
  const clearChat = async () => {
    const question = user
      ? 'Delete your saved chat with Bulldog? This removes it from your account and can\'t be undone.'
      : 'Clear this chat with Bulldog?'
    if (!window.confirm(question)) return
    if (user) {
      try {
        await clearChatHistory()
      } catch {
        window.alert("Sorry, we couldn't delete your chat right now. Please try again.")
        return
      }
    }
    setMessages([])
    clearResults()
  }

  useEffect(() => {
    bodyRef.current?.scrollTo({ top: bodyRef.current.scrollHeight, behavior: 'smooth' })
  }, [messages, sending, open])

  const send = async (text: string) => {
    const message = text.trim()
    if (!message || sending) return
    // Guests send their in-tab history; for logged-in shoppers the server uses the saved copy.
    const history: ChatTurn[] = user
      ? []
      : messages.map(({ role, content, products }) => ({
          role, content, product_ids: products?.map((p) => p.product_id) ?? [],
        }))
    setMessages((m) => [...m, { role: 'user', content: message }])
    setInput('')
    setSending(true)
    try {
      const res = await chat(message, history, page)
      setMessages((m) => {
        const next = [...m]
        // B2: show the cleaned message instead of what was typed, with a short notice.
        if (res.safe_message) {
          next[next.length - 1] = {
            role: 'user', content: res.safe_message,
            notice: `🔒 For your security, we removed ${res.redacted.join(', ')} from your message.`,
          }
        }
        return [...next, { role: 'assistant', content: res.reply, products: res.products }]
      })
      // Render the agent's structured matches on the page as full product cards.
      // Skip it when the only match is the product already on screen (nothing new to show).
      const onlyCurrentItem = res.products.length === 1 && res.products[0].product_id === page.product_id
      if (res.products.length > 0 && !onlyCurrentItem) {
        show({ title: res.results_title ?? "Bulldog's picks", question: message, products: res.products })
      }
    } catch (err) {
      // e.g. the 20-messages-a-minute limit returns a friendly message from the server.
      const msg = (err as Error).message
      setMessages((m) => [...m, { role: 'assistant', content: msg.startsWith('Something went wrong') ? "Sorry, I couldn't reach the shop just now. Please try again." : msg }])
    } finally {
      setSending(false)
    }
  }

  const onSubmit = (e: FormEvent) => {
    e.preventDefault()
    send(input)
  }

  const greeting = `Woof! I'm Bulldog${user ? `. Welcome back, ${user.first_name}!` : '!'} Ask me about Yale gear, sizes, prices or what's in stock.`

  return (
    <div className="chat">
      {open && (
        <section className="chat-panel" role="dialog" aria-label="Bulldog chat">
          <header className="chat-header">
            <span className="chat-avatar" aria-hidden><BulldogFace size={34} /></span>
            <div>
              <strong>Bulldog</strong>
              <span className="chat-status">
                {user ? 'Chat auto saved to your account for 30 days' : 'Guest chat · not saved'}
              </span>
            </div>
            <button className="chat-close" aria-label="Close chat" onClick={() => setOpen(false)}>×</button>
          </header>

          <div className="chat-body" ref={bodyRef} aria-live="polite">
            <div className="chat-msg assistant"><div className="chat-bubble">{greeting}</div></div>
            {messages.length === 0 && (
              <div className="chat-suggestions">
                {quickQuestions(page).map((q) => <button key={q} className="chip" onClick={() => send(q)}>{q}</button>)}
              </div>
            )}
            {messages.map((m, i) => (
              <div key={i} className={`chat-msg ${m.role}`}>
                <div className="chat-bubble">{m.role === 'assistant' ? renderMarkdown(m.content) : m.content}</div>
                {m.notice && <p className="chat-notice">{m.notice}</p>}
                {m.products && m.products.length > 0 && (
                  <div className="chat-cards">
                    {m.products.map((p) => (
                      <Link key={p.product_id} to={`/products/${p.product_id}`} className="chat-card">
                        <img src={p.image_url} alt="" />
                        <span className="chat-card-name">{p.name}</span>
                        <span className="chat-card-price">{formatPrice(p.price)}{!p.in_stock && ' · Sold out'}</span>
                      </Link>
                    ))}
                  </div>
                )}
              </div>
            ))}
            {sending && <div className="chat-msg assistant"><div className="chat-bubble typing" aria-label="Bulldog is typing"><span /><span /><span /></div></div>}
          </div>

          {/* F1: on a product page, keep the item questions one tap away even mid-conversation. */}
          {page.product_id && messages.length > 0 && !sending && (
            <div className="chat-quick">
              {quickQuestions(page).map((q) => <button key={q} className="chip" onClick={() => send(q)}>{q}</button>)}
            </div>
          )}
          <form className="chat-input" onSubmit={onSubmit}>
            <button type="button" className="chat-clear" onClick={clearChat}
                    disabled={sending || messages.length === 0}
                    title={user ? 'Delete your saved chat' : 'Clear this chat'}>
              Clear Chat
            </button>
            <input ref={inputRef} value={input} onChange={(e) => setInput(e.target.value)} placeholder="Ask Bulldog…"
                   aria-label="Message" maxLength={1000} />
            <button type="submit" disabled={sending || !input.trim()}>Send</button>
          </form>
        </section>
      )}
      {mood !== 'idle' && <span className={`bulldog-bubble bubble-${mood}`} aria-hidden="true">{BUBBLES[mood]}</span>}
      <button ref={launcherRef} className={`chat-launcher launcher-${mood}`} data-interaction={mood}
              aria-label={open ? 'Close Bulldog chat' : 'Chat with Bulldog'}
              aria-expanded={open} onClick={onLauncherClick}>
        <BulldogFace mood={mood} size={50} />
      </button>
    </div>
  )
}
