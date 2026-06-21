"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const LINKS = [
  { href: "/", label: "Rounds", icon: "⛳", match: (p: string) => p === "/" || p.startsWith("/rounds") },
  { href: "/trends", label: "Trends", icon: "📈", match: (p: string) => p.startsWith("/trends") },
];

export default function Sidebar() {
  const pathname = usePathname();
  return (
    <aside className="hidden md:flex w-60 shrink-0 flex-col gap-8 border-r border-border bg-panel/50 px-4 py-8 backdrop-blur-sm">
      <div className="px-2">
        <div className="flex items-center gap-2 text-lg font-semibold">
          <span className="grid h-9 w-9 place-items-center rounded-xl bg-accent/15 text-accent text-xl">
            ⛳
          </span>
          <span>Golf Tracker</span>
        </div>
        <p className="mt-1 px-0.5 text-xs text-muted">Garmin Fenix 6</p>
      </div>

      <nav className="flex flex-col gap-1">
        {LINKS.map((l) => {
          const active = l.match(pathname);
          return (
            <Link
              key={l.href}
              href={l.href}
              className={`nav-link ${active ? "nav-link-active" : ""}`}
            >
              <span className="text-base">{l.icon}</span>
              {l.label}
            </Link>
          );
        })}
      </nav>

      <div className="mt-auto px-2 text-[11px] leading-relaxed text-muted">
        Data from Garmin Connect &amp; FIT files.
      </div>
    </aside>
  );
}
