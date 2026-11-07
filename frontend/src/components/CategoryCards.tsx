import React from 'react'

interface CategoryCardsProps {
  onSelect: (type: 'video' | 'audio' | 'image' | 'cloud', promptText: string) => void
}

export const CategoryCards: React.FC<CategoryCardsProps> = ({ onSelect }) => {
  const categories = [
    {
      id: 'video',
      title: 'Video',
      subtitle: 'YouTube, Reels, TikTok',
      badge: '4K Ultra HD',
      type: 'video' as const,
      prompt: 'Paste a Video link (YouTube, Instagram Reel, TikTok, Facebook, Twitter)...',
      iconBg: 'bg-[#10B981]', // Emerald / green
      icon: (
        <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
        </svg>
      ),
    },
    {
      id: 'audio',
      title: 'Audio',
      subtitle: 'MP3, 320kbps, WAV',
      badge: 'Studio Audio',
      type: 'audio' as const,
      prompt: 'Paste an Audio or Video link to extract MP3 (SoundCloud, YouTube, Podcasts)...',
      iconBg: 'bg-[#C026D3]', // Magenta / purple
      icon: (
        <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3" />
        </svg>
      ),
    },
    {
      id: 'cloud',
      title: 'Cloud Media',
      subtitle: 'TeraBox, Reddit, Vimeo',
      badge: 'Unlimited GB',
      type: 'cloud' as const,
      prompt: 'Paste a Cloud Storage or Social link (TeraBox, Reddit, Vimeo, Dailymotion)...',
      iconBg: 'bg-[#FF4D26]', // Coral / orange
      icon: (
        <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M3 15a4 4 0 004 4h9a5 5 0 10-.1-9.999 5.002 5.002 0 00-9.78 2.096A4.001 4.001 0 003 15z" />
        </svg>
      ),
    },
    {
      id: 'image',
      title: 'Images',
      subtitle: 'Pinterest, Carousels',
      badge: 'Original HD',
      type: 'image' as const,
      prompt: 'Paste a Pinterest Pin, Instagram Photo Carousel, or Twitter photo link...',
      iconBg: 'bg-[#3B82F6]', // Electric Blue
      icon: (
        <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
        </svg>
      ),
    },
  ]

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between px-1">
        <label className="text-[11px] font-display font-bold text-neutral-400 uppercase tracking-wider">
          Download by Category:
        </label>
        <span className="text-[10px] text-neutral-400 font-medium">Tap to paste</span>
      </div>

      <div className="grid grid-cols-2 gap-3">
        {categories.map((cat) => (
          <button
            key={cat.id}
            onClick={() => onSelect(cat.type, cat.prompt)}
            className="group relative bg-white border border-black/[0.06] hover:border-black/20 rounded-[22px] p-3.5 sm:p-4 text-left transition-all hover:shadow-md active:scale-96 shadow-2xs flex flex-col justify-between overflow-hidden"
          >
            {/* Top Row: Floating Icon & Info Badge */}
            <div className="flex items-center justify-between">
              <div
                className={`w-10 h-10 rounded-2xl ${cat.iconBg} flex items-center justify-center shadow-md transition-transform group-hover:scale-110`}
              >
                {cat.icon}
              </div>
              <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded-full bg-[#F4F4F7] text-neutral-600 border border-black/[0.04]">
                {cat.badge}
              </span>
            </div>

            {/* Bottom Row: Title and Subtitle */}
            <div className="mt-3.5 space-y-0.5">
              <h4 className="font-display font-extrabold text-sm text-[#0F0F12] group-hover:text-[#FF4D26] transition-colors flex items-center justify-between">
                <span>{cat.title}</span>
                <span className="opacity-0 group-hover:opacity-100 transition-opacity text-xs text-[#FF4D26]">
                  →
                </span>
              </h4>
              <p className="text-[10px] text-neutral-400 font-medium truncate">
                {cat.subtitle}
              </p>
            </div>
          </button>
        ))}
      </div>
    </div>
  )
}

