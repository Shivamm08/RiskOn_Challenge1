import type { QueryContext } from "@/lib/suitability/types";

function contextSummary(context: QueryContext) {
  return [context.bookingCentre, context.clientCategory, context.serviceModel]
    .filter(Boolean)
    .join(" · ");
}

export function MessageBubble({
  question,
  context,
  askedAt,
}: {
  question: string;
  context: QueryContext;
  askedAt: string;
}) {
  const summary = contextSummary(context);
  const time = new Date(askedAt).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

  return (
    <div className="flex justify-end">
      <div className="max-w-[85%] rounded-md rounded-br-none border border-gold/30 bg-cream px-3.5 py-2.5 text-cream-foreground">
        <p className="text-sm leading-relaxed">{question}</p>
        <p className="mt-1.5 flex flex-wrap items-center gap-x-2 font-mono text-[10px] text-cream-foreground/70">
          <span>{time}</span>
          {summary && <span>· {summary}</span>}
        </p>
      </div>
    </div>
  );
}
