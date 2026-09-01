import { createFileRoute } from "@tanstack/react-router";
import { AlertTriangle, ShieldCheck } from "lucide-react";
import { toast } from "sonner";

import { PageFrame, StatusPill } from "@/components/experts/PageFrame";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/lib/auth";
import { getExpert } from "@/lib/experts/roster";
import { useExperts } from "@/lib/experts/store";

const title = "Supervisor Reviews — Suitability Copilot";
const description =
  "Contradiction flags and peer-flagged knowledge-base contributions awaiting a supervisor decision.";

export const Route = createFileRoute("/expert/reviews")({
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
  component: ReviewsPage,
});

function ReviewsPage() {
  const { user } = useAuth();
  const { reviews, decideReview } = useExperts();
  const me = getExpert(user?.expertId);
  const mine = reviews.filter((r) => (me ? r.supervisorId === me.id : true));

  return (
    <PageFrame
      eyebrow="Expert portal"
      title="Supervisor reviews"
      intro="Items escalated to you as the next rank up: answers that contradict existing wiki guidance, and published contributions a peer has flagged."
    >
      <ul className="space-y-3">
        {mine.length === 0 && (
          <li className="rounded-md border border-border bg-card px-4 py-8 text-center text-sm text-muted-foreground">
            No items awaiting your decision.
          </li>
        )}
        {mine.map((r) => {
          const expert = getExpert(r.expertId);
          return (
            <li
              key={r.id}
              className="overflow-hidden rounded-md border border-border border-l-2 border-l-danger bg-card"
            >
              <header className="flex flex-wrap items-center justify-between gap-2 border-b border-border bg-danger-surface px-4 py-2.5">
                <span className="label-xs flex items-center gap-1.5 text-danger-foreground">
                  <AlertTriangle className="size-3.5 text-danger" />
                  {r.kind === "contradiction"
                    ? "Contradiction flagged"
                    : "KB contribution flagged by a peer"}
                </span>
                <StatusPill status={r.status} />
              </header>

              <div className="space-y-3 px-4 py-4">
                <p className="text-sm font-medium leading-snug">{r.question}</p>
                <p className="text-[11px] text-muted-foreground">
                  Submitted by {expert?.name} · {expert?.rank}, {expert?.office}
                </p>

                <div className="grid gap-3 md:grid-cols-2">
                  <div className="rounded-sm border border-border bg-surface-2 p-3">
                    <p className="label-xs mb-1.5 text-muted-foreground">Existing wiki guidance</p>
                    <p className="text-xs leading-relaxed">{r.wikiExcerpt}</p>
                  </div>
                  <div className="rounded-sm border border-gold/40 bg-surface-2 p-3">
                    <p className="label-xs mb-1.5 text-gold">Expert's new answer</p>
                    <p className="text-xs leading-relaxed">{r.answer}</p>
                  </div>
                </div>

                {r.status === "open" ? (
                  <div className="flex flex-wrap gap-2 border-t border-border pt-3">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => {
                        decideReview(r.id, "kept");
                        toast.success("Existing wiki guidance kept");
                      }}
                    >
                      Keep existing wiki guidance
                    </Button>
                    <Button
                      size="sm"
                      onClick={() => {
                        decideReview(r.id, "updated");
                        toast.success("Wiki guidance updated with the expert's answer");
                      }}
                    >
                      Update wiki guidance with expert's answer
                    </Button>
                  </div>
                ) : (
                  <p className="flex items-center gap-1.5 border-t border-border pt-3 text-xs text-muted-foreground">
                    <ShieldCheck className="size-3.5 text-success" />
                    {r.status === "kept"
                      ? "Decision: existing wiki guidance kept."
                      : "Decision: wiki guidance updated with the expert's answer."}
                  </p>
                )}
              </div>
            </li>
          );
        })}
      </ul>
    </PageFrame>
  );
}
