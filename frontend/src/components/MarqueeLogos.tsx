import React from 'react'

interface PlatformItem {
  id: string
  name: string
  prompt: string
  icon: React.ReactNode
}

export const PLATFORMS_DATA: PlatformItem[] = [
  {
    id: 'youtube',
    name: 'YouTube',
    prompt: 'Paste a YouTube video or Shorts link (up to 4K)...',
    icon: (
      <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none">
        <path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814z" fill="#FF0000"/>
        <path d="M9.545 15.568V8.432L15.818 12l-6.273 3.568z" fill="#FFFFFF"/>
      </svg>
    ),
  },
  {
    id: 'instagram',
    name: 'Instagram',
    prompt: 'Paste an Instagram Reel, Post, or Carousel link...',
    icon: (
      <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none">
        <defs>
          <radialGradient id="ig-grad-marquee" cx="20%" cy="110%" r="130%">
            <stop offset="0%" stopColor="#ffdb8b"/>
            <stop offset="25%" stopColor="#fc6a44"/>
            <stop offset="50%" stopColor="#c72d8f"/>
            <stop offset="100%" stopColor="#7720a4"/>
          </radialGradient>
        </defs>
        <rect width="24" height="24" rx="6" fill="url(#ig-grad-marquee)"/>
        <rect x="5.2" y="5.2" width="13.6" height="13.6" rx="3.8" stroke="#ffffff" strokeWidth="1.7" fill="none"/>
        <circle cx="12" cy="12" r="3.2" stroke="#ffffff" strokeWidth="1.7" fill="none"/>
        <circle cx="15.8" cy="8.2" r="0.9" fill="#ffffff"/>
      </svg>
    ),
  },
  {
    id: 'tiktok',
    name: 'TikTok',
    prompt: 'Paste a TikTok video link for watermark-free download...',
    icon: (
      <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
        <path d="M19.59 6.69a4.83 4.83 0 0 1-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 0 1-5.2 1.74 2.89 2.89 0 0 1 2.31-4.64c.29 0 .58.04.86.12V9.42a6.34 6.34 0 0 0-.86-.06 6.34 6.34 0 0 0-6.34 6.34 6.34 6.34 0 0 0 6.34 6.34 6.34 6.34 0 0 0 6.34-6.34V9.08a8.2 8.2 0 0 0 4.77 1.52V7.15a4.85 4.85 0 0 1-1-.46z" fill="#000000"/>
      </svg>
    ),
  },
  {
    id: 'pinterest',
    name: 'Pinterest',
    prompt: 'Paste a Pinterest Pin or Multi-Image Story link...',
    icon: (
      <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none">
        <circle cx="12" cy="12" r="12" fill="#E60023"/>
        <path d="M12.017 3C7.05 3 3 7.05 3 12.017c0 3.82 2.378 7.086 5.744 8.358-.08-.707-.152-1.794.032-2.568.165-.701 1.066-4.516 1.066-4.516s-.272-.544-.272-1.35c0-1.264.733-2.208 1.644-2.208.775 0 1.15.582 1.15 1.28 0 .78-.496 1.947-.753 3.028-.214.907.453 1.647 1.348 1.647 1.618 0 2.862-1.706 2.862-4.17 0-2.18-1.566-3.704-3.803-3.704-2.593 0-4.115 1.945-4.115 3.956 0 .783.301 1.623.678 2.08.075.09.086.169.063.26-.069.288-.224.912-.255 1.04-.04.168-.135.204-.312.123-1.166-.543-1.894-2.25-1.894-3.62 0-2.95 2.144-5.66 6.182-5.66 3.246 0 5.768 2.313 5.768 5.405 0 3.226-2.033 5.823-4.855 5.823-.948 0-1.84-.493-2.146-1.077l-.584 2.227c-.211.814-.783 1.834-1.167 2.456.88.272 1.815.42 2.784.42 4.967 0 9.017-4.05 9.017-9.017C21.034 7.05 16.984 3 12.017 3z" fill="#FFFFFF"/>
      </svg>
    ),
  },
  {
    id: 'twitter',
    name: 'Twitter / X',
    prompt: 'Paste an X / Twitter video, photo, or GIF link...',
    icon: (
      <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="currentColor">
        <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" fill="#000000"/>
      </svg>
    ),
  },
  {
    id: 'terabox',
    name: 'TeraBox',
    prompt: 'Paste a TeraBox cloud video or file share link...',
    icon: (
      <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none">
        <path d="M19.35 10.04C18.67 6.59 15.64 4 12 4 9.11 4 6.6 5.64 5.35 8.04 2.34 8.36 0 10.91 0 14c0 3.31 2.69 6 6 6h13c2.76 0 5-2.24 5-5 0-2.64-2.05-4.78-4.65-4.96z" fill="#2B7DE9"/>
        <rect x="9.5" y="11" width="5" height="5" rx="1.2" fill="#FFFFFF"/>
      </svg>
    ),
  },
  {
    id: 'facebook',
    name: 'Facebook',
    prompt: 'Paste a Facebook Video or Reel link...',
    icon: (
      <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none">
        <circle cx="12" cy="12" r="12" fill="#1877F2"/>
        <path d="M15.117 12.5l.526-3.428h-3.29V6.848c0-.939.26-1.579 1.607-1.579h1.718V2.203A23.013 23.013 0 0 0 13.17 2c-2.479 0-4.177 1.513-4.177 4.293v2.78H6v3.428h3v8.5a12.04 12.04 0 0 0 3 0v-8.5h3.117z" fill="#FFFFFF"/>
      </svg>
    ),
  },
  {
    id: 'reddit',
    name: 'Reddit',
    prompt: 'Paste a Reddit video or gallery post link...',
    icon: (
      <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none">
        <circle cx="12" cy="12" r="12" fill="#FF4500"/>
        <path d="M19.78 12.22a1.69 1.69 0 0 0-2.88-1.2 7.74 7.74 0 0 0-4.65-1.46l.79-3.73 2.58.55a1.19 1.19 0 1 0 1.25-1.07 1.18 1.18 0 0 0-1.16.92l-2.88-.61a.3.3 0 0 0-.35.22l-.93 4.39a7.84 7.84 0 0 0-4.8 1.45 1.7 1.7 0 0 0-2.09 2.58 3.51 3.51 0 0 0-.08.77c0 2.76 3.22 5 7.19 5s7.19-2.24 7.19-5a3.51 3.51 0 0 0-.08-.77 1.7 1.7 0 0 0 .91-1.04zm-10.74.87a1.19 1.19 0 1 1 1.19 1.19 1.19 1.19 0 0 1-1.19-1.19zm6.85 3.32a4.42 4.42 0 0 1-3.89 0 .29.29 0 0 1 .28-.51 3.86 3.86 0 0 0 3.33 0 .29.29 0 0 1 .28.51zm-.94-2.13a1.19 1.19 0 1 1 1.19-1.19 1.19 1.19 0 0 1-1.19 1.19z" fill="#FFFFFF"/>
      </svg>
    ),
  },
  {
    id: 'soundcloud',
    name: 'SoundCloud',
    prompt: 'Paste a SoundCloud track or album link to extract 320kbps MP3...',
    icon: (
      <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none">
        <rect width="24" height="24" rx="6" fill="#FF5500"/>
        <path d="M6 14.5a.75.75 0 0 1-.75-.75v-3.5a.75.75 0 0 1 1.5 0v3.5a.75.75 0 0 1-.75.75zm2.5 1a.75.75 0 0 1-.75-.75v-5.5a.75.75 0 0 1 1.5 0v5.5a.75.75 0 0 1-.75.75zm2.5.5a.75.75 0 0 1-.75-.75v-7.5a.75.75 0 0 1 1.5 0v7.5a.75.75 0 0 1-.75.75zm7.5-2.5a3.25 3.25 0 0 0-2.4-3.13 4 4 0 0 0-7.1 1.63v4.5h9.5a2.5 2.5 0 0 0 0-5z" fill="#FFFFFF"/>
      </svg>
    ),
  },
  {
    id: 'vimeo',
    name: 'Vimeo',
    prompt: 'Paste a Vimeo video link...',
    icon: (
      <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none">
        <rect width="24" height="24" rx="6" fill="#1AB7EA"/>
        <path d="M18.8 8.4c-.1 2.2-1.6 5.3-4.6 9.1-3.1 3.9-5.7 5.9-7.8 5.9-1.3 0-2.3-1.2-3.2-3.7-.6-2.3-1.1-4.5-1.8-6.7-.6-2.2-1.3-3.3-2-3.3-.2 0-.8.4-1.7 1.1l-.8-1.1c1.3-1.1 2.5-2.3 3.8-3.4 1.6-1.4 2.8-2.2 3.7-2.2 2 0 3.2 1.4 3.6 4.2.4-3.4 2.2-5.1 5.3-5.1 2.4 0 3.5 1.1 3.5 3.4 0 .8-.1 1.6-.3 2.5z" fill="#FFFFFF" transform="scale(0.8) translate(3, 3)"/>
      </svg>
    ),
  },
  {
    id: 'twitch',
    name: 'Twitch',
    prompt: 'Paste a Twitch clip or VOD link...',
    icon: (
      <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none">
        <path d="M2.143 0L.714 3.571v17.143h5.715V24h3.571l3.572-3.286h4.285L23.286 15V0H2.143zm19.285 13.929l-3.214 3.214h-4.643l-3.214 3.214v-3.214H5.357V2.143h16.071v11.786zm-8.571-7.143h2.143v6.429h-2.143V6.786zm-5.357 0h2.143v6.429H7.5V6.786z" fill="#9146FF"/>
      </svg>
    ),
  },
]

interface MarqueeLogosProps {
  onSelect: (name: string, promptText: string) => void
}

export const MarqueeLogos: React.FC<MarqueeLogosProps> = ({ onSelect }) => {
  // Duplicate array once for seamless infinite loop
  const duplicated = [...PLATFORMS_DATA, ...PLATFORMS_DATA]

  return (
    <div className="relative w-full overflow-hidden py-1.5 select-none">
      {/* Left / Right Soft Edge Fades */}
      <div className="absolute left-0 top-0 bottom-0 w-8 bg-gradient-to-r from-[#F4F4F7] to-transparent z-10 pointer-events-none" />
      <div className="absolute right-0 top-0 bottom-0 w-8 bg-gradient-to-l from-[#F4F4F7] to-transparent z-10 pointer-events-none" />

      {/* Marquee Track */}
      <div className="animate-marquee-smooth flex items-center gap-2">
        {duplicated.map((p, idx) => (
          <button
            key={`${p.id}-${idx}`}
            onClick={() => onSelect(p.name, p.prompt)}
            className="flex items-center gap-2 px-3 py-1.5 bg-white border border-black/[0.07] hover:border-[#FF4D26] rounded-full shadow-2xs hover:shadow-xs transition-all active:scale-95 flex-shrink-0 group cursor-pointer"
          >
            <div className="flex-shrink-0 flex items-center justify-center transition-transform group-hover:scale-110">
              {p.icon}
            </div>
            <span className="text-[11px] font-display font-bold text-[#0F0F12] group-hover:text-[#FF4D26] transition-colors whitespace-nowrap">
              {p.name}
            </span>
          </button>
        ))}
      </div>
    </div>
  )
}

