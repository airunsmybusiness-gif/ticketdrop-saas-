"use client";

/**
 * Printable invoice — a paper-white preview the office can print or save
 * as PDF with the browser's print dialog (the buttons hide when printing).
 */
import { useCallback, useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { Printer, ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";

type InvoiceData = {
  invoice: {
    invoice_number: string; customer_name: string | null;
    subtotal: string; tax: string; total: string; created_at: string;
  };
  company: {
    name: string; address: string | null; phone: string | null;
    tax_rate: string | null; tax_label: string | null; invoice_terms: string | null;
  };
  tickets: {
    id: number; ticket_number: string | null; ticket_date: string | null;
    operator_name: string | null; actual_volume: string | null;
    hours_charged: string | null; product: string | null;
  }[];
  rates: { rate_per_m3: number; rate_per_hour: number };
};

const money = (n: number) => `$${n.toLocaleString("en-CA", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

export default function InvoicePage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [data, setData] = useState<InvoiceData | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const res = await fetch(`/api/billing/invoice/${id}`);
      if (res.status === 401 || res.status === 403) { router.push("/dashboard/login"); return; }
      if (!res.ok) { setError("Invoice not found."); return; }
      setData(await res.json());
    } catch {
      setError("Could not load the invoice — check your connection.");
    }
  }, [id, router]);

  useEffect(() => { load(); }, [load]);

  if (error) return <main className="p-10 text-center text-muted">{error}</main>;
  if (!data) return <main className="p-10 text-center text-muted">Loading invoice…</main>;

  const { invoice, company, tickets, rates } = data;
  const issued = new Date(invoice.created_at);
  const due = new Date(issued.getTime() + 30 * 24 * 3600 * 1000);

  // line items: volume row (and hours row) per ticket
  const lines: { desc: string; qty: number; unit: string; rate: number; amount: number }[] = [];
  for (const t of tickets) {
    const vol = Number(t.actual_volume ?? 0);
    const hrs = Number(t.hours_charged ?? 0);
    const tag = `Ticket ${t.ticket_number || `#${t.id}`} · ${t.ticket_date?.slice(0, 10) ?? ""}`;
    if (vol > 0) lines.push({ desc: `${tag} — ${t.product || "Fluid hauling"}`, qty: vol, unit: "m³", rate: rates.rate_per_m3, amount: vol * rates.rate_per_m3 });
    if (hrs > 0 && rates.rate_per_hour > 0) lines.push({ desc: `${tag} — hourly / standby`, qty: hrs, unit: "hr", rate: rates.rate_per_hour, amount: hrs * rates.rate_per_hour });
  }

  return (
    <main className="min-h-screen bg-background px-4 py-8 print:bg-white print:p-0">
      {/* toolbar (hidden when printing) */}
      <div className="mx-auto mb-5 flex max-w-3xl items-center justify-between print:hidden">
        <Button variant="secondary" size="sm" onClick={() => router.push("/billing")}>
          <ArrowLeft className="h-4 w-4" /> Back to billing
        </Button>
        <Button size="sm" onClick={() => window.print()}>
          <Printer className="h-4 w-4" /> Print / Save as PDF
        </Button>
      </div>

      {/* paper */}
      <div className="mx-auto max-w-3xl rounded-xl bg-white p-8 text-slate-900 shadow-2xl print:max-w-none print:rounded-none print:p-6 print:shadow-none sm:p-10">
        {/* header band */}
        <div className="flex items-start justify-between rounded-lg bg-slate-900 px-6 py-5 text-white">
          <div>
            <h1 className="text-xl font-bold">{company.name}</h1>
            <p className="mt-1 text-xs text-slate-300">
              {[company.address, company.phone].filter(Boolean).join(" · ")}
            </p>
          </div>
          <div className="text-right">
            <p className="text-xl font-bold tracking-wide text-orange-400">INVOICE</p>
            <p className="mt-1 text-xs text-slate-300">{invoice.invoice_number}</p>
          </div>
        </div>

        {/* meta */}
        <div className="mt-6 flex flex-wrap justify-between gap-4 text-sm">
          <div>
            <p className="text-xs uppercase tracking-wider text-slate-400">Bill to</p>
            <p className="mt-1 font-semibold">{invoice.customer_name || "Customer"}</p>
          </div>
          <div className="text-right">
            <p><span className="text-slate-400">Date:</span> {issued.toLocaleDateString()}</p>
            <p><span className="text-slate-400">Due:</span> {due.toLocaleDateString()}</p>
          </div>
        </div>

        {/* line items */}
        <table className="mt-6 w-full text-sm">
          <thead>
            <tr className="bg-slate-100 text-left text-xs uppercase tracking-wider text-slate-500">
              <th className="rounded-l px-3 py-2.5">Description</th>
              <th className="px-3 py-2.5 text-right">Qty</th>
              <th className="px-3 py-2.5">Unit</th>
              <th className="px-3 py-2.5 text-right">Rate</th>
              <th className="rounded-r px-3 py-2.5 text-right">Amount</th>
            </tr>
          </thead>
          <tbody>
            {lines.map((l, i) => (
              <tr key={i} className="border-b border-slate-100">
                <td className="px-3 py-2.5">{l.desc}</td>
                <td className="px-3 py-2.5 text-right tabular-nums">{l.qty.toLocaleString()}</td>
                <td className="px-3 py-2.5">{l.unit}</td>
                <td className="px-3 py-2.5 text-right tabular-nums">{money(l.rate)}</td>
                <td className="px-3 py-2.5 text-right tabular-nums">{money(l.amount)}</td>
              </tr>
            ))}
          </tbody>
        </table>

        {/* totals */}
        <div className="mt-5 ml-auto w-56 space-y-1.5 text-sm">
          <div className="flex justify-between"><span className="text-slate-500">Subtotal</span><span className="tabular-nums">{money(Number(invoice.subtotal))}</span></div>
          <div className="flex justify-between">
            <span className="text-slate-500">{company.tax_label || "Tax"} ({Number(company.tax_rate ?? 0)}%)</span>
            <span className="tabular-nums">{money(Number(invoice.tax))}</span>
          </div>
          <div className="flex justify-between border-t-2 border-orange-500 pt-2 text-base font-bold">
            <span>Total</span><span className="tabular-nums text-orange-600">{money(Number(invoice.total))}</span>
          </div>
        </div>

        {/* footer */}
        <div className="mt-8 border-t border-slate-200 pt-4 text-xs text-slate-500">
          {company.invoice_terms && <p>{company.invoice_terms}</p>}
          <p className="mt-1">Thank you for your business — {company.name}</p>
        </div>
      </div>
    </main>
  );
}
