import { createFileRoute } from "@tanstack/react-router";
import { BookOpenCheck, Inbox, X } from "lucide-react";
import { useEffect, useState } from "react";
import { toast } from "sonner";

import { ExpertClock, ExpertTier, RoutingReasoning } from "@/components/experts/ExpertRoutingCard";
import { PageFrame, StatusPill } from "@/components/experts/PageFrame";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/lib/auth";
import { getExpert } from "@/lib/experts/roster";
import { useExperts } from "@/lib/experts/store";
import { cn } from "@/lib/utils";

const title = "Messages — Suitability Copilot";
const description =
  "Inbox of every suitability escalation sent to a subject matter expert, with routing reasoning and expert responses.";

export const Route = createFileRoute("/messages")({
  validateSearch: (search: Record<string, unknown>): { m?: string } => {
    const value = search["m"];
    return typeof value === "string" ? { m: value } : {};
  },
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
  component: MessagesPage,
});

function when(iso: string) {
  return new Date(iso).toLocaleString(undefined, {
    day: "2-digit",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function Bubble({
  who,
  at,
  side,
  children,
}: {
  who: string;
  at: string;
  side: "left" | "right";
  children: React.ReactNode;
}) {
  return (
    <div className={cn("flex", side === "right" ? "justify-end" : "justify-start")}>
      <div className="max-w-[85%]">
        <p
          className={cn(
            "mb-1 font-mono text-[10px] text-muted-foreground",
            side === "right" && "text-right",
          )}
        >
          {who} · {when(at)}
        </p>
        <div
          className={cn(
            "rounded-md border px-3 py-2.5 text-sm leading-relaxed",
            side === "right"
              ? "border-gold/40 bg-surface-2"
              : "border-border bg-card",
          )}
        >
          {children}
        </div>
      </div>
    </div>
  );
}

function MessagesPage() {
  const { m } = Route.useSearch();
  const { user } = useAuth();
  const { messages, favorabilityOf, publishAnswer } = useExperts();
  const [openId, setOpenId] = useState<string | null>(m ?? messages[0]?.id ?? null);
  const [profileOpen, setProfileOpen] = useState(false);
  const [kbPromptDismissed, setKbPromptDismissed] = useState<string[]>([]);

  useEffect(() => {
    if (m) setOpenId(m);
  }, [m]);

  const open = messages.find((msg) => msg.id === openId) ?? null;
  const expert = getExpert(open?.expertId);

  return (
    <PageFrame
      eyebrow="Escalations"
      title="Messages"
      intro="Every escalation you have sent to a subject matter expert, why that expert was chosen, and their answer once it arrives."
    >
      <div
        className={cn(
          "grid gap-4",
          profileOpen && open
            ? "lg:grid-cols-[minmax(0,260px)_minmax(0,1fr)_minmax(0,300px)]"
            : "lg:grid-cols-[minmax(0,320px)_minmax(0,1fr)]",
        )}
      >
        <ul className="space-y-1.5">
          {messages.length === 0 && (
            <li className="rounded-sm border border-border bg-card px-3 py-6 text-center text-xs text-muted-foreground">
              No escalations sent yet.
            </li>
          )}
          {messages.map((msg) => {
            const target = getExpert(msg.expertId);
            return (
              <li key={msg.id}>
                <button
                  type="button"
                  onClick={() => setOpenId(msg.id)}
                  className={cn(
                    "w-full rounded-sm border px-3 py-2.5 text-left transition-colors",
                    msg.id === openId
                      ? "border-gold/50 bg-surface-2"
                      : "border-border bg-card hover:border-gold/40",
                  )}
                >
                  <div className="flex items-start justify-between gap-2">
                    <span className="line-clamp-2 text-xs leading-snug">{msg.question}</span>
                    <StatusPill status={msg.status} />
                  </div>
                  <p className="mt-1.5 text-[11px] text-muted-foreground">
                    {target?.name} · {target?.office} · {when(msg.askedAt)}
                  </p>
                </button>
              </li>
            );
          })}
        </ul>

        {open && expert ? (
          <article className="space-y-4">
            <button
              type="button"
              onClick={() => setProfileOpen((v) => !v)}
              aria-expanded={profileOpen}
              className="flex w-full flex-wrap items-start justify-between gap-3 rounded-md border border-border bg-card p-4 text-left transition-colors hover:border-gold/50"
            >
              <span className="min-w-0">
                <span className="block text-sm font-medium">{expert.name}</span>
                <span className="block text-xs text-muted-foreground">
                  {expert.rank} · {expert.office}
                </span>
                <ExpertTier expert={expert} className="mt-0.5 block" />
              </span>
              <span className="shrink-0 text-right">
                <ExpertClock expertId={expert.id} />
                <span className="mt-0.5 block font-mono text-[11px] text-muted-foreground">
                  {expert.accuracy}% accuracy · favorability {favorabilityOf(expert)}/100
                </span>
                <span className="mt-1 block text-[10px] uppercase tracking-wide text-gold">
                  {profileOpen ? "Hide profile" : "View profile"}
                </span>
              </span>
            </button>

            <div className="space-y-3 rounded-md border border-border bg-surface p-4">
              <div className="flex flex-wrap gap-1.5 text-[11px] text-muted-foreground">
                {Object.entries(open.context).map(([k, v]) => (
                  <span key={k} className="rounded-sm border border-border px-1.5 py-px">
                    {String(v)}
                  </span>
                ))}
              </div>

              <Bubble who={open.askedBy} at={open.askedAt} side="right">
                {open.question}
              </Bubble>

              {open.answer ? (
                <>
                  <Bubble who={expert.name} at={open.answer.answeredAt} side="left">
                    {open.answer.text}
                  </Bubble>

                  {open.answer.publishedToKb ? (
                    <p className="flex items-center gap-2 rounded-sm border border-success/40 bg-success-surface px-3 py-2 text-xs">
                      <BookOpenCheck className="size-3.5" /> This answer is in the knowledge base.
                    </p>
                  ) : (
                    !kbPromptDismissed.includes(open.id) && (
                      <div className="rounded-sm border border-gold/50 bg-surface-2 px-3 py-3">
                        <p className="text-sm font-medium">
                          Add this answer to the knowledge base?
                        </p>
                        <div className="mt-2.5 flex gap-2">
                          <Button
                            size="sm"
                            onClick={() => {
                              publishAnswer(open.id);
                              toast.success("Published to knowledge base");
                            }}
                          >
                            Yes
                          </Button>
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() =>
                              setKbPromptDismissed((prev) => [...prev, open.id])
                            }
                          >
                            No
                          </Button>
                        </div>
                      </div>
                    )
                  )}
                </>
              ) : (
                <p className="flex items-center gap-2 rounded-sm border border-warning/40 bg-warning-surface px-3 py-2 text-xs">
                  <Inbox className="size-3.5 text-warning" /> Waiting for {expert.name}'s response.
                </p>
              )}
            </div>
          </article>
        ) : (
          <div className="rounded-md border border-border bg-card p-6 text-sm text-muted-foreground">
            Select an escalation to see its thread.
          </div>
        )}

        {profileOpen && open && expert && (
          <aside className="space-y-3 rounded-md border border-border bg-card p-4 lg:sticky lg:top-4 lg:self-start">
            <div className="flex items-start justify-between gap-2">
              <div>
                <p className="label-xs text-gold">Expert profile</p>
                <p className="mt-1 text-sm font-medium">{expert.name}</p>
                <p className="text-xs text-muted-foreground">{expert.title}</p>
              </div>
              <button
                type="button"
                onClick={() => setProfileOpen(false)}
                aria-label="Close expert profile"
                className="rounded-sm border border-border p-1 text-muted-foreground transition-colors hover:border-gold hover:text-gold"
              >
                <X className="size-3.5" />
              </button>
            </div>

            <dl className="space-y-1.5 text-xs">
              <div className="flex justify-between gap-2">
                <dt className="text-muted-foreground">Office</dt>
                <dd>
                  {expert.office} ({expert.regionTier})
                </dd>
              </div>
              <div className="flex justify-between gap-2">
                <dt className="text-muted-foreground">Escalation tier</dt>
                <dd className="text-right">{expert.rank}</dd>
              </div>
              <div className="flex justify-between gap-2">
                <dt className="text-muted-foreground">Local time</dt>
                <dd>
                  <ExpertClock expertId={expert.id} />
                </dd>
              </div>
              <div className="flex justify-between gap-2">
                <dt className="text-muted-foreground">Accuracy</dt>
                <dd className="font-mono">{expert.accuracy}%</dd>
              </div>
              <div className="flex justify-between gap-2">
                <dt className="text-muted-foreground">Favorability</dt>
                <dd className="font-mono">{favorabilityOf(expert)}/100</dd>
              </div>
              <div className="flex justify-between gap-2">
                <dt className="text-muted-foreground">Answered</dt>
                <dd className="font-mono">{expert.answered}</dd>
              </div>
            </dl>
            <ExpertTier expert={expert} className="block" />
            <p className="text-xs text-muted-foreground">{expert.specialty}</p>

            <div className="border-t border-border pt-3">
              <RoutingReasoning decision={open.routing} />
            </div>
            {user && (
              <p className="text-[10px] text-muted-foreground">
                Routing computed for {user.name} at {when(open.routing.decidedAt)}.
              </p>
            )}
          </aside>
        )}
      </div>
    </PageFrame>
  );
}
