import { Card, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { MapPin, CheckCircle2, Play } from "lucide-react";

/**
 * Driver view skeleton — phone-first, big buttons.
 * MOCK DATA for layout; the migration plan wires this to the loads table.
 */
export default function DriverPage() {
  return (
    <div className="mx-auto max-w-md space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">My loads</h1>
        <p className="mt-1 text-sm text-muted">Signed in as John D.</p>
      </div>

      {/* new request */}
      <Card className="border-amber-500/30">
        <div className="flex items-center justify-between">
          <CardTitle>Load #215 · Acme Oil</CardTitle>
          <Badge tone="amber">New request</Badge>
        </div>
        <CardDescription className="mt-3 space-y-1.5">
          <span className="flex items-center gap-2">
            <MapPin className="h-4 w-4 text-brand-light" /> Well 12 → Terminal A
          </span>
          <span className="block">Truck 3 / Trailer T196</span>
        </CardDescription>
        <div className="mt-5 grid grid-cols-2 gap-3">
          <Button size="lg">
            <CheckCircle2 className="h-4 w-4" /> Accept
          </Button>
          <Button variant="secondary" size="lg">Decline</Button>
        </div>
      </Card>

      {/* active load */}
      <Card className="border-brand/30">
        <div className="flex items-center justify-between">
          <CardTitle>Load #214 · Northern Energy</CardTitle>
          <Badge tone="brand">Accepted</Badge>
        </div>
        <CardDescription className="mt-3 space-y-1.5">
          <span className="flex items-center gap-2">
            <MapPin className="h-4 w-4 text-brand-light" /> 05-22 battery → Hardisty
          </span>
          <span className="block">Truck 3 / Trailer T196</span>
        </CardDescription>
        <div className="mt-5">
          <Button size="lg" className="w-full">
            <Play className="h-4 w-4" /> Start load — I&apos;m on my way
          </Button>
        </div>
      </Card>

      <p className="text-xs text-muted">
        Skeleton with mock data. Completing a load opens the digital field ticket
        (volumes, hazards checklist, photo, signature) — same flow as today.
      </p>
    </div>
  );
}
