import { HelpCircle } from "lucide-react";

import { ReasoningTrail } from "./ReasoningTrail";
import { useSuitability } from "@/lib/suitability/store";
import type { Exchange } from "@/lib/suitability/types";

export function ResponseCardClarification({ exchange }: { exchange: Exchange }) {
  const { response } = exchange;
  const { ask, pendingQuestion } = useSuitability();

  return (
    <article className="overflow-hidden rounded-md border border-border border-l-2 border-l-info bg-card">
      <header className="flex items-center gap-2 border-b border-border bg-info-surface px-4 py-2.5">
        <HelpCircle className="size-4 text-info" />
        <span className="label-xs text-info-foreground">Clarification needed</span>
      </header>

      <div className="space-y-4 px-4 py-4">
        <p className="font-display text-[15px] leading-relaxed">
          {response.clarification_question}
        </p>

        {(response.quick_replies?.length ?? 0) > 0 && (
          <div>
            <p className="label-xs mb-2 text-muted-foreground">Quick reply</p>
            <div className="flex flex-wrap gap-1.5">
              {response.quick_replies!.map((reply) => (
                <button
                  key={reply}
                  type="button"
                  disabled={pendingQuestion !== null}
                  onClick={() => void ask(reply)}
                  className="rounded-sm border border-info/40 bg-info-surface px-2.5 py-1.5 text-xs font-medium text-info-foreground transition-colors hover:border-info disabled:opacity-50"
                >
                  {reply}
                </button>
              ))}
            </div>
            <p className="mt-2 text-[11px] text-muted-foreground">
              Or answer in your own words in the input below.
            </p>
          </div>
        )}

        <ReasoningTrail
          steps={response.reasoning ?? []}
          scopeFlags={response.scope_flags}
          label="Why this was asked"
        />
      </div>
    </article>
  );
}
