import { createFileRoute } from "@tanstack/react-router";

import { PageFrame, StatusPill } from "@/components/experts/PageFrame";
import { useAuth } from "@/lib/auth";
import { getExpert } from "@/lib/experts/roster";
import { useExperts } from "@/lib/experts/store";

const title = "Expert Audit Trail — Suitability Copilot";
const description =
  "Every question you answered as a suitability expert, whether it was published to the knowledge base, and its current status.";

export const Route = createFileRoute("/expert/audit")({
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
  component: ExpertAuditPage,
});

function ExpertAuditPage() {
  const { user } = useAuth();
  const { messages } = useExperts();
  const expert = getExpert(user?.expertId);
  const mine = messages.filter((m) => (expert ? m.expertId === expert.id : true));

  return (
    <PageFrame
      eyebrow="Expert portal"
      title="Audit trail"
      intro="Your own answering record, scoped to escalations routed to you."
    >
      <div className="overflow-x-auto rounded-md border border-border bg-card">
        <table className="w-full text-left text-xs">
          <thead className="border-b border-border bg-surface-2">
            <tr className="label-xs text-muted-foreground">
              <th className="px-3 py-2 font-medium">Asked</th>
              <th className="px-3 py-2 font-medium">Question</th>
              <th className="px-3 py-2 font-medium">RM</th>
              <th className="px-3 py-2 font-medium">Answered</th>
              <th className="px-3 py-2 font-medium">In KB</th>
              <th className="px-3 py-2 font-medium">Status</th>
            </tr>
          </thead>
          <tbody>
            {mine.length === 0 && (
              <tr>
                <td colSpan={6} className="px-3 py-8 text-center text-muted-foreground">
                  No escalations on your record yet.
                </td>
              </tr>
            )}
            {mine.map((m) => (
              <tr key={m.id} className="border-b border-border last:border-0 align-top">
                <td className="whitespace-nowrap px-3 py-2.5 font-mono text-[11px] text-muted-foreground">
                  {new Date(m.askedAt).toLocaleDateString()}
                </td>
                <td className="max-w-md px-3 py-2.5 leading-snug">{m.question}</td>
                <td className="whitespace-nowrap px-3 py-2.5 text-muted-foreground">{m.askedBy}</td>
                <td className="whitespace-nowrap px-3 py-2.5 font-mono text-[11px] text-muted-foreground">
                  {m.answer ? new Date(m.answer.answeredAt).toLocaleDateString() : "—"}
                </td>
                <td className="whitespace-nowrap px-3 py-2.5 text-muted-foreground">
                  {m.answer?.publishedToKb
                    ? "Published"
                    : m.answer?.contradictsWiki
                      ? "Contradiction flagged"
                      : "No"}
                </td>
                <td className="px-3 py-2.5">
                  <StatusPill status={m.status} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </PageFrame>
  );
}
