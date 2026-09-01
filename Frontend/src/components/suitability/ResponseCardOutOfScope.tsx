import { CircleOff } from "lucide-react";

import { ReasoningTrail } from "./ReasoningTrail";
import type { Exchange } from "@/lib/suitability/types";

export function ResponseCardOutOfScope({ exchange }: { exchange: Exchange }) {
  const { response } = exchange;

  return (
    <article className="overflow-hidden rounded-md border border-border border-l-2 bg-card">
      <header className="flex items-center gap-2 border-b border-border bg-muted px-4 py-2.5">
        <CircleOff className="size-4 text-muted-foreground" />
        <span className="label-xs text-muted-foreground">Out of scope</span>
      </header>
      <div className="space-y-4 px-4 py-4">
        <p className="text-sm leading-relaxed">{response.answer}</p>
        <ReasoningTrail steps={response.reasoning ?? []} scopeFlags={response.scope_flags} />
      </div>
    </article>
  );
}
