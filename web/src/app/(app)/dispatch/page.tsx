"use client";

/**
 * Dispatch form — create a job order and send it to a driver (or leave it
 * unassigned and assign from the board later). Big fields, clear labels,
 * datalists fed from the company's saved customers/trucks/trailers.
 */
import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, Send, CheckCircle2 } from "lucide-react";
import { Card, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input, Label } from "@/components/ui/input";
import { HAZARD_ITEMS } from "@/lib/hazards";

function fetchT(url: string, init?: RequestInit): Promise<Response> {
  return fetch(url, { ...init, signal: AbortSignal.timeout(15_000) });
}

type Options = {
  drivers: { id: number; name: string }[];
  customers: string[];
  trucks: string[];
  trailers: string[];
};

const PRODUCTS = [
  "Crude oil (UN1267)", "Produced water", "Fresh water", "Condensate",
  "Frac fluid", "Drilling mud", "Emulsion", "Methanol",
];

export default function DispatchPage() {
  const router = useRouter();
  const [opts, setOpts] = useState<Options | null>(null);
  const [customer, setCustomer] = useState("");
  const [pickup, setPickup] = useState("");
  const [delivery, setDelivery] = useState("");
  const [product, setProduct] = useState("");
  const [estVolume, setEstVolume] = useState("");
  const [truck, setTruck] = useState("");
  const [trailer, setTrailer] = useState("");
  const [driverId, setDriverId] = useState("");
  const [notes, setNotes] = useState("");
  const [hazards, setHazards] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [created, setCreated] = useState<{ id: number; status: string } | null>(null);

  const loadOptions = useCallback(async () => {
    try {
      const res = await fetchT("/api/dispatch/options");
      if (res.status === 401 || res.status === 403) { router.push("/dashboard/login"); return; }
      if (res.ok) setOpts(await res.json());
    } catch { /* options are conveniences; the form still works without them */ }
  }, [router]);

  useEffect(() => { loadOptions(); }, [loadOptions]);

  function toggle(h: string) {
    setHazards((hs) => (hs.includes(h) ? hs.filter((x) => x !== h) : [...hs, h]));
  }

  async function submit() {
    setError(null);
    if (!customer.trim()) return setError("Enter the customer");
    if (!pickup.trim()) return setError("Enter the pickup location");
    if (!delivery.trim()) return setError("Enter the delivery location");
    setBusy(true);
    try {
      const res = await fetchT("/api/dispatch/create", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          customer: customer.trim(),
          pickup: pickup.trim(),
          delivery: delivery.trim(),
          product: product.trim() || undefined,
          estimated_volume: estVolume || undefined,
          truck: truck.trim() || undefined,
          trailer: trailer.trim() || undefined,
          driver_id: driverId || undefined,
          notes: notes.trim() || undefined,
          hazards,
        }),
      });
      if (res.status === 401 || res.status === 403) { router.push("/dashboard/login"); return; }
      const data = await res.json().catch(() => ({}));
      if (!res.ok) { setError(data.error || "Could not create the load"); return; }
      setCreated({ id: data.load_id, status: data.status });
    } catch {
      setError("No connection — check your signal and try again.");
    } finally {
      setBusy(false);
    }
  }

  // ------------------------------------------------------------- success
  if (created) {
    const driverName = opts?.drivers.find((d) => String(d.id) === driverId)?.name;
    return (
      <div className="mx-auto max-w-xl space-y-5">
        <Card className="border-ok/30 text-center">
          <CheckCircle2 className="mx-auto h-10 w-10 text-ok" />
          <h1 className="mt-3 text-2xl font-semibold">Load #{created.id} created</h1>
          <p className="mt-2 text-muted">
            {created.status === "ASSIGNED"
              ? <>Sent to <span className="text-foreground">{driverName}</span> — it&apos;s on their phone now.</>
              : "Unassigned — pick a driver from the job board when you're ready."}
          </p>
          <div className="mt-6 grid grid-cols-2 gap-3">
            <Button variant="secondary" size="lg" onClick={() => {
              setCreated(null); setCustomer(""); setPickup(""); setDelivery("");
              setProduct(""); setEstVolume(""); setNotes(""); setHazards([]); setDriverId("");
            }}>
              New load
            </Button>
            <Link href="/dashboard">
              <Button size="lg" className="w-full">Back to board</Button>
            </Link>
          </div>
        </Card>
      </div>
    );
  }

  // ------------------------------------------------------------- form
  const selectCls =
    "h-11 w-full rounded-lg border border-white/10 bg-surface-2 px-3 text-[15px] text-foreground focus:border-brand focus:outline-none focus:ring-2 focus:ring-brand/25";

  return (
    <div className="mx-auto max-w-2xl space-y-5 pb-16">
      <div className="flex items-center gap-3">
        <Link href="/dashboard">
          <Button variant="ghost" size="sm" aria-label="Back to dashboard">
            <ArrowLeft className="h-4 w-4" />
          </Button>
        </Link>
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">New load</h1>
          <p className="mt-0.5 text-sm text-muted">Create a job order and send it to a driver.</p>
        </div>
      </div>

      <Card className="space-y-4">
        <CardTitle>Job order</CardTitle>
        <div>
          <Label htmlFor="customer">Customer</Label>
          <Input id="customer" list="customers" placeholder="e.g. Acme Oil"
                 value={customer} onChange={(e) => setCustomer(e.target.value)} />
          <datalist id="customers">
            {opts?.customers.map((c) => <option key={c} value={c} />)}
          </datalist>
        </div>
        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <Label htmlFor="pickup">Pickup location</Label>
            <Input id="pickup" placeholder="Well site or facility"
                   value={pickup} onChange={(e) => setPickup(e.target.value)} />
          </div>
          <div>
            <Label htmlFor="delivery">Delivery location</Label>
            <Input id="delivery" placeholder="Destination"
                   value={delivery} onChange={(e) => setDelivery(e.target.value)} />
          </div>
        </div>
        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <Label htmlFor="product">Product</Label>
            <Input id="product" list="products" placeholder="e.g. Produced water"
                   value={product} onChange={(e) => setProduct(e.target.value)} />
            <datalist id="products">
              {PRODUCTS.map((p) => <option key={p} value={p} />)}
            </datalist>
          </div>
          <div>
            <Label htmlFor="estvol">Estimated volume (m³)</Label>
            <Input id="estvol" inputMode="decimal" placeholder="40"
                   value={estVolume} onChange={(e) => setEstVolume(e.target.value)} />
          </div>
        </div>
      </Card>

      <Card className="space-y-4">
        <CardTitle>Assignment</CardTitle>
        <CardDescription>Pick a driver now, or leave it and assign from the board.</CardDescription>
        <div>
          <Label htmlFor="driver">Driver</Label>
          <select id="driver" className={selectCls} value={driverId}
                  onChange={(e) => setDriverId(e.target.value)}>
            <option value="">Assign later</option>
            {opts?.drivers.map((d) => (
              <option key={d.id} value={d.id}>{d.name}</option>
            ))}
          </select>
        </div>
        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <Label htmlFor="truck">Truck</Label>
            <Input id="truck" list="trucks" placeholder="e.g. Truck 3"
                   value={truck} onChange={(e) => setTruck(e.target.value)} />
            <datalist id="trucks">
              {opts?.trucks.map((t) => <option key={t} value={t} />)}
            </datalist>
          </div>
          <div>
            <Label htmlFor="trailer">Trailer</Label>
            <Input id="trailer" list="trailers" placeholder="e.g. T196"
                   value={trailer} onChange={(e) => setTrailer(e.target.value)} />
            <datalist id="trailers">
              {opts?.trailers.map((t) => <option key={t} value={t} />)}
            </datalist>
          </div>
        </div>
      </Card>

      <Card>
        <CardTitle>⚠️ Known site hazards</CardTitle>
        <CardDescription className="mt-1">
          Tick what dispatch already knows — the driver sees these on the load and
          confirms the full checklist at completion.
        </CardDescription>
        <div className="mt-4 grid grid-cols-1 gap-2 sm:grid-cols-2">
          {HAZARD_ITEMS.map((h) => {
            const on = hazards.includes(h);
            return (
              <button key={h} type="button" onClick={() => toggle(h)}
                className={`flex min-h-11 items-center gap-3 rounded-lg border px-3.5 text-left text-sm transition-colors ${
                  on ? "border-brand bg-brand/15 text-foreground" : "border-white/10 bg-surface-2 text-muted"
                }`}>
                <span className={`flex h-5 w-5 shrink-0 items-center justify-center rounded border text-xs font-bold ${
                  on ? "border-brand bg-brand text-white" : "border-white/25"
                }`}>{on ? "✓" : ""}</span>
                {h}
              </button>
            );
          })}
        </div>
      </Card>

      <Card>
        <Label htmlFor="notes">Notes for the driver (optional)</Label>
        <Input id="notes" placeholder="Special instructions, gate codes, contacts…"
               value={notes} onChange={(e) => setNotes(e.target.value)} />
      </Card>

      {error && <p className="text-sm text-red-400">{error}</p>}

      <Button size="lg" className="w-full" onClick={submit} disabled={busy}>
        <Send className="h-4 w-4" />
        {busy ? "Sending…" : driverId ? "Send to driver" : "Create load (assign later)"}
      </Button>
    </div>
  );
}
