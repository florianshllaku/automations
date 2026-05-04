"use client"

import Link from "next/link"
import { useState } from "react"
import { Menu, X } from "lucide-react"
import { cn } from "@/lib/utils"

const menuLinks = [
  { label: "about us", href: "/about" },
  { label: "contact", href: "/contact" },
  { label: "careers", href: "/careers" },
]

const projectLinks = [
  { label: "architecture", href: "/architecture" },
  { label: "interiors", href: "/interiors" },
  { label: "graphics", href: "/design" },
]

export function Header() {
  const [menuOpen, setMenuOpen] = useState(false)
  const [projectsOpen, setProjectsOpen] = useState(false)

  return (
    <>
      <header className="fixed top-0 left-0 right-0 z-50 bg-white">
        <nav className="flex items-center justify-between px-6 py-4 lg:px-12">
          {/* Menu Button */}
          <button
            onClick={() => setMenuOpen(!menuOpen)}
            className="p-2 -ml-2 hover:opacity-60 transition-opacity"
            aria-label="Toggle menu"
          >
            {menuOpen ? (
              <X className="w-6 h-6" strokeWidth={1.5} />
            ) : (
              <Menu className="w-6 h-6" strokeWidth={1.5} />
            )}
          </button>

          {/* Logo Mark — Home Button */}
          <Link
            href="/"
            onClick={() => setMenuOpen(false)}
            className="hover:opacity-60 transition-opacity -mr-2"
            aria-label="Go to homepage"
          >
            <img
              src="/images/logo-mark.png"
              alt="studiovendi home"
              className="h-3 w-auto"
            />
          </Link>
        </nav>
      </header>

      {/* Full Screen Menu */}
      <div
        className={cn(
          "fixed inset-0 z-40 bg-background transition-transform duration-500 ease-in-out pt-20",
          menuOpen ? "translate-x-0" : "-translate-x-full"
        )}
      >
        <div className="h-full overflow-auto px-6 lg:px-12 py-8">
          <ul className="flex flex-col gap-4">
            {/* Projects with dropdown */}
            <li>
              <button
                onClick={() => setProjectsOpen(!projectsOpen)}
                className="text-2xl lg:text-3xl font-bold hover:opacity-60 transition-opacity flex items-center gap-2"
                aria-expanded={projectsOpen}
              >
                projects
                <span
                  className={cn(
                    "inline-block transition-transform duration-300 text-xl",
                    projectsOpen ? "rotate-90" : ""
                  )}
                >
                  ›
                </span>
              </button>

              {/* Projects dropdown list */}
              <div
                className={cn(
                  "overflow-hidden transition-all duration-300 ease-in-out",
                  projectsOpen ? "max-h-96 mt-4" : "max-h-0"
                )}
              >
                <ul className="flex flex-col gap-2 pl-6">
                  {projectLinks.map((link) => (
                    <li key={link.href}>
                      <Link
                        href={link.href}
                        onClick={() => setMenuOpen(false)}
                        className="text-xl lg:text-2xl font-light hover:opacity-60 transition-opacity lowercase"
                      >
                        {link.label}
                      </Link>
                    </li>
                  ))}
                </ul>
              </div>
            </li>

            {/* Other menu links below Projects */}
            {menuLinks.map((link) => (
              <li key={link.href}>
                <Link
                  href={link.href}
                  onClick={() => setMenuOpen(false)}
                  className="text-2xl lg:text-3xl font-bold hover:opacity-60 transition-opacity lowercase"
                >
                  {link.label}
                </Link>
              </li>
            ))}
          </ul>
        </div>
      </div>

    </>
  )
}
