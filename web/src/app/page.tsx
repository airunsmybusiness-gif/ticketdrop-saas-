import Link from "next/link";
import {
  Truck,
  ClipboardList,
  FileCheck2,
  Receipt,
  ShieldCheck,
  Camera,
  Building2,
  ArrowRight,
  CheckCircle2,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

const features = [
  {
    icon: ClipboardList,
    title: "Dispatch in seconds",
    desc: "Send a load to a driver with customer, pickup, delivery, truck and trailer. Live status from assigned to completed.",
  },
  {
    icon: FileCheck2,
    title: "Digital field tickets",
    desc: "Drivers complete the full ticket on their phone — volumes, times, product, signature. No more lost paper.",
  },
  {
    icon: ShieldCheck,
    title: "Hazards checklist built in",
    desc: "H2S, high-pressure lines, lease road traffic and more — ticked hazards print on the official PDF record.",
  },
  {
    icon: Camera,
    title: "Backup photo of every load",
    desc: "One photo at completion, attached to the ticket forever. Disputes end before they start.",
  },
  {
    icon: Receipt,
    title: "One-click invoicing",
    desc: "Verified tickets become branded PDF invoices with your rates, GST and sequential numbering.",
  },
  {
    icon: Building2,
    title: "Your name on everything",
    desc: "Multi-company from day one: each hauler gets their own branding, colors, users and data.",
  },
];

const steps = [
  { n: "01", t: "Dispatch sends the load", d: "Customer, route, truck — assigned to a driver instantly." },
  { n: "02", t: "Driver hauls & completes", d: "Acknowledge, start, then fill the digital ticket with hazards and a photo." },
  { n: "03", t: "Office verifies", d: "AR reviews the ticket and PDF record, then marks it ready to bill." },
  { n: "04", t: "Invoice goes out", d: "Branded PDF invoice with your rates and tax — downloaded or sent same day." },
];

export default function Home() {
  return (
    <main className="min-h-screen">
      {/* ---------------------------------------------------------- nav */}
      <header className="sticky top-0 z-40 border-b border-white/5 bg-background/80 backdrop-blur">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-6">
          <Link href="/" className="flex items-center gap-2 font-semibold">
            <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand text-white">
              <Truck className="h-4 w-4" />
            </span>
            TicketDrop
          </Link>
          <nav className="hidden items-center gap-8 text-sm text-muted md:flex">
            <a href="#features" className="hover:text-foreground">Features</a>
            <a href="#how" className="hover:text-foreground">How it works</a>
          </nav>
          <div className="flex items-center gap-3">
            <Link href="/login">
              <Button variant="ghost" size="sm">Sign in</Button>
            </Link>
            <Link href="/driver/login">
              <Button variant="outline" size="sm">Driver login</Button>
            </Link>
          </div>
        </div>
      </header>

      {/* ---------------------------------------------------------- hero */}
      <section className="bg-grid relative">
        <div className="glow absolute inset-0" aria-hidden />
        <div className="relative mx-auto max-w-6xl px-6 pb-24 pt-20 text-center md:pt-28">
          <Badge tone="brand" className="mb-6">
            Built for oilfield hauling companies
          </Badge>
          <h1 className="mx-auto max-w-3xl text-4xl font-semibold leading-tight tracking-tight md:text-6xl">
            Paper tickets are costing you{" "}
            <span className="bg-gradient-to-r from-brand-light to-brand bg-clip-text text-transparent">
              loads of money
            </span>
          </h1>
          <p className="mx-auto mt-6 max-w-xl text-lg text-muted">
            TicketDrop runs your whole flow — dispatch, digital field tickets with
            hazards & photos, and branded PDF invoices — in one simple system your
            drivers will actually use.
          </p>
          <div className="mt-10 flex flex-col items-center justify-center gap-4 sm:flex-row">
            <Link href="/login">
              <Button size="lg">
                Start dispatching <ArrowRight className="h-4 w-4" />
              </Button>
            </Link>
            <a href="#how">
              <Button variant="secondary" size="lg">See how it works</Button>
            </a>
          </div>
          <div className="mt-10 flex flex-wrap items-center justify-center gap-x-8 gap-y-2 text-sm text-muted">
            {["No training required", "Works on any phone", "Your branding, not ours"].map((t) => (
              <span key={t} className="flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-brand-light" /> {t}
              </span>
            ))}
          </div>
        </div>
      </section>

      {/* ---------------------------------------------------------- features */}
      <section id="features" className="border-t border-white/5 py-24">
        <div className="mx-auto max-w-6xl px-6">
          <p className="text-sm font-medium uppercase tracking-widest text-brand-light">
            Everything in one place
          </p>
          <h2 className="mt-3 max-w-xl text-3xl font-semibold tracking-tight md:text-4xl">
            From load request to paid invoice
          </h2>
          <div className="mt-12 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {features.map(({ icon: Icon, title, desc }) => (
              <Card key={title} className="transition-colors hover:border-brand/40">
                <span className="mb-4 flex h-10 w-10 items-center justify-center rounded-lg bg-brand/15 text-brand-light">
                  <Icon className="h-5 w-5" />
                </span>
                <CardTitle>{title}</CardTitle>
                <CardDescription className="mt-2">{desc}</CardDescription>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* ---------------------------------------------------------- how it works */}
      <section id="how" className="border-t border-white/5 py-24">
        <div className="mx-auto max-w-6xl px-6">
          <p className="text-sm font-medium uppercase tracking-widest text-brand-light">
            How it works
          </p>
          <h2 className="mt-3 text-3xl font-semibold tracking-tight md:text-4xl">
            Four steps. Zero paper.
          </h2>
          <div className="mt-12 grid gap-4 md:grid-cols-4">
            {steps.map((s) => (
              <div key={s.n} className="rounded-xl border border-white/10 bg-surface p-6">
                <span className="font-mono text-sm text-brand-light">{s.n}</span>
                <h3 className="mt-3 font-semibold">{s.t}</h3>
                <p className="mt-2 text-sm text-muted">{s.d}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ---------------------------------------------------------- CTA */}
      <section className="border-t border-white/5 py-24">
        <div className="mx-auto max-w-6xl px-6">
          <div className="glow relative overflow-hidden rounded-2xl border border-brand/25 bg-surface px-8 py-16 text-center">
            <h2 className="text-3xl font-semibold tracking-tight md:text-4xl">
              Run your hauls on TicketDrop
            </h2>
            <p className="mx-auto mt-4 max-w-md text-muted">
              Set up your company, add your drivers, and dispatch your first load
              in under an hour.
            </p>
            <div className="mt-8">
              <Link href="/login">
                <Button size="lg">
                  Get started <ArrowRight className="h-4 w-4" />
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* ---------------------------------------------------------- footer */}
      <footer className="border-t border-white/5 py-10">
        <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-4 px-6 text-sm text-muted md:flex-row">
          <span className="flex items-center gap-2">
            <Truck className="h-4 w-4 text-brand-light" /> TicketDrop
          </span>
          <span>© {new Date().getFullYear()} TicketDrop. Built for the field.</span>
        </div>
      </footer>
    </main>
  );
}
