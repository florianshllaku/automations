import Link from "next/link"
import { InteriorNav } from "@/components/interior-nav"

const gallery = [
  "/images/001_POSTEDIT2.png",
  "/images/002_POSTEDIT2.png",
  "/images/003_POSTEDIT2.png",
  "/images/004_POSTEDIT2.png",
  "/images/005_POSTEDIT2.png",
  "/images/006_POSTEDIT2.png",
  "/images/007_POSTEDIT2.png",
  "/images/008_POSTEDIT2.png",
  "/images/009_POSTEDIT2.png",
  "/images/010_POSTEDIT2.png",
  "/images/011_POSTEDIT2.png",
  "/images/012_POSTEDIT2.png",
  "/images/013_POSTEDIT2.png",
  "/images/015_POSTEDIT2.png",
  "/images/016_POSTEDIT2.png",
  "/images/020_POSTEDIT2.png",
  "/images/021_POSTEDIT2.png",
  "/images/022_POSTEDIT2.png",
  "/images/014_POSTEDIT2.png",
  "/images/017_POSTEDIT2.png",
  "/images/019_POSTEDIT2.png",
  "/images/018_POSTEDIT2.png",
]

export default function BRPrivateVillaPage() {
  return (
    <main className="pb-20 bg-background flex-1">
      {/* Hero — Full Viewport */}
      <div className="relative w-full h-screen mb-16 lg:mb-24 overflow-hidden">
        <img
          src="/images/header_POSTEDIT2.png"
          alt="br. private villa"
          className="absolute inset-0 w-full h-full object-cover"
        />
        <div className="absolute inset-0 bg-gradient-to-b from-black/10 via-transparent to-black/40" />
        <div className="absolute bottom-10 left-6 lg:left-12">
          <p className="text-white/60 text-xs tracking-[0.3em] uppercase font-light mb-2">studiovendi</p>
          <h1 className="text-white text-5xl lg:text-7xl font-bold lowercase">br. private villa</h1>
        </div>
      </div>

      {/* Content Container */}
      <div className="px-6 lg:px-12 max-w-6xl mx-auto">
        {/* Metadata Grid */}
        <dl className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-16 pb-16 border-b border-border">
          <div>
            <dt className="text-sm font-bold mb-1">Location</dt>
            <dd className="text-base font-light">Bern, Switzerland</dd>
          </div>
          <div>
            <dt className="text-sm font-bold mb-1">Year</dt>
            <dd className="text-base font-light">2025</dd>
          </div>
          <div>
            <dt className="text-sm font-bold mb-1">Type</dt>
            <dd className="text-base font-light">Residential</dd>
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

      {/* Project Description */}
      <div className="w-full px-6 md:px-0 md:w-1/2 mx-auto mb-12 lg:mb-16 space-y-5 font-light text-sm lg:text-base leading-relaxed">
        <p>This residential project, conceived and realized with a holistic approach to modern luxury, represents a sophisticated unification of noble materials and architectural lighting. Our goal was to create a seamless visual flow between the spaces, where every detail speaks of calm and disciplined elegance.</p>
        <p>In the living space, we prioritized the warmth of walnut wood, using it as a long modular backdrop for the media area. To break the uniformity and add a natural dramatic touch, we integrated a vertical element of green marble (Verde Alpi). This stone not only adds color and movement, but also serves as a visual bridge to the dining area. Modular sofas in sand tones and textured carpet were chosen to offer maximum comfort without weighing down the look, while hidden LED cove lighting on the ceiling and behind the panels was designed to create a welcoming atmosphere and give the walls a "breathing" feel.</p>
        <p>The transition to the kitchen and dining area was achieved through a continuity of materials, but giving the green marble the leading role. The large island and the protective wall (backsplash) are completely covered in this noble stone, which is illuminated by thin, integrated shelves to emphasize its dramatic features. We chose the linear lighting above the dining table to be minimalist and technical, allowing the attention to remain on the rich textures. Sculptural design chairs and a glass-enclosed wine cellar complete this environment that aims to offer the experience of an elite private restaurant within the home.</p>
        <p>The bedroom was conceived as an oasis of calm, while maintaining the same rich palette. The walnut-paneled wall behind the bed serves as a large architectural headboard, creating a sense of protection and privacy. The bed with a thin base and a brown suede leather headboard harmonizes with the textile covers in earth tones. For the large windows, we integrated black Venetian blinds, which allow for precise light control and create shadow plays on the herringbone parquet. The bronze pendant lamps on the sides of the bed were added as a sophisticated metallic detail to complete the composition.</p>
        <p>Through this project, we have proven how "heavy" materials such as marble and wood can be balanced through a light architecture of light and clean lines, resulting in a residence that is as functional as it is a work of art.</p>
      </div>

      {/* Gallery */}
      <div className="flex flex-col gap-3 lg:gap-6 items-center">
        {gallery.map((src, index) => (
          <div key={src} className="relative w-full md:w-1/2">
            <img
              src={src}
              alt={`br. private villa view ${index + 1}`}
              className="w-full h-auto"
            />
          </div>
        ))}
      </div>

      <InteriorNav prev={{ href: "/interiors/fa-apartment", label: "f.a. apartment" }} />
    </main>
  )
}
