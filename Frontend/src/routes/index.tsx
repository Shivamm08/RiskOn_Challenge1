import { createFileRoute, useRouterState } from "@tanstack/react-router";
import { Loader2 } from "lucide-react";
import { useEffect, useRef } from "react";

import { AppShell } from "@/components/suitability/AppShell";
import { ChatInput } from "@/components/suitability/ChatInput";
import { ContextBar } from "@/components/suitability/ContextBar";
import { MessageBubble } from "@/components/suitability/MessageBubble";
import { ResponseCardAnswered } from "@/components/suitability/ResponseCardAnswered";
import { ResponseCardClarification } from "@/components/suitability/ResponseCardClarification";
import { ResponseCardEscalated } from "@/components/suitability/ResponseCardEscalated";
import { CitationPanel } from "@/components/suitability/SourceCitation";
import { useSuitability } from "@/lib/suitability/store";
import { CURRENT_RM } from "@/lib/suitability/seed";
import type { Exchange } from "@/lib/suitability/types";

const title = "Suitability Copilot — Julius Baer Internal";
const description =
  "Source-cited answers to client suitability and compliance questions for Relationship Managers, with transparent escalation to the right human expert.";

export const Route = createFileRoute("/")({
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
  component: CopilotPage,
});

function ResponseCard({ exchange }: { exchange: Exchange }) {
  switch (exchange.response.status) {
    case "answered":
      return <ResponseCardAnswered exchange={exchange} />;
    case "escalated":
      return <ResponseCardEscalated exchange={exchange} />;
    case "clarification_needed":
      return <ResponseCardClarification exchange={exchange} />;
  }
}

function CopilotPage() {
  const { thread, pendingQuestion, activeCitation, context } = useSuitability();
  const hash = useRouterState({ select: (s) => s.location.hash });
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (hash) {
      document.getElementById(hash)?.scrollIntoView({ block: "center" });
      return;
    }
    bottomRef.current?.scrollIntoView({ block: "end" });
  }, [hash, thread.length, pendingQuestion]);

  return (
    <AppShell>
      <div className="flex min-h-0 flex-1">
        <div className="flex min-w-0 flex-1 flex-col">
          <div className="min-h-0 flex-1 overflow-y-auto">
            <div className="mx-auto max-w-3xl space-y-6 px-5 py-6">
              <header className="border-b border-border pb-4">
                <p className="label-xs text-gold">Suitability &amp; compliance</p>
                <h1 className="mt-1 text-xl font-medium text-gold">
                  Answers with sources, or the right expert.
                </h1>
                <p className="mt-1.5 text-sm text-muted-foreground">
                  Every answer is traceable to an exact wiki excerpt. Where the wiki does not cover
                  the question, the Copilot routes to a named expert instead of guessing.
                </p>
              </header>

              {thread.map((exchange) => (
                <div key={exchange.id} id={exchange.id} className="space-y-3 scroll-mt-6">
                  <MessageBubble
                    question={exchange.question}
                    context={exchange.context}
                    askedAt={exchange.askedAt}
                  />
                  <ResponseCard exchange={exchange} />
                </div>
              ))}

              {pendingQuestion && (
                <div className="space-y-3">
                  <MessageBubble
                    question={pendingQuestion}
                    context={context}
                    askedAt={new Date().toISOString()}
                  />
                  <div className="flex items-center gap-2 rounded-md border border-border bg-card px-4 py-3 text-xs text-muted-foreground">
                    <Loader2 className="size-3.5 animate-spin text-gold" />
                    Checking connected knowledge sources…
                  </div>
                </div>
              )}

              <div ref={bottomRef} />
            </div>
          </div>

          <div className="border-t border-border bg-surface/60 px-5 py-4">
            <div className="mx-auto max-w-3xl space-y-3">
              <ContextBar />
              <ChatInput />
              <p className="text-[11px] text-muted-foreground">
                Signed in as {CURRENT_RM}. All questions and answers are recorded in the audit
                trail.
              </p>
            </div>
          </div>
        </div>

        {activeCitation && (
          <div className="hidden lg:block">
            <CitationPanel />
          </div>
        )}
      </div>
    </AppShell>
  );
}
