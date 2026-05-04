import { ProjectLayout } from "@/components/project-layout"

const projects = [
  {
    id: "milan-design-week",
    title: "Milan Design Week 2024",
    location: "Milan, Italy",
    year: "2024",
    category: "Exhibition",
    status: "Completed",
    image: "/images/exh-1.jpg",
  },
  {
    id: "art-basel",
    title: "Art Basel Installation",
    location: "Basel, Switzerland",
    year: "2024",
    category: "Installation",
    status: "Completed",
    image: "/images/exh-2.jpg",
  },
  {
    id: "venice-biennale",
    title: "Venice Biennale Pavilion",
    location: "Venice, Italy",
    year: "2024",
    category: "Exhibition",
    status: "Completed",
    image: "/images/exh-3.jpg",
  },
  {
    id: "brand-launch",
    title: "Brand Launch Event",
    location: "New York, USA",
    year: "2023",
    category: "Event",
    status: "Completed",
    image: "/images/exh-4.jpg",
  },
  {
    id: "retrospective",
    title: "Retrospective Exhibition",
    location: "Tokyo, Japan",
    year: "2024",
    category: "Exhibition",
    status: "In Progress",
    image: "/images/exh-5.jpg",
  },
  {
    id: "pop-up-store",
    title: "Pop-up Store Design",
    location: "London, UK",
    year: "2023",
    category: "Event",
    status: "Completed",
    image: "/images/exh-6.jpg",
  },
]

export default function ExhibitionsPage() {
  return (
    <ProjectLayout
      title="STUDIO VENDI EXHIBITIONS & EVENTS"
      description="creates immersive experiences that tell compelling stories through space, light, and materials. Our exhibition design team transforms concepts into memorable environments, whether for international fairs, brand presentations, or cultural institutions. Each project is approached as a unique narrative opportunity, crafting spaces that engage, inspire, and leave lasting impressions."
      projects={projects}
      categories={["Exhibition", "Installation", "Event", "Fair"]}
      locations={["Milan, Italy", "Basel, Switzerland", "Venice, Italy", "New York, USA", "Tokyo, Japan", "London, UK"]}
      statuses={["Completed", "In Progress", "Upcoming"]}
    />
  )
}
