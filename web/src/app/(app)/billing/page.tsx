"use client";

/**
 * Billing / AR — review submitted tickets (details + photo), approve them
 * for invoicing, and turn ready tickets into invoices. Three tabs:
 * Review → Ready to invoice → Invoices.
 */
import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { CheckCircle2, AlertTriangle, Receipt, RefreshCw, Camera } from "lucide-react";
import { Card, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input, Label } from "@/components/ui/input";

function fetchT(url: string, init?: RequestInit): Promise<Response> {
  return fetch(url, { ...init, signal: AbortSignal.timeout(15_000) });
}

type ReviewTicket = {
  id: number; ticket_number: string | null; ticket_date: string | null;
  customer_name: string | null; operator_name: string | null;
  actual_volume: string | null; hours_charged: string | null;
  hazards: string[] | null; hazard_notes: string | null;
  driver_signature: string | null; load_id: number | null;
  pickup_location: string | null; delivery_location: string | null;
  product: string | null; has_photo: boolean;
};
type ReadyTicket = {
  id: number; ticket_number: string | null; ticket_date: string | null;
  customer_name: string | null; actual_volume: string | null; hours_charged: string | null;
};
type Invoice = {
  id: number; invoice_number: string; customer_name: string | null;
  subtotal: string; tax: string; total: string; created_at: string;
};
type Rates = { rate_per_m3: number; rate_per_hour: number; tax_rate: number; tax_label: string };
type Data = { to_review: ReviewTicket[]; ready: ReadyTicket[]; invoices: Invoice[]; rates: Rates };

const money = (n: number) => `$${n.toLocaleString("en-CA", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

export default function BillingPage() {
  const router = useRouter();
  const [data, setData] = useState<Data | null>(null);
  const [tab, setTab] = useState<"review" | "ready" | "invoices">("review");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      const res = await fetchT("/api/billing/tickets");
      if (res.status === 401 || res.status === 403) { router.push("/dashboard/login"); return; }
      if (res.ok) setData(await res.json());
    } catch { /* keep last data */ }
  }, [router]);

  useEffect(() => {
    refresh();
    const poll = setInterval(() => {
      if (document.visibilityState === "visible") refresh();
    }, 30_000);
    return () => clearInterval(poll);
  }, [refresh]);

  async function review(ticketId: number, action: "approve" | "dispute") {
    setBusy(true);
    setMessage(null);
    try {
      const res = await fetchT("/api/billing/review", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ticket_id: ticketId, action }),
      });
      const d = await res.json().catch(() => ({}));
      if (!res.ok) { setMessage(d.error || "Could not update the ticket"); return; }
      setMessage(action === "approve" ? "✅ Ticket approved — it's in Ready to invoice." : "Ticket marked disputed.");
      await refresh();
    } catch {
      setMessage("No connection — try again in a moment.");
    } finally {
      setBusy(false);
    }
  }

  if (!data) {
    return <div className="mx-auto max-w-4xl"><p className="text-muted">Loading billing…</p></div>;
  }

  const tabs = [
    { key: "review" as const, label: `To review (${data.to_review.length})` },
    { key: "ready" as const, label: `Ready to invoice (${data.ready.length})` },
    { key: "invoices" as const, label: `Invoices (${data.invoices.length})` },
  ];

  return (
    <div className="mx-auto max-w-4xl space-y-5 pb-16">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight md:text-3xl">Billing / AR</h1>
          <p className="mt-1 text-sm text-muted">Review field tickets, approve them, send invoices.</p>
        </div>
        <Button variant="secondary" size="sm" onClick={refresh}>
          <RefreshCw className="h-4 w-4" /> Refresh
        </Button>
      </div>

      {/* tabs */}
      <div className="flex gap-2 overflow-x-auto">
        {tabs.map((t) => (
          <button key={t.key} onClick={() => setTab(t.key)}
            className={`whitespace-nowrap rounded-lg border px-4 py-2.5 text-sm font-medium transition-colors ${
              tab === t.key
                ? "border-brand bg-brand/15 text-brand-light"
                : "border-white/10 bg-surface text-muted hover:text-foreground"
            }`}>
            {t.label}
          </button>
        ))}
      </div>

      {message && <p className="text-sm text-muted">{message}</p>}

      {tab === "review" && <ReviewTab tickets={data.to_review} busy={busy} onReview={review} />}
      {tab === "ready" && <ReadyTab tickets={data.ready} rates={data.rates} onCreated={(id) => router.push(`/billing/invoice/${id}`)} />}
      {tab === "invoices" && <InvoicesTab invoices={data.invoices} onOpen={(id) => router.push(`/billing/invoice/${id}`)} />}
    </div>
  );
}

/* ------------------------------------------------------------------ */
function ReviewTab({ tickets, busy, onReview }: {
  tickets: ReviewTicket[]; busy: boolean;
  onReview: (id: number, action: "approve" | "dispute") => void;
}) {
  if (tickets.length === 0)
    return <Card><CardDescription>No tickets waiting for review. Completed loads land here automatically.</CardDescription></Card>;

  return (
    <div className="space-y-4">
      {tickets.map((t) => (
        <Card key={t.id}>
          <div className="flex flex-wrap items-center justify-between gap-2">
            <CardTitle>Ticket {t.ticket_number || `#${t.id}`} · {t.customer_name || "—"}</CardTitle>
            <Badge tone="amber">Needs review</Badge>
          </div>
          <CardDescription className="mt-2 space-y-1">
            <span className="block">{t.pickup_location || "—"} → {t.delivery_location || "—"}{t.product ? ` · ${t.product}` : ""}</span>
            <span className="block">
              Driver <span className="text-foreground">{t.operator_name}</span> · {t.actual_volume ?? "—"} m³
              {Number(t.hours_charged) > 0 ? ` · ${t.hours_charged} hr` : ""} · {t.ticket_date?.slice(0, 10) || "—"}
              {t.driver_signature ? ` · signed ${t.driver_signature}` : ""}
            </span>
          </CardDescription>

          {t.hazards && t.hazards.length > 0 && (
            <p className="mt-3 flex items-start gap-2 rounded-lg border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-sm text-amber-300">
              <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
              <span>{t.hazards.join(" · ")}{t.hazard_notes ? ` — ${t.hazard_notes}` : ""}</span>
            </p>
          )}

          {t.has_photo ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={`/api/billing/photo/${t.id}`} alt={`Load photo for ticket ${t.ticket_number || t.id}`}
                 className="mt-4 max-h-64 rounded-lg border border-white/10" />
          ) : (
            <p className="mt-4 flex items-center gap-2 rounded-lg border border-white/10 bg-surface-2 px-3 py-2.5 text-sm text-muted">
              <Camera className="h-4 w-4" /> No photo attached
            </p>
          )}

          <div className="mt-5 grid grid-cols-2 gap-3">
            <Button size="lg" disabled={busy} onClick={() => onReview(t.id, "approve")}>
              <CheckCircle2 className="h-4 w-4" /> Approve
            </Button>
            <Button variant="secondary" size="lg" disabled={busy} onClick={() => onReview(t.id, "dispute")}>
              Dispute
            </Button>
          </div>
        </Card>
      ))}
    </div>
  );
}

/* ------------------------------------------------------------------ */
function ReadyTab({ tickets, rates, onCreated }: {
  tickets: ReadyTicket[]; rates: Rates; onCreated: (invoiceId: number) => void;
}) {
  const [rateM3, setRateM3] = useState(String(rates.rate_per_m3 || ""));
  const [rateHr, setRateHr] = useState(String(rates.rate_per_hour || ""));
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (tickets.length === 0)
    return <Card><CardDescription>Nothing ready to invoice. Approve tickets in the Review tab first.</CardDescription></Card>;

  // group by customer — one invoice per customer
  const groups = new Map<string, ReadyTicket[]>();
  for (const t of tickets) {
    const key = t.customer_name || "Unknown";
    groups.set(key, [...(groups.get(key) ?? []), t]);
  }
  const m3 = parseFloat(rateM3) || 0;
  const hr = parseFloat(rateHr) || 0;

  async function createInvoice(group: ReadyTicket[]) {
    setBusy(true);
    setError(null);
    try {
      const res = await fetchT("/api/billing/invoice", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ticket_ids: group.map((t) => t.id),
          rate_per_m3: m3 || undefined,
          rate_per_hour: hr || undefined,
        }),
      });
      const d = await res.json().catch(() => ({}));
      if (!res.ok) { setError(d.error || "Could not create the invoice"); return; }
      onCreated(d.invoice_id);
    } catch {
      setError("No connection — try again in a moment.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-4">
      <Card className="space-y-3">
        <CardTitle>Rates for this invoice</CardTitle>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <Label htmlFor="rm3">Rate per m³ ($)</Label>
            <Input id="rm3" inputMode="decimal" value={rateM3} onChange={(e) => setRateM3(e.target.value)} />
          </div>
          <div>
            <Label htmlFor="rhr">Rate per hour ($)</Label>
            <Input id="rhr" inputMode="decimal" value={rateHr} onChange={(e) => setRateHr(e.target.value)} />
          </div>
        </div>
        <CardDescription>Prefilled from Settings — change per-invoice if needed. {rates.tax_label} {rates.tax_rate}% is added automatically.</CardDescription>
      </Card>

      {error && <p className="text-sm text-red-400">{error}</p>}

      {[...groups.entries()].map(([customer, group]) => {
        const subtotal = group.reduce((sum, t) =>
          sum + Number(t.actual_volume ?? 0) * m3 + Number(t.hours_charged ?? 0) * hr, 0);
        const tax = subtotal * rates.tax_rate / 100;
        return (
          <Card key={customer}>
            <div className="flex flex-wrap items-center justify-between gap-2">
              <CardTitle>{customer}</CardTitle>
              <Badge tone="brand">{group.length} ticket{group.length > 1 ? "s" : ""}</Badge>
            </div>
            <div className="mt-3 divide-y divide-white/5 rounded-lg border border-white/10">
              {group.map((t) => (
                <div key={t.id} className="flex items-center justify-between px-4 py-2.5 text-sm">
                  <span>{t.ticket_number || `#${t.id}`} · {t.ticket_date?.slice(0, 10)}</span>
                  <span className="text-muted">
                    {t.actual_volume ?? 0} m³{Number(t.hours_charged) > 0 ? ` + ${t.hours_charged} hr` : ""}
                  </span>
                </div>
              ))}
            </div>
            <div className="mt-4 flex flex-wrap items-center justify-between gap-3">
              <p className="text-sm text-muted">
                Subtotal <span className="text-foreground">{money(subtotal)}</span>
                {" · "}{rates.tax_label} <span className="text-foreground">{money(tax)}</span>
                {" · "}Total <span className="font-semibold text-brand-light">{money(subtotal + tax)}</span>
              </p>
              <Button disabled={busy || subtotal <= 0} onClick={() => createInvoice(group)}>
                <Receipt className="h-4 w-4" /> Create invoice
              </Button>
            </div>
          </Card>
        );
      })}
    </div>
  );
}

/* ------------------------------------------------------------------ */
function InvoicesTab({ invoices, onOpen }: { invoices: Invoice[]; onOpen: (id: number) => void }) {
  if (invoices.length === 0)
    return <Card><CardDescription>No invoices yet.</CardDescription></Card>;
  return (
    <Card className="p-0">
      <div className="divide-y divide-white/5">
        {invoices.map((inv) => (
          <button key={inv.id} onClick={() => onOpen(inv.id)}
            className="flex w-full items-center justify-between gap-3 px-6 py-4 text-left transition-colors hover:bg-white/5">
            <div>
              <p className="font-medium">{inv.invoice_number}</p>
              <p className="text-sm text-muted">{inv.customer_name} · {new Date(inv.created_at).toLocaleDateString()}</p>
            </div>
            <span className="font-semibold text-brand-light">{money(Number(inv.total))}</span>
          </button>
        ))}
      </div>
    </Card>
  );
}
