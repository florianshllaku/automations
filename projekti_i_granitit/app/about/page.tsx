import Image from "next/image"

export default function AboutPage() {
  return (
    <main className="pt-24 bg-white text-black font-light flex-1">
      {/* Hero Image - Studio Vendi Logo Light Fixture */}
      <div className="relative w-full aspect-[4/3] md:aspect-[21/9] mb-16 lg:mb-24">
        <Image
          src="/images/about-hero.jpg"
          alt="Studio Vendi illuminated logo fixture"
          fill
          className="object-cover"
          priority
        />
      </div>

      {/* Intro Section */}
      <div className="px-6 lg:px-12 pb-20">
        <div className="max-w-4xl mb-20">
          <h1 className="text-4xl lg:text-6xl font-bold mb-10 lowercase">about us</h1>

          <div className="space-y-8">
            <p className="text-lg lg:text-xl leading-relaxed font-light">
              <span className="font-bold">studiovendi</span> is a multidisciplinary design
              studio founded in 2024, working across architecture, interior design, graphic
              design, illustration, and 3D visualization.
            </p>

            <p className="text-lg lg:text-xl leading-relaxed font-light">
              Each project is approached as a process of exploration—where form, material, and
              context are developed into solutions with meaning and identity.
            </p>

            <p className="text-lg lg:text-xl leading-relaxed font-light">
              Based in Prishtina and collaborating with partners in Germany, Switzerland, and
              Norway, <span className="font-bold">studiovendi</span> operates across different
              scales and contexts, delivering projects both locally and internationally.
            </p>

            <p className="text-lg lg:text-xl leading-relaxed font-light">
              Our work is supported by a strong technical foundation. We implement BIM
              methodologies across varying levels of development and information, adapting
              workflows to meet specific client and project requirements. From early concept
              stages to construction documentation and asset management, our focus remains on
              efficiency, accuracy, and quality.
            </p>

            <p className="text-lg lg:text-xl leading-relaxed font-light">
              We develop projects ranging from small to large scale, using advanced modeling and
              visualization tools to create precise and data-rich 3D representations. Our
              expertise includes architectural modeling, high-end visualizations, and
              Scan-to-BIM processes based on point cloud data from existing structures.
            </p>

            <p className="text-lg lg:text-xl leading-relaxed font-light">
              In parallel, we engage in brand strategy and visual communication—developing
              identities, campaigns, and design systems that extend beyond spatial design.
            </p>

            <p className="text-lg lg:text-xl leading-relaxed font-light">
              For us, design is structure, thought, and intent. We work closely with our
              clients throughout every phase of the project, ensuring clarity, collaboration,
              and consistency. We believe that strong communication and commitment to quality
              are essential to delivering work that is both precise and lasting.
            </p>
          </div>
        </div>
      </div>
    </main>
  )
}
