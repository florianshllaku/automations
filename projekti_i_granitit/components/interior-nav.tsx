"use client"

import Link from "next/link"
import { useEffect, useState } from "react"

interface NavItem {
  href: string
  label: string
}

interface InteriorNavProps {
  prev?: NavItem
  next?: NavItem
}

export function InteriorNav({ prev, next }: InteriorNavProps) {
  const [visible, setVisible] = useState(false)

  useEffect(() => {
    const handleScroll = () => {
      setVisible(window.scrollY > window.innerHeight * 0.6)
    }
    window.addEventListener("scroll", handleScroll, { passive: true })
    return () => window.removeEventListener("scroll", handleScroll)
  }, [])

  return (
    <div
      className={`fixed bottom-14 left-1/2 -translate-x-1/2 z-40 flex items-center gap-4 md:gap-10 w-[90vw] md:w-auto justify-between md:justify-normal transition-opacity duration-300 ${
        visible ? "opacity-100 pointer-events-auto" : "opacity-0 pointer-events-none"
      }`}
    >
      {prev ? (
        <Link
          href={prev.href}
          className="text-sm font-light lowercase bg-white/80 backdrop-blur-sm px-4 py-3 hover:opacity-60 transition-opacity"
        >
          ← {prev.label}
        </Link>
      ) : (
        <span className="w-0" />
      )}
      {next ? (
        <Link
          href={next.href}
          className="text-sm font-light lowercase bg-white/80 backdrop-blur-sm px-4 py-3 hover:opacity-60 transition-opacity"
        >
          {next.label} →
        </Link>
      ) : (
        <span className="w-0" />
      )}
    </div>
  )
}
