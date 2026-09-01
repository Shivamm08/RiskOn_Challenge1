import { createFileRoute } from "@tanstack/react-router";
import { AlertTriangle, BookOpenCheck, Send } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

import { ExpertRoutingCard } from "@/components/experts/ExpertRoutingCard";
import { PageFrame, StatusPill } from "@/components/experts/PageFrame";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Textarea } from "@/components/ui/textarea";
import { useAuth } from "@/lib/auth";
import { getExpert, supervisorOf } from "@/lib/experts/roster";
import { useExperts } from "@/lib/experts/store";
import { cn } from "@/lib/utils";

const title = "Expert Inbox — Suitability Copilot";
const description =
  "Escalated suitability questions routed to you, with the routing reasoning, answer drafting and knowledge-base publishing.";

export const Route = createFileRoute("/expert/")({
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
  component: ExpertInboxPage,
});

function ExpertInboxPage() {
  const { user } = useAuth();
  const { messages, answerEscalation, publishAnswer } = useExperts();
  const expert = getExpert(user?.expertId);
  const supervisor = expert ? supervisorOf(expert) : undefined;

  const inbox = messages.filter((m) => (expert ? m.expertId === expert.id : true));
  const [openId, setOpenId] = useState<string | null>(inbox[0]?.id ?? null);
  const [draft, setDraft] = useState("");
  const [contradicts, setContradicts] = useState(false);
  const [askPublish, setAskPublish] = useState<string | null>(null);

  const open = inbox.find((m) => m.id === openId) ?? null;

  return (
    <PageFrame
      eyebrow="Expert portal"
      title="Inbox"
      intro="Questions the routing engine sent to you. Answer them, then decide whether the answer belongs in the knowledge base."
    >
      <div className="grid gap-4 lg:grid-cols-[minmax(0,320px)_minmax(0,1fr)]">
        <ul className="space-y-1.5">
          {inbox.length === 0 && (
            <li className="rounded-sm border border-border bg-card px-3 py-6 text-center text-xs text-muted-foreground">
              Nothing routed to you right now.
            </li>
          )}
          {inbox.map((m) => (
            <li key={m.id}>
              <button
                type="button"
                onClick={() => {
                  setOpenId(m.id);
                  setDraft("");
                  setContradicts(false);
                  setAskPublish(null);
                }}
                className={cn(
                  "w-full rounded-sm border px-3 py-2.5 text-left transition-colors",
                  m.id === openId
                    ? "border-gold/50 bg-surface-2"
                    : "border-border bg-card hover:border-gold/40",
                )}
              >
                <div className="flex items-start justify-between gap-2">
                  <span className="line-clamp-2 text-xs leading-snug">{m.question}</span>
                  <StatusPill status={m.status} />
                </div>
                <p className="mt-1.5 text-[11px] text-muted-foreground">from {m.askedBy}</p>
              </button>
            </li>
          ))}
        </ul>

        {open ? (
          <article className="space-y-4 rounded-md border border-border bg-card p-4">
            <header className="flex items-start justify-between gap-3">
              <h2 className="text-[15px] font-medium leading-snug">{open.question}</h2>
              <StatusPill status={open.status} />
            </header>

            <div>
              <p className="label-xs mb-1.5 text-muted-foreground">Client context</p>
              <div className="flex flex-wrap gap-1.5 text-[11px]">
                {(["bookingCentre", "clientCategory", "serviceModel"] as const).map((k) => (
                  <span key={k} className="rounded-sm border border-border px-1.5 py-0.5">
                    {k === "bookingCentre"
                      ? "Booking centre"
                      : k === "clientCategory"
                        ? "Client category"
                        : "Service model"}
                    : {open.context[k] ?? "not provided"}
                  </span>
                ))}
              </div>
            </div>

            <ExpertRoutingCard decision={open.routing} fixedAt={open.routing.decidedAt} />

            {open.answer ? (
              <div className="space-y-3">
                <div
                  className={cn(
                    "rounded-sm border px-3 py-3",
                    open.answer.contradictsWiki
                      ? "border-danger/40 bg-danger-surface"
                      : "border-success/40 bg-success-surface",
                  )}
                >
                  <p className="label-xs flex items-center gap-1.5">
                    {open.answer.contradictsWiki ? (
                      <>
                        <AlertTriangle className="size-3.5 text-danger" /> Contradiction flagged —
                        sent to {supervisor?.name ?? "your supervisor"} for a decision
                      </>
                    ) : (
                      <>
                        <BookOpenCheck className="size-3.5" /> Answer sent
                        {open.answer.publishedToKb ? " · published to knowledge base" : ""}
                      </>
                    )}
                  </p>
                  <p className="mt-1.5 text-sm leading-relaxed">{open.answer.text}</p>
                </div>

                {askPublish === open.id && !open.answer.publishedToKb && !open.answer.contradictsWiki && (
                  <div className="rounded-sm border border-gold/50 bg-surface-2 px-3 py-3">
                    <p className="text-sm font-medium">Add this answer to the knowledge base?</p>
                    <div className="mt-2.5 flex gap-2">
                      <Button
                        size="sm"
                        onClick={() => {
                          publishAnswer(open.id);
                          setAskPublish(null);
                          toast.success("Published to knowledge base");
                        }}
                      >
                        Yes, publish
                      </Button>
                      <Button size="sm" variant="ghost" onClick={() => setAskPublish(null)}>
                        No
                      </Button>
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="space-y-2.5 border-t border-border pt-3">
                <label className="label-xs text-muted-foreground" htmlFor="answer">
                  Your answer
                </label>
                <Textarea
                  id="answer"
                  rows={5}
                  value={draft}
                  onChange={(e) => setDraft(e.target.value)}
                  placeholder="Answer the RM's question, citing the applicable policy where possible."
                  className="text-sm"
                />
                <label className="flex items-start gap-2 text-xs text-muted-foreground">
                  <Checkbox
                    checked={contradicts}
                    onCheckedChange={(v) => setContradicts(v === true)}
                    className="mt-px"
                  />
                  This contradicts existing wiki guidance
                </label>
                <Button
                  size="sm"
                  disabled={!draft.trim()}
                  onClick={() => {
                    answerEscalation(open.id, draft.trim(), { contradictsWiki: contradicts });
                    if (contradicts) {
                      toast.error(
                        `Contradiction flagged — routed to ${supervisor?.name ?? "your supervisor"}`,
                      );
                    } else {
                      setAskPublish(open.id);
                      toast.success("Answer sent to the Relationship Manager");
                    }
                    setDraft("");
                    setContradicts(false);
                  }}
                >
                  <Send className="size-3.5" /> Send answer
                </Button>
              </div>
            )}
          </article>
        ) : (
          <div className="rounded-md border border-border bg-card p-6 text-sm text-muted-foreground">
            Select a question to answer it.
          </div>
        )}
      </div>
    </PageFrame>
  );
}
