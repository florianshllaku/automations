"use client"

import Image from "next/image"
import Link from "next/link"
import { useState } from "react"
import { List, ChevronDown } from "lucide-react"

const products = [
  {
    id: "moka-pot",
    title: "Moka Pot",
    brand: "Alessi",
    year: "2024",
    category: "Kitchen",
    image: "/images/design-1.jpg",
  },
  {
    id: "lounge-chair",
    title: "Lounge Chair",
    brand: "Cassina",
    year: "2023",
    category: "Furniture",
    image: "/images/design-2.jpg",
  },
  {
    id: "pendant-lamp",
    title: "Pendant Lamp",
    brand: "Flos",
    year: "2024",
    category: "Lighting",
    image: "/images/design-3.jpg",
  },
  {
    id: "sofa-system",
    title: "Modular Sofa System",
    brand: "Living Divani",
    year: "2023",
    category: "Furniture",
    image: "/images/design-4.jpg",
  },
  {
    id: "dining-table",
    title: "Dining Table",
    brand: "Porro",
    year: "2024",
    category: "Furniture",
    image: "/images/design-5.jpg",
  },
  {
    id: "bathroom-collection",
    title: "Bathroom Collection",
    brand: "Boffi",
    year: "2024",
    category: "Bathroom",
    image: "/images/design-6.jpg",
  },
]

export default function DesignPage() {
  const [selectedCategory, setSelectedCategory] = useState("All categories")
  const [viewMode, setViewMode] = useState<"grid" | "list">("grid")

  const categories = ["Kitchen", "Furniture", "Lighting", "Bathroom", "Accessories"]

  const filteredProducts = products.filter((product) => {
    if (selectedCategory !== "All categories" && product.category !== selectedCategory) return false
    return true
  })

  return (
    <main className="min-h-screen pt-24 pb-20">
      {/* Hero Product */}
      <div className="relative h-[60vh] flex items-center justify-center mb-16">
        <div className="relative w-full max-w-lg h-full">
          <Image
            src="/images/design-hero.jpg"
            alt="Featured Design"
            fill
            className="object-contain"
            priority
          />
        </div>
        <button className="absolute bottom-8 left-1/2 -translate-x-1/2 w-10 h-10 border border-foreground rounded-full flex items-center justify-center hover:bg-foreground hover:text-background transition-colors">
          <ChevronDown className="w-5 h-5" />
        </button>
      </div>

      {/* Content */}
      <div className="px-6 lg:px-12">
        {/* Title */}
        <div className="max-w-3xl mb-16">
          <h1 className="text-sm font-medium uppercase tracking-wider mb-4">STUDIO VENDI DESIGN</h1>
          <p className="text-base lg:text-lg leading-relaxed text-foreground/80">
            creates products that embody timeless elegance and functional innovation. Our design philosophy centers on simplicity, quality materials, and meticulous craftsmanship, resulting in pieces that seamlessly integrate into contemporary living spaces while standing the test of time.
          </p>
        </div>

        {/* Filters */}
        <div className="flex flex-wrap items-center gap-4 mb-12">
          <span className="text-sm font-medium">Filter by:</span>
          
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

        {/* Products Grid */}
        {viewMode === "grid" ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 lg:gap-8">
            {filteredProducts.map((product) => (
              <Link
                key={product.id}
                href={`/design/${product.id}`}
                className="group"
              >
                <div className="aspect-square relative overflow-hidden mb-4 bg-muted/30">
                  <Image
                    src={product.image}
                    alt={product.title}
                    fill
                    className="object-contain p-8 transition-transform duration-500 group-hover:scale-105"
                  />
                </div>
                <h3 className="text-sm font-medium mb-1">{product.title}</h3>
                <p className="text-xs text-muted-foreground">
                  {product.brand} — {product.year}
                </p>
              </Link>
            ))}
          </div>
        ) : (
          <div className="space-y-4">
            {filteredProducts.map((product) => (
              <Link
                key={product.id}
                href={`/design/${product.id}`}
                className="flex items-center gap-6 py-4 border-b border-foreground/10 hover:opacity-60 transition-opacity"
              >
                <div className="w-24 h-24 relative flex-shrink-0 bg-muted/30">
                  <Image
                    src={product.image}
                    alt={product.title}
                    fill
                    className="object-contain p-2"
                  />
                </div>
                <div className="flex-1">
                  <h3 className="text-sm font-medium">{product.title}</h3>
                  <p className="text-xs text-muted-foreground">
                    {product.brand} — {product.year}
                  </p>
                </div>
                <span className="text-xs text-muted-foreground hidden md:block">
                  {product.category}
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
      </div>

    </main>
  )
}
