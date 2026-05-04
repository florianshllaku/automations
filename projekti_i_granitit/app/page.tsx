import { BendLogo } from "@/components/ui/bend-logo"

export default function HomePage() {
  return (
    <main className="relative bg-white flex-1 flex">
      {/* Hero: interactive 3D Bend Logo fills the available viewport */}
      <section className="relative w-full flex-1">
        <div className="absolute inset-0">
          <BendLogo src="/images/logo.png" />
        </div>
      </section>
    </main>
  )
}
