"use client";

/**
 * Dispatch dashboard — live job board, driver list, and summary stats.
 * Polls every 15s while visible and refreshes on focus/reconnect, so it
 * recovers by itself after any dropped connection.
 */
import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { RefreshCw, LogOut, MapPin, Users, WifiOff, Plus, AlertTriangle } from "lucide-react";
import { Card, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

const POLL_MS = 15_000;

function fetchT(url: string, init?: RequestInit): Promise<Response> {
  return fetch(url, { ...init, signal: AbortSignal.timeout(15_000) });
}

type Job = {
  id: number; customer: string; pickup_location: string | null;
  delivery_location: string | null; truck: string | null; trailer: string | null;
  product: string | null; hazards: string[] | null;
  status: string; status_changed_at: string; driver_name: string | null;
};
type Driver = { id: number; name: string; load_id: number | null; customer: string | null; load_status: string | null };
type Stats = { pending: string; active: string; completed_today: string; tickets_to_review: string };
type Data = { user: string; role: string; company: string; stats: Stats; jobs: Job[]; drivers: Driver[]; time: string };

const tone: Record<string, "amber" | "brand" | "green" | "grey"> = {
  REQUESTED: "amber", ASSIGNED: "amber", ACCEPTED: "brand", IN_PROGRESS: "brand",
  COMPLETED: "green", DECLINED: "grey",
};
const label: Record<string, string> = {
  REQUESTED: "Unassigned", ASSIGNED: "Awaiting ack", ACCEPTED: "Accepted",
  IN_PROGRESS: "In progress", COMPLETED: "Completed", DECLINED: "Declined",
};

function ago(iso: string): string {
  const mins = Math.max(0, Math.round((Date.now() - new Date(iso).getTime()) / 60000));
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const h = Math.floor(mins / 60);
  return h < 24 ? `${h}h ${mins % 60}m ago` : `${Math.floor(h / 24)}d ago`;
}

export default function DashboardPage() {
  const router = useRouter();
  const [data, setData] = useState<Data | null>(null);
  const [stale, setStale] = useState(false);
  const [updatedAt, setUpdatedAt] = useState<Date | null>(null);

  const refresh = useCallback(async () => {
    try {
      const res = await fetchT("/api/dashboard");
      if (res.status === 401 || res.status === 403) { router.push("/dashboard/login"); return; }
      if (!res.ok) { setStale(true); return; }
      setData(await res.json());
      setStale(false);
      setUpdatedAt(new Date());
    } catch {
      setStale(true); // keep showing the last data, marked as stale
    }
  }, [router]);

  useEffect(() => {
    refresh();
    const poll = setInterval(() => {
      if (document.visibilityState === "visible") refresh();
    }, POLL_MS);
    const onVisible = () => { if (document.visibilityState === "visible") refresh(); };
    document.addEventListener("visibilitychange", onVisible);
    window.addEventListener("online", onVisible);
    return () => {
      clearInterval(poll);
      document.removeEventListener("visibilitychange", onVisible);
      window.removeEventListener("online", onVisible);
    };
  }, [refresh]);

  async function logout() {
    try { await fetchT("/api/auth/logout", { method: "POST" }); } catch { /* ok */ }
    router.push("/dashboard/login");
  }

  if (!data) {
    return (
      <div className="mx-auto max-w-6xl">
        <p className="text-muted">Loading the board…</p>
      </div>
    );
  }

  const s = data.stats;
  const stats = [
    { label: "Waiting", value: s.pending, accent: "text-amber-400" },
    { label: "Active hauls", value: s.active, accent: "text-brand-light" },
    { label: "Completed today", value: s.completed_today, accent: "text-ok" },
    { label: "Tickets to review", value: s.tickets_to_review, accent: "text-foreground" },
  ];

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      {/* header row */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight md:text-3xl">{data.company}</h1>
          <p className="mt-1 text-sm text-muted">
            Live board · {data.user} ({data.role})
            {updatedAt && <> · updated {updatedAt.toLocaleTimeString()}</>}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Link href="/dispatch">
            <Button size="sm">
              <Plus className="h-4 w-4" /> New load
            </Button>
          </Link>
          <Button variant="secondary" size="sm" onClick={refresh}>
            <RefreshCw className="h-4 w-4" /> Refresh
          </Button>
          <Button variant="ghost" size="sm" onClick={logout} aria-label="Sign out">
            <LogOut className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {stale && (
        <div className="flex items-center gap-2 rounded-lg border border-amber-500/30 bg-amber-500/10 px-4 py-3 text-sm text-amber-300">
          <WifiOff className="h-4 w-4 shrink-0" />
          Connection problem — showing the last data. Retrying automatically.
        </div>
      )}

      {/* summary stats */}
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        {stats.map((x) => (
          <Card key={x.label} className="p-5">
            <CardDescription className="text-xs uppercase tracking-wider">{x.label}</CardDescription>
            <p className={`mt-2 text-4xl font-semibold tabular-nums ${x.accent}`}>{x.value}</p>
          </Card>
        ))}
      </div>

      <div className="grid gap-6 lg:grid-cols-[1fr_320px]">
        {/* ------------------------------------------------ job board */}
        <Card className="p-0">
          <div className="flex items-center justify-between border-b border-white/5 px-6 py-4">
            <CardTitle>Job board</CardTitle>
            <span className="text-xs text-muted">{data.jobs.length} loads</span>
          </div>
          {data.jobs.length === 0 ? (
            <div className="px-6 py-10 text-center">
              <p className="text-sm text-muted">No loads on the board.</p>
              <Link href="/dispatch" className="mt-3 inline-block">
                <Button size="sm"><Plus className="h-4 w-4" /> Dispatch the first load</Button>
              </Link>
            </div>
          ) : (
            <div className="divide-y divide-white/5">
              {data.jobs.map((j) => (
                <div key={j.id} className="flex flex-col gap-3 px-6 py-4 sm:flex-row sm:items-center sm:justify-between">
                  <div className="min-w-0">
                    <p className="truncate font-medium">
                      <span className="text-brand-light">#{j.id}</span> · {j.customer}
                      {j.hazards && j.hazards.length > 0 && (
                        <span className="ml-2 inline-flex items-center gap-1 text-xs text-amber-400"
                              title={j.hazards.join(", ")}>
                          <AlertTriangle className="h-3.5 w-3.5" /> {j.hazards.length}
                        </span>
                      )}
                    </p>
                    <p className="mt-0.5 flex items-center gap-1.5 truncate text-sm text-muted">
                      <MapPin className="h-3.5 w-3.5 shrink-0" />
                      {j.pickup_location || "—"} → {j.delivery_location || "—"}
                      {j.product && <span className="text-muted/80">· {j.product}</span>}
                    </p>
                    <p className="mt-0.5 text-sm text-muted">
                      {j.driver_name || "Unassigned"} · {j.truck || "—"}/{j.trailer || "—"} · {ago(j.status_changed_at)}
                    </p>
                  </div>
                  <div className="flex items-center gap-2 self-start sm:self-center">
                    {(j.status === "REQUESTED" || j.status === "DECLINED") && (
                      <AssignControl job={j} drivers={data.drivers} onDone={refresh} />
                    )}
                    <Badge tone={tone[j.status] ?? "grey"}>
                      {label[j.status] ?? j.status}
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>

        {/* ------------------------------------------------ drivers */}
        <Card className="h-fit p-0">
          <div className="flex items-center gap-2 border-b border-white/5 px-6 py-4">
            <Users className="h-4 w-4 text-brand-light" />
            <CardTitle>Drivers</CardTitle>
          </div>
          <div className="divide-y divide-white/5">
            {data.drivers.map((d) => (
              <div key={d.id} className="px-6 py-3.5">
                <div className="flex items-center justify-between gap-2">
                  <p className="font-medium">{d.name}</p>
                  {d.load_id ? (
                    <Badge tone={tone[d.load_status ?? ""] ?? "grey"}>
                      {label[d.load_status ?? ""] ?? d.load_status}
                    </Badge>
                  ) : (
                    <Badge tone="grey">Free</Badge>
                  )}
                </div>
                {d.load_id && (
                  <p className="mt-0.5 text-sm text-muted">#{d.load_id} · {d.customer}</p>
                )}
              </div>
            ))}
            {data.drivers.length === 0 && (
              <p className="px-6 py-8 text-center text-sm text-muted">No active drivers yet.</p>
            )}
          </div>
        </Card>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Inline driver assignment for unassigned / declined loads.           */
/* ------------------------------------------------------------------ */
function AssignControl({ job, drivers, onDone }: {
  job: Job;
  drivers: Driver[];
  onDone: () => void;
}) {
  const [driverId, setDriverId] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState(false);

  async function assign() {
    if (!driverId) return;
    setBusy(true);
    setErr(false);
    try {
      const res = await fetchT("/api/dispatch/assign", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ load_id: job.id, driver_id: Number(driverId) }),
      });
      if (!res.ok) { setErr(true); return; }
      onDone();
    } catch {
      setErr(true);
    } finally {
      setBusy(false);
    }
  }

  return (
    <span className="flex items-center gap-2">
      <select
        aria-label={`Assign driver to load ${job.id}`}
        className={`h-9 rounded-lg border bg-surface-2 px-2 text-sm text-foreground focus:border-brand focus:outline-none ${err ? "border-red-500/60" : "border-white/10"}`}
        value={driverId}
        onChange={(e) => setDriverId(e.target.value)}
      >
        <option value="">Driver…</option>
        {drivers.map((d) => (
          <option key={d.id} value={d.id}>{d.name}</option>
        ))}
      </select>
      <Button size="sm" onClick={assign} disabled={busy || !driverId}>
        {busy ? "…" : "Assign"}
      </Button>
    </span>
  );
}
