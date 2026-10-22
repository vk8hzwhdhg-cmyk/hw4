// Types and fetch helpers for the FastAPI backend (backend/main.py).

export type StockStatus = 'in stock' | 'low stock' | 'sold out'

export interface SizeStock {
  size: string
  quantity: number
  status: StockStatus
}

export interface ProductSummary {
  product_id: string
  name: string
  category: string
  garment_type: string
  description: string
  colors: string[]
  price: number
  image_url: string
  total_stock: number
}

export interface ProductDetail extends ProductSummary {
  search_tags: string[]
  sizes: SizeStock[]
}

export interface Category {
  category: string
  count: number
}

export interface Collection {
  collection: string
  count: number
}

export interface User {
  id: number
  first_name: string
  last_name: string
  email: string
}

export interface RegisterInput {
  first_name: string
  last_name: string
  email: string
  password: string
  confirm_password: string
}

async function get<T>(path: string): Promise<T> {
  const res = await fetch(path)
  if (!res.ok) throw new Error(res.status === 404 ? 'Not found' : `Request failed (${res.status})`)
  return res.json() as Promise<T>
}

// POST JSON; on error, throw the backend's friendly `detail` message.
async function post<T>(path: string, body?: unknown): Promise<T> {
  const res = await fetch(path, {
    method: 'POST',
    headers: body ? { 'Content-Type': 'application/json' } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  })
  if (!res.ok) {
    const data = await res.json().catch(() => null)
    throw new Error(typeof data?.detail === 'string' ? data.detail : 'Something went wrong. Please try again.')
  }
  return (res.status === 204 ? undefined : await res.json()) as T
}

// What every product card renders: the Products grid, Home, Bulldog's picks and the chat.
// For chat results this is exactly the server's ProductCard (backend/models.py).
export interface CardData {
  product_id: string
  name: string
  category: string
  price: number
  image_url: string
  short_description: string
  in_stock: boolean
}

export interface ChatProductCard extends CardData {
  colors: string[]
}

export const toCard = (p: ProductSummary): CardData => ({
  product_id: p.product_id,
  name: p.name,
  category: p.category,
  price: p.price,
  image_url: p.image_url,
  short_description: shortDescription(p.description),
  in_stock: p.total_stock > 0,
})

export interface ChatTurn {
  role: 'user' | 'assistant'
  content: string
  product_ids?: string[]
}

// Where the shopper is when they send a message (PageContext in backend/models.py).
export interface PageContext {
  path: string
  product_id?: string
  category?: string
  search?: string
}

export interface HistoryMessage {
  role: 'user' | 'assistant'
  content: string
  results_title: string | null
  products: ChatProductCard[]
  created_at: string
}

// API contract for POST /api/chat (ChatResponse in backend/models.py).
export interface ChatResponse {
  reply: string
  results_title: string | null
  products: ChatProductCard[]
  redacted: string[]
  safe_message: string | null
}

export const chat = (message: string, history: ChatTurn[], page: PageContext) =>
  post<ChatResponse>('/api/chat', { message, history, page })

// Saved chat for logged-in shoppers (the session cookie identifies them).
export const chatHistory = () => get<{ messages: HistoryMessage[] }>('/api/chat/history')
export const clearChatHistory = async () => {
  const res = await fetch('/api/chat/history', { method: 'DELETE' })
  if (!res.ok) throw new Error('Could not clear chat history.')
}

// ---- cart, restock alerts, account, size guide ----

export interface CartItem {
  product_id: string
  size: string
  quantity: number
}

export interface CartLine {
  product_id: string
  name: string | null
  size: string
  price: number | null
  image_url: string | null
  quantity: number
  requested: number
  available: number
  line_total: number
  status: 'ok' | 'limited' | 'sold_out' | 'unavailable'
  message: string | null
}

export interface AppliedDiscount {
  code: string
  percent_off: number
  amount: number
  expires_at: string
}

export interface CartQuote {
  lines: CartLine[]
  item_count: number
  subtotal: number
  discount?: AppliedDiscount | null
  discount_error?: string | null
  total?: number
}

export interface DiscountInfo {
  code: string
  percent_off: number
  issued_at: string
  expires_at: string
  status: 'active' | 'expired' | 'redeemed'
}

export interface RestockAlert {
  id: number
  product_id: string
  product_name: string
  size: string
  created_at: string
}

export interface AccountSummary {
  first_name: string
  last_name: string
  email: string
  member_since: string
  saved_messages: number
  restock_alerts: RestockAlert[]
  discount: DiscountInfo | null
}

export interface SizeChart {
  label: string
  applies_to: string[]
  columns: string[]
  sizes: Record<string, number[] | null>
}

export interface SizeGuide {
  title: string
  note: string
  fit_note: string
  how_to_measure: string
  body_chest_inches: Record<string, string | null>
  charts: Record<string, SizeChart>
}

async function del(path: string): Promise<void> {
  const res = await fetch(path, { method: 'DELETE' })
  if (!res.ok) throw new Error('Something went wrong. Please try again.')
}

export const store = {
  quote: (items: CartItem[], discount_code?: string) => post<CartQuote>('/api/cart/quote', { items, discount_code }),
  sizeGuide: () => get<SizeGuide>('/api/size-guide'),
  notifyMe: (product_id: string, size: string, email?: string) =>
    post<RestockAlert>('/api/restock-alerts', { product_id, size, email }),
  deleteAlert: (id: number) => del(`/api/restock-alerts/${id}`),
  account: () => get<AccountSummary>('/api/account'),
}

export const auth = {
  me: () => get<User | null>('/api/auth/me'),
  login: (email: string, password: string) => post<User>('/api/auth/login', { email, password }),
  register: (input: RegisterInput) => post<User>('/api/auth/register', input),
  logout: () => post<void>('/api/auth/logout'),
}

export const api = {
  products: (params: { category?: string; q?: string; collection?: string } = {}) => {
    const qs = new URLSearchParams(
      Object.entries(params).filter((e): e is [string, string] => Boolean(e[1])),
    ).toString()
    return get<ProductSummary[]>(`/api/products${qs ? `?${qs}` : ''}`)
  },
  product: (id: string) => get<ProductDetail>(`/api/products/${encodeURIComponent(id)}`),
  categories: () => get<Category[]>('/api/categories'),
  collections: () => get<Collection[]>('/api/collections'),
}

// Server timestamps are UTC "YYYY-MM-DD HH:MM:SS".
export const formatDate = (ts: string) =>
  new Date(ts.replace(' ', 'T') + 'Z').toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })

export const formatPrice = (price: number) =>
  price.toLocaleString('en-US', { style: 'currency', currency: 'USD' })

// First sentence of a description, for product cards.
export const shortDescription = (text: string) => {
  const first = text.split(/(?<=\.)\s/)[0]
  return first.length > 120 ? `${first.slice(0, 117).trimEnd()}…` : first
}
