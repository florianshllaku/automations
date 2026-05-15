import Image from "next/image"

interface Project {
  id: string
  title: string
  location: string
  year: string
  category: string
  status: string
  image: string
}

interface ProjectLayoutProps {
  title: string
  description: string
  projects: Project[]
  categories?: string[]
  locations?: string[]
  statuses?: string[]
}

export function ProjectLayout({
  title,
  description,
  projects,
}: ProjectLayoutProps) {
  return (
    <main className="min-h-screen pt-24 pb-20 px-6 lg:px-12">
      {/* Header Section */}
      <div className="max-w-3xl mb-16">
        <h1 className="text-sm font-medium uppercase tracking-wider mb-4">{title}</h1>
        <p className="text-base lg:text-lg leading-relaxed text-foreground/80">{description}</p>
      </div>

      {/* Projects Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 lg:gap-8">
        {projects.map((project) => (
          <div key={project.id}>
            <div className="aspect-[4/3] relative overflow-hidden mb-4">
              <Image
                src={project.image}
                alt={project.title}
                fill
                className="object-cover"
              />
            </div>
            <h3 className="text-sm font-medium mb-1">{project.title}</h3>
            <p className="text-xs text-muted-foreground">
              {project.location} — {project.year}
            </p>
          </div>
        ))}
      </div>
    </main>
  )
}
