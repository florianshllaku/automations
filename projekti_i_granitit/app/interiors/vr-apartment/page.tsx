import Link from "next/link"
import { InteriorNav } from "@/components/interior-nav"

const gallery = [
  { src: "/images/vr-apartment-07.png", alt: "v.r. apartment living room with marble fireplace and media wall" },
  { src: "/images/vr-apartment-02.png", alt: "v.r. apartment living room with black spiral staircase" },
  { src: "/images/vr-apartment-04.png", alt: "v.r. apartment living area with spiral staircase and marble media wall" },
  { src: "/images/vr-apartment-01.png", alt: "v.r. apartment kitchen island with marble countertop" },
  { src: "/images/vr-apartment-08.png", alt: "v.r. apartment open plan kitchen and dining" },
  { src: "/images/vr-apartment-05.png", alt: "v.r. apartment dining area with wood table and open shelving" },
  { src: "/images/vr-apartment-06.png", alt: "v.r. apartment dining table detail from above" },
  { src: "/images/vr-apartment-03.png", alt: "v.r. apartment open living and kitchen view" },
]

export default function VRApartmentPage() {
  return (
    <main className="pt-20 pb-20 bg-background flex-1">
      {/* Hero image - natural aspect ratio, centered at 50% width */}
      <div className="relative w-full mb-12 lg:mb-20 flex justify-center">
        <img
          src={gallery[0].src}
          alt={gallery[0].alt}
          className="w-1/2 h-auto"
        />
      </div>

      {/* Content Container */}
      <div className="px-6 lg:px-12 max-w-6xl mx-auto">
        {/* Title */}
        <h1 className="text-5xl lg:text-6xl font-bold mb-8 lowercase">
          v.r. apartment
        </h1>

        {/* Metadata Grid */}
        <dl className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-16 pb-16 border-b border-border">
          <div>
            <dt className="text-sm font-bold mb-1">Location</dt>
            <dd className="text-base font-light">Kosovë</dd>
          </div>
          <div>
            <dt className="text-sm font-bold mb-1">Year</dt>
            <dd className="text-base font-light">2024</dd>
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

      {/* Project Description - same width as images */}
      <div className="w-1/2 mx-auto mb-12 lg:mb-16 space-y-5 font-light text-sm lg:text-base leading-relaxed">
        <p>This environment represents an elegant interweaving of neoclassical and contemporary styles, where a special attention is paid to symmetry and noble materials such as marble and wood.</p>
        <p>The living space is dominated by a marble fireplace with its own ash that stands as a reference point, surrounded by wall frames that give structure and a kind of architectural order to the room. The media wall is conceived as a collage of textures, where the wood panel with vertical veins breaks the coldness of the calacatta marble, while an integrated library on the side adds a functional element that fills the volume. A very artistic detail is the organically shaped mirror and the hanging lampshade that resembles tree branches with white flowers, bringing a sense of naturalness to an environment with mainly straight lines.</p>
        <p>Moving towards the kitchen area, the design takes on a more "shaker" and traditional character, but refreshed with neutral colors such as "greige" and browns. The dark center island serves as a strong visual contrast to the rest of the furnishings, connecting beautifully with the marble surface that is repeated here as well. The use of metal mesh on the cabinet doors and open shelves gives the kitchen a slightly European rustic feel, while modern stainless steel appliances keep it firmly within our time.</p>
        <p>A careful mix of light sources is noticeable around, from the spherical lampshades above the island to the small lamps above the dining table, which create a soft, layered lighting. The entire house follows an open flow where the warm wood floor serves as a unifying element, creating a natural transition between the relaxation area and the cooking area.</p>
      </div>

      {/* Gallery - centered at 50% width, stacked images at natural aspect ratios */}
      <div className="flex flex-col gap-3 lg:gap-6 items-center">
        {gallery.slice(1).map((img) => (
          <div key={img.src} className="relative w-1/2">
            <img
              src={img.src}
              alt={img.alt}
              className="w-full h-auto"
            />
          </div>
        ))}
      </div>

      <InteriorNav
        prev={{ href: "/interiors/private-airbnb", label: "private airbnb" }}
        next={{ href: "/interiors/noun-agency", label: "noun agency" }}
      />
    </main>
  )
}
