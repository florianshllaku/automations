import { ProjectLayout } from "@/components/project-layout"

const projects = [
  {
    id: "villa-moderna",
    title: "Villa Moderna",
    location: "Milan, Italy",
    year: "2024",
    category: "Residential",
    status: "Completed",
    image: "/images/arch-1.jpg",
  },
  {
    id: "cultural-center",
    title: "Cultural Center",
    location: "New York, USA",
    year: "2023",
    category: "Cultural",
    status: "Completed",
    image: "/images/arch-2.jpg",
  },
  {
    id: "waterfront-tower",
    title: "Waterfront Tower",
    location: "Dubai, UAE",
    year: "2024",
    category: "Commercial",
    status: "In Progress",
    image: "/images/arch-3.jpg",
  },
  {
    id: "urban-residence",
    title: "Urban Residence",
    location: "London, UK",
    year: "2023",
    category: "Residential",
    status: "Completed",
    image: "/images/arch-4.jpg",
  },
  {
    id: "tech-campus",
    title: "Tech Campus",
    location: "San Francisco, USA",
    year: "2025",
    category: "Commercial",
    status: "In Progress",
    image: "/images/arch-5.jpg",
  },
  {
    id: "art-museum",
    title: "Contemporary Art Museum",
    location: "Tokyo, Japan",
    year: "2024",
    category: "Cultural",
    status: "Completed",
    image: "/images/arch-6.jpg",
  },
]

export default function ArchitecturePage() {
  return (
    <ProjectLayout
      title="STUDIO VENDI ARCHITECTURE"
      description="is the department dedicated to masterplans, architecture and landscape design. Each stage of the design process is backed up by extensive research, studies, hand drawn sketches, 3D renderings and BIM modelling, as well as small and large scale models developed by the in-house workshop. This department also includes a team that develops entries for idea and design competitions, approaching the projects from different perspectives and proposing original and innovative ideas."
      projects={projects}
      categories={["Residential", "Commercial", "Cultural", "Hospitality"]}
      locations={["Milan, Italy", "New York, USA", "London, UK", "Dubai, UAE", "Tokyo, Japan", "San Francisco, USA"]}
      statuses={["Completed", "In Progress", "Concept"]}
    />
  )
}
