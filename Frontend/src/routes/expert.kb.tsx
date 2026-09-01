import { createFileRoute } from "@tanstack/react-router";
import { BookOpenCheck, ThumbsDown, ThumbsUp } from "lucide-react";
import { toast } from "sonner";

import { PageFrame } from "@/components/experts/PageFrame";
import { useAuth } from "@/lib/auth";
import { getExpert } from "@/lib/experts/roster";
import { useExperts } from "@/lib/experts/store";
import { cn } from "@/lib/utils";

const title = "Recently Added to KB — Suitability Copilot";
const description =
  "Expert answers newly published to the suitability knowledge base, with peer endorsements and review flags.";

export const Route = createFileRoute("/expert/kb")({
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
  component: KbPage,
});

function KbPage() {
  const { user } = useAuth();
  const { kbEntries, reactToKb } = useExperts();
  const me = user?.expertId ?? "guest-expert";

  return (
    <PageFrame
      eyebrow="Knowledge base"
      title="Recently added to KB"
      intro="Peer review for newly published guidance. Endorsing raises the contributor's favorability; flagging sends the entry to their supervisor rather than changing the KB."
    >
      <ul className="space-y-3">
        {kbEntries.map((entry) => {
          const author = getExpert(entry.expertId);
          const endorsed = entry.endorsedBy.includes(me);
          const flagged = entry.flaggedBy.includes(me);
          return (
            <li key={entry.id} className="rounded-md border border-border bg-card p-4">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <p className="label-xs flex items-center gap-1.5 text-gold">
                  <BookOpenCheck className="size-3.5" /> {author?.name ?? "Expert"} ·{" "}
                  {author?.office}
                </p>
                {entry.endorsedBy.length > 0 && (
                  <span className="rounded-sm border border-success/40 bg-success-surface px-1.5 py-px text-[10px] uppercase tracking-wide text-success-foreground">
                    Endorsed by {entry.endorsedBy.length} expert
                    {entry.endorsedBy.length === 1 ? "" : "s"}
                  </span>
                )}
                {entry.flaggedBy.length > 0 && (
                  <span className="rounded-sm border border-danger/40 bg-danger-surface px-1.5 py-px text-[10px] uppercase tracking-wide text-danger-foreground">
                    Flagged — supervisor review
                  </span>
                )}
              </div>

              <h2 className="mt-2 text-[15px] font-medium leading-snug">{entry.question}</h2>
              <p className="mt-1.5 text-sm leading-relaxed text-muted-foreground">{entry.answer}</p>
              <p className="mt-2 font-mono text-[11px] text-muted-foreground">
                {entry.sourceTitle} · {new Date(entry.publishedAt).toLocaleString()}
              </p>

              <div className="mt-3 flex gap-2 border-t border-border pt-3">
                <button
                  type="button"
                  disabled={endorsed || entry.expertId === me}
                  onClick={() => {
                    reactToKb(entry.id, me, "up");
                    toast.success("Endorsement recorded");
                  }}
                  className={cn(
                    "flex items-center gap-1.5 rounded-sm border px-2 py-1 text-xs transition-colors disabled:opacity-50",
                    endorsed
                      ? "border-success/50 bg-success-surface text-success-foreground"
                      : "border-border hover:border-gold",
                  )}
                >
                  <ThumbsUp className="size-3.5" /> {endorsed ? "Endorsed" : "Endorse"}
                </button>
                <button
                  type="button"
                  disabled={flagged || entry.expertId === me}
                  onClick={() => {
                    reactToKb(entry.id, me, "down");
                    toast.error("Flagged — routed to the contributor's supervisor");
                  }}
                  className={cn(
                    "flex items-center gap-1.5 rounded-sm border px-2 py-1 text-xs transition-colors disabled:opacity-50",
                    flagged
                      ? "border-danger/50 bg-danger-surface text-danger-foreground"
                      : "border-border hover:border-gold",
                  )}
                >
                  <ThumbsDown className="size-3.5" /> {flagged ? "Flagged" : "Flag for review"}
                </button>
              </div>
            </li>
          );
        })}
      </ul>
    </PageFrame>
  );
}
