import Link from "next/link"

const gallery = [
  { src: "/images/noun-agency-01.png", alt: "noun agency lounge area with KAWS companion and Wassily chair" },
  { src: "/images/noun-agency-02.png", alt: "noun agency reading zone with Togo sofa and glass shelving" },
  { src: "/images/noun-agency-03.png", alt: "noun agency workspace with pool table and ring pendant" },
  { src: "/images/noun-agency-04.png", alt: "noun agency workspace with iMac and clothing rack" },
  { src: "/images/noun-agency-05.png", alt: "noun agency production bay with HP plotters and illuminated sign" },
]

export default function NounAgencyPage() {
  return (
    <main className="pt-20 pb-20 bg-background flex-1">
      {/* Hero image - natural aspect ratio, centered at 50% width */}
      <div className="relative w-full mb-12 lg:mb-20 flex justify-center">
        <img
          src="/images/noun-agency-01.png"
          alt="noun agency interior"
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
          noun agency
        </h1>

        <dl className="grid grid-cols-[auto_1fr] gap-x-8 gap-y-3 text-base lg:text-lg max-w-md">
          <dt className="font-bold lowercase">location</dt>
          <dd className="font-light">Switzerland</dd>

          <dt className="font-bold lowercase">year</dt>
          <dd className="font-light">2024</dd>

          <dt className="font-bold lowercase">type</dt>
          <dd className="font-light">Office</dd>
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
