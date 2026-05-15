import Link from "next/link"
import { InteriorNav } from "@/components/interior-nav"

const gallery = [
  { src: "/images/noun-agency-01.png", alt: "noun agency lounge area with KAWS companion and Wassily chair" },
  { src: "/images/noun-agency-02.png", alt: "noun agency reading zone with Togo sofa and glass shelving" },
  { src: "/images/noun-agency-03.png", alt: "noun agency workspace with pool table and ring pendant" },
  { src: "/images/noun-agency-04.png", alt: "noun agency workspace with iMac and clothing rack" },
  { src: "/images/noun-agency-05.png", alt: "noun agency production bay with HP plotters and illuminated sign" },
]

export default function NounAgencyPage() {
  return (
    <main className="pb-20 bg-background flex-1">
      {/* Hero — Full Viewport */}
      <div className="relative w-full h-screen mb-16 lg:mb-24 overflow-hidden">
        <img
          src="/images/noun-agency-01.png"
          alt="noun agency interior"
          className="absolute inset-0 w-full h-full object-cover"
        />
        <div className="absolute inset-0 bg-gradient-to-b from-black/10 via-transparent to-black/40" />
        <div className="absolute bottom-10 left-6 lg:left-12">
          <p className="text-white/60 text-xs tracking-[0.3em] uppercase font-light mb-2">studiovendi</p>
          <h1 className="text-white text-5xl lg:text-7xl font-bold lowercase">noun agency</h1>
        </div>
      </div>

      {/* Content Container */}
      <div className="px-6 lg:px-12 max-w-6xl mx-auto">
        {/* Metadata Grid */}
        <dl className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-16 pb-16 border-b border-border">
          <div>
            <dt className="text-sm font-bold mb-1">Location</dt>
            <dd className="text-base font-light">Switzerland</dd>
          </div>
          <div>
            <dt className="text-sm font-bold mb-1">Year</dt>
            <dd className="text-base font-light">2024</dd>
          </div>
          <div>
            <dt className="text-sm font-bold mb-1">Type</dt>
            <dd className="text-base font-light">Office</dd>
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
        <p>Set in Winterthur, the space unfolds through a restrained monochromatic palette of black, white, and grey, where geometry and materiality take precedence over decoration. Natural light filters through vertical louvers, casting controlled bands of shadow that move across the surfaces, creating a quiet chiaroscuro effect with a distinctly cinematic, almost clinical precision.</p>
        <p>The furniture reads less as utility and more as a curated collection of objects. A chair inspired by the Wassily Chair introduces a tactile contrast through its tubular metal frame and cowhide-like texture, softening the rigidity of the setting. Nearby, a transparent acrylic armchair plays with perception, its black cylindrical supports grounding an otherwise weightless form. The presence of a KAWS Companion in matte black shifts the interior toward a gallery-like atmosphere, embedding a layer of pop-cultural reference within an otherwise disciplined composition.</p>
        <p>Material contrasts define the spatial experience. Reflective surfaces, such as the mirrored glass table and the polished floor, disperse light and subtly expand the room's visual boundaries. In opposition, the dense black carpet and the creased leather sofa absorb light, adding depth and anchoring the composition. Raw, almost brutalist accessories with stone-like textures introduce a sense of weight and tactility, preventing the space from becoming overly polished or sterile.</p>
        <p>What emerges is an interior that balances restraint with intention. It avoids conventional notions of comfort, instead leaning into a colder, more controlled aesthetic where each element is carefully positioned and visually accountable. The result feels less like a living space and more like a precisely composed environment—somewhere between a private gallery and a staged architectural statement.</p>
      </div>

      {/* Gallery - centered at 50% width, stacked images at natural aspect ratios */}
      <div className="flex flex-col gap-3 lg:gap-6 items-center">
        {gallery.slice(1).map((img) => (
          <div key={img.src} className="relative w-full md:w-1/2">
            <img
              src={img.src}
              alt={img.alt}
              className="w-full h-auto"
            />
          </div>
        ))}
      </div>

      <InteriorNav
        prev={{ href: "/interiors/vr-apartment", label: "v.r. apartment" }}
        next={{ href: "/interiors/fa-apartment", label: "f.a. apartment" }}
      />
    </main>
  )
}
