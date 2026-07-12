import * as React from "react";
import { cn } from "@/lib/utils";

const tones = {
  brand: "bg-brand/15 text-brand-light border-brand/30",
  green: "bg-emerald-500/15 text-emerald-400 border-emerald-500/30",
  amber: "bg-amber-500/15 text-amber-400 border-amber-500/30",
  grey: "bg-white/8 text-muted border-white/10",
} as const;

export function Badge({
  tone = "grey",
  className,
  ...props
}: React.HTMLAttributes<HTMLSpanElement> & { tone?: keyof typeof tones }) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium",
        tones[tone],
        className
      )}
      {...props}
    />
  );
}
