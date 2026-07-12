"use client";

/**
 * Driver home — phone-first, glove-friendly, and tolerant of dead zones.
 *
 * Offline strategy (simple on purpose):
 *  - The last loads list is cached in localStorage, so the page still renders
 *    with no signal.
 *  - Accept / Start / Complete first try the network. If that fails, the
 *    request goes into an "outbox" in localStorage and is retried
 *    automatically when the connection comes back (or on next open).
 */
import { useCallback, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { MapPin, Play, CheckCircle2, RefreshCw, WifiOff, LogOut } from "lucide-react";
import { Card, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input, Label } from "@/components/ui/input";
import { HAZARD_ITEMS } from "@/lib/hazards";

type Load = {
  id: number;
  customer: string;
  pickup_location: string | null;
  delivery_location: string | null;
  truck: string | null;
  trailer: string | null;
  notes: string | null;
  status: "ASSIGNED" | "ACCEPTED" | "IN_PROGRESS" | "COMPLETED";
};

type OutboxItem = { key: string; url: string; body: unknown; label: string };

const CACHE_KEY = "td_loads_cache";
const OUTBOX_KEY = "td_outbox";

function readOutbox(): OutboxItem[] {
  try { return JSON.parse(localStorage.getItem(OUTBOX_KEY) || "[]"); } catch { return []; }
}
function writeOutbox(items: OutboxItem[]) {
  localStorage.setItem(OUTBOX_KEY, JSON.stringify(items));
}

const statusTone = { ASSIGNED: "amber", ACCEPTED: "brand", IN_PROGRESS: "brand", COMPLETED: "green" } as const;
const statusLabel = { ASSIGNED: "New request", ACCEPTED: "Accepted", IN_PROGRESS: "In progress", COMPLETED: "Completed" } as const;

export default function DriverPage() {
  const router = useRouter();
  const [driver, setDriver] = useState<string>("");
  const [loads, setLoads] = useState<Load[]>([]);
  const [pendingCount, setPendingCount] = useState(0);
  const [offline, setOffline] = useState(false);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [completing, setCompleting] = useState<Load | null>(null);
  const syncing = useRef(false);

  // ------------------------------------------------------------- data
  const refresh = useCallback(async () => {
    try {
      const res = await fetch("/api/driver/loads");
      if (res.status === 401) { router.push("/driver/login"); return; }
      const data = await res.json();
      setLoads(data.loads);
      setDriver(data.driver);
      setOffline(false);
      localStorage.setItem(CACHE_KEY, JSON.stringify(data));
    } catch {
      // offline — fall back to the cached list
      setOffline(true);
      try {
        const cached = JSON.parse(localStorage.getItem(CACHE_KEY) || "null");
        if (cached) { setLoads(cached.loads); setDriver(cached.driver); }
      } catch { /* no cache yet */ }
    }
  }, [router]);

  const syncOutbox = useCallback(async () => {
    if (syncing.current) return;
    syncing.current = true;
    try {
      let items = readOutbox();
      while (items.length > 0) {
        const item = items[0];
        let res: Response;
        try {
          res = await fetch(item.url, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(item.body),
          });
        } catch {
          break; // still offline — keep the queue and stop
        }
        if (res.status === 401) { router.push("/driver/login"); break; }
        // Success or a definitive rejection (validation/conflict): remove from queue.
        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          setMessage(`"${item.label}" was rejected: ${err.error || res.status}`);
        }
        items = items.slice(1);
        writeOutbox(items);
      }
      setPendingCount(readOutbox().length);
    } finally {
      syncing.current = false;
    }
  }, [router]);

  useEffect(() => {
    setPendingCount(readOutbox().length);
    const boot = async () => { await syncOutbox(); await refresh(); };
    boot();
    const onOnline = () => { setOffline(false); syncOutbox().then(refresh); };
    const onOffline = () => setOffline(true);
    window.addEventListener("online", onOnline);
    window.addEventListener("offline", onOffline);
    return () => {
      window.removeEventListener("online", onOnline);
      window.removeEventListener("offline", onOffline);
    };
  }, [refresh, syncOutbox]);

  // -------------------------------------------------- send or queue
  async function sendOrQueue(url: string, body: unknown, label: string,
                             optimistic: () => void) {
    setBusy(true);
    setMessage(null);
    try {
      const res = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (res.status === 401) { router.push("/driver/login"); return; }
      const data = await res.json().catch(() => ({}));
      if (!res.ok) { setMessage(data.error || "Something went wrong"); return; }
      await refresh();
      setMessage(`✅ ${label}`);
    } catch {
      // offline → queue it and update the screen optimistically
      const items = readOutbox();
      items.push({ key: `${Date.now()}`, url, body, label });
      try {
        writeOutbox(items);
        setPendingCount(items.length);
        optimistic();
        setOffline(true);
        setMessage(`📱 No signal — "${label}" is saved on this phone and will send automatically.`);
      } catch {
        setMessage("Storage is full — free up space or find signal and try again.");
      }
    } finally {
      setBusy(false);
    }
  }

  function act(load: Load, action: "accept" | "decline" | "start") {
    const next = action === "accept" ? "ACCEPTED" : action === "start" ? "IN_PROGRESS" : "COMPLETED";
    sendOrQueue("/api/driver/action", { load_id: load.id, action },
      `Load #${load.id} ${action}`, () => {
        setLoads((ls) => action === "decline"
          ? ls.filter((l) => l.id !== load.id)
          : ls.map((l) => (l.id === load.id ? { ...l, status: next as Load["status"] } : l)));
      });
  }

  async function logout() {
    try { await fetch("/api/auth/logout", { method: "POST" }); } catch { /* ok */ }
    localStorage.removeItem(CACHE_KEY);
    router.push("/driver/login");
  }

  // ------------------------------------------------------------- UI
  if (completing) {
    return (
      <CompleteForm
        load={completing}
        busy={busy}
        onCancel={() => setCompleting(null)}
        onSubmit={(body) => {
          sendOrQueue("/api/driver/complete", { ...body, load_id: completing.id },
            `Ticket for load #${completing.id}`, () => {
              setLoads((ls) => ls.map((l) =>
                l.id === completing.id ? { ...l, status: "COMPLETED" } : l));
            });
          setCompleting(null);
        }}
      />
    );
  }

  return (
    <div className="mx-auto max-w-md space-y-5 pb-16">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">My loads</h1>
          <p className="mt-1 text-sm text-muted">{driver ? `Signed in as ${driver}` : "…"}</p>
        </div>
        <div className="flex gap-2">
          <Button variant="ghost" size="sm" onClick={refresh} aria-label="Refresh">
            <RefreshCw className="h-4 w-4" />
          </Button>
          <Button variant="ghost" size="sm" onClick={logout} aria-label="Sign out">
            <LogOut className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {offline && (
        <div className="flex items-center gap-2 rounded-lg border border-amber-500/30 bg-amber-500/10 px-4 py-3 text-sm text-amber-300">
          <WifiOff className="h-4 w-4 shrink-0" />
          No signal — showing your last list. Anything you do is saved and sent later.
        </div>
      )}
      {pendingCount > 0 && (
        <div className="rounded-lg border border-brand/30 bg-brand/10 px-4 py-3 text-sm text-brand-light">
          {pendingCount} update{pendingCount > 1 ? "s" : ""} waiting to send.
        </div>
      )}
      {message && <p className="text-sm text-muted">{message}</p>}

      {loads.length === 0 && !offline && (
        <Card><CardDescription>No loads assigned right now. Pull down or tap refresh.</CardDescription></Card>
      )}

      {loads.map((l) => (
        <Card key={l.id} className={l.status === "IN_PROGRESS" ? "border-brand/40" : ""}>
          <div className="flex items-center justify-between gap-3">
            <CardTitle>#{l.id} · {l.customer}</CardTitle>
            <Badge tone={statusTone[l.status]}>{statusLabel[l.status]}</Badge>
          </div>
          <CardDescription className="mt-3 space-y-1.5">
            <span className="flex items-center gap-2">
              <MapPin className="h-4 w-4 shrink-0 text-brand-light" />
              {l.pickup_location || "—"} → {l.delivery_location || "—"}
            </span>
            <span className="block">{l.truck || "—"} / {l.trailer || "—"}</span>
            {l.notes && <span className="block text-amber-300/90">📝 {l.notes}</span>}
          </CardDescription>

          <div className="mt-5">
            {l.status === "ASSIGNED" && (
              <div className="grid grid-cols-2 gap-3">
                <Button size="lg" disabled={busy} onClick={() => act(l, "accept")}>
                  <CheckCircle2 className="h-4 w-4" /> Accept
                </Button>
                <Button variant="secondary" size="lg" disabled={busy} onClick={() => act(l, "decline")}>
                  Decline
                </Button>
              </div>
            )}
            {l.status === "ACCEPTED" && (
              <Button size="lg" className="w-full" disabled={busy} onClick={() => act(l, "start")}>
                <Play className="h-4 w-4" /> Start load — I&apos;m on my way
              </Button>
            )}
            {l.status === "IN_PROGRESS" && (
              <Button size="lg" className="w-full" disabled={busy} onClick={() => setCompleting(l)}>
                <CheckCircle2 className="h-4 w-4" /> Complete load — fill ticket
              </Button>
            )}
          </div>
        </Card>
      ))}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Completion form: ticket #, volume, hours, hazards, photo, notes,    */
/* signature. Photo is resized on the phone before upload/queueing.    */
/* ------------------------------------------------------------------ */
function CompleteForm({ load, busy, onCancel, onSubmit }: {
  load: Load;
  busy: boolean;
  onCancel: () => void;
  onSubmit: (body: Record<string, unknown>) => void;
}) {
  const [ticketNumber, setTicketNumber] = useState("");
  const [volume, setVolume] = useState("");
  const [hours, setHours] = useState("");
  const [hazards, setHazards] = useState<string[]>([]);
  const [hazardNotes, setHazardNotes] = useState("");
  const [notes, setNotes] = useState("");
  const [signature, setSignature] = useState("");
  const [photo, setPhoto] = useState<string | null>(null); // data URL
  const [error, setError] = useState<string | null>(null);

  function toggle(h: string) {
    setHazards((hs) => (hs.includes(h) ? hs.filter((x) => x !== h) : [...hs, h]));
  }

  // Downscale the photo on-device so it uploads fast on one bar of LTE
  // (and fits in the offline outbox).
  function onPhoto(file: File | undefined) {
    if (!file) return;
    const img = new Image();
    img.onload = () => {
      const MAX = 1280;
      const scale = Math.min(1, MAX / Math.max(img.width, img.height));
      const canvas = document.createElement("canvas");
      canvas.width = Math.round(img.width * scale);
      canvas.height = Math.round(img.height * scale);
      canvas.getContext("2d")!.drawImage(img, 0, 0, canvas.width, canvas.height);
      setPhoto(canvas.toDataURL("image/jpeg", 0.8));
      URL.revokeObjectURL(img.src);
    };
    img.src = URL.createObjectURL(file);
  }

  function submit() {
    setError(null);
    if (!ticketNumber.trim()) return setError("Enter your ticket #");
    const vol = parseFloat(volume);
    if (!vol || vol <= 0) return setError("Enter the actual volume (m³)");
    if (!signature.trim()) return setError("Type your full name as signature");
    if (hazards.includes("Other (see notes)") && !hazardNotes.trim())
      return setError("You ticked 'Other' — describe it in hazard notes");
    onSubmit({
      ticket_number: ticketNumber.trim(),
      actual_volume: vol,
      hours: parseFloat(hours) || 0,
      hazards,
      hazard_notes: hazardNotes.trim() || undefined,
      notes: notes.trim() || undefined,
      signature: signature.trim(),
      photo_base64: photo || undefined,
    });
  }

  return (
    <div className="mx-auto max-w-md space-y-5 pb-16">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Complete load #{load.id}</h1>
        <p className="mt-1 text-sm text-muted">{load.customer} · {load.pickup_location} → {load.delivery_location}</p>
      </div>

      <Card className="space-y-4">
        <div className="grid grid-cols-2 gap-3">
          <div>
            <Label htmlFor="tnum">Ticket #</Label>
            <Input id="tnum" inputMode="numeric" placeholder="361334"
                   value={ticketNumber} onChange={(e) => setTicketNumber(e.target.value)} />
          </div>
          <div>
            <Label htmlFor="vol">Actual volume (m³)</Label>
            <Input id="vol" inputMode="decimal" placeholder="40.0"
                   value={volume} onChange={(e) => setVolume(e.target.value)} />
          </div>
        </div>
        <div>
          <Label htmlFor="hrs">Hours charged (optional)</Label>
          <Input id="hrs" inputMode="decimal" placeholder="1.0"
                 value={hours} onChange={(e) => setHours(e.target.value)} />
        </div>
      </Card>

      <Card>
        <CardTitle>⚠️ Site &amp; load hazards</CardTitle>
        <CardDescription className="mt-1">Tick everything present on this job.</CardDescription>
        <div className="mt-4 grid grid-cols-1 gap-2">
          {HAZARD_ITEMS.map((h) => {
            const on = hazards.includes(h);
            return (
              <button key={h} type="button" onClick={() => toggle(h)}
                className={`flex min-h-12 items-center gap-3 rounded-lg border px-4 text-left text-sm transition-colors ${
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
        {hazards.includes("Other (see notes)") && (
          <div className="mt-3">
            <Label htmlFor="hnotes">Hazard notes</Label>
            <Input id="hnotes" placeholder="Describe the other hazard…"
                   value={hazardNotes} onChange={(e) => setHazardNotes(e.target.value)} />
          </div>
        )}
      </Card>

      <Card>
        <CardTitle>📸 Backup photo of the load</CardTitle>
        <CardDescription className="mt-1">One photo of the load or paperwork.</CardDescription>
        <input type="file" accept="image/*" capture="environment"
               className="mt-4 block w-full text-sm text-muted file:mr-3 file:rounded-lg file:border-0 file:bg-brand file:px-4 file:py-2.5 file:text-sm file:font-medium file:text-white"
               onChange={(e) => onPhoto(e.target.files?.[0])} />
        {photo && (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={photo} alt="Load photo preview" className="mt-3 max-h-48 rounded-lg border border-white/10" />
        )}
      </Card>

      <Card className="space-y-4">
        <div>
          <Label htmlFor="notes">Notes (optional)</Label>
          <Input id="notes" placeholder="Anything the office should know…"
                 value={notes} onChange={(e) => setNotes(e.target.value)} />
        </div>
        <div>
          <Label htmlFor="sig">Signature — type your full name</Label>
          <Input id="sig" placeholder="John Driver"
                 value={signature} onChange={(e) => setSignature(e.target.value)} />
        </div>
      </Card>

      {error && <p className="text-sm text-red-400">{error}</p>}

      <div className="grid grid-cols-2 gap-3">
        <Button variant="secondary" size="lg" onClick={onCancel} disabled={busy}>Back</Button>
        <Button size="lg" onClick={submit} disabled={busy}>
          {busy ? "Saving…" : "Submit ticket"}
        </Button>
      </div>
    </div>
  );
}
