import { createFileRoute } from "@tanstack/react-router";
import { Minus, Plus } from "lucide-react";

import { PageFrame } from "@/components/experts/PageFrame";
import { useAuth } from "@/lib/auth";
import { getExpert, rankTierLabel, supervisorOf } from "@/lib/experts/roster";
import { useExperts } from "@/lib/experts/store";

const title = "Favorability & Ranking — Suitability Copilot";
const description =
  "Your favorability score, how endorsements and flags move it, and how it feeds expert routing and performance reviews.";

export const Route = createFileRoute("/expert/favorability")({
  head: () => ({
    meta: [
      { title },
      { name: "description", content: description },
      { property: "og:title", content: title },
      { property: "og:description", content: description },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
      { name: "robots", content: "noindex" },
    ],
  }),
  component: FavorabilityPage,
});

function FavorabilityPage() {
  const { user } = useAuth();
  const { kbEntries, favorabilityOf, favorabilityDelta, reviews } = useExperts();
  const expert = getExpert(user?.expertId);

  if (!expert) {
    return (
      <PageFrame eyebrow="Expert portal" title="Favorability & ranking">
        <p className="text-sm text-muted-foreground">
          This view is scoped to a roster expert. Sign in with one of the roster quick-selects to see
          a live score.
        </p>
      </PageFrame>
    );
  }

  const mine = kbEntries.filter((e) => e.expertId === expert.id);
  const endorsements = mine.reduce((n, e) => n + e.endorsedBy.length, 0);
  const flags = mine.reduce((n, e) => n + e.flaggedBy.length, 0);
  const contradictionFlags = reviews.filter((r) => r.expertId === expert.id).length;
  const delta = favorabilityDelta[expert.id] ?? 0;
  const score = favorabilityOf(expert);
  const base = expert.favorability;
  const supervisor = supervisorOf(expert);

  return (
    <PageFrame
      eyebrow="Expert portal"
      title="Favorability & ranking"
      intro="Favorability weights how often the routing engine selects you, alongside rank, geography and availability."
    >
      <div className="space-y-4">
        <section className="rounded-md border border-border bg-card p-5">
          <div className="flex flex-wrap items-end gap-6">
            <div>
              <p className="label-xs text-muted-foreground">Current favorability</p>
              <p className="font-mono text-5xl font-medium text-gold">{score}</p>
              <p className="mt-1 text-[11px] text-muted-foreground">out of 100</p>
            </div>
            <div className="min-w-0 flex-1">
              <div className="h-2 w-full overflow-hidden rounded-full bg-surface-2">
                <div className="h-full bg-gold" style={{ width: `${score}%` }} />
              </div>
              <p className="mt-2 text-xs text-muted-foreground">
                {expert.rank} · {expert.office} · {expert.answered} questions answered ·{" "}
                {expert.accuracy}% accuracy
              </p>
            </div>
          </div>

          <ul className="mt-5 divide-y divide-border border-t border-border">
            <li className="flex items-center justify-between py-2 text-sm">
              <span>
                Base score from rank{" "}
                <span className="text-muted-foreground">
                  ({rankTierLabel(expert.rank)})
                </span>
              </span>
              <span className="font-mono">{base}</span>
            </li>
            <li className="flex items-center justify-between py-2 text-sm">
              <span className="flex items-center gap-1.5">
                <Plus className="size-3.5 text-success" /> Peer endorsements on your KB
                contributions ({endorsements} × 2)
              </span>
              <span className="font-mono text-success-foreground">+{endorsements * 2}</span>
            </li>
            <li className="flex items-center justify-between py-2 text-sm">
              <span className="flex items-center gap-1.5">
                <Minus className="size-3.5 text-danger" /> Flags raised on your contributions (
                {flags} × 3)
              </span>
              <span className="font-mono text-danger-foreground">−{flags * 3}</span>
            </li>
            <li className="flex items-center justify-between py-2 text-sm">
              <span>Net adjustment this session</span>
              <span className="font-mono">
                {delta >= 0 ? "+" : ""}
                {delta}
              </span>
            </li>
            {contradictionFlags > 0 && (
              <li className="flex items-center justify-between py-2 text-sm">
                <span>Contradiction flags awaiting supervisor decision</span>
                <span className="font-mono text-warning">{contradictionFlags}</span>
              </li>
            )}
          </ul>

          <p className="mt-4 border-t border-border pt-3 text-xs leading-relaxed text-muted-foreground">
            Higher favorability increases how often you're routed to, and is visible to your
            supervisor{supervisor ? ` (${supervisor.name}, ${supervisor.rank})` : ""} and used in
            performance conversations.
          </p>
        </section>

        <section className="rounded-md border border-border bg-card p-4">
          <h2 className="text-[15px] font-medium text-gold">Your KB contributions</h2>
          {mine.length === 0 ? (
            <p className="mt-2 text-xs text-muted-foreground">
              Nothing published yet. Publish an answer from your inbox to start building a record.
            </p>
          ) : (
            <ul className="mt-3 divide-y divide-border">
              {mine.map((e) => (
                <li key={e.id} className="py-2.5">
                  <p className="text-sm leading-snug">{e.question}</p>
                  <p className="mt-1 text-[11px] text-muted-foreground">
                    Endorsed by {e.endorsedBy.length} expert{e.endorsedBy.length === 1 ? "" : "s"}
                    {e.flaggedBy.length > 0 ? ` · ${e.flaggedBy.length} flag(s) under review` : ""}
                  </p>
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>
    </PageFrame>
  );
}
