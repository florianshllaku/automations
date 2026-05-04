import Link from "next/link"
import Image from "next/image"
import { Instagram, Facebook, Linkedin } from "lucide-react"

export default function ContactPage() {
  return (
    <main className="pt-24 bg-white text-black font-light flex-1 flex flex-col">
      {/* Hero Image - Studio Vendi Branded Banner */}
      <div className="relative w-full aspect-[21/9] mb-16 lg:mb-24">
        <Image
          src="/images/contact-hero-banner.png"
          alt="Studio Vendi"
          fill
          className="object-cover"
          priority
        />
      </div>

      {/* Content */}
      <div className="px-6 lg:px-12 max-w-4xl">
        <h1 className="text-5xl lg:text-6xl font-bold mb-12 lowercase">contact</h1>

        <div className="space-y-8 font-light">
          {/* Address */}
          <div>
            <p className="text-base lg:text-lg">
              Rr. Vellezerit Gervalla, Bregu i Diellit,
            </p>
            <p className="text-base lg:text-lg">Prishtinë 10000</p>
            <p className="text-base lg:text-lg">Kosovë</p>
          </div>

          {/* Phone + Email */}
          <div>
            <p className="text-base lg:text-lg">T +383 49 666 123</p>
            <p className="text-base lg:text-lg">
              <Link
                href="mailto:info@studiovendi.com"
                className="hover:opacity-60 transition-opacity underline underline-offset-4 decoration-1"
              >
                info@studiovendi.com
              </Link>
            </p>
          </div>

          {/* Follow us */}
          <div className="pt-4">
            <p className="text-base lg:text-lg font-bold mb-4">Follow us:</p>
            <div className="flex items-center gap-5">
              <Link
                href="https://www.instagram.com/studiovendi/"
                target="_blank"
                rel="noopener noreferrer"
                aria-label="Instagram"
                className="text-black hover:opacity-60 transition-opacity"
              >
                <Instagram className="w-5 h-5" strokeWidth={1.5} />
              </Link>
              <Link
                href="https://www.facebook.com/profile.php?id=61579407150510"
                target="_blank"
                rel="noopener noreferrer"
                aria-label="Facebook"
                className="text-black hover:opacity-60 transition-opacity"
              >
                <Facebook className="w-5 h-5" strokeWidth={1.5} />
              </Link>
              <Link
                href="https://www.linkedin.com/company/112236834/admin/dashboard/"
                target="_blank"
                rel="noopener noreferrer"
                aria-label="LinkedIn"
                className="text-black hover:opacity-60 transition-opacity"
              >
                <Linkedin className="w-5 h-5" strokeWidth={1.5} />
              </Link>
            </div>
          </div>
        </div>
      </div>
    </main>
  )
}
