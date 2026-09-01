import { Check, LogOut, MessageSquare, RefreshCw, ShieldCheck, X } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { useAuth } from "@/lib/auth";
import type { EscalationCase } from "@/lib/suitability/types";

function apiBase(): string {
  return ((import.meta.env["VITE_API_URL"] as string | undefined) ?? "").replace(/\/$/, "");
}

export function ExpertWorkspace() {
  const { user, signOut } = useAuth();
  const [cases, setCases] = useState<EscalationCase[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [reply, setReply] = useState("");
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    if (!user || !apiBase()) return;
    const response = await fetch(
      `${apiBase()}/cases?user_name=${encodeURIComponent(user.name)}&view=assigned`,
    );
    if (!response.ok) throw new Error("Could not load escalation inbox");
    const next = (await response.json()) as EscalationCase[];
    setCases(next);
    setSelectedId((current) => current ?? next[0]?.id ?? null);
  }, [user]);

  useEffect(() => {
    void load().catch(() => toast.error("Could not connect to the escalation inbox."));
    const interval = window.setInterval(() => void load(), 3_000);
    return () => window.clearInterval(interval);
  }, [load]);

  const selected = cases.find((item) => item.id === selectedId) ?? null;

  async function sendReply() {
    if (!user || !selected || !reply.trim()) return;
    setBusy(true);
    try {
      const response = await fetch(`${apiBase()}/cases/${selected.id}/messages`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          sender_id: user.id, sender_name: user.name,
          sender_kind: "expert", content: reply.trim(),
        }),
      });
      if (!response.ok) throw new Error("Reply failed");
      setReply("");
      await load();
      toast.success("Answer sent to the Relationship Manager.");
    } catch {
      toast.error("The answer could not be sent.");
    } finally {
      setBusy(false);
    }
  }

  async function decide(candidateId: string, decision: "accepted" | "rejected") {
    if (!user) return;
    setBusy(true);
    try {
      const response = await fetch(`${apiBase()}/knowledge-candidates/${candidateId}/decision`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ reviewer_name: user.name, decision }),
      });
      if (!response.ok) throw new Error("Decision failed");
      await load();
      toast.success(decision === "accepted" ? "Knowledge added to retrieval." : "Draft rejected.");
    } catch {
      toast.error("The knowledge decision could not be saved.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex min-h-screen bg-background text-foreground">
      <aside className="w-80 border-r border-border bg-surface">
        <div className="border-b border-border p-4">
          <p className="label-xs text-gold">Escalation inbox</p>
          <h1 className="mt-1 text-lg font-medium">{user?.name}</h1>
          <p className="text-xs text-muted-foreground">{user?.role}</p>
        </div>
        <div className="flex items-center justify-between border-b border-border px-4 py-2">
          <span className="label-xs text-muted-foreground">Assigned ({cases.length})</span>
          <button type="button" onClick={() => void load()} className="text-gold">
            <RefreshCw className="size-3.5" />
          </button>
        </div>
        <ul className="p-2">
          {cases.map((item) => (
            <li key={item.id}>
              <button
                type="button"
                onClick={() => setSelectedId(item.id)}
                className={`mb-1 w-full rounded-sm border px-3 py-2.5 text-left ${
                  selectedId === item.id ? "border-gold bg-cream" : "border-border bg-card"
                }`}
              >
                <span className="line-clamp-2 text-sm">{item.question}</span>
                <span className="mt-1 block text-[11px] text-muted-foreground">
                  {item.requester_name} · {item.status}
                </span>
              </button>
            </li>
          ))}
          {cases.length === 0 && (
            <li className="p-4 text-center text-sm text-muted-foreground">No assigned questions.</li>
          )}
        </ul>
        <button type="button" onClick={signOut} className="m-4 flex items-center gap-2 text-xs text-gold">
          <LogOut className="size-3.5" /> Log out
        </button>
      </aside>

      <main className="min-w-0 flex-1 p-6">
        {!selected ? (
          <div className="flex h-full items-center justify-center text-muted-foreground">
            Select an escalation.
          </div>
        ) : (
          <div className="mx-auto max-w-3xl space-y-5">
            <header className="rounded-md border border-border bg-card p-5">
              <div className="flex items-center gap-2 text-gold">
                <ShieldCheck className="size-4" />
                <span className="label-xs">{selected.assigned_tier.replaceAll("_", " ")}</span>
              </div>
              <h2 className="mt-3 text-xl">{selected.question}</h2>
              <p className="mt-1 text-xs text-muted-foreground">Asked by {selected.requester_name}</p>
            </header>

            <section className="space-y-3 rounded-md border border-border bg-card p-5">
              <h3 className="flex items-center gap-2 text-sm font-medium">
                <MessageSquare className="size-4 text-gold" /> Conversation
              </h3>
              {selected.messages.map((message) => (
                <div key={message.id} className="rounded-sm border border-border bg-surface-2 p-3">
                  <p className="text-[11px] text-muted-foreground">{message.sender_name}</p>
                  <p className="mt-1 text-sm">{message.content}</p>
                </div>
              ))}
              {selected.status === "open" && (
                <div className="space-y-2 pt-2">
                  <Textarea
                    value={reply}
                    onChange={(event) => setReply(event.target.value)}
                    placeholder="Write the authoritative answer for the RM…"
                    rows={5}
                  />
                  <Button onClick={() => void sendReply()} disabled={busy || !reply.trim()}>
                    Send answer
                  </Button>
                </div>
              )}
            </section>

            {selected.knowledge_candidate && (
              <section className="rounded-md border border-gold/40 bg-card p-5">
                <p className="label-xs text-gold">LLM-suggested knowledge item</p>
                <h3 className="mt-2 text-lg">{selected.knowledge_candidate.title}</h3>
                <p className="mt-2 text-xs font-medium text-muted-foreground">
                  {selected.knowledge_candidate.question}
                </p>
                <p className="mt-2 text-sm leading-relaxed">{selected.knowledge_candidate.answer}</p>
                <div className="mt-3 flex flex-wrap gap-1">
                  {selected.knowledge_candidate.keywords.map((keyword) => (
                    <span key={keyword} className="rounded-sm border border-border px-2 py-0.5 text-[11px]">
                      {keyword}
                    </span>
                  ))}
                </div>
                {selected.knowledge_candidate.status === "pending" ? (
                  <div className="mt-4 flex gap-2">
                    <Button disabled={busy} onClick={() => void decide(selected.knowledge_candidate!.id, "accepted")}>
                      <Check className="mr-1 size-4" /> Accept and publish
                    </Button>
                    <Button variant="outline" disabled={busy} onClick={() => void decide(selected.knowledge_candidate!.id, "rejected")}>
                      <X className="mr-1 size-4" /> Reject
                    </Button>
                  </div>
                ) : (
                  <p className="mt-4 text-xs font-medium uppercase text-muted-foreground">
                    {selected.knowledge_candidate.status}
                  </p>
                )}
              </section>
            )}
          </div>
        )}
      </main>
    </div>
  );
}
