import Image from "next/image"
import Link from "next/link"

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
    <main className="pt-20 pb-20 bg-background flex-1">
      {/* Hero Image - natural aspect ratio, centered at 50% width */}
      <div className="relative w-full mb-12 flex justify-center">
        <img
          src={images[0]}
          alt="Private Airbnb"
          className="w-1/2 h-auto"
        />
      </div>

      {/* Content Container */}
      <div className="px-6 lg:px-12 max-w-6xl mx-auto">
        {/* Title */}
        <h1 className="text-5xl lg:text-6xl font-bold mb-8 lowercase">
          private airbnb
        </h1>

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

      {/* Image Gallery - Centered at 50% Width, natural aspect ratios */}
      <div className="space-y-0 flex flex-col items-center">
        {images.slice(1).map((image, index) => (
          <div key={index} className="relative w-1/2">
            <img
              src={image}
              alt={`Private Airbnb view ${index + 2}`}
              className="w-full h-auto"
            />
          </div>
        ))}
      </div>
    </main>
  )
}
