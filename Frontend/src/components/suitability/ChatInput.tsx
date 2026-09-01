import { CornerDownLeft, Send } from "lucide-react";
import { useEffect, useRef, useState } from "react";

import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { EXAMPLE_QUESTIONS } from "@/lib/suitability/seed";
import { useSuitability } from "@/lib/suitability/store";

export function ChatInput() {
  const { ask, pendingQuestion } = useSuitability();
  const [value, setValue] = useState("");
  const ref = useRef<HTMLTextAreaElement>(null);
  const busy = pendingQuestion !== null;

  useEffect(() => {
    if (!busy) ref.current?.focus();
  }, [busy]);

  const submit = (question: string) => {
    if (!question.trim() || busy) return;
    setValue("");
    void ask(question);
  };

  return (
    <div className="space-y-2.5">
      <form
        onSubmit={(e) => {
          e.preventDefault();
          submit(value);
        }}
        className="relative"
      >
        <Textarea
          ref={ref}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              submit(value);
            }
          }}
          rows={2}
          disabled={busy}
          placeholder="Ask a suitability or compliance question…"
          className="min-h-[76px] resize-none bg-surface pr-14 text-sm leading-relaxed"
        />
        <Button
          type="submit"
          size="icon"
          disabled={busy || !value.trim()}
          aria-label="Send question"
          className="absolute bottom-2.5 right-2.5"
        >
          <Send className="size-4" />
        </Button>
      </form>

      <div className="flex flex-wrap items-center gap-1.5">
        <span className="label-xs mr-1 flex items-center gap-1 text-muted-foreground">
          <CornerDownLeft className="size-3" /> Enter to send
        </span>
        {EXAMPLE_QUESTIONS.map((q) => (
          <button
            key={q}
            type="button"
            disabled={busy}
            onClick={() => submit(q)}
            className="rounded-sm border border-border bg-surface-2 px-2 py-1 text-[11px] text-muted-foreground transition-colors hover:border-gold/60 hover:text-foreground disabled:opacity-50"
          >
            {q}
          </button>
        ))}
      </div>
    </div>
  );
}
