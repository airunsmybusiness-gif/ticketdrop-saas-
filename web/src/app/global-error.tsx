"use client";

// Last-resort error screen if even the root layout crashes.
export default function GlobalError({ error, reset }: { error: Error & { digest?: string }; reset: () => void }) {
  return (
    <html lang="en">
      <body style={{ background: "#07070b", color: "#f4f4f6", fontFamily: "system-ui", display: "flex", minHeight: "100vh", alignItems: "center", justifyContent: "center", flexDirection: "column", gap: 16, padding: 24, textAlign: "center" }}>
        <h1 style={{ fontSize: 22, fontWeight: 600 }}>Something went wrong</h1>
        <p style={{ color: "#9ca3af", maxWidth: 360, fontSize: 14 }}>
          Please reload the page. If this keeps happening, contact your office.
        </p>
        {error.digest && <p style={{ color: "#6b7280", fontSize: 12 }}>Error code: {error.digest}</p>}
        <button onClick={reset} style={{ background: "#8b5cf6", color: "#fff", border: 0, borderRadius: 8, padding: "12px 28px", fontSize: 14, fontWeight: 500, cursor: "pointer" }}>
          Reload
        </button>
      </body>
    </html>
  );
}
