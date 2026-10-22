// Lets any page open the Bulldog chat (e.g. "Ask Bulldog about this item").
export const OPEN_BULLDOG = 'bulldog:open'

export const openBulldog = () => window.dispatchEvent(new Event(OPEN_BULLDOG))
