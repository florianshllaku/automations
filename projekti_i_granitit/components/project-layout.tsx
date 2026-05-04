"use client"

import Image from "next/image"
import Link from "next/link"
import { useState } from "react"
import { List } from "lucide-react"

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
  categories = [],
  locations = [],
  statuses = [],
}: ProjectLayoutProps) {
  const [selectedCategory, setSelectedCategory] = useState("All categories")
  const [selectedLocation, setSelectedLocation] = useState("All locations")
  const [selectedStatus, setSelectedStatus] = useState("All statuses")
  const [viewMode, setViewMode] = useState<"grid" | "list">("grid")

  const filteredProjects = projects.filter((project) => {
    if (selectedCategory !== "All categories" && project.category !== selectedCategory) return false
    if (selectedLocation !== "All locations" && project.location !== selectedLocation) return false
    if (selectedStatus !== "All statuses" && project.status !== selectedStatus) return false
    return true
  })

  return (
    <main className="min-h-screen pt-24 pb-20 px-6 lg:px-12">
      {/* Header Section */}
      <div className="max-w-3xl mb-16">
        <h1 className="text-sm font-medium uppercase tracking-wider mb-4">{title}</h1>
        <p className="text-base lg:text-lg leading-relaxed text-foreground/80">{description}</p>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-4 mb-12">
        <span className="text-sm font-medium">Filter by:</span>
        
        {categories.length > 0 && (
          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="bg-foreground/10 text-sm px-4 py-2 rounded-none appearance-none cursor-pointer min-w-[160px]"
          >
            <option>All categories</option>
            {categories.map((cat) => (
              <option key={cat}>{cat}</option>
            ))}
          </select>
        )}

        {locations.length > 0 && (
          <select
            value={selectedLocation}
            onChange={(e) => setSelectedLocation(e.target.value)}
            className="bg-foreground/10 text-sm px-4 py-2 rounded-none appearance-none cursor-pointer min-w-[160px]"
          >
            <option>All locations</option>
            {locations.map((loc) => (
              <option key={loc}>{loc}</option>
            ))}
          </select>
        )}

        {statuses.length > 0 && (
          <select
            value={selectedStatus}
            onChange={(e) => setSelectedStatus(e.target.value)}
            className="bg-foreground/10 text-sm px-4 py-2 rounded-none appearance-none cursor-pointer min-w-[160px]"
          >
            <option>All statuses</option>
            {statuses.map((status) => (
              <option key={status}>{status}</option>
            ))}
          </select>
        )}

        <div className="ml-auto">
          <button
            onClick={() => setViewMode(viewMode === "grid" ? "list" : "grid")}
            className="flex items-center gap-2 text-sm hover:opacity-60 transition-opacity"
          >
            <List className="w-4 h-4" />
            {viewMode === "grid" ? "List" : "Grid"}
          </button>
        </div>
      </div>

      {/* Projects Grid */}
      {viewMode === "grid" ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 lg:gap-8">
          {filteredProjects.map((project) => (
            <Link
              key={project.id}
              href={`/projects/${project.id}`}
              className="group"
            >
              <div className="aspect-[4/3] relative overflow-hidden mb-4">
                <Image
                  src={project.image}
                  alt={project.title}
                  fill
                  className="object-cover transition-transform duration-500 group-hover:scale-105"
                />
              </div>
              <h3 className="text-sm font-medium mb-1">{project.title}</h3>
              <p className="text-xs text-muted-foreground">
                {project.location} — {project.year}
              </p>
            </Link>
          ))}
        </div>
      ) : (
        <div className="space-y-4">
          {filteredProjects.map((project) => (
            <Link
              key={project.id}
              href={`/projects/${project.id}`}
              className="flex items-center gap-6 py-4 border-b border-foreground/10 hover:opacity-60 transition-opacity"
            >
              <div className="w-24 h-16 relative flex-shrink-0">
                <Image
                  src={project.image}
                  alt={project.title}
                  fill
                  className="object-cover"
                />
              </div>
              <div className="flex-1">
                <h3 className="text-sm font-medium">{project.title}</h3>
                <p className="text-xs text-muted-foreground">
                  {project.location} — {project.year}
                </p>
              </div>
              <span className="text-xs text-muted-foreground hidden md:block">
                {project.category}
              </span>
            </Link>
          ))}
        </div>
      )}

      {/* Load More */}
      <div className="mt-12">
        <button className="bg-foreground text-background px-6 py-3 text-sm hover:opacity-80 transition-opacity">
          Load more
        </button>
      </div>

    </main>
  )
}
