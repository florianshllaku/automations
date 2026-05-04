"use client"

import { useEffect, useRef, useState } from "react"
import NextImage from "next/image"

// A pen tip glides left-to-right across the logo, revealing it
// through an organic wavy mask with an ink splash at the tip.
export function Handwritten() {
  const [progress, setProgress] = useState(0)
  const [done, setDone] = useState(false)
  const containerRef = useRef<HTMLDivElement>(null)
  const mouseYRef = useRef(0.5)

  useEffect(() => {
    const start = performance.now()
    let raf: number
    const duration = 4800

    const loop = (now: number) => {
      const p = Math.min((now - start) / duration, 1)
      // Slight ease-in-out
      const eased = p < 0.5 ? 2 * p * p : 1 - Math.pow(-2 * p + 2, 2) / 2
      setProgress(eased)
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
      if (!containerRef.current) return
      const r = containerRef.current.getBoundingClientRect()
      mouseYRef.current = (e.clientY - r.top) / r.height
    }
    window.addEventListener("mousemove", onMove)
    return () => window.removeEventListener("mousemove", onMove)
  }, [])

  // Wobble gives the edge a wavy hand-drawn feel
  const wobbleOffset = Math.sin(progress * 40) * 1.5

  return (
    <div
      ref={containerRef}
      className="relative min-h-screen w-full bg-white flex items-center justify-center overflow-hidden"
    >
      <div
        className="relative"
        style={{ width: "min(70vw, 1000px)", aspectRatio: "4 / 1" }}
      >
        {/* Faint ghost of the logo so it's clear what's being written */}
        <NextImage
          src="/images/logo.png"
          alt=""
          width={1000}
          height={250}
          priority
          className="absolute inset-0 w-full h-auto"
          style={{ opacity: done ? 0 : 0.05 }}
        />

        {/* The "written" portion of the logo */}
        <div
          className="absolute inset-0 transition-opacity duration-700"
          style={{
            clipPath: `polygon(
              0 0,
              ${progress * 100 + wobbleOffset}% 0,
              ${progress * 100 + wobbleOffset + 1}% 25%,
              ${progress * 100 + wobbleOffset - 0.5}% 50%,
              ${progress * 100 + wobbleOffset + 0.5}% 75%,
              ${progress * 100 + wobbleOffset}% 100%,
              0 100%
            )`,
            opacity: done ? 0 : 1,
          }}
        >
          <NextImage
            src="/images/logo.png"
            alt="Studio Vendi"
            width={1000}
            height={250}
            priority
            className="w-full h-auto"
          />
        </div>

        {/* Pen tip indicator */}
        {!done && (
          <>
            {/* Soft ink bleed around pen */}
            <div
              className="absolute rounded-full bg-black"
              style={{
                left: `${progress * 100}%`,
                top: `${50 + (mouseYRef.current - 0.5) * 20}%`,
                width: "40px",
                height: "40px",
                transform: "translate(-50%, -50%)",
                opacity: 0.08,
                filter: "blur(14px)",
              }}
            />
            {/* Pen tip dot */}
            <div
              className="absolute bg-black rounded-full"
              style={{
                left: `${progress * 100}%`,
                top: `${50 + (mouseYRef.current - 0.5) * 20}%`,
                width: "6px",
                height: "6px",
                transform: "translate(-50%, -50%)",
                boxShadow: "0 0 10px rgba(0,0,0,0.6)",
              }}
            />
          </>
        )}

        {/* Final crisp logo */}
        <NextImage
          src="/images/logo.png"
          alt="Studio Vendi"
          width={1000}
          height={250}
          priority
          className={`absolute inset-0 w-full h-auto transition-opacity duration-700 ${
            done ? "opacity-100" : "opacity-0"
          }`}
        />
      </div>
    </div>
  )
}
