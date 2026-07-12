import Link from "next/link";
import {
  Truck,
  LayoutDashboard,
  ClipboardList,
  Receipt,
  Settings,
} from "lucide-react";

const nav = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/dispatch", label: "Dispatch", icon: ClipboardList },
  { href: "/billing", label: "Billing", icon: Receipt },
  { href: "/dashboard#settings", label: "Settings", icon: Settings },
];

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen">
      {/* sidebar */}
      <aside className="hidden w-60 shrink-0 flex-col border-r border-white/5 bg-surface md:flex">
        <Link href="/" className="flex h-16 items-center gap-2 border-b border-white/5 px-5 font-semibold">
          <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand text-white">
            <Truck className="h-4 w-4" />
          </span>
          TicketDrop
        </Link>
        <nav className="flex-1 space-y-1 p-3">
          {nav.map(({ href, label, icon: Icon }) => (
            <Link
              key={label}
              href={href}
              className="flex items-center gap-3 rounded-lg px-3 py-2 text-sm text-muted transition-colors hover:bg-white/5 hover:text-foreground"
            >
              <Icon className="h-4 w-4" />
              {label}
            </Link>
          ))}
        </nav>
        <div className="border-t border-white/5 p-4 text-xs text-muted">
          Built for the field.
        </div>
      </aside>

      {/* main */}
      <div className="flex-1">
        <header className="flex h-16 items-center border-b border-white/5 px-6 md:hidden">
          <Link href="/" className="font-semibold">TicketDrop</Link>
        </header>
        <main className="p-6 md:p-8">{children}</main>
      </div>
    </div>
  );
}
