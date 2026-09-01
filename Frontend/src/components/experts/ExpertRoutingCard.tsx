import { ChevronDown, Clock, Compass, MapPin, Moon } from "lucide-react";
import { useEffect, useState } from "react";

import { getExpert, localTime, rankTierLabel, type Expert } from "@/lib/experts/roster";
import type { RoutingDecision } from "@/lib/experts/routing";
import { useExperts } from "@/lib/experts/store";
import { cn } from "@/lib/utils";

/** Live-ticking local clock for an expert. */
export function ExpertClock({ expertId, fixedAt }: { expertId: string; fixedAt?: string }) {
  const [now, setNow] = useState<Date>(() => (fixedAt ? new Date(fixedAt) : new Date()));

  useEffect(() => {
    if (fixedAt) return;
    const t = setInterval(() => setNow(new Date()), 30_000);
    return () => clearInterval(t);
  }, [fixedAt]);

  const expert = getExpert(expertId);
  if (!expert) return null;
  const t = localTime(expert, now);

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 font-mono text-[11px]",
        t.working ? "text-success-foreground" : "text-warning",
      )}
    >
      {t.working ? <Clock className="size-3" /> : <Moon className="size-3" />}
      {t.label} local, {expert.office}
    </span>
  );
}

/** "Tier 2 of 5 — Business Front Support". */
export function ExpertTier({ expert, className }: { expert: Expert; className?: string }) {
  return (
    <span className={cn("text-[11px] text-muted-foreground", className)}>
      {rankTierLabel(expert.rank)}
    </span>
  );
}

/** The routing engine's reasoning, rendered as a numbered list. */
export function RoutingReasoning({ decision }: { decision: RoutingDecision }) {
  return (
    <div>
      <p className="label-xs mb-2 flex items-center gap-1.5 text-muted-foreground">
        <Compass className="size-3.5" /> Why this expert
      </p>
      <ol className="space-y-1.5">
        {decision.reasoning.map((line, i) => (
          <li key={i} className="flex gap-2 text-xs leading-relaxed text-muted-foreground">
            <span className="font-mono text-[10px] text-gold">{i + 1}</span>
            <span>{line}</span>
          </li>
        ))}
      </ol>
      <p className="mt-2.5 flex items-center gap-1.5 text-[11px] text-muted-foreground">
        <MapPin className="size-3" /> Matched at the {decision.matchedTier} tier.
      </p>
    </div>
  );
}

function CandidateRow({
  expert,
  decision,
  chosen,
  fixedAt,
  defaultOpen,
}: {
  expert: Expert;
  decision: RoutingDecision;
  chosen: boolean;
  fixedAt?: string;
  defaultOpen?: boolean;
}) {
  const [open, setOpen] = useState(!!defaultOpen);
  const { favorabilityOf } = useExperts();
  const others = decision.candidateIds
    .filter((cid) => cid !== expert.id)
    .map((cid) => getExpert(cid))
    .filter((e): e is Expert => !!e);

  return (
    <li className={cn("rounded-sm border", chosen ? "border-gold/50 bg-surface-2" : "border-border")}>
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        className="flex w-full items-start gap-3 px-3 py-2.5 text-left"
      >
        <span className="mt-0.5 flex size-8 shrink-0 items-center justify-center rounded-full bg-cream text-[11px] font-medium text-cream-foreground">
          {expert.initials}
        </span>
        <span className="min-w-0 flex-1">
          <span className="flex flex-wrap items-center gap-x-2">
            <span className="text-sm font-medium">{expert.name}</span>
            {chosen && (
              <span className="label-xs rounded-sm border border-gold/50 px-1 py-px text-gold">
                Routed here
              </span>
            )}
          </span>
          <span className="block text-xs text-muted-foreground">
            {expert.rank} · {expert.office}
          </span>
        </span>
        <ChevronDown
          className={cn(
            "mt-1.5 size-3.5 shrink-0 text-muted-foreground transition-transform",
            open && "rotate-180",
          )}
        />
      </button>

      {open && (
        <div className="space-y-2.5 border-t border-border px-3 py-3">
          <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
            <ExpertClock expertId={expert.id} {...(fixedAt ? { fixedAt } : {})} />
            <ExpertTier expert={expert} />
            <span className="font-mono text-[11px] text-muted-foreground">
              {expert.accuracy}% accuracy · favorability {favorabilityOf(expert)}/100
            </span>
          </div>
          <p className="text-xs text-muted-foreground">{expert.specialty}</p>
          {chosen ? (
            <RoutingReasoning decision={decision} />
          ) : (
            <p className="text-xs leading-relaxed text-muted-foreground">
              Considered at the {decision.matchedTier} tier.{" "}
              {others.length > 0
                ? `Ranked against ${others.map((o) => `${o.name} (${o.rank})`).join(", ")}.`
                : ""}{" "}
              Not selected — the routed expert ranked higher or was the available match at the time
              of the escalation.
            </p>
          )}
        </div>
      )}
    </li>
  );
}

export function ExpertRoutingCard({
  decision,
  fixedAt,
  compact,
}: {
  decision: RoutingDecision;
  fixedAt?: string;
  compact?: boolean;
}) {
  const chosenExpert = getExpert(decision.expertId);
  if (!chosenExpert) return null;

  const candidates = [
    chosenExpert,
    ...decision.candidateIds
      .filter((cid) => cid !== chosenExpert.id)
      .map((cid) => getExpert(cid))
      .filter((e): e is Expert => !!e),
  ];

  return (
    <div className="rounded-sm border border-border bg-surface-2 p-3">
      <p className="label-xs mb-2 text-muted-foreground">
        Candidates considered ({candidates.length})
      </p>
      <ul className="space-y-1.5">
        {(compact ? candidates.slice(0, 1) : candidates).map((expert) => (
          <CandidateRow
            key={expert.id}
            expert={expert}
            decision={decision}
            chosen={expert.id === chosenExpert.id}
            {...(fixedAt ? { fixedAt } : {})}
          />
        ))}
      </ul>
    </div>
  );
}
