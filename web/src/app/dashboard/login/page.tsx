"use client";

// Office sign-in (dispatch / admin / AR): same Name + PIN accounts as the
// Streamlit app, same pad as the driver login.
import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Truck, Delete } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input, Label } from "@/components/ui/input";

export default function OfficeLoginPage() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [pin, setPin] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  function press(d: string) {
    setError(null);
    if (pin.length < 8) setPin(pin + d);
  }

  async function submit() {
    if (!name || pin.length < 4) {
      setError("Enter your name and at least a 4-digit PIN.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("/api/auth/office", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, pin }),
      });
      if (!res.ok) throw new Error();
      router.push("/dashboard");
    } catch {
      setError("Wrong name or PIN. Please try again.");
      setPin("");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="bg-grid flex min-h-screen items-center justify-center px-6">
      <div className="glow pointer-events-none absolute inset-0" aria-hidden />
      <div className="relative w-full max-w-sm">
        <Link href="/" className="mb-8 flex items-center justify-center gap-2 font-semibold">
          <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-brand text-white">
            <Truck className="h-4 w-4" />
          </span>
          TicketDrop
        </Link>

        <div className="rounded-xl border border-white/10 bg-surface p-8">
          <h1 className="text-xl font-semibold">Office sign in</h1>
          <p className="mt-1 text-sm text-muted">Dispatch, billing and admin.</p>

          <div className="mt-6 space-y-4">
            <div>
              <Label htmlFor="name">Your name</Label>
              <Input id="name" placeholder="e.g. Dispatch" value={name}
                     onChange={(e) => setName(e.target.value)} />
            </div>
            <div>
              <Label>PIN</Label>
              <div className="flex h-12 items-center justify-center gap-3 rounded-lg border border-white/10 bg-surface-2 text-2xl tracking-[0.5em]">
                {pin ? "•".repeat(pin.length) : <span className="text-base text-muted/50">— — — —</span>}
              </div>
            </div>
            <div className="grid grid-cols-3 gap-2">
              {["1","2","3","4","5","6","7","8","9"].map((d) => (
                <Button key={d} variant="secondary" size="lg" onClick={() => press(d)}>{d}</Button>
              ))}
              <Button variant="ghost" size="lg" onClick={() => setPin("")}>Clear</Button>
              <Button variant="secondary" size="lg" onClick={() => press("0")}>0</Button>
              <Button variant="ghost" size="lg" onClick={() => setPin(pin.slice(0, -1))} aria-label="Backspace">
                <Delete className="h-5 w-5" />
              </Button>
            </div>
            {error && <p className="text-sm text-red-400">{error}</p>}
            <Button className="w-full" size="lg" onClick={submit} disabled={loading}>
              {loading ? "Checking…" : "Sign in"}
            </Button>
          </div>
        </div>

        <p className="mt-6 text-center text-sm text-muted">
          Driving today?{" "}
          <Link href="/driver/login" className="text-brand-light hover:underline">
            Use the driver login
          </Link>
        </p>
      </div>
    </main>
  );
}
