import { cn } from "@/lib/utils";

export function ConfidenceBadge({
  value,
  label = "Confidence",
  className,
}: {
  value: number;
  label?: string;
  className?: string;
}) {
  const pct = Math.round(value * 100);
  const high = value >= 0.85;
  const tone = high ? "text-success" : "text-warning";
  const bar = high ? "bg-success" : "bg-warning";

  return (
    <div className={cn("flex items-center gap-2", className)}>
      <span className="label-xs text-muted-foreground">{label}</span>
      <div className="h-1.5 w-20 overflow-hidden rounded-full bg-muted">
        <div className={cn("h-full rounded-full", bar)} style={{ width: `${pct}%` }} />
      </div>
      <span className={cn("font-mono text-xs font-medium tabular-nums", tone)}>{pct}%</span>
    </div>
  );
}
