import { NavLink } from "react-router-dom";

const navLinkBase =
  "rounded-full px-3 py-2 text-sm font-semibold transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[rgba(15,118,110,0.35)] focus-visible:ring-offset-2";
const navLinkInactive =
  "text-[var(--text)] hover:bg-[rgba(15,118,110,0.12)] hover:text-[var(--accent-strong)]";
const navLinkActive = "bg-[var(--accent-soft)] text-[var(--accent-strong)]";
const navLinkClass = ({ isActive }: { isActive: boolean }) =>
  `${navLinkBase} ${isActive ? navLinkActive : navLinkInactive}`;

const navItems = [
  { to: "/", label: "Generate", end: true },
  { to: "/datasets", label: "Datasets", end: true },
  { to: "/runs", label: "Runs", end: false },
] as const;

export default function Navbar() {
  return (
    <header className="flex items-center justify-between gap-6 rounded-4xl border border-border bg-(--surface) px-5 py-4 shadow-(--shadow) animate-[rise_0.5s_ease_both] max-[720px]:flex-col max-[720px]:items-start">
      <div className="flex items-center gap-4">
        <span className="inline-flex h-11 w-11 items-center justify-center rounded-[14px] bg-accent font-bold uppercase tracking-[0.08em] text-white">
          GA
        </span>
        <div>
          <div className="text-[1.1rem] font-bold text-(--text)">Timetable Studio</div>
          <div className="text-sm text-muted">FastAPI + GA runner</div>
        </div>
      </div>

      <nav
        className="flex flex-wrap items-center gap-3 text-sm font-semibold max-[720px]:w-full"
        aria-label="Primary"
      >
        {navItems.map((item) => (
          <NavLink key={item.to} to={item.to} end={item.end} className={navLinkClass}>
            {item.label}
          </NavLink>
        ))}
      </nav>
    </header>
  );
}
