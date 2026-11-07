import React, { useState, useEffect } from 'react'
import { motion } from 'framer-motion'

const STATUS_STEPS = [
  'Detecting media source & platform...',
  'Resolving direct video & audio streams...',
  'Extracting highest resolution assets (up to 4K)...',
  'Analyzing photo gallery & uncompressed files...',
]

const PLATFORM_EMOJIS = ['▶️', '📸', '🎵', '📌', '𝕏', '☁️', '🤖']

export const FetchingLoader: React.FC = () => {
  const [stepIdx, setStepIdx] = useState(0)
  const [emojiIdx, setEmojiIdx] = useState(0)

  useEffect(() => {
    const stepTimer = setInterval(() => {
      setStepIdx((prev) => (prev + 1) % STATUS_STEPS.length)
    }, 1200)

    const emojiTimer = setInterval(() => {
      setEmojiIdx((prev) => (prev + 1) % PLATFORM_EMOJIS.length)
    }, 600)

    return () => {
      clearInterval(stepTimer)
      clearInterval(emojiTimer)
    }
  }, [])

  return (
    <motion.div
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 15 }}
      className="bg-white rounded-[26px] border border-black/[0.06] p-6 shadow-xs space-y-5 overflow-hidden relative"
    >
      {/* Background Ambient Glow */}
      <div className="absolute -top-10 -right-10 w-36 h-36 bg-[#FF4D26]/10 rounded-full blur-3xl pointer-events-none animate-pulse" />
      <div className="absolute -bottom-10 -left-10 w-36 h-36 bg-blue-500/10 rounded-full blur-3xl pointer-events-none animate-pulse" />

      {/* Center Radar / Spinning Icon */}
      <div className="flex flex-col items-center justify-center py-4 space-y-4">
        <div className="relative w-20 h-20 flex items-center justify-center">
          {/* Pulsing Outer Rings */}
          <motion.div
            className="absolute inset-0 rounded-full border-2 border-[#FF4D26]/30"
            animate={{ scale: [1, 1.35, 1], opacity: [0.8, 0, 0.8] }}
            transition={{ repeat: Infinity, duration: 1.8, ease: 'easeInOut' }}
          />
          <motion.div
            className="absolute inset-0 rounded-full border border-blue-500/20"
            animate={{ scale: [1, 1.6, 1], opacity: [0.6, 0, 0.6] }}
            transition={{ repeat: Infinity, duration: 2.4, ease: 'easeInOut', delay: 0.3 }}
          />

          {/* Central Rotating Card */}
          <motion.div
            className="w-14 h-14 rounded-2xl bg-[#0F0F12] text-white flex items-center justify-center text-2xl shadow-lg relative z-10"
            animate={{ rotate: [0, 10, -10, 0] }}
            transition={{ repeat: Infinity, duration: 3, ease: 'easeInOut' }}
          >
            <span>{PLATFORM_EMOJIS[emojiIdx]}</span>
          </motion.div>
        </div>

        {/* Dynamic Status Text */}
        <div className="text-center space-y-1">
          <h4 className="font-display font-extrabold text-sm text-[#0F0F12] flex items-center justify-center gap-1.5">
            <span>Extracting Media</span>
            <span className="flex gap-0.5">
              <motion.span animate={{ opacity: [0, 1, 0] }} transition={{ repeat: Infinity, duration: 1.2, delay: 0 }}>.</motion.span>
              <motion.span animate={{ opacity: [0, 1, 0] }} transition={{ repeat: Infinity, duration: 1.2, delay: 0.2 }}>.</motion.span>
              <motion.span animate={{ opacity: [0, 1, 0] }} transition={{ repeat: Infinity, duration: 1.2, delay: 0.4 }}>.</motion.span>
            </span>
          </h4>
          <p className="text-xs text-neutral-500 font-medium h-4 transition-all duration-300">
            {STATUS_STEPS[stepIdx]}
          </p>
        </div>
      </div>

      {/* Shimmering Skeleton Preview Box */}
      <div className="p-3 bg-[#FAFAFC] border border-black/[0.04] rounded-2xl flex gap-3.5 items-center animate-pulse">
        <div className="w-20 h-16 rounded-xl bg-neutral-200/80 flex-shrink-0" />
        <div className="flex-1 space-y-2">
          <div className="h-3.5 bg-neutral-200/80 rounded-md w-3/4" />
          <div className="h-2.5 bg-neutral-200/60 rounded-md w-1/2" />
        </div>
      </div>
    </motion.div>
  )
}

