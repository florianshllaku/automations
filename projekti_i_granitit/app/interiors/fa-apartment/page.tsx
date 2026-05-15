import Link from "next/link"
import { InteriorNav } from "@/components/interior-nav"

const gallery = [
  "/images/001_POSTEDIT.png",
  "/images/002_POSTEDIT.png",
  "/images/003_POSTEDIT.png",
  "/images/004_POSTEDIT.png",
  "/images/005_POSTEDIT.png",
  "/images/006_POSTEDIT.png",
  "/images/007_POSTEDIT.png",
  "/images/008_POSTEDIT.png",
  "/images/009_POSTEDIT.png",
  "/images/010_POSTEDIT.png",
  "/images/011_POSTEDIT.png",
]

export default function FAApartmentPage() {
  return (
    <main className="pb-20 bg-background flex-1">
      {/* Hero — Full Viewport */}
      <div className="relative w-full h-screen mb-16 lg:mb-24 overflow-hidden">
        <img
          src="/images/header_POSTEDIT.png"
          alt="f.a. apartment"
          className="absolute inset-0 w-full h-full object-cover"
        />
        <div className="absolute inset-0 bg-gradient-to-b from-black/10 via-transparent to-black/40" />
        <div className="absolute bottom-10 left-6 lg:left-12">
          <p className="text-white/60 text-xs tracking-[0.3em] uppercase font-light mb-2">studiovendi</p>
          <h1 className="text-white text-5xl lg:text-7xl font-bold lowercase">f.a. apartment</h1>
        </div>
      </div>

      {/* Content Container */}
      <div className="px-6 lg:px-12 max-w-6xl mx-auto">
        {/* Metadata Grid */}
        <dl className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-16 pb-16 border-b border-border">
          <div>
            <dt className="text-sm font-bold mb-1">Location</dt>
            <dd className="text-base font-light">Kosovë, Prishtinë</dd>
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
        <p>Set in Prishtina, this 2025 residential interior shifts away from stark contrast and instead embraces a warm, earthy palette built on layers of chocolate tones, bronze, muted gold, natural wood, and grey-veined marble. The atmosphere feels composed yet inviting—there's a sense of comfort without compromising on precision or visual control.</p>
        <p>The media wall becomes the anchor of the space, treated as a fully integrated architectural element rather than a backdrop. A large, subtly textured black panel absorbs the presence of the TV, allowing it to recede when not in use. Beneath it, a long stretch of white marble with soft grey veining grounds the composition, acting as a continuous base where a few restrained objects—candles, delicate vessels—sit with intention rather than decoration. To one side, built-in shelving introduces a curated vertical moment, where sculptural ceramics and quiet forms add rhythm without disrupting the overall calm.</p>
        <p>What gives the space its balance is the dialogue between strict lines and softened forms. The architecture leans into linear precision—ribbed wood panels, extended glass frames, and thin ceiling elements establish a clear grid—while the furniture counters this with rounded silhouettes. A large, curved sofa in chocolate velvet and a polished bronze table introduce a sense of flow, breaking the rigidity just enough to keep the space from feeling static.</p>
        <p>Materiality plays a central role in how the space is experienced. Bronze and warm metallic finishes catch and reflect light subtly, while marble appears in two distinct expressions—one more restrained and linear along the media wall, the other more dramatic in the background. Concealed lighting under shelves and along the marble base adds a soft glow that enhances texture rather than overpowering it, while ceiling spotlights remain minimal and almost invisible.</p>
        <p>Toward the back, the space opens fluidly into another zone, where a darker, more reflective palette takes over. A sculptural marble island and glossy wall panels suggest a continuation of the same design language, but with a slightly more dramatic tone. The transition feels intentional—less like moving between rooms and more like shifting through layers of the same spatial narrative.</p>
      </div>

      {/* Gallery */}
      <div className="flex flex-col gap-3 lg:gap-6 items-center">
        {gallery.map((src, index) => (
          <div key={src} className="relative w-full md:w-1/2">
            <img
              src={src}
              alt={`f.a. apartment view ${index + 1}`}
              className="w-full h-auto"
            />
          </div>
        ))}
      </div>

      <InteriorNav
        prev={{ href: "/interiors/noun-agency", label: "noun agency" }}
        next={{ href: "/interiors/br-private-villa", label: "br. private villa" }}
      />
    </main>
  )
}
