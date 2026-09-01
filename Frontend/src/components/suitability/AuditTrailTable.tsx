import { ChevronRight, Download, Search } from "lucide-react";
import { useMemo, useState } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useSuitability } from "@/lib/suitability/store";
import { TIER_LADDER, type Exchange, type ResponseStatus } from "@/lib/suitability/types";
import { cn } from "@/lib/utils";

const STATUS_STYLE: Record<ResponseStatus, string> = {
  answered: "border-success/40 bg-success-surface text-success-foreground",
  escalated: "border-danger/40 bg-danger-surface text-danger-foreground",
  clarification_needed: "border-info/40 bg-info-surface text-info-foreground",
  out_of_scope: "border-border bg-muted text-muted-foreground",
};

const STATUS_LABEL: Record<ResponseStatus, string> = {
  answered: "Answered",
  escalated: "Escalated",
  clarification_needed: "Clarification",
  out_of_scope: "Out of scope",
};

const FILTERS: ("all" | ResponseStatus)[] = [
  "all",
  "answered",
  "escalated",
  "clarification_needed",
  "out_of_scope",
];

function tierLabel(tier: string) {
  return TIER_LADDER.find((t) => t.tier === tier)?.label ?? tier;
}

function Detail({ exchange }: { exchange: Exchange }) {
  const { response, resolution } = exchange;
  return (
    <div className="grid gap-5 border-t border-border bg-surface-2 px-4 py-4 lg:grid-cols-2">
      <div className="space-y-3">
        <p className="label-xs text-muted-foreground">Cited excerpts</p>
        {response.sources.length === 0 ? (
          <p className="text-xs text-muted-foreground">No sources retrieved above threshold.</p>
        ) : (
          response.sources.map((source, i) => (
            <div key={source.page_title} className="border-l-2 border-gold pl-3">
              <p className="text-xs font-medium">
                <span className="font-mono text-gold">[{i + 1}]</span> {source.page_title}
              </p>
              <p className="mt-1 font-display text-[13px] leading-relaxed text-muted-foreground">
                “{source.excerpt}”
              </p>
            </div>
          ))
        )}
        {response.scope_flags.length > 0 && (
          <div className="flex flex-wrap gap-1.5 pt-1">
            {response.scope_flags.map((flag) => (
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

      <div className="space-y-4">
        {response.answer && (
          <div>
            <p className="label-xs text-muted-foreground">Answer issued</p>
            <p className="mt-1 text-xs leading-relaxed">{response.answer}</p>
          </div>
        )}
        {response.clarification_question && (
          <div>
            <p className="label-xs text-muted-foreground">Clarification requested</p>
            <p className="mt-1 text-xs leading-relaxed">{response.clarification_question}</p>
          </div>
        )}
        {response.escalation && (
          <div>
            <p className="label-xs text-muted-foreground">Escalation reasoning</p>
            <p className="mt-1 text-xs leading-relaxed">{response.escalation.reason}</p>
            <dl className="mt-2 space-y-1 text-xs">
              <div className="flex gap-2">
                <dt className="w-24 shrink-0 text-muted-foreground">Tier</dt>
                <dd>{tierLabel(response.escalation.tier)}</dd>
              </div>
              <div className="flex gap-2">
                <dt className="w-24 shrink-0 text-muted-foreground">Routed to</dt>
                <dd>
                  {response.escalation.expert.name} — {response.escalation.expert.role},{" "}
                  {response.escalation.expert.team}
                </dd>
              </div>
              <div className="flex gap-2">
                <dt className="w-24 shrink-0 text-muted-foreground">Fallback</dt>
                <dd>
                  {response.escalation.fallback_contact.name} —{" "}
                  {response.escalation.fallback_contact.role}
                </dd>
              </div>
            </dl>
          </div>
        )}
        {(response.reasoning?.length ?? 0) > 0 && (
          <div>
            <p className="label-xs text-muted-foreground">Reasoning trail</p>
            <ol className="mt-1 space-y-1">
              {response.reasoning!.map((step, i) => (
                <li key={i} className="flex gap-2 text-xs leading-relaxed text-muted-foreground">
                  <span className="font-mono text-gold">{String(i + 1).padStart(2, "0")}</span>
                  {step}
                </li>
              ))}
            </ol>
          </div>
        )}
        {resolution && (
          <div className="rounded-sm border border-success/40 bg-success-surface px-3 py-2">
            <p className="label-xs text-success-foreground">
              Resolved by {resolution.resolvedBy} ·{" "}
              {new Date(resolution.resolvedAt).toLocaleString()}
            </p>
            <p className="mt-1 text-xs leading-relaxed">{resolution.note}</p>
          </div>
        )}
      </div>
    </div>
  );
}

export function AuditTrailTable() {
  const { auditRecords } = useSuitability();
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState<"all" | ResponseStatus>("all");
  const [expanded, setExpanded] = useState<string | null>(null);

  const rows = useMemo(() => {
    const q = query.trim().toLowerCase();
    return auditRecords.filter((e) => {
      if (status !== "all" && e.response.status !== status) return false;
      if (!q) return true;
      return (
        e.question.toLowerCase().includes(q) ||
        e.askedBy.toLowerCase().includes(q) ||
        (e.response.answer ?? "").toLowerCase().includes(q) ||
        e.response.sources.some((s) => s.page_title.toLowerCase().includes(q))
      );
    });
  }, [auditRecords, query, status]);

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-3">
        <div className="relative min-w-56 flex-1">
          <Search className="absolute left-2.5 top-1/2 size-3.5 -translate-y-1/2 text-muted-foreground" />
          <Input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search questions, RMs, answers, sources"
            className="bg-surface pl-8 text-sm"
          />
        </div>
        <div className="flex items-center gap-1">
          {FILTERS.map((f) => (
            <button
              key={f}
              type="button"
              onClick={() => setStatus(f)}
              className={cn(
                "label-xs rounded-sm border px-2 py-1.5 transition-colors",
                status === f
                  ? "border-gold bg-cream text-cream-foreground"
                  : "border-border text-muted-foreground hover:text-foreground",
              )}
            >
              {f === "all" ? "All" : STATUS_LABEL[f]}
            </button>
          ))}
        </div>
        <Button variant="outline" size="sm" onClick={() => toast.info("Export queued (demo)")}>
          <Download className="size-3.5" /> Export
        </Button>
      </div>

      <div className="overflow-hidden rounded-md border border-border bg-card">
        <div className="hidden grid-cols-[130px_100px_1fr_110px_90px_80px_120px_28px] gap-3 border-b border-border bg-surface-2 px-4 py-2 lg:grid">
          {["Timestamp", "RM", "Question", "Status", "Confidence", "Sources", "Resolution", ""].map(
            (h) => (
              <span key={h} className="label-xs text-muted-foreground">
                {h}
              </span>
            ),
          )}
        </div>

        <ul className="divide-y divide-border">
          {rows.map((exchange) => {
            const open = expanded === exchange.id;
            return (
              <li key={exchange.id}>
                <button
                  type="button"
                  onClick={() => setExpanded(open ? null : exchange.id)}
                  className="grid w-full grid-cols-1 gap-2 px-4 py-3 text-left transition-colors hover:bg-surface-2 lg:grid-cols-[130px_100px_1fr_110px_90px_80px_120px_28px] lg:items-center lg:gap-3"
                >
                  <span className="font-mono text-[11px] text-muted-foreground">
                    {new Date(exchange.askedAt).toLocaleString([], {
                      day: "2-digit",
                      month: "short",
                      hour: "2-digit",
                      minute: "2-digit",
                    })}
                  </span>
                  <span className="text-xs text-muted-foreground">{exchange.askedBy}</span>
                  <span className="line-clamp-2 text-xs leading-snug">{exchange.question}</span>
                  <span
                    className={cn(
                      "label-xs w-fit rounded-sm border px-1.5 py-0.5",
                      STATUS_STYLE[exchange.response.status],
                    )}
                  >
                    {STATUS_LABEL[exchange.response.status]}
                  </span>
                  <span className="font-mono text-xs tabular-nums text-muted-foreground">
                    {Math.round(exchange.response.confidence.answer_confidence * 100)}%
                  </span>
                  <span className="font-mono text-xs text-muted-foreground">
                    {exchange.response.sources.length}
                  </span>
                  <span className="text-[11px] text-muted-foreground">
                    {exchange.resolution
                      ? `Resolved · ${exchange.resolution.resolvedBy}`
                      : exchange.response.status === "escalated"
                        ? "Open"
                        : "—"}
                  </span>
                  <ChevronRight
                    className={cn(
                      "hidden size-3.5 text-muted-foreground transition-transform lg:block",
                      open && "rotate-90",
                    )}
                  />
                </button>
                {open && <Detail exchange={exchange} />}
              </li>
            );
          })}
          {rows.length === 0 && (
            <li className="px-4 py-10 text-center text-xs text-muted-foreground">
              No records match the current filters.
            </li>
          )}
        </ul>
      </div>
    </div>
  );
}
