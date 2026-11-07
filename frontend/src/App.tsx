/**
 * All-in-One Media Downloader — Mobile Mini App
 *
 * Standalone, mobile-optimized media downloader for YouTube (up to 4K),
 * Instagram, TikTok, Pinterest (multi-photo albums), Twitter/X, TeraBox,
 * Reddit, Vimeo, SoundCloud, and 1000+ platforms.
 */

import React, { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import toast, { Toaster } from 'react-hot-toast'
import { SlidingBanner } from './components/SlidingBanner'
import { CategoryCards } from './components/CategoryCards'
import { FetchingLoader } from './components/FetchingLoader'
import { MarqueeLogos } from './components/MarqueeLogos'

// API endpoint (works with Vite proxy or direct to port 8001)
const API_BASE = import.meta.env.VITE_API_BASE || ''

// ── Platform Brand Styling ────────────────────────────────────
const PLATFORM_ICONS: Record<string, { emoji: string; gradient: string }> = {
  youtube:     { emoji: '▶️',  gradient: 'from-red-500 to-red-700' },
  instagram:   { emoji: '📸', gradient: 'from-pink-500 via-purple-500 to-orange-400' },
  tiktok:      { emoji: '🎵', gradient: 'from-black to-gray-800' },
  twitter:     { emoji: '𝕏',  gradient: 'from-blue-400 to-blue-600' },
  facebook:    { emoji: '📘', gradient: 'from-blue-600 to-blue-800' },
  pinterest:   { emoji: '📌', gradient: 'from-red-600 to-red-800' },
  reddit:      { emoji: '🤖', gradient: 'from-orange-500 to-orange-700' },
  vimeo:       { emoji: '🎬', gradient: 'from-cyan-500 to-cyan-700' },
  dailymotion: { emoji: '🎞️', gradient: 'from-blue-500 to-blue-700' },
  soundcloud:  { emoji: '🔊', gradient: 'from-orange-500 to-orange-600' },
  twitch:      { emoji: '🟣', gradient: 'from-purple-500 to-purple-700' },
  bilibili:    { emoji: '📺', gradient: 'from-cyan-400 to-cyan-600' },
  terabox:     { emoji: '☁️', gradient: 'from-blue-500 to-blue-700' },
  diskwala:    { emoji: '💾', gradient: 'from-blue-600 to-indigo-700' },
  mdisk:       { emoji: '💿', gradient: 'from-emerald-500 to-teal-700' },
  likee:       { emoji: '💚', gradient: 'from-green-400 to-green-600' },
  snapchat:    { emoji: '👻', gradient: 'from-yellow-400 to-yellow-500' },
  linkedin:    { emoji: '💼', gradient: 'from-blue-600 to-blue-800' },
  tumblr:      { emoji: '📝', gradient: 'from-gray-600 to-gray-800' },
  threads:     { emoji: '🧵', gradient: 'from-gray-800 to-black' },
  other:       { emoji: '🌐', gradient: 'from-gray-600 to-gray-800' },
}

const POPULAR_PLATFORMS = [
  { name: 'YouTube', icon: '▶️' },
  { name: 'Instagram', icon: '📸' },
  { name: 'TikTok', icon: '🎵' },
  { name: 'Pinterest', icon: '📌' },
  { name: 'Twitter/X', icon: '𝕏' },
  { name: 'TeraBox', icon: '☁️' },
  { name: 'Reddit', icon: '🤖' },
  { name: 'Facebook', icon: '📘' },
  { name: 'Vimeo', icon: '🎬' },
]

// ── Types ─────────────────────────────────────────────────────
interface PlatformInfo {
  id: string
  name: string
  color: string
}

interface GalleryImage {
  id: string
  index: number
  url: string
  preview_url: string
  resolution: string
  ext: string
  title: string
}

interface ImageQuality {
  format_id: string
  resolution: string
  width?: number
  height?: number
  ext: string
  filesize_mb?: number
  url: string
  quality_label?: string
}

interface MediaInfo {
  id: string
  title: string
  channel: string
  duration_formatted: string
  view_count: number
  like_count: number
  thumbnail: string
  platform: PlatformInfo
  webpage_url: string
  description: string
  is_image_only?: boolean
  is_multi_image?: boolean
  gallery_images?: GalleryImage[]
  video_qualities: Array<{
    format_id: string
    resolution: string
    height: number
    ext: string
    filesize_mb: number
  }>
  audio_qualities: Array<{
    format: string
    bitrate: string
    quality_label: string
  }>
  image_qualities?: Array<ImageQuality>
}

export default function App() {
  const [urlInput, setUrlInput] = useState('')
  const [placeholder, setPlaceholder] = useState('Paste YouTube, Instagram, Pinterest, TikTok...')
  const [isBoxGlow, setIsBoxGlow] = useState(false)
  const [isFetching, setIsFetching] = useState(false)
  const [mediaInfo, setMediaInfo] = useState<MediaInfo | null>(null)
  const [mediaType, setMediaType] = useState<'video' | 'audio' | 'image'>('video')
  const [selectedQuality, setSelectedQuality] = useState('720')
  const [isDownloading, setIsDownloading] = useState(false)
  const [downloadingImgId, setDownloadingImgId] = useState<string | null>(null)
  const [downloadingAll, setDownloadingAll] = useState(false)
  const [downloadProgress, setDownloadProgress] = useState(0)

  const inputRef = useRef<HTMLInputElement>(null)

  const platform = mediaInfo?.platform || null
  const platformStyle = PLATFORM_ICONS[platform?.id || 'other'] || PLATFORM_ICONS.other

  // Telegram User detection
  const tgUser = (window as any).Telegram?.WebApp?.initDataUnsafe?.user

  // Channel Membership Verification State
  const [isMember, setIsMember] = useState<boolean>(true)
  const [channelInfo, setChannelInfo] = useState<{ channel: string; channel_url: string }>({
    channel: '@toolboxkit',
    channel_url: 'https://t.me/toolboxkit',
  })

  // Verify channel membership on mount
  useEffect(() => {
    if (tgUser?.id) {
      fetch(`${API_BASE}/api/telegram/check-membership?user_id=${tgUser.id}`)
        .then((res) => res.json())
        .then((data) => {
          if (data && typeof data.is_member === 'boolean') {
            setIsMember(data.is_member)
            if (data.channel) {
              setChannelInfo({ channel: data.channel, channel_url: data.channel_url || 'https://t.me/toolboxkit' })
            }
          }
        })
        .catch(() => {})
    }
  }, [tgUser?.id])

  // ── Telegram Mini App & URL Auto-Load ───────────────────────
  useEffect(() => {
    const tg = (window as any).Telegram?.WebApp
    if (tg) {
      tg.ready?.()
      tg.expand?.()
      try {
        tg.setHeaderColor?.('#F4F4F7')
        tg.setBackgroundColor?.('#F4F4F7')
      } catch (e) {}
    }

    const params = new URLSearchParams(window.location.search)
    const initialUrl = params.get('url')
    if (initialUrl && initialUrl.trim().startsWith('http')) {
      setUrlInput(initialUrl.trim())
      setIsBoxGlow(true)
      setTimeout(() => setIsBoxGlow(false), 2000)
    }
  }, [])

  const triggerHaptic = (type: 'light' | 'medium' | 'heavy' | 'success' | 'error' = 'medium') => {
    try {
      const tg = (window as any).Telegram?.WebApp
      if (!tg?.HapticFeedback) return
      if (type === 'success' || type === 'error') {
        tg.HapticFeedback.notificationOccurred(type)
      } else {
        tg.HapticFeedback.impactOccurred(type)
      }
    } catch (e) {}
  }

  // ── Category or Banner Select Handler ───────────────────────
  const handleCategorySelect = (type: string, promptText: string) => {
    triggerHaptic('light')
    setPlaceholder(promptText)
    setIsBoxGlow(true)
    setTimeout(() => setIsBoxGlow(false), 2200)

    inputRef.current?.scrollIntoView({ behavior: 'smooth', block: 'center' })
    inputRef.current?.focus()
    toast(`Paste your ${type.toUpperCase()} link!`, { icon: '🎯' })
  }

  // ── Paste from Clipboard ────────────────────────────────────
  const handlePaste = async () => {
    try {
      if (navigator.clipboard && navigator.clipboard.readText) {
        const text = await navigator.clipboard.readText()
        if (text && text.trim().startsWith('http')) {
          setUrlInput(text.trim())
          toast.success('Pasted link from clipboard!')
          return
        }
      }
      toast('Paste your link directly in the box below', { icon: '📋' })
    } catch {
      toast('Please long-press and paste into the box', { icon: '👉' })
    }
  }

  // ── Fetch Media Metadata ────────────────────────────────────
  const handleFetch = async (overrideUrl?: string) => {
    const targetUrl = (overrideUrl || urlInput).trim()
    if (!targetUrl) {
      toast.error('Please paste a video or photo link')
      return
    }

    setIsFetching(true)
    setMediaInfo(null)
    triggerHaptic('medium')

    try {
      const res = await fetch(`${API_BASE}/api/downloader/info`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: targetUrl }),
      })

      if (!res.ok) {
        const errJson = await res.json().catch(() => ({}))
        throw new Error(errJson.detail || 'Could not process media link')
      }

      const data: MediaInfo = await res.json()
      setMediaInfo(data)

      // Dynamic Format Selection
      if (data.video_qualities && data.video_qualities.length > 0) {
        setMediaType('video')
        const preferred =
          data.video_qualities.find((q) => q.resolution === '1080p') ||
          data.video_qualities.find((q) => q.resolution === '720p') ||
          data.video_qualities[0]
        setSelectedQuality(preferred.resolution.replace('p', '').replace('Best', '9999'))
      } else if (data.is_image_only && data.image_qualities && data.image_qualities.length > 0) {
        setMediaType('image')
        setSelectedQuality(data.image_qualities[0].format_id || 'orig')
      } else if (data.audio_qualities && data.audio_qualities.length > 0) {
        setMediaType('audio')
        setSelectedQuality('320')
      }

      toast.success(`${data.platform?.name || 'Media'} ready to download!`)
    } catch (err: any) {
      toast.error(err.message || 'Failed to extract media', { duration: 5000 })
    } finally {
      setIsFetching(false)
    }
  }

  // ── Single Main Media Download ──────────────────────────────
  const handleDownloadMain = async () => {
    if (!mediaInfo || !urlInput.trim()) return

    setIsDownloading(true)
    const pName = platform?.name || 'Media'
    const tgUserId = (window as any).Telegram?.WebApp?.initDataUnsafe?.user?.id
    const toastId = toast.loading(`Preparing ${pName} download...`)

    try {
      const res = await fetch(`${API_BASE}/api/downloader/download`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          url: urlInput.trim(),
          media_type: mediaType,
          quality: selectedQuality,
          telegram_user_id: tgUserId,
        }),
      })

      if (!res.ok) {
        const errJson = await res.json().catch(() => ({}))
        throw new Error(errJson.detail || 'Download request failed')
      }

      const disposition = res.headers.get('content-disposition') || ''
      let filename = ''
      const utf8Match = disposition.match(/filename\*=UTF-8''([^;]+)/)
      if (utf8Match && utf8Match[1]) {
        filename = decodeURIComponent(utf8Match[1])
      } else {
        const basicMatch = disposition.match(/filename="?([^";]+)"?/)
        if (basicMatch && basicMatch[1]) {
          filename = basicMatch[1]
        }
      }

      if (!filename) {
        let ext = 'mp4'
        if (mediaType === 'audio') {
          ext = selectedQuality === 'wav' ? 'wav' : 'mp3'
        } else if (mediaType === 'image') {
          ext = 'jpg'
        }
        const cleanTitle = (mediaInfo.title || 'media').replace(/[^a-zA-Z0-9_\-\s]/g, '_').trim().slice(0, 35)
        filename = `${cleanTitle}_${selectedQuality}.${ext}`
      }

      const blob = await res.blob()
      const downloadUrl = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = downloadUrl
      a.download = filename
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(downloadUrl)

      triggerHaptic('success')
      const chatNote = tgUserId ? ' & sent to your Telegram chat!' : '!'
      toast.success(`Download complete & saved${chatNote}`, { id: toastId, duration: 4000 })
    } catch (err: any) {
      const errMsg = err.message || 'Download failed'
      triggerHaptic('error')
      toast.error(errMsg, { id: toastId, duration: 6000 })
    } finally {
      setIsDownloading(false)
    }
  }

  // ── Download Single Photo from Album ─────────────────────────
  const downloadOneImageBlob = async (img: GalleryImage) => {
    const tgUserId = (window as any).Telegram?.WebApp?.initDataUnsafe?.user?.id
    const res = await fetch(`${API_BASE}/api/downloader/download`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        url: urlInput.trim(),
        media_type: 'image',
        quality: 'orig',
        image_url: img.url,
        telegram_user_id: tgUserId,
      }),
    })

    if (!res.ok) {
      const errJson = await res.json().catch(() => ({}))
      throw new Error(errJson.detail || `Download failed for Photo #${img.index}`)
    }

    const disposition = res.headers.get('content-disposition') || ''
    let filename = ''
    const utf8Match = disposition.match(/filename\*=UTF-8''([^;]+)/)
    if (utf8Match && utf8Match[1]) {
      filename = decodeURIComponent(utf8Match[1])
    } else {
      const basicMatch = disposition.match(/filename="?([^";]+)"?/)
      if (basicMatch && basicMatch[1]) {
        filename = basicMatch[1]
      }
    }

    if (!filename) {
      const cleanTitle = (mediaInfo?.title || 'photo').replace(/[^a-zA-Z0-9_\-\s]/g, '_').trim().slice(0, 30)
      filename = `${cleanTitle}_photo_${img.index}.${img.ext || 'jpg'}`
    }

    const blob = await res.blob()
    const downloadUrl = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = downloadUrl
    a.download = filename
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(downloadUrl)
  }

  const handleDownloadSingleImage = async (img: GalleryImage) => {
    if (!mediaInfo || !urlInput.trim()) return

    setDownloadingImgId(img.id)
    const toastId = toast.loading(`Downloading Photo #${img.index}...`)
    try {
      await downloadOneImageBlob(img)
      toast.success(`Photo #${img.index} downloaded!`, { id: toastId })
    } catch (err: any) {
      toast.error(`Error: ${err.message}`, { id: toastId })
    } finally {
      setDownloadingImgId(null)
    }
  }

  const handleDownloadAllImages = async () => {
    if (!mediaInfo?.gallery_images?.length || !urlInput.trim()) return

    setDownloadingAll(true)
    setDownloadProgress(0)
    const total = mediaInfo.gallery_images.length
    const toastId = toast.loading(`Downloading all ${total} photos...`)

    try {
      for (let i = 0; i < total; i++) {
        const img = mediaInfo.gallery_images[i]
        setDownloadProgress(i + 1)
        await downloadOneImageBlob(img)
        if (i < total - 1) {
          await new Promise((resolve) => setTimeout(resolve, 600))
        }
      }
      toast.success(`All ${total} photos downloaded!`, { id: toastId })
    } catch (err: any) {
      toast.error(`Error: ${err.message}`, { id: toastId })
    } finally {
      setDownloadingAll(false)
      setDownloadProgress(0)
    }
  }

  const hasVideo = mediaInfo && mediaInfo.video_qualities && mediaInfo.video_qualities.length > 0
  const hasAudio = mediaInfo && mediaInfo.audio_qualities && mediaInfo.audio_qualities.length > 0
  const hasImages = mediaInfo && mediaInfo.image_qualities && mediaInfo.image_qualities.length > 0

  return (
    <div className="min-h-screen flex flex-col justify-between safe-top safe-bottom pb-28">
      <Toaster position="top-center" toastOptions={{ style: { borderRadius: '16px', background: '#0F0F12', color: '#fff', fontSize: '13px' } }} />

      {/* ── Mandatory Channel Membership Modal ─────────────────── */}
      {!isMember && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-md p-4">
          <motion.div
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            className="bg-white rounded-3xl border border-black/10 max-w-sm w-full p-6 text-center shadow-2xl space-y-4"
          >
            <div className="w-16 h-16 bg-blue-50 border border-blue-200 rounded-2xl mx-auto flex items-center justify-center text-3xl shadow-xs">
              📢
            </div>
            <div>
              <h3 className="text-xl font-bold text-gray-900">Join Channel to Continue</h3>
              <p className="text-xs text-gray-500 mt-1.5 leading-relaxed">
                To unlock 4K downloads, 320kbps audio, and high-speed extraction, you must be a member of our official channel:
              </p>
              <div className="inline-block mt-3 px-3.5 py-1 bg-blue-50 border border-blue-200/80 rounded-full text-blue-600 font-bold text-xs tracking-wide">
                {channelInfo.channel}
              </div>
            </div>

            <div className="space-y-2 pt-2">
              <button
                onClick={() => {
                  triggerHaptic('medium')
                  const tg = (window as any).Telegram?.WebApp
                  if (tg?.openTelegramLink) {
                    tg.openTelegramLink(channelInfo.channel_url)
                  } else {
                    window.open(channelInfo.channel_url, '_blank')
                  }
                }}
                className="w-full py-3 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-bold text-sm rounded-2xl shadow-md shadow-blue-500/25 transition active:scale-[0.98]"
              >
                📢 Join {channelInfo.channel}
              </button>
              <button
                onClick={() => {
                  triggerHaptic('light')
                  if (tgUser?.id) {
                    const tId = toast.loading('Verifying membership...')
                    fetch(`${API_BASE}/api/telegram/check-membership?user_id=${tgUser.id}`)
                      .then((res) => res.json())
                      .then((data) => {
                        if (data?.is_member) {
                          setIsMember(true)
                          toast.success('Membership verified! Welcome.', { id: tId })
                          triggerHaptic('success')
                        } else {
                          toast.error(`Please tap the button above to join ${channelInfo.channel} first!`, { id: tId })
                          triggerHaptic('error')
                        }
                      })
                      .catch(() => {
                        setIsMember(true)
                        toast.dismiss(tId)
                      })
                  } else {
                    setIsMember(true)
                  }
                }}
                className="w-full py-2.5 bg-gray-100 hover:bg-gray-200 text-gray-700 text-xs font-bold rounded-2xl border border-gray-200 transition active:scale-[0.98]"
              >
                ✅ I Have Joined (Verify)
              </button>
            </div>
          </motion.div>
        </div>
      )}

      {/* ── Mobile Header ────────────────────────────────────── */}
      <header className="sticky top-0 z-30 bg-[#F4F4F7]/90 backdrop-blur-md border-b border-black/[0.06] px-4 py-3.5">
        <div className="max-w-xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-2xl bg-[#0F0F12] text-white flex items-center justify-center font-bold shadow-sm">
              <svg className="w-4 h-4 text-[#FF4D26]" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
              </svg>
            </div>
            <div>
              <h1 className="font-display font-bold text-sm text-[#0F0F12] leading-tight flex items-center gap-1.5">
                All-in-One Downloader
                <span className="text-[10px] px-1.5 py-0.2 bg-[#FF4D26]/10 text-[#FF4D26] font-mono rounded font-bold">PRO</span>
              </h1>
              <p className="text-[10px] text-neutral-400 font-medium">Up to 4K • Video, Audio & Albums</p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {tgUser?.first_name && (
              <span className="px-2 py-0.5 bg-blue-500/10 text-blue-600 border border-blue-500/20 rounded-full text-[10px] font-bold">
                👋 {tgUser.first_name}
              </span>
            )}
            <span className="px-2.5 py-1 bg-emerald-500/10 text-emerald-700 border border-emerald-500/20 rounded-full text-[10px] font-bold font-mono">
              ⚡ 100% Free
            </span>
          </div>
        </div>
      </header>

      {/* ── Main Scrollable Body ─────────────────────────────── */}
      <main className="max-w-xl mx-auto w-full px-4 pt-4 space-y-4 flex-1">
        
        {/* ── Official Platform Brand Logos Marquee ──────────────────── */}
        <MarqueeLogos onSelect={handleCategorySelect} />

        {/* ── Input Card ─────────────────────────────────────── */}
        <div className="bg-white rounded-[26px] border border-black/[0.06] p-4 sm:p-5 shadow-xs space-y-3">
          <div className="flex items-center justify-between">
            <label className="text-[11px] font-display font-bold text-neutral-400 uppercase tracking-wider">
              Paste Media Link:
            </label>
            <button
              onClick={handlePaste}
              className="text-[11px] font-display font-bold text-[#FF4D26] hover:underline flex items-center gap-1 active:scale-95"
            >
              <span>📋</span> Paste Link
            </button>
          </div>

          <div
            className={`flex items-center gap-2 px-3.5 py-3 bg-[#FAFAFC] border rounded-2xl transition-all shadow-inner ${
              isBoxGlow
                ? 'border-[#FF4D26] ring-4 ring-[#FF4D26]/20 bg-white scale-[1.01]'
                : 'border-black/10 focus-within:border-[#FF4D26] focus-within:bg-white'
            }`}
          >
            <svg className="w-4 h-4 text-neutral-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
            </svg>
            <input
              ref={inputRef}
              type="url"
              value={urlInput}
              onChange={(e) => setUrlInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleFetch()}
              placeholder={placeholder}
              className="w-full bg-transparent border-none outline-none text-xs text-[#0F0F12] font-sans placeholder-neutral-400"
            />
            {urlInput && (
              <button
                onClick={() => setUrlInput('')}
                className="text-neutral-400 hover:text-black text-xs font-bold p-1"
              >
                ✕
              </button>
            )}
          </div>

          <button
            onClick={() => handleFetch()}
            disabled={isFetching || !urlInput.trim()}
            className="w-full py-3.5 bg-[#0F0F12] text-white rounded-2xl text-xs font-display font-bold hover:bg-[#FF4D26] disabled:opacity-40 transition-all flex items-center justify-center gap-2 shadow-xs active:scale-98"
          >
            {isFetching ? (
              <>
                <motion.span animate={{ rotate: 360 }} transition={{ repeat: Infinity, duration: 1, ease: 'linear' }}>
                  ⏳
                </motion.span>
                <span>Extracting Media Stream...</span>
              </>
            ) : (
              <>
                <span>Fetch Media</span>
                <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M7 17L17 7M17 7H7M17 7V17" />
                </svg>
              </>
            )}
          </button>
        </div>

        {/* ── Beautiful Animated Loader during Fetching ─────────── */}
        <AnimatePresence>
          {isFetching && <FetchingLoader />}
        </AnimatePresence>

        {/* ── Extracted Media Details Card ───────────────────── */}
        <AnimatePresence>
          {mediaInfo && !isFetching && (
            <motion.div
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 15 }}
              className="bg-white rounded-[26px] border border-black/[0.06] p-4 sm:p-5 shadow-xs space-y-4"
            >
              {/* Platform header */}
              <div className="flex items-center justify-between flex-wrap gap-2">
                <div className="flex items-center gap-1.5">
                  <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-white text-[11px] font-bold bg-gradient-to-r ${platformStyle.gradient}`}>
                    <span>{platformStyle.emoji}</span>
                    <span>{platform?.name || 'Media'}</span>
                  </span>
                  {mediaInfo.gallery_images && mediaInfo.gallery_images.length > 1 ? (
                    <span className="px-2 py-0.5 rounded-full bg-blue-50 text-blue-700 border border-blue-200 text-[10px] font-bold">
                      📸 {mediaInfo.gallery_images.length} Photos
                    </span>
                  ) : mediaInfo.is_image_only ? (
                    <span className="px-2 py-0.5 rounded-full bg-purple-50 text-purple-700 border border-purple-200 text-[10px] font-bold">
                      📸 Image Post
                    </span>
                  ) : null}
                </div>

                {mediaInfo.webpage_url && (
                  <a
                    href={mediaInfo.webpage_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-[11px] font-semibold text-neutral-500 hover:text-black flex items-center gap-1 underline"
                  >
                    <span>Original</span>
                    <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M7 17L17 7M17 7H7M17 7V17" />
                    </svg>
                  </a>
                )}
              </div>

              {/* Media Preview Box */}
              <div className="flex gap-3.5 p-3 bg-[#FAFAFC] border border-black/[0.06] rounded-2xl items-center">
                {mediaInfo.thumbnail && (
                  <div className="w-24 h-20 rounded-xl overflow-hidden shadow-2xs flex-shrink-0 relative bg-neutral-900 flex items-center justify-center">
                    <img
                      src={mediaInfo.thumbnail}
                      alt={mediaInfo.title}
                      referrerPolicy="no-referrer"
                      className="w-full h-full object-cover"
                    />
                    {mediaInfo.duration_formatted && mediaInfo.duration_formatted !== '0:00' && (
                      <span className="absolute bottom-1 right-1 px-1 py-0.2 bg-black/80 text-white font-mono text-[9px] rounded font-bold">
                        {mediaInfo.duration_formatted}
                      </span>
                    )}
                  </div>
                )}
                <div className="flex-1 min-w-0 space-y-1">
                  <h3 className="font-display font-bold text-xs text-[#0F0F12] line-clamp-2 leading-tight">
                    {mediaInfo.title}
                  </h3>
                  <p className="text-[11px] text-neutral-500 truncate">
                    By: <strong className="text-neutral-800">{mediaInfo.channel}</strong>
                  </p>
                </div>
              </div>

              {/* TeraBox Fast Download Direct Card */}
              {platform?.id === 'terabox' && (
                <div className="p-3 bg-blue-50/80 border border-blue-200/60 rounded-2xl flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-sm">☁️</span>
                    <div>
                      <div className="text-[11px] font-display font-bold text-blue-950">TeraBox Cloud Media</div>
                      <div className="text-[10px] text-blue-700">Direct server stream ready for device save</div>
                    </div>
                  </div>
                  <span className="text-[10px] font-mono font-bold bg-blue-200/70 text-blue-800 px-2.5 py-1 rounded-full">
                    Direct
                  </span>
                </div>
              )}

              {/* Output Format Switcher */}
              <div className="space-y-2">
                <label className="text-[11px] font-display font-bold text-neutral-400 uppercase tracking-wider">
                  Select Format:
                </label>
                <div className="flex bg-[#F4F4F7] p-1 rounded-2xl gap-1">
                  {hasVideo && (
                    <button
                      onClick={() => {
                        setMediaType('video')
                        const pref =
                          mediaInfo.video_qualities.find((q) => q.resolution === '1080p') ||
                          mediaInfo.video_qualities[0]
                        setSelectedQuality(pref.resolution.replace('p', '').replace('Best', '9999'))
                      }}
                      className={`flex-1 py-2 rounded-xl text-xs font-display font-bold transition-all flex items-center justify-center gap-1 ${
                        mediaType === 'video' ? 'bg-white text-[#0F0F12] shadow-2xs' : 'text-neutral-500'
                      }`}
                    >
                      <span>🎬</span>
                      <span>Video</span>
                    </button>
                  )}
                  {hasAudio && (
                    <button
                      onClick={() => {
                        setMediaType('audio')
                        setSelectedQuality('320')
                      }}
                      className={`flex-1 py-2 rounded-xl text-xs font-display font-bold transition-all flex items-center justify-center gap-1 ${
                        mediaType === 'audio' ? 'bg-white text-[#0F0F12] shadow-2xs' : 'text-neutral-500'
                      }`}
                    >
                      <span>🎵</span>
                      <span>Audio</span>
                    </button>
                  )}
                  {hasImages && (
                    <button
                      onClick={() => {
                        setMediaType('image')
                        setSelectedQuality(mediaInfo.image_qualities![0].format_id || 'orig')
                      }}
                      className={`flex-1 py-2 rounded-xl text-xs font-display font-bold transition-all flex items-center justify-center gap-1 ${
                        mediaType === 'image' ? 'bg-white text-[#0F0F12] shadow-2xs' : 'text-neutral-500'
                      }`}
                    >
                      <span>📸</span>
                      <span>Image</span>
                    </button>
                  )}
                </div>
              </div>

              {/* Resolution Options Grid */}
              <div className="space-y-2">
                <label className="text-[11px] font-display font-bold text-neutral-400 uppercase tracking-wider">
                  {mediaType === 'video' ? 'Video Resolution:' : mediaType === 'audio' ? 'Audio Bitrate:' : 'Quality:'}
                </label>
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                  {mediaType === 'video' &&
                    mediaInfo.video_qualities.map((q) => {
                      const qVal = q.resolution.replace('p', '').replace('Best', '9999')
                      const isSel = selectedQuality === qVal
                      const is4K = q.height >= 2160
                      const isHD = q.height >= 1080
                      return (
                        <button
                          key={q.resolution}
                          onClick={() => setSelectedQuality(qVal)}
                          className={`p-2.5 rounded-xl border text-left transition-all ${
                            isSel ? 'bg-[#0F0F12] text-white border-[#0F0F12] shadow-xs' : 'bg-[#FAFAFC] border-black/5 text-[#0F0F12]'
                          }`}
                        >
                          <div className="flex items-center justify-between">
                            <span className="font-display font-bold text-xs">{q.resolution}</span>
                            {is4K && (
                              <span className={`text-[8px] px-1 py-0.2 rounded font-bold ${isSel ? 'bg-amber-400/30 text-amber-200' : 'bg-amber-100 text-amber-700'}`}>
                                4K
                              </span>
                            )}
                            {isHD && !is4K && (
                              <span className={`text-[8px] px-1 py-0.2 rounded font-bold ${isSel ? 'bg-blue-400/30 text-blue-200' : 'bg-blue-100 text-blue-700'}`}>
                                HD
                              </span>
                            )}
                          </div>
                          <span className={`text-[10px] mt-0.5 block ${isSel ? 'text-neutral-400' : 'text-neutral-400'}`}>
                            {q.filesize_mb > 0 ? `~${q.filesize_mb} MB` : 'MP4'}
                          </span>
                        </button>
                      )
                    })}

                  {mediaType === 'audio' &&
                    mediaInfo.audio_qualities.map((q) => {
                      const qVal = q.format === 'wav' ? 'wav' : q.bitrate.replace('kbps', '')
                      const isSel = selectedQuality === qVal
                      return (
                        <button
                          key={q.quality_label}
                          onClick={() => setSelectedQuality(qVal)}
                          className={`p-2.5 rounded-xl border text-left transition-all ${
                            isSel ? 'bg-[#0F0F12] text-white border-[#0F0F12] shadow-xs' : 'bg-[#FAFAFC] border-black/5 text-[#0F0F12]'
                          }`}
                        >
                          <div className="flex items-center justify-between">
                            <span className="font-display font-bold text-xs uppercase">{q.format}</span>
                            <span className={`text-[9px] px-1 py-0.2 rounded font-bold ${isSel ? 'bg-white/20' : 'bg-neutral-200 text-neutral-700'}`}>
                              {q.bitrate}
                            </span>
                          </div>
                          <span className={`text-[10px] mt-0.5 truncate block ${isSel ? 'text-neutral-400' : 'text-neutral-400'}`}>
                            {q.quality_label}
                          </span>
                        </button>
                      )
                    })}

                  {mediaType === 'image' &&
                    mediaInfo.image_qualities &&
                    mediaInfo.image_qualities.map((img) => {
                      const isSel = selectedQuality === img.format_id
                      return (
                        <button
                          key={img.format_id}
                          onClick={() => setSelectedQuality(img.format_id)}
                          className={`p-2.5 rounded-xl border text-left transition-all ${
                            isSel ? 'bg-[#0F0F12] text-white border-[#0F0F12] shadow-xs' : 'bg-[#FAFAFC] border-black/5 text-[#0F0F12]'
                          }`}
                        >
                          <div className="flex items-center justify-between">
                            <span className="font-display font-bold text-xs">{img.resolution}</span>
                            <span className={`text-[9px] px-1 py-0.2 rounded font-bold uppercase ${isSel ? 'bg-white/20' : 'bg-neutral-200 text-neutral-700'}`}>
                              {img.ext}
                            </span>
                          </div>
                          <span className={`text-[10px] mt-0.5 truncate block ${isSel ? 'text-neutral-400' : 'text-neutral-400'}`}>
                            {img.quality_label || 'Original Photo'}
                          </span>
                        </button>
                      )
                    })}
                </div>
              </div>

              {/* ── Multi-Image Album Gallery Grid ──────────────── */}
              {mediaInfo.gallery_images && mediaInfo.gallery_images.length > 1 && (
                <div className="pt-4 border-t border-black/[0.08] space-y-3">
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="font-display font-bold text-xs text-[#0F0F12] flex items-center gap-1.5">
                        <span>📸</span> Album Gallery ({mediaInfo.gallery_images.length} Photos)
                      </h4>
                      <p className="text-[10px] text-neutral-400">Download single photos or all at once</p>
                    </div>

                    <button
                      onClick={handleDownloadAllImages}
                      disabled={downloadingAll || downloadingImgId !== null}
                      className="px-3 py-1.5 bg-[#0F0F12] text-white rounded-xl text-[11px] font-display font-bold hover:bg-[#FF4D26] disabled:opacity-50 transition-all flex items-center gap-1 shadow-xs active:scale-95"
                    >
                      {downloadingAll ? (
                        <>
                          <motion.span animate={{ rotate: 360 }} transition={{ repeat: Infinity, duration: 1, ease: 'linear' }}>
                            ⏳
                          </motion.span>
                          <span>({downloadProgress}/{mediaInfo.gallery_images.length})</span>
                        </>
                      ) : (
                        <span>Download All</span>
                      )}
                    </button>
                  </div>

                  <div className="grid grid-cols-2 sm:grid-cols-3 gap-2.5">
                    {mediaInfo.gallery_images.map((img) => {
                      const isDownloadingThis = downloadingImgId === img.id
                      return (
                        <div
                          key={img.id}
                          className="bg-[#FAFAFC] border border-black/[0.08] rounded-2xl p-2 flex flex-col justify-between space-y-2 shadow-2xs"
                        >
                          <div className="relative aspect-[3/4] rounded-xl overflow-hidden bg-neutral-900 flex items-center justify-center">
                            <img
                              src={img.preview_url || img.url}
                              alt={img.title}
                              loading="lazy"
                              referrerPolicy="no-referrer"
                              className="w-full h-full object-cover"
                            />
                            <span className="absolute top-1.5 left-1.5 px-1.5 py-0.2 bg-black/80 text-white text-[9px] font-mono font-bold rounded">
                              #{img.index}
                            </span>
                            <span className="absolute top-1.5 right-1.5 px-1.5 py-0.2 bg-emerald-500/90 text-white text-[8px] font-bold rounded uppercase">
                              {img.ext}
                            </span>
                          </div>

                          <button
                            onClick={() => handleDownloadSingleImage(img)}
                            disabled={isDownloadingThis || downloadingAll}
                            className="w-full py-1.5 bg-[#0F0F12] text-white hover:bg-emerald-600 disabled:opacity-50 rounded-xl text-[11px] font-display font-bold transition-all flex items-center justify-center gap-1 shadow-2xs active:scale-95"
                          >
                            {isDownloadingThis ? (
                              <span>Saving...</span>
                            ) : (
                              <>
                                <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                                  <path strokeLinecap="round" strokeLinejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                                </svg>
                                <span>Save</span>
                              </>
                            )}
                          </button>
                        </div>
                      )
                    })}
                  </div>
                </div>
              )}
            </motion.div>
          )}
        </AnimatePresence>

        {/* ── Sliding Banner Section (Carousel) ───────────────── */}
        <SlidingBanner onSelectType={(type, prompt) => handleCategorySelect(type, prompt || 'Paste your link...')} />

        {/* ── Category Cards Grid (Video, Audio, Cloud, Images) ── */}
        <CategoryCards onSelect={(type, prompt) => handleCategorySelect(type, prompt)} />

      </main>

      {/* ── Mobile Sticky Bottom Action Bar ───────────────────── */}
      {mediaInfo && (
        <div className="fixed bottom-0 left-0 right-0 bg-white/95 backdrop-blur-md border-t border-black/[0.08] p-3 safe-bottom z-40">
          <div className="max-w-xl mx-auto flex items-center gap-3">
            <div className="flex-1 min-w-0">
              <span className="text-[10px] text-neutral-400 font-bold uppercase tracking-wider block">
                Selected
              </span>
              <p className="text-xs font-display font-bold text-[#0F0F12] truncate">
                {platform?.name} {mediaType.toUpperCase()} ({selectedQuality === '9999' ? 'Best' : selectedQuality}
                {mediaType === 'video' && selectedQuality !== '9999' ? 'p' : mediaType === 'audio' ? 'kbps' : ''})
              </p>
            </div>

            <button
              onClick={handleDownloadMain}
              disabled={isDownloading}
              className="px-6 py-3 bg-emerald-600 hover:bg-emerald-700 text-white font-display font-bold text-xs rounded-2xl disabled:opacity-50 transition-all flex items-center gap-2 shadow-md active:scale-95 flex-shrink-0"
            >
              {isDownloading ? (
                <>
                  <motion.span animate={{ rotate: 360 }} transition={{ repeat: Infinity, duration: 1, ease: 'linear' }}>
                    ⏳
                  </motion.span>
                  <span>Downloading...</span>
                </>
              ) : (
                <>
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2.5}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                  </svg>
                  <span>Download</span>
                </>
              )}
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
