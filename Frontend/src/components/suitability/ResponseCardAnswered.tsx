import { ShieldCheck } from "lucide-react";

import { ConfidenceBadge } from "./ConfidenceBadge";
import { ReasoningTrail } from "./ReasoningTrail";
import { SourceChip } from "./SourceCitation";
import type { Exchange } from "@/lib/suitability/types";

export function ResponseCardAnswered({ exchange }: { exchange: Exchange }) {
  const { response } = exchange;

  return (
    <article className="overflow-hidden rounded-md border border-border border-l-2 border-l-success bg-card">
      <header className="flex flex-wrap items-center justify-between gap-3 border-b border-border bg-success-surface px-4 py-2.5">
        <div className="flex items-center gap-2">
          <ShieldCheck className="size-4 text-success" />
          <span className="label-xs text-success-foreground">Answered</span>
        </div>
        <ConfidenceBadge value={response.confidence.answer_confidence} />
      </header>

      <div className="space-y-4 px-4 py-4">
        <p className="text-sm leading-relaxed">{response.answer}</p>

        {response.sources.length > 0 && (
          <div>
            <p className="label-xs mb-2 text-muted-foreground">
              Sources · {response.sources.length}
            </p>
            <div className="grid gap-1.5 sm:grid-cols-2">
              {response.sources.map((source, i) => (
                <SourceChip
                  key={source.page_title}
                  source={source}
                  exchangeId={exchange.id}
                  index={i}
                />
              ))}
            </div>
          </div>
        )}

        <ReasoningTrail steps={response.reasoning ?? []} scopeFlags={response.scope_flags} />
      </div>
    </article>
  );
}
