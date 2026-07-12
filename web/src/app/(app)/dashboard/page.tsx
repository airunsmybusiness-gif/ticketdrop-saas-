import { Card, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Plus } from "lucide-react";

/**
 * Admin dashboard skeleton.
 * The numbers and rows below are MOCK DATA so you can see the layout —
 * the migration plan wires each block to Supabase queries scoped by company_id.
 */
const stats = [
  { label: "Awaiting ack", value: 3, tone: "amber" as const },
  { label: "In progress", value: 5, tone: "brand" as const },
  { label: "Completed today", value: 12, tone: "green" as const },
  { label: "Ready to bill", value: 7, tone: "grey" as const },
];

const loads = [
  { id: 214, customer: "Acme Oil", route: "Well 12 → Terminal A", driver: "John D.", status: "In progress", tone: "brand" as const },
  { id: 213, customer: "Northern Energy", route: "05-22 battery → Hardisty", driver: "Sarah M.", status: "Acknowledged", tone: "amber" as const },
  { id: 212, customer: "Acme Oil", route: "Well 7 → Disposal 3", driver: "Mike H.", status: "Completed", tone: "green" as const },
  { id: 211, customer: "Prairie Crude", route: "Pad 4 → Terminal A", driver: "John D.", status: "Completed", tone: "green" as const },
];

export default function DashboardPage() {
  return (
    <div className="mx-auto max-w-5xl space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Dashboard</h1>
          <p className="mt-1 text-sm text-muted">Live view of today&apos;s hauls.</p>
        </div>
        <Button>
          <Plus className="h-4 w-4" /> New load
        </Button>
      </div>

      {/* stat cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {stats.map((s) => (
          <Card key={s.label} className="p-5">
            <CardDescription>{s.label}</CardDescription>
            <p className="mt-2 text-3xl font-semibold">{s.value}</p>
          </Card>
        ))}
      </div>

      {/* recent loads */}
      <Card className="p-0">
        <div className="border-b border-white/5 px-6 py-4">
          <CardTitle>Recent loads</CardTitle>
        </div>
        <div className="divide-y divide-white/5">
          {loads.map((l) => (
            <div key={l.id} className="flex items-center justify-between gap-4 px-6 py-4">
              <div className="min-w-0">
                <p className="truncate font-medium">
                  #{l.id} · {l.customer}
                </p>
                <p className="truncate text-sm text-muted">
                  {l.route} — {l.driver}
                </p>
              </div>
              <Badge tone={l.tone}>{l.status}</Badge>
            </div>
          ))}
        </div>
      </Card>

      <p className="text-xs text-muted">
        Skeleton with mock data — see REBUILD_PLAN.md for wiring each block to Supabase.
      </p>
    </div>
  );
}
