"use client";

// Catches any unexpected crash in a page and shows a friendly recovery screen
// instead of a blank page. The error is logged to the browser console and,
// on Vercel/Railway, to the server logs.
import { useEffect } from "react";
import { Button } from "@/components/ui/button";

export default function ErrorPage({ error, reset }: { error: Error & { digest?: string }; reset: () => void }) {
  useEffect(() => {
    console.error("page_crashed", error);
  }, [error]);

  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-4 px-6 text-center">
      <h1 className="text-2xl font-semibold">Something went wrong</h1>
      <p className="max-w-sm text-sm text-muted">
        The page hit an unexpected error. Your data is safe — anything you
        submitted was either saved or is still in your outbox.
      </p>
      {error.digest && <p className="text-xs text-muted">Error code: {error.digest}</p>}
      <div className="flex gap-3">
        <Button onClick={reset}>Try again</Button>
        <Button variant="secondary" onClick={() => (window.location.href = "/")}>Go home</Button>
      </div>
    </main>
  );
}
