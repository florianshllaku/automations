import Image from "next/image"
import Link from "next/link"
import { InteriorNav } from "@/components/interior-nav"

export default function PrivateAirbnbPage() {
  const images = [
    "/images/private-airbnb-10.png",
    "/images/private-airbnb-01.png",
    "/images/private-airbnb-02.png",
    "/images/private-airbnb-03.png",
    "/images/private-airbnb-04.png",
    "/images/private-airbnb-05.png",
    "/images/private-airbnb-06.png",
    "/images/private-airbnb-07.png",
    "/images/private-airbnb-08.png",
    "/images/private-airbnb-09.png",
    "/images/private-airbnb-11.png",
    "/images/private-airbnb-12.png",
    "/images/private-airbnb-13.png",
    "/images/private-airbnb-14.png",
  ]

  return (
    <main className="pb-20 bg-background flex-1">
      {/* Hero — Full Viewport */}
      <div className="relative w-full h-screen mb-16 lg:mb-24 overflow-hidden">
        <video
          src="/images/header_aribnb.mp4"
          autoPlay
          muted
          loop
          playsInline
          className="absolute inset-0 w-full h-full object-cover"
        />
        <div className="absolute inset-0 bg-gradient-to-b from-black/10 via-transparent to-black/40" />
        <div className="absolute bottom-10 left-6 lg:left-12">
          <p className="text-white/60 text-xs tracking-[0.3em] uppercase font-light mb-2">studiovendi</p>
          <h1 className="text-white text-5xl lg:text-7xl font-bold lowercase">private airbnb</h1>
        </div>
      </div>

      {/* Content Container */}
      <div className="px-6 lg:px-12 max-w-6xl mx-auto">
        {/* Metadata Grid */}
        <dl className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-16 pb-16 border-b border-border">
          <div>
            <dt className="text-sm font-bold mb-1">Location</dt>
            <dd className="text-base font-light">Stuttgart, Germany</dd>
          </div>
          <div>
            <dt className="text-sm font-bold mb-1">Year</dt>
            <dd className="text-base font-light">2025</dd>
          </div>
          <div>
            <dt className="text-sm font-bold mb-1">Type</dt>
            <dd className="text-base font-light">Commercial-Public</dd>
          </div>
        </dl>

        {/* Back Link */}
        <Link
          href="/interiors"
          className="inline-block text-sm font-light hover:opacity-60 transition-opacity mb-16"
        >
          ← back to interiors
        </Link>
      </div>

      {/* Project Description - same width as images */}
      <div className="w-full px-6 md:px-0 md:w-1/2 mx-auto mb-12 lg:mb-16 space-y-5 font-light text-sm lg:text-base leading-relaxed">
        <p>The space is conceived as a central living environment, where balance between composition, color, and volume shapes a refined and cohesive atmosphere, creating a clear and coherent spatial experience.</p>
        <p>Design approach is based on visual clarity and the use of uniformly colored materials, contributing to a calm and contemporary aesthetic.</p>
        <p>Clean surfaces and balanced tones define a functional space with a refined visual presence. The space follows the same formal logic, where controlled colors and simple forms support a calm and balanced atmosphere.</p>
        <p>The composition aims to provide visual comfort and a sense of ease in everyday use. The design adopts a more expressive character, placing different architectural languages in dialogue.</p>
        <p>The contrast between form and color creates a strong visual identity and a distinctive moment within the project. The spatial treatment maintains conceptual coherence through the use of colored materials and a clean compositional approach.</p>
        <p>A restrained and controlled aesthetic contributes to a clear, orderly, and functional environment. The design continues with the same visual language, supporting a calm and balanced environment.</p>
        <p>Colors, light, and form work together to create a consistent and comfortable spatial experience.</p>
      </div>

      {/* Image Gallery - Centered at 50% Width, natural aspect ratios */}
      <div className="flex flex-col gap-3 lg:gap-6 items-center">
        {images.slice(1).map((image, index) => (
          <div key={index} className="relative w-full md:w-1/2">
            <img
              src={image}
              alt={`Private Airbnb view ${index + 2}`}
              className="w-full h-auto"
            />
          </div>
        ))}
      </div>

      <InteriorNav next={{ href: "/interiors/vr-apartment", label: "v.r. apartment" }} />
    </main>
  )
}
