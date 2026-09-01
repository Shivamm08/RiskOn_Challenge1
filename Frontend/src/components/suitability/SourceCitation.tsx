import { BadgeCheck, ExternalLink, FileText, Quote, X } from "lucide-react";

import { Button } from "@/components/ui/button";
import { useExperts } from "@/lib/experts/store";
import { useSuitability } from "@/lib/suitability/store";
import type { SourceRef } from "@/lib/suitability/types";
import { cn } from "@/lib/utils";

/** Peer-endorsement trust indicator for KB-sourced guidance. */
export function TrustBadge({ sourceTitle }: { sourceTitle: string }) {
  const { kbForSource } = useExperts();
  const entry = kbForSource(sourceTitle);
  if (!entry || entry.endorsedBy.length === 0) return null;
  return (
    <span className="mt-1 inline-flex items-center gap-1 rounded-sm border border-success/40 bg-success-surface px-1 py-px text-[10px] uppercase tracking-wide text-success-foreground">
      <BadgeCheck className="size-2.5" /> Endorsed by {entry.endorsedBy.length} expert
      {entry.endorsedBy.length === 1 ? "" : "s"}
    </span>
  );
}


export function SourceChip({
  source,
  exchangeId,
  index,
}: {
  source: SourceRef;
  exchangeId: string;
  index: number;
}) {
  const { openCitation, activeCitation, openSource } = useSuitability();
  const isActive =
    activeCitation?.exchangeId === exchangeId &&
    activeCitation.source.page_title === source.page_title;

  return (
    <button
      type="button"
      onClick={() => {
        openCitation(source, exchangeId);
        openSource(source);
      }}
      title={source.excerpt}
      className={cn(
        "group flex max-w-full items-start gap-2 rounded-sm border px-2.5 py-2 text-left transition-colors",
        isActive
          ? "border-gold bg-cream text-cream-foreground"
          : "border-border bg-surface-2 hover:border-gold/60",
      )}
    >
      <FileText className="mt-0.5 size-3.5 shrink-0 text-gold" />
      <span className="min-w-0">
        <span className="block text-xs font-medium leading-snug">
          <span className="font-mono text-gold">[{index + 1}]</span> {source.page_title}
        </span>
        <span className="mt-0.5 block truncate text-[11px] text-muted-foreground">
          {source.excerpt}
        </span>
        <TrustBadge sourceTitle={source.page_title} />
      </span>

    </button>
  );
}

export function CitationPanel() {
  const { activeCitation, closeCitation, openSource } = useSuitability();
  if (!activeCitation) return null;
  const { source } = activeCitation;

  return (
    <aside className="flex h-full w-full shrink-0 flex-col border-l border-border bg-surface lg:w-96">
      <div className="flex items-center justify-between border-b border-border px-5 py-3">
        <h2 className="label-xs text-muted-foreground">Source citation</h2>
        <Button variant="ghost" size="icon" onClick={closeCitation} aria-label="Close citation">
          <X className="size-4" />
        </Button>
      </div>
      <div className="flex-1 overflow-y-auto px-5 py-5">
        <p className="label-xs text-gold">Cited document</p>
        <h3 className="mt-1.5 text-base font-medium leading-snug">{source.page_title}</h3>
        <div className="mt-5 border-l-2 border-gold bg-surface-2 px-4 py-3.5">
          <Quote className="mb-2 size-3.5 text-gold" />
          <p className="font-display text-[15px] leading-relaxed">{source.excerpt}</p>
        </div>
        <Button
          variant="outline"
          size="sm"
          className="mt-4 w-full text-xs"
          onClick={() => openSource(source)}
        >
          {(source.fileType ?? (source.url ? "link" : "doc")) === "link" ? (
            <>
              <ExternalLink className="size-3.5" /> Open in new tab
            </>
          ) : (
            <>
              <FileText className="size-3.5" /> Open {(source.fileType ?? "doc").toUpperCase()}{" "}
              preview
            </>
          )}
        </Button>
        <dl className="mt-5 space-y-2.5 border-t border-border pt-4 text-xs">
          <div className="flex justify-between gap-4">
            <dt className="text-muted-foreground">Knowledge base</dt>
            <dd className="text-right">Suitability Wiki</dd>
          </div>
          <div className="flex justify-between gap-4">
            <dt className="text-muted-foreground">Reference</dt>
            <dd className="font-mono text-right">{source.url ?? "internal / not linked"}</dd>
          </div>
          <div className="flex justify-between gap-4">
            <dt className="text-muted-foreground">Retrieved</dt>
            <dd className="text-right">Verbatim excerpt, unmodified</dd>
          </div>
        </dl>
        <p className="mt-5 text-[11px] leading-relaxed text-muted-foreground">
          This excerpt is the exact passage relied upon for the answer. If the passage does not
          support the answer as written, escalate to your Suitability Champion.
        </p>
      </div>
    </aside>
  );
}
