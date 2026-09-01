import { createFileRoute } from "@tanstack/react-router";

import { ExpertClock, ExpertRoutingCard } from "@/components/experts/ExpertRoutingCard";
import { PageFrame } from "@/components/experts/PageFrame";
import { EXPERTS } from "@/lib/experts/roster";
import { ROUTING_SCENARIOS, scenarioDecision } from "@/lib/experts/routing";
import { useExperts } from "@/lib/experts/store";

const title = "Expert Routing — Suitability Copilot";
const description =
  "How escalations are routed: geographic tiers, rank hierarchy and timezone availability across the global suitability expert roster.";

export const Route = createFileRoute("/routing")({
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
  component: RoutingPage,
});

function RoutingPage() {
  const { favorabilityOf } = useExperts();

  return (
    <PageFrame
      eyebrow="Routing engine"
      title="Expert routing"
      intro="Escalations search outward from the client's booking centre — branch, country, region, then global — and pick the highest-ranked expert who is inside working hours locally."
    >
      <div className="space-y-4">
        {ROUTING_SCENARIOS.map((scenario) => (
          <section key={scenario.id} className="rounded-md border border-border bg-card p-4">
            <p className="label-xs text-gold">{scenario.atLabel}</p>
            <h2 className="mt-1 text-[15px] font-medium">{scenario.title}</h2>
            <p className="mt-1 text-xs leading-relaxed text-muted-foreground">{scenario.blurb}</p>
            <p className="mt-2.5 rounded-sm border border-border bg-surface-2 px-3 py-2 text-sm leading-snug">
              {scenario.question}
            </p>
            <div className="mt-3">
              <ExpertRoutingCard decision={scenarioDecision(scenario)} fixedAt={scenario.at} />
            </div>
          </section>
        ))}

        <section className="rounded-md border border-border bg-card p-4">
          <h2 className="text-[15px] font-medium text-gold">Global SME roster</h2>
          <p className="mt-1 text-xs text-muted-foreground">
            Live local times, rank and track record for every expert available to the routing engine.
          </p>
          <ul className="mt-3 divide-y divide-border">
            {EXPERTS.map((e) => (
              <li key={e.id} className="flex flex-wrap items-center gap-3 py-2.5">
                <span className="flex size-8 shrink-0 items-center justify-center rounded-full bg-cream text-[11px] font-medium text-cream-foreground">
                  {e.initials}
                </span>
                <span className="min-w-0 flex-1">
                  <span className="block text-sm">{e.name}</span>
                  <span className="block text-[11px] text-muted-foreground">
                    {e.title} · {e.specialty}
                  </span>
                </span>
                <ExpertClock expertId={e.id} />
                <span className="font-mono text-[11px] text-muted-foreground">
                  {e.accuracy}% · {e.answered} answers · fav {favorabilityOf(e)}
                </span>
              </li>
            ))}
          </ul>
        </section>
      </div>
    </PageFrame>
  );
}
