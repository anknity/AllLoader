import React, { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'

interface SlideItem {
  id: string
  tag: string
  tagColor: string
  title: string
  subtitle: string
  gradient: string
  badgeText: string
  icon: string
  image: string
  targetType: 'video' | 'audio' | 'image'
  prompt: string
}

const SLIDES: SlideItem[] = [
  {
    id: 'video',
    tag: '4K ULTRA HD',
    tagColor: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30',
    title: 'Download Any Video up to 4K',
    subtitle: 'YouTube, Instagram Reels, TikTok, Facebook & Twitter watermark-free.',
    gradient: 'from-[#07130F]/95 via-[#0A231B]/85 to-[#050C0A]/95',
    badgeText: '2160p • 1080p • 60fps',
    icon: '🎬',
    image: '/banners/video_banner.jpg',
    targetType: 'video',
    prompt: 'Paste a Video link (YouTube, Instagram Reels, TikTok, Twitter)...',
  },
  {
    id: 'audio',
    tag: 'STUDIO SOUND',
    tagColor: 'bg-purple-500/20 text-purple-300 border-purple-500/30',
    title: 'Extract 320kbps MP3 & Lossless',
    subtitle: 'SoundCloud, YouTube Music, Podcasts & Audio in pure master quality.',
    gradient: 'from-[#13091B]/95 via-[#230F33]/85 to-[#0D0513]/95',
    badgeText: '320kbps • 192kbps • WAV',
    icon: '🎵',
    image: '/banners/audio_banner.jpg',
    targetType: 'audio',
    prompt: 'Paste an Audio or Song link (SoundCloud, YouTube Audio, Podcasts)...',
  },
  {
    id: 'image',
    tag: 'PHOTO & ALBUMS',
    tagColor: 'bg-blue-500/20 text-blue-300 border-blue-500/30',
    title: 'Pinterest & Instagram Carousels',
    subtitle: 'Extract all original uncompressed photos with one-click album batch saving.',
    gradient: 'from-[#081220]/95 via-[#0C2442]/85 to-[#050C16]/95',
    badgeText: 'Full Ultra HD • Batch Save',
    icon: '📸',
    image: '/banners/image_banner.jpg',
    targetType: 'image',
    prompt: 'Paste a Pinterest Pin, Instagram Photo Carousel, or Twitter photo link...',
  },
]

interface SlidingBannerProps {
  onSelectType: (type: 'video' | 'audio' | 'image', customPlaceholder?: string) => void
}

export const SlidingBanner: React.FC<SlidingBannerProps> = ({ onSelectType }) => {
  const [current, setCurrent] = useState(0)
  const [isPaused, setIsPaused] = useState(false)

  useEffect(() => {
    if (isPaused) return
    const timer = setInterval(() => {
      setCurrent((prev) => (prev + 1) % SLIDES.length)
    }, 4500)
    return () => clearInterval(timer)
  }, [isPaused])

  const slide = SLIDES[current]

  return (
    <div
      className="relative rounded-[26px] overflow-hidden border border-black/[0.08] shadow-sm select-none group"
      onMouseEnter={() => setIsPaused(true)}
      onMouseLeave={() => setIsPaused(false)}
      onTouchStart={() => setIsPaused(true)}
      onTouchEnd={() => setIsPaused(false)}
    >
      <AnimatePresence mode="wait">
        <motion.div
          key={slide.id}
          initial={{ opacity: 0, scale: 0.98 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.98 }}
          transition={{ duration: 0.4, ease: 'easeInOut' }}
          className={`relative p-5 sm:p-6 bg-gradient-to-br ${slide.gradient} text-white min-h-[180px] flex flex-col justify-between overflow-hidden`}
        >
          {/* Background Illustration Artwork */}
          {slide.image && (
            <img
              src={slide.image}
              alt={slide.title}
              className="absolute inset-0 w-full h-full object-cover opacity-35 mix-blend-screen scale-105 pointer-events-none transition-transform duration-1000 group-hover:scale-110"
            />
          )}

          {/* Top Tag & Badge */}
          <div className="flex items-center justify-between z-10">
            <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold font-mono tracking-wider border backdrop-blur-xs ${slide.tagColor}`}>
              {slide.tag}
            </span>
            <span className="text-[10px] font-mono font-bold text-white/80 bg-black/40 border border-white/10 px-2.5 py-0.5 rounded-full backdrop-blur-md">
              {slide.badgeText}
            </span>
          </div>

          {/* Middle Content */}
          <div className="my-2 z-10 max-w-[85%] space-y-1">
            <h3 className="font-display font-extrabold text-base sm:text-lg leading-tight flex items-center gap-2 drop-shadow-sm">
              <span className="text-xl">{slide.icon}</span>
              <span>{slide.title}</span>
            </h3>
            <p className="text-[11px] text-white/80 line-clamp-2 leading-relaxed font-medium">
              {slide.subtitle}
            </p>
          </div>

          {/* Bottom Action & Pagination Dots */}
          <div className="flex items-center justify-between pt-1 z-10">
            <button
              onClick={() => onSelectType(slide.targetType, slide.prompt)}
              className="px-3.5 py-1.5 bg-white text-[#0F0F12] hover:bg-[#FF4D26] hover:text-white rounded-xl text-[11px] font-display font-bold transition-all shadow-md flex items-center gap-1.5 active:scale-95"
            >
              <span>Paste & Download</span>
              <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M14 5l7 7m0 0l-7 7m7-7H3" />
              </svg>
            </button>

            {/* Dots */}
            <div className="flex items-center gap-1.5 bg-black/30 backdrop-blur-md px-2 py-1 rounded-full border border-white/10">
              {SLIDES.map((s, idx) => (
                <button
                  key={s.id}
                  onClick={() => setCurrent(idx)}
                  className={`h-1.5 rounded-full transition-all ${
                    idx === current ? 'w-5 bg-white shadow-xs' : 'w-1.5 bg-white/40 hover:bg-white/80'
                  }`}
                  aria-label={`Go to slide ${idx + 1}`}
                />
              ))}
            </div>
          </div>
        </motion.div>
      </AnimatePresence>
    </div>
  )
}
