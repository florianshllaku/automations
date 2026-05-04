import Link from "next/link"

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

      {/* Title + metadata */}
      <div className="px-6 lg:px-12 max-w-4xl mb-16 lg:mb-24">
        <Link
          href="/interiors"
          className="inline-block text-sm font-light lowercase mb-6 hover:opacity-60 transition-opacity"
        >
          ← back to interiors
        </Link>

        <h1 className="text-3xl lg:text-5xl font-bold mb-10 lg:mb-14 lowercase">
          v.r. apartment
        </h1>

        <dl className="grid grid-cols-[auto_1fr] gap-x-8 gap-y-3 text-base lg:text-lg max-w-md">
          <dt className="font-bold lowercase">location</dt>
          <dd className="font-light">Kosovë</dd>

          <dt className="font-bold lowercase">year</dt>
          <dd className="font-light">2024</dd>

          <dt className="font-bold lowercase">type</dt>
          <dd className="font-light">Residential</dd>
        </dl>
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
    </main>
  )
}
