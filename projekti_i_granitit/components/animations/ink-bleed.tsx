"use client"

import { useEffect, useRef, useState } from "react"
import NextImage from "next/image"

// The logo is a CSS mask. Ink drops grow & merge ONLY inside the logo shape,
// creating a real "ink soaking into paper" effect that forms the logo.
export function InkBleed() {
  const containerRef = useRef<HTMLDivElement>(null)
  const [revealed, setRevealed] = useState(false)
  const [drops, setDrops] = useState<
    { x: number; y: number; maxSize: number; delay: number; duration: number }[]
  >([])
  const [time, setTime] = useState(0)
  const mouseRef = useRef({ x: 0.5, y: 0.5 })

  // Create a set of ink drop positions across the logo shape
  useEffect(() => {
    const newDrops = []
    // 10 drops spread across the logo width
    for (let i = 0; i < 14; i++) {
      newDrops.push({
        x: 10 + Math.random() * 80, // 10-90% across
        y: 20 + Math.random() * 60, // 20-80% vertically
        maxSize: 40 + Math.random() * 30, // in vw
        delay: i * 180 + Math.random() * 200,
        duration: 2200 + Math.random() * 800,
      })
    }
    setDrops(newDrops)

    const start = performance.now()
    let rafId: number
    const loop = (now: number) => {
      setTime(now - start)
      if (now - start < 5200) {
        rafId = requestAnimationFrame(loop)
      } else {
        setRevealed(true)
      }
    }
    rafId = requestAnimationFrame(loop)
    return () => cancelAnimationFrame(rafId)
  }, [])

  useEffect(() => {
    const onMove = (e: MouseEvent) => {
      if (!containerRef.current) return
      const rect = containerRef.current.getBoundingClientRect()
      mouseRef.current.x = (e.clientX - rect.left) / rect.width
      mouseRef.current.y = (e.clientY - rect.top) / rect.height
    }
    window.addEventListener("mousemove", onMove)
    return () => window.removeEventListener("mousemove", onMove)
  }, [])

  return (
    <div
      ref={containerRef}
      className="relative min-h-screen w-full bg-white flex items-center justify-center overflow-hidden"
    >
      {/* Gooey filter so ink drops merge organically */}
      <svg className="absolute h-0 w-0" aria-hidden="true">
        <defs>
          <filter id="ink-gooey">
            <feGaussianBlur in="SourceGraphic" stdDeviation="8" />
            <feColorMatrix
              type="matrix"
              values="1 0 0 0 0
                      0 1 0 0 0
                      0 0 1 0 0
                      0 0 0 28 -12"
            />
          </filter>
        </defs>
      </svg>

      {/* The masked ink container - ink shows only where the logo exists */}
      <div
        className={`relative transition-opacity duration-700 ${revealed ? "opacity-0" : "opacity-100"}`}
        style={{
          width: "min(70vw, 1000px)",
          aspectRatio: "4 / 1",
          WebkitMaskImage: "url(/images/logo.png)",
          maskImage: "url(/images/logo.png)",
          WebkitMaskSize: "contain",
          maskSize: "contain",
          WebkitMaskRepeat: "no-repeat",
          maskRepeat: "no-repeat",
          WebkitMaskPosition: "center",
          maskPosition: "center",
        }}
      >
        <div
          className="absolute inset-0"
          style={{ filter: "url(#ink-gooey)" }}
        >
          {drops.map((d, i) => {
            const elapsed = Math.max(0, time - d.delay)
            const progress = Math.min(elapsed / d.duration, 1)
            const eased = 1 - Math.pow(1 - progress, 2)
            const size = d.maxSize * eased
            // Subtle drift based on mouse
            const driftX = (mouseRef.current.x - 0.5) * 3
            const driftY = (mouseRef.current.y - 0.5) * 3
            return (
              <div
                key={i}
                className="absolute rounded-full bg-black"
                style={{
                  left: `${d.x + driftX}%`,
                  top: `${d.y + driftY}%`,
                  width: `${size}%`,
                  height: `${size * 4}%`, // taller since aspect ratio is 4:1
                  transform: "translate(-50%, -50%)",
                  transition: "left 0.4s ease-out, top 0.4s ease-out",
                }}
              />
            )
          })}
        </div>
      </div>

      {/* Final clean logo fades in */}
      <NextImage
        src="/images/logo.png"
        alt="Studio Vendi"
        width={1000}
        height={250}
        priority
        className={`absolute w-[560px] sm:w-[700px] md:w-[800px] lg:w-[1000px] h-auto transition-opacity duration-700 ${
          revealed ? "opacity-100" : "opacity-0"
        }`}
      />
    </div>
  )
}
