"use client"

import { useEffect, useRef, useState } from "react"
import NextImage from "next/image"

// Each particle IS a pixel from the actual logo image.
// They start scattered across the screen and fly home to form the logo.
export function PixelAssembly() {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const mouseRef = useRef({ x: -9999, y: -9999 })
  const [revealed, setRevealed] = useState(false)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext("2d")
    if (!ctx) return

    let animationFrameId: number
    let running = true

    const resize = () => {
      canvas.width = window.innerWidth
      canvas.height = window.innerHeight
    }
    resize()

    const img = new window.Image()
    img.crossOrigin = "anonymous"
    img.src = "/images/logo.png"

    img.onload = () => {
      // Target size & position of the final logo
      const maxW = Math.min(window.innerWidth * 0.7, 1000)
      const scale = maxW / img.width
      const logoW = img.width * scale
      const logoH = img.height * scale
      const logoX = (window.innerWidth - logoW) / 2
      const logoY = (window.innerHeight - logoH) / 2

      // Draw to offscreen canvas to sample pixels
      const off = document.createElement("canvas")
      off.width = logoW
      off.height = logoH
      const offCtx = off.getContext("2d")
      if (!offCtx) return
      offCtx.drawImage(img, 0, 0, logoW, logoH)
      const data = offCtx.getImageData(0, 0, logoW, logoH).data

      // Sample every Nth pixel; create a particle for dark ones
      const step = 3
      type P = {
        tx: number
        ty: number
        x: number
        y: number
        vx: number
        vy: number
        delay: number
        size: number
      }
      const particles: P[] = []

      for (let y = 0; y < logoH; y += step) {
        for (let x = 0; x < logoW; x += step) {
          const i = (y * logoW + x) * 4
          const r = data[i]
          const g = data[i + 1]
          const b = data[i + 2]
          const a = data[i + 3]
          // Dark, visible pixels only (that's the logo ink)
          if (a > 150 && r < 80 && g < 80 && b < 80) {
            // Start from a random point on the page edges
            const side = Math.floor(Math.random() * 4)
            let sx = 0
            let sy = 0
            if (side === 0) {
              sx = Math.random() * window.innerWidth
              sy = -20
            } else if (side === 1) {
              sx = window.innerWidth + 20
              sy = Math.random() * window.innerHeight
            } else if (side === 2) {
              sx = Math.random() * window.innerWidth
              sy = window.innerHeight + 20
            } else {
              sx = -20
              sy = Math.random() * window.innerHeight
            }
            particles.push({
              tx: logoX + x,
              ty: logoY + y,
              x: sx,
              y: sy,
              vx: 0,
              vy: 0,
              delay: Math.random() * 1800,
              size: step - 1,
            })
          }
        }
      }

      const startTime = performance.now()
      const duration = 5000

      const animate = (now: number) => {
        if (!running) return
        const elapsed = now - startTime
        const globalProgress = Math.min(elapsed / duration, 1)

        ctx.clearRect(0, 0, canvas.width, canvas.height)

        for (let p of particles) {
          const pElapsed = Math.max(0, elapsed - p.delay)
          const pProgress = Math.min(pElapsed / (duration - 1800), 1)
          // Ease-out cubic for snappy arrival
          const ease = 1 - Math.pow(1 - pProgress, 3)

          // Spring toward target
          const targetX = p.tx
          const targetY = p.ty
          p.x = p.x + (targetX - p.x) * (0.04 + ease * 0.12)
          p.y = p.y + (targetY - p.y) * (0.04 + ease * 0.12)

          // Mouse repulsion while particles are still moving
          if (globalProgress < 0.95) {
            const dx = p.x - mouseRef.current.x
            const dy = p.y - mouseRef.current.y
            const dist = Math.hypot(dx, dy)
            if (dist < 120 && dist > 0) {
              const force = (120 - dist) / 120
              p.x += (dx / dist) * force * 8
              p.y += (dy / dist) * force * 8
            }
          }

          // Fade opacity with arrival
          ctx.fillStyle = `rgba(0,0,0,${0.4 + ease * 0.6})`
          ctx.fillRect(p.x, p.y, p.size, p.size)
        }

        if (globalProgress < 1) {
          animationFrameId = requestAnimationFrame(animate)
        } else {
          setRevealed(true)
        }
      }

      animationFrameId = requestAnimationFrame(animate)
    }

    const onMove = (e: MouseEvent) => {
      mouseRef.current.x = e.clientX
      mouseRef.current.y = e.clientY
    }
    const onLeave = () => {
      mouseRef.current.x = -9999
      mouseRef.current.y = -9999
    }

    window.addEventListener("resize", resize)
    window.addEventListener("mousemove", onMove)
    window.addEventListener("mouseleave", onLeave)

    return () => {
      running = false
      cancelAnimationFrame(animationFrameId)
      window.removeEventListener("resize", resize)
      window.removeEventListener("mousemove", onMove)
      window.removeEventListener("mouseleave", onLeave)
    }
  }, [])

  return (
    <div className="relative min-h-screen w-full bg-white flex items-center justify-center overflow-hidden">
      <canvas
        ref={canvasRef}
        className={`absolute inset-0 transition-opacity duration-700 ${revealed ? "opacity-0" : "opacity-100"}`}
      />
      <NextImage
        src="/images/logo.png"
        alt="Studio Vendi"
        width={1000}
        height={250}
        priority
        className={`w-[560px] sm:w-[700px] md:w-[800px] lg:w-[1000px] h-auto transition-opacity duration-700 ${
          revealed ? "opacity-100" : "opacity-0"
        }`}
      />
    </div>
  )
}
