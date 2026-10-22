import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'
import type { CartItem } from './api'

const KEY = 'cc_cart'
const MAX_QTY = 10

interface CartState {
  items: CartItem[]
  count: number
  add: (product_id: string, size: string, quantity: number) => void
  setQuantity: (product_id: string, size: string, quantity: number) => void
  remove: (product_id: string, size: string) => void
  clear: () => void
}

const CartContext = createContext<CartState | null>(null)

function load(): CartItem[] {
  try {
    const parsed = JSON.parse(localStorage.getItem(KEY) ?? '[]')
    return Array.isArray(parsed) ? parsed.filter((i) => i && i.product_id && i.size && i.quantity > 0) : []
  } catch {
    return []
  }
}

// The cart lives in this browser (localStorage) and holds only ids, sizes and quantities.
// Prices and stock are always re-read from the server when the cart is shown.
export function CartProvider({ children }: { children: ReactNode }) {
  const [items, setItems] = useState<CartItem[]>(load)
  useEffect(() => localStorage.setItem(KEY, JSON.stringify(items)), [items])

  const same = (i: CartItem, id: string, size: string) => i.product_id === id && i.size === size
  const value: CartState = {
    items,
    count: items.reduce((n, i) => n + i.quantity, 0),
    add: (id, size, quantity) =>
      setItems((cur) =>
        cur.some((i) => same(i, id, size))
          ? cur.map((i) => (same(i, id, size) ? { ...i, quantity: Math.min(MAX_QTY, i.quantity + quantity) } : i))
          : [...cur, { product_id: id, size, quantity: Math.min(MAX_QTY, quantity) }],
      ),
    setQuantity: (id, size, quantity) =>
      setItems((cur) => cur.map((i) => (same(i, id, size) ? { ...i, quantity: Math.max(1, Math.min(MAX_QTY, quantity)) } : i))),
    remove: (id, size) => setItems((cur) => cur.filter((i) => !same(i, id, size))),
    clear: () => setItems([]),
  }
  return <CartContext.Provider value={value}>{children}</CartContext.Provider>
}

export function useCart() {
  const ctx = useContext(CartContext)
  if (!ctx) throw new Error('useCart must be used inside <CartProvider>')
  return ctx
}
