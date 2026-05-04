import { ProjectLayout } from "@/components/project-layout"

const projects = [
  {
    id: "brand-identity-luxury",
    title: "Luxury Brand Identity",
    location: "Milan, Italy",
    year: "2024",
    category: "Branding",
    status: "Completed",
    image: "/images/gfx-1.jpg",
  },
  {
    id: "editorial-design",
    title: "Editorial Design System",
    location: "New York, USA",
    year: "2023",
    category: "Editorial",
    status: "Completed",
    image: "/images/gfx-2.jpg",
  },
  {
    id: "packaging-collection",
    title: "Packaging Collection",
    location: "Paris, France",
    year: "2024",
    category: "Packaging",
    status: "Completed",
    image: "/images/gfx-3.jpg",
  },
  {
    id: "wayfinding-system",
    title: "Wayfinding System",
    location: "Tokyo, Japan",
    year: "2024",
    category: "Signage",
    status: "Completed",
    image: "/images/gfx-4.jpg",
  },
  {
    id: "digital-campaign",
    title: "Digital Campaign",
    location: "London, UK",
    year: "2024",
    category: "Digital",
    status: "Completed",
    image: "/images/gfx-5.jpg",
  },
  {
    id: "art-direction",
    title: "Art Direction Project",
    location: "Berlin, Germany",
    year: "2023",
    category: "Art Direction",
    status: "Completed",
    image: "/images/gfx-6.jpg",
  },
]

export default function GraphicsPage() {
  return (
    <ProjectLayout
      title="STUDIO VENDI GRAPHICS"
      description="delivers comprehensive visual communication solutions that strengthen brand identities and create meaningful connections with audiences. Our graphic design team combines strategic thinking with creative excellence, developing cohesive visual systems across all touchpoints—from brand identity and editorial design to packaging, signage, and digital experiences."
      projects={projects}
      categories={["Branding", "Editorial", "Packaging", "Signage", "Digital", "Art Direction"]}
      locations={["Milan, Italy", "New York, USA", "Paris, France", "Tokyo, Japan", "London, UK", "Berlin, Germany"]}
      statuses={["Completed", "In Progress"]}
    />
  )
}
