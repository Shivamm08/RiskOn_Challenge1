import { ChevronRight } from "lucide-react";

import { cn } from "@/lib/utils";
import { TIER_LADDER, type EscalationTier } from "@/lib/suitability/types";

export function EscalationLadder({ active }: { active: EscalationTier }) {
  return (
    <div className="flex flex-wrap items-center gap-x-1 gap-y-1.5">
      {TIER_LADDER.map((step, i) => {
        const isActive = step.tier === active;
        return (
          <div key={step.tier} className="flex items-center gap-1">
            <span
              className={cn(
                "label-xs rounded-sm border px-2 py-1",
                isActive
                  ? "border-danger bg-danger-surface text-danger-foreground"
                  : "border-border text-muted-foreground",
              )}
            >
              {step.label}
            </span>
            {i < TIER_LADDER.length - 1 && (
              <ChevronRight className="size-3 shrink-0 text-muted-foreground/60" />
            )}
          </div>
        );
      })}
    </div>
  );
}
