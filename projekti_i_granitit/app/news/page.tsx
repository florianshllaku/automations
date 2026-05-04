import Image from "next/image"
import Link from "next/link"

const featuredNews = {
  id: "design-week-2026",
  title: "Milan Design Week 2026",
  date: "APRIL 2026",
  image: "/images/news-featured.jpg",
  description: "Discover Studio Vendi new projects and products presented at the Salone del Mobile and Milan Design Week 2026.",
}

const newsItems = [
  {
    id: "open-studio",
    title: "Open Studio Cafe",
    date: "MARCH 2026",
    image: "/images/news-1.jpg",
    description: "From 21st to 24th April, the two Milan studios of Studio Vendi will open to the public with an exhibition of recent works in architecture, interior design, product design, and graphics.",
  },
  {
    id: "lighthouse-palazzo",
    title: "Lighthouse at Palazzo Reale",
    date: "JANUARY 2026",
    image: "/images/news-2.jpg",
    description: "Studio Vendi's Lighthouse project for Salvatori will be displayed at the Palazzo Reale in Milan from 28th January to 21st June.",
  },
  {
    id: "boat-show",
    title: "New Yacht BGX83 unveiled at the Dusseldorf Boat Show",
    date: "JANUARY 2026",
    image: "/images/news-3.jpg",
    description: "On the occasion of the 2026 Dusseldorf Boat Show, the new BGX83 featuring interiors designed by Studio Vendi was unveiled.",
  },
  {
    id: "ad100-selection",
    title: "Studio Vendi is among the AD100 selection",
    date: "DECEMBER 2025",
    image: "/images/news-4.jpg",
    description: "Happy and honored for Studio Vendi to be part of the AD100 selection for 2026, among some of the world's most talented creatives.",
  },
  {
    id: "art-basel-miami",
    title: "Art Basel Miami Beach",
    date: "DECEMBER 2025",
    image: "/images/news-5.jpg",
    description: "Studio Vendi designs the Collectors Lounge for Art Basel Miami Beach in collaboration with the Salone del Mobile.Milano.",
  },
  {
    id: "riyadh-event",
    title: "Red in progress. Salone del Mobile Milano meets Riyadh",
    date: "NOVEMBER 2025",
    image: "/images/news-6.jpg",
    description: "Studio Vendi designed the Business Lounge for 'Red in progress. Salone del Mobile Milano meets Riyadh', transforming the King Abdullah Financial District.",
  },
]

const agendaItems = [
  {
    date: "20 April 2026",
    title: "Milano Design Week",
    subtitle: "Salone Internazionale del Mobile",
    period: "20th April - 26th April",
  },
  {
    date: "28 January 2026",
    title: "Metafisica/Metafisiche exhibition",
    subtitle: "January 28th - June 21st",
    period: "Palazzo Reale, Milan",
  },
]

export default function NewsPage() {
  return (
    <main className="min-h-screen pt-24 pb-20 px-6 lg:px-12">
      {/* Title */}
      <h1 className="text-5xl lg:text-7xl font-light mb-12">News</h1>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-12">
        {/* Main Content */}
        <div className="lg:col-span-2">
          {/* Featured News */}
          <Link href={`/news/${featuredNews.id}`} className="block mb-12 group">
            <p className="text-sm text-amber-600 font-medium mb-2">{featuredNews.date}</p>
            <h2 className="text-xl lg:text-2xl font-medium mb-4">{featuredNews.title}</h2>
            <div className="relative aspect-video mb-4 overflow-hidden">
              <Image
                src={featuredNews.image}
                alt={featuredNews.title}
                fill
                className="object-cover transition-transform duration-500 group-hover:scale-105"
              />
            </div>
            <p className="text-sm text-muted-foreground">{featuredNews.description}</p>
          </Link>

          {/* News Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {newsItems.map((item) => (
              <Link key={item.id} href={`/news/${item.id}`} className="group">
                <p className="text-xs text-amber-600 font-medium mb-2">{item.date}</p>
                <h3 className="text-base font-medium mb-3">{item.title}</h3>
                <div className="relative aspect-video mb-3 overflow-hidden bg-muted">
                  <Image
                    src={item.image}
                    alt={item.title}
                    fill
                    className="object-cover transition-transform duration-500 group-hover:scale-105"
                  />
                </div>
                <p className="text-xs text-muted-foreground leading-relaxed">{item.description}</p>
              </Link>
            ))}
          </div>

          {/* Pagination */}
          <div className="flex items-center gap-2 mt-12">
            <span className="w-8 h-8 flex items-center justify-center bg-foreground text-background text-sm">1</span>
            <span className="text-sm text-muted-foreground">...</span>
            <button className="w-8 h-8 flex items-center justify-center hover:bg-muted text-sm">2</button>
            <button className="w-8 h-8 flex items-center justify-center hover:bg-muted text-sm">3</button>
            <button className="w-8 h-8 flex items-center justify-center hover:bg-muted text-sm">4</button>
            <span className="text-sm text-muted-foreground">...</span>
            <button className="w-8 h-8 flex items-center justify-center hover:bg-muted text-sm">21</button>
          </div>
        </div>

        {/* Sidebar */}
        <div className="lg:col-span-1">
          {/* Agenda */}
          <div className="mb-12">
            <h3 className="text-sm text-amber-600 font-medium mb-6">AGENDA</h3>
            <div className="space-y-6">
              {agendaItems.map((item, index) => (
                <div key={index}>
                  <p className="text-sm font-medium mb-1">{item.date}</p>
                  <p className="text-sm">{item.title}</p>
                  <p className="text-xs text-muted-foreground">{item.subtitle}</p>
                  <p className="text-xs text-muted-foreground">{item.period}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Newsletter */}
          <div className="bg-muted p-6">
            <p className="text-xs text-amber-600 font-medium mb-4">STAY TUNED</p>
            <h4 className="text-sm font-medium mb-4">Subscribe to our newsletter</h4>
            <input
              type="email"
              placeholder="insert your email"
              className="w-full bg-background px-3 py-2 text-sm mb-3 border-0"
            />
            <label className="flex items-start gap-2 text-xs text-muted-foreground mb-4">
              <input type="checkbox" className="mt-0.5" />
              <span>
                I&apos;ve read and accept the{" "}
                <Link href="/terms" className="underline">
                  terms & conditions
                </Link>
                .
              </span>
            </label>
            <button className="w-full bg-foreground text-background py-2 text-sm hover:opacity-80 transition-opacity">
              subscribe
            </button>
          </div>
        </div>
      </div>

    </main>
  )
}
