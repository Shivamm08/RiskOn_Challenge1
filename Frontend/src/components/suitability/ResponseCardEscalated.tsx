import { AlertTriangle, BellRing, CheckCircle2, LifeBuoy, User } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { EscalationLadder } from "./EscalationLadder";
import { ReasoningTrail } from "./ReasoningTrail";
import { SourceChip } from "./SourceCitation";
import { useSuitability } from "@/lib/suitability/store";
import type { Exchange } from "@/lib/suitability/types";

import { useAuth } from "@/lib/auth";

function expertEmail(name: string) {
  const parts = name.replace(/\./g, "").trim().split(/\s+/);
  const last = parts[parts.length - 1] ?? "expert";
  const first = parts.length > 1 ? parts[0] : "";
  return `${[first, last].filter(Boolean).join(".").toLowerCase()}@juliusbaer.com`;
}

function firstName(name: string) {
  const parts = name.trim().split(/\s+/);
  const first = parts[0] ?? name;
  const last = parts[parts.length - 1] ?? name;
  return first.replace(".", "").length > 1 ? first : last;
}


export function ResponseCardEscalated({ exchange }: { exchange: Exchange }) {
  const { response, resolution } = exchange;
  const escalation = response.escalation;
  const { resolveExchange } = useSuitability();
  const { user } = useAuth();
  const [resolving, setResolving] = useState(false);
  const [note, setNote] = useState("");

  if (!escalation) return null;

  const shortQuestion =
    exchange.question.length > 60
      ? `${exchange.question.slice(0, 57).trimEnd()}…`
      : exchange.question;

  const experts = escalation.experts?.length ? escalation.experts : [escalation.expert];
  const primaryExpert = experts[0] ?? escalation.expert;
  const alternativeExperts = experts.slice(1, 4);

  const mailto = `mailto:${expertEmail(primaryExpert.name)}?subject=${encodeURIComponent(
    `Suitability question — ${shortQuestion}`,
  )}&body=${encodeURIComponent(
    [
      `Dear ${firstName(primaryExpert.name)},`,
      "",
      `The Suitability Copilot could not confidently answer a client-related question and is routing it to you as ${primaryExpert.role}. ${escalation.reason}`,
      "",
      exchange.question,
      "",
      "Kind regards,",
      user?.name ?? "",
    ].join("\n"),
  )}`;


  return (
    <article className="overflow-hidden rounded-md border border-border border-l-2 border-l-danger bg-card">
      <header className="flex flex-wrap items-center justify-between gap-3 border-b border-border bg-danger-surface px-4 py-2.5">
        <div className="flex items-center gap-2">
          <AlertTriangle className="size-4 text-danger" />
          <span className="label-xs text-danger-foreground">Escalated</span>
        </div>
        <span className="font-mono text-[11px] text-muted-foreground">
          answer {Math.round(response.confidence.answer_confidence * 100)}% · routing{" "}
          {Math.round(response.confidence.routing_confidence * 100)}%
        </span>
      </header>

      <div className="space-y-4 px-4 py-4">
        <h3 className="text-[15px] font-medium leading-snug">
          I can't confidently answer this — here's who can help.
        </h3>

        <div className="rounded-sm border border-border bg-surface-2 p-3.5">
          <div className="flex items-start gap-3">
            <span className="mt-0.5 flex size-8 shrink-0 items-center justify-center rounded-full bg-cream text-cream-foreground">
              <User className="size-4" />
            </span>
            <div className="min-w-0">
              <p className="text-sm font-medium">{primaryExpert.name}</p>
              <p className="text-xs text-muted-foreground">{primaryExpert.role}</p>
              <p className="text-xs text-muted-foreground">{primaryExpert.team}</p>
            </div>
          </div>
          <p className="mt-3 border-t border-border pt-3 text-xs leading-relaxed text-muted-foreground">
            {escalation.reason}
          </p>
        </div>

        {alternativeExperts.length > 0 && (
          <div className="rounded-sm border border-border bg-surface-2 p-3.5">
            <p className="label-xs mb-2 text-muted-foreground">Other suitable contacts</p>
            <div className="space-y-2">
              {alternativeExperts.map((expert) => (
                <div key={expert.name} className="flex items-center justify-between gap-3 rounded-sm border border-border bg-card px-2.5 py-2 text-xs">
                  <div>
                    <p className="font-medium">{expert.name}</p>
                    <p className="text-muted-foreground">{expert.role}</p>
                  </div>
                  <span className="text-muted-foreground">{expert.team}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        <div>
          <p className="label-xs mb-2 text-muted-foreground">Escalation tier</p>
          <EscalationLadder active={escalation.tier} />
        </div>

        <p className="flex items-start gap-2 rounded-sm border border-warning/40 bg-warning-surface px-3 py-2 text-xs leading-relaxed">
          <LifeBuoy className="mt-0.5 size-3.5 shrink-0 text-warning" />
          <span>
            If {primaryExpert.name} is unavailable, contact{" "}
            <span className="font-medium">{escalation.fallback_contact.name}</span> —{" "}
            {escalation.fallback_contact.role}.
          </span>
        </p>

        {response.sources.length > 0 && (
          <div>
            <p className="label-xs mb-2 text-muted-foreground">Checked sources</p>
            <div className="grid gap-1.5 sm:grid-cols-2">
              {response.sources.map((source, i) => (
                <SourceChip
                  key={source.page_title}
                  source={source}
                  exchangeId={exchange.id}
                  index={i}
                />
              ))}
            </div>
          </div>
        )}

        <ReasoningTrail
          steps={response.reasoning ?? []}
          scopeFlags={response.scope_flags}
          label="Why this was escalated"
        />

        {resolution ? (
          <div className="rounded-sm border border-success/40 bg-success-surface px-3 py-2.5">
            <p className="label-xs flex items-center gap-1.5 text-success-foreground">
              <CheckCircle2 className="size-3.5" /> Resolved by {resolution.resolvedBy}
            </p>
            <p className="mt-1.5 text-xs leading-relaxed">{resolution.note}</p>
          </div>
        ) : resolving ? (
          <div className="space-y-2 border-t border-border pt-3">
            <label className="label-xs text-muted-foreground" htmlFor={`res-${exchange.id}`}>
              Resolution received from {escalation.expert.name}
            </label>
            <Textarea
              id={`res-${exchange.id}`}
              value={note}
              onChange={(e) => setNote(e.target.value)}
              rows={3}
              placeholder="Record the expert's answer verbatim for the audit trail."
              className="text-sm"
            />
            <div className="flex gap-2">
              <Button
                size="sm"
                disabled={!note.trim()}
                onClick={() => {
                  resolveExchange(exchange.id, note.trim(), escalation.expert.name);
                  setResolving(false);
                  toast.success("Resolution recorded in the audit trail");
                }}
              >
                Save resolution
              </Button>
              <Button size="sm" variant="ghost" onClick={() => setResolving(false)}>
                Cancel
              </Button>
            </div>
          </div>
        ) : (
          <div className="flex flex-wrap gap-2 border-t border-border pt-3">
            <Button size="sm" asChild>
              <a href={mailto}>
                <BellRing className="size-3.5" /> Notify recommended expert
              </a>
            </Button>

            <Button size="sm" variant="outline" onClick={() => setResolving(true)}>
              <CheckCircle2 className="size-3.5" /> Mark as resolved
            </Button>
          </div>
        )}
      </div>
    </article>
  );
}
