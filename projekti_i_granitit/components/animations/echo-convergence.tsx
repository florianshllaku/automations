"use client"

import { useEffect, useRef, useState } from "react"
import NextImage from "next/image"

// Many offset copies of the logo at different scales/rotations fly through
// space and converge into a single crisp logo. The logo IS the animation.
export function EchoConvergence() {
  const [progress, setProgress] = useState(0)
  const [done, setDone] = useState(false)
  const mouseRef = useRef({ x: 0.5, y: 0.5 })
  const [mouse, setMouse] = useState({ x: 0.5, y: 0.5 })

  useEffect(() => {
    const start = performance.now()
    let raf: number
    const duration = 5000

    const loop = (now: number) => {
      const p = Math.min((now - start) / duration, 1)
      // Ease-out quart for dramatic convergence
      const eased = 1 - Math.pow(1 - p, 4)
      setProgress(eased)
      setMouse({ ...mouseRef.current })
      if (p < 1) {
        raf = requestAnimationFrame(loop)
      } else {
        setDone(true)
      }
    }
    raf = requestAnimationFrame(loop)
    return () => cancelAnimationFrame(raf)
  }, [])

  useEffect(() => {
    const onMove = (e: MouseEvent) => {
      mouseRef.current.x = e.clientX / window.innerWidth
      mouseRef.current.y = e.clientY / window.innerHeight
    }
    window.addEventListener("mousemove", onMove)
    return () => window.removeEventListener("mousemove", onMove)
  }, [])

  // 18 echo copies
  const echoes = Array.from({ length: 18 }, (_, i) => {
    const angle = (i / 18) * Math.PI * 2
    const radius = 200 + (i % 3) * 80
    // Start position in a spiral
    const startX = Math.cos(angle) * radius
    const startY = Math.sin(angle) * radius
    const startRotate = (i - 9) * 8
    const startScale = 0.4 + ((i * 7) % 5) * 0.15

    // Mouse parallax
    const parallaxX = (mouse.x - 0.5) * (1 - progress) * 60
    const parallaxY = (mouse.y - 0.5) * (1 - progress) * 60

    const x = startX * (1 - progress) + parallaxX
    const y = startY * (1 - progress) + parallaxY
    const rotate = startRotate * (1 - progress)
    const scale = startScale + (1 - startScale) * progress
    const opacity = 0.08 + progress * 0.1

    return { i, x, y, rotate, scale, opacity }
  })

  return (
    <div className="relative min-h-screen w-full bg-white flex items-center justify-center overflow-hidden">
      {!done && (
        <div className="absolute inset-0 flex items-center justify-center">
          {echoes.map((e) => (
            <NextImage
              key={e.i}
              src="/images/logo.png"
              alt=""
              width={1000}
              height={250}
              priority
              className="absolute w-[560px] sm:w-[700px] md:w-[800px] lg:w-[1000px] h-auto pointer-events-none"
              style={{
                transform: `translate(${e.x}px, ${e.y}px) rotate(${e.rotate}deg) scale(${e.scale})`,
                opacity: e.opacity,
                filter: `blur(${(1 - progress) * 6}px)`,
              }}
            />
          ))}
        </div>
      )}

      {/* The final, crisp logo */}
      <NextImage
        src="/images/logo.png"
        alt="Studio Vendi"
        width={1000}
        height={250}
        priority
        className="w-[560px] sm:w-[700px] md:w-[800px] lg:w-[1000px] h-auto relative"
        style={{
          opacity: Math.pow(progress, 2),
          transform: done
            ? "none"
            : `scale(${0.85 + progress * 0.15})`,
        }}
      />
    </div>
  )
}
