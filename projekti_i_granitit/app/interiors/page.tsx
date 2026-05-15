import Image from "next/image"
import Link from "next/link"

const projects = [
  {
    slug: "private-airbnb",
    title: "private airbnb",
    location: "Stuttgart, Germany",
    year: "2025",
    type: "Commercial-Public",
    image: "/images/private-airbnb-10.png",
  },
  {
    slug: "vr-apartment",
    title: "v.r. apartment",
    location: "Kosovë",
    year: "2024",
    type: "Residential",
    image: "/images/vr-apartment-07.png",
  },
  {
    slug: "noun-agency",
    title: "noun agency",
    location: "Switzerland",
    year: "2024",
    type: "Office",
    image: "/images/noun-agency-02.png",
  },
  {
    slug: "fa-apartment",
    title: "f.a. apartment",
    location: "Kosovë, Prishtinë",
    year: "2025",
    type: "Residential",
    image: "/images/header_POSTEDIT.png",
  },
  {
    slug: "br-private-villa",
    title: "br. private villa",
    location: "Bern, Switzerland",
    year: "2025",
    type: "Residential",
    image: "/images/header_POSTEDIT2.png",
  },
]

export default function InteriorsPage() {
  return (
    <main className="pb-20 bg-background flex-1">
      {/* Hero Image — Full Viewport */}
      <div className="relative w-full h-screen mb-16 lg:mb-24">
        <Image
          src="/images/interiors-hero-banner.png"
          alt="studiovendi interiors"
          fill
          priority
          className="object-cover"
          sizes="100vw"
        />
        <div className="absolute inset-0 bg-gradient-to-b from-black/10 via-transparent to-black/40" />
        <div className="absolute bottom-10 left-6 lg:left-12">
          <p className="text-white/60 text-xs tracking-[0.3em] uppercase font-light mb-2">studiovendi</p>
          <h1 className="text-white text-5xl lg:text-7xl font-bold lowercase">interiors</h1>
        </div>
      </div>

      {/* Content */}
      <div className="px-6 lg:px-12 max-w-4xl">
        <div className="space-y-8 font-light text-base lg:text-lg leading-relaxed">
          <p>
            <span className="font-bold lowercase">studiovendi</span> places
            particular importance on interior spaces, treating them not merely
            as physical structures, but as living organisms that carry memory,
            function, and human sensitivity. Every space holds its own
            character, its rhythm, and a silent way of communicating with those
            who experience it.
          </p>

          <p>
            Our intention is to preserve this inner identity, not by covering
            it with unnecessary form, but by revealing it through a careful
            and considered approach. We believe that design should not impose
            itself, but rather uncover what already exists at the essence of a
            space.
          </p>

          <p>
            Each project should create a sense of approachability, a quiet
            invitation to enter and to stay. Spaces must be welcoming not only
            in an aesthetic sense, but also emotionally, building a natural
            connection between the human being and the environment that
            surrounds them.
          </p>

          <p>
            In this way, design becomes an act of sensitive interpretation,
            where form, light, and material come together to create an
            experience that is felt more than it is seen.
          </p>
        </div>
      </div>

      {/* Projects grid */}
      <section className="px-6 lg:px-12 mt-24 lg:mt-32">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 lg:gap-12">
          {projects.map((project) => (
            <Link
              key={project.slug}
              href={`/interiors/${project.slug}`}
              className="group block relative overflow-hidden"
            >
              <div className="relative w-full aspect-[4/3] overflow-hidden bg-neutral-100">
                {project.image && (
                  <Image
                    src={project.image}
                    alt={project.title}
                    fill
                    className="object-cover transition-transform duration-[1200ms] ease-out group-hover:scale-105"
                    sizes="(max-width: 768px) 100vw, 50vw"
                  />
                )}

                {/* Dark overlay fades in on hover */}
                <div className="absolute inset-0 bg-black/0 group-hover:bg-black/40 transition-colors duration-500 ease-out" />

                {/* Project info overlay — fades up on hover */}
                <div className="absolute inset-0 flex flex-col justify-end p-6 lg:p-8 opacity-0 translate-y-4 group-hover:opacity-100 group-hover:translate-y-0 transition-all duration-500 ease-out">
                  <h3 className="text-2xl lg:text-3xl font-bold lowercase text-white mb-2">
                    {project.title}
                  </h3>
                  <p className="text-sm lg:text-base font-light text-white/90">
                    {project.location} · {project.year} · {project.type}
                  </p>
                </div>
              </div>
            </Link>
          ))}
        </div>
      </section>
    </main>
  )
}
