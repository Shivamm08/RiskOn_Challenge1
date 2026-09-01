import { ChevronDown } from "lucide-react";
import { useState } from "react";

import { cn } from "@/lib/utils";

export function ReasoningTrail({
  steps,
  scopeFlags,
  label = "Why this answer",
}: {
  steps: string[];
  scopeFlags: string[];
  label?: string;
}) {
  const [open, setOpen] = useState(false);
  if (steps.length === 0 && scopeFlags.length === 0) return null;

  return (
    <div className="border-t border-border pt-3">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="label-xs flex items-center gap-1.5 text-muted-foreground transition-colors hover:text-foreground"
        aria-expanded={open}
      >
        <ChevronDown className={cn("size-3.5 transition-transform", open && "rotate-180")} />
        {label}
      </button>
      {open && (
        <div className="mt-3 space-y-3">
          {steps.length > 0 && (
            <ol className="space-y-1.5">
              {steps.map((step, i) => (
                <li key={i} className="flex gap-2.5 text-xs leading-relaxed text-muted-foreground">
                  <span className="font-mono text-gold">{String(i + 1).padStart(2, "0")}</span>
                  <span>{step}</span>
                </li>
              ))}
            </ol>
          )}
          {scopeFlags.length > 0 && (
            <div className="flex flex-wrap gap-1.5">
              {scopeFlags.map((flag) => (
                <span
                  key={flag}
                  className="rounded-sm border border-border px-1.5 py-0.5 font-mono text-[10px] text-muted-foreground"
                >
                  {flag}
                </span>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
