export type BulldogMood = 'idle' | 'wink' | 'bark' | 'lick'

// A small drawn bulldog (Handsome Dan colors) whose eye, mouth and tongue can change.
export default function BulldogFace({ mood = 'idle', size = 40 }: { mood?: BulldogMood; size?: number }) {
  return (
    <svg viewBox="0 0 64 64" width={size} height={size} className={`bulldog bulldog-${mood}`} aria-hidden="true">
      {/* ears */}
      <path d="M9 21 C5 10 13 7 20 13 L23 20 Z" fill="#8a5a3c" />
      <path d="M55 21 C59 10 51 7 44 13 L41 20 Z" fill="#8a5a3c" />
      {/* head + jowls */}
      <path d="M32 13 C47 13 56 22 56 35 C56 47 46 56 32 56 C18 56 8 47 8 35 C8 22 17 13 32 13 Z" fill="#ead2b0" />
      <path d="M18 18 C22 16 26 16 29 18 L26 30 C22 28 19 24 18 18 Z" fill="#c99a6b" opacity=".55" />
      {/* brow wrinkles */}
      <path d="M25 22 Q32 19 39 22" stroke="#b5835b" strokeWidth="1.6" fill="none" strokeLinecap="round" />
      <path d="M27 25.5 Q32 23.5 37 25.5" stroke="#b5835b" strokeWidth="1.3" fill="none" strokeLinecap="round" />
      {/* white muzzle */}
      <ellipse cx="32" cy="43" rx="16" ry="11" fill="#fffaf2" />
      {/* eyes */}
      <circle cx="23.5" cy="32" r="3.4" fill="#1d1d1d" />
      <circle cx="24.6" cy="30.9" r="1" fill="#fff" />
      {mood === 'wink' ? (
        <path className="bulldog-wink-eye" d="M37 32.5 Q40.5 35.5 44 32.5" stroke="#1d1d1d" strokeWidth="2.2" fill="none" strokeLinecap="round" />
      ) : (
        <>
          <circle cx="40.5" cy="32" r="3.4" fill="#1d1d1d" />
          <circle cx="41.6" cy="30.9" r="1" fill="#fff" />
        </>
      )}
      {/* nose */}
      <path d="M26.5 37.5 C26.5 35 37.5 35 37.5 37.5 C37.5 40.5 34 41.5 32 41.5 C30 41.5 26.5 40.5 26.5 37.5 Z" fill="#2b1d16" />
      <ellipse cx="29.8" cy="37.3" rx="1.4" ry=".8" fill="#5a4136" />
      {/* mouth */}
      {mood === 'bark' ? (
        <path d="M24.5 45 Q32 57 39.5 45 Q32 48 24.5 45 Z" fill="#7a2230" stroke="#2b1d16" strokeWidth="1.2" strokeLinejoin="round" />
      ) : (
        <path d="M25 45 Q28.5 48.5 32 45 Q35.5 48.5 39 45" stroke="#2b1d16" strokeWidth="1.6" fill="none" strokeLinecap="round" />
      )}
      {/* underbite teeth */}
      <path d="M27.2 46.2 l1.3 -2.6 l1.3 2.6 Z M34.2 46.2 l1.3 -2.6 l1.3 2.6 Z" fill="#fff" stroke="#2b1d16" strokeWidth=".6" />
      {/* tongue (lick) */}
      {mood === 'lick' && (
        <path className="bulldog-tongue" d="M29 46.5 C29 55 35 55 35 46.5 Z" fill="#e8697b" stroke="#b8475a" strokeWidth=".8" />
      )}
      {/* navy collar with Y tag */}
      <path d="M17 54 Q32 61 47 54" stroke="#00366b" strokeWidth="3.4" fill="none" strokeLinecap="round" />
      <circle cx="32" cy="59" r="3" fill="#fff" stroke="#00366b" strokeWidth="1" />
      <text x="32" y="60.6" fontSize="4.2" fontFamily="Georgia, serif" fontWeight="700" textAnchor="middle" fill="#00366b">Y</text>
    </svg>
  )
}
