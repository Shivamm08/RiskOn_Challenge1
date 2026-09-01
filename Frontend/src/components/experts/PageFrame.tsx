import type { ReactNode } from "react";

import { AppShell } from "@/components/suitability/AppShell";

export function PageFrame({
  eyebrow,
  title,
  intro,
  children,
}: {
  eyebrow: string;
  title: string;
  intro?: string;
  children: ReactNode;
}) {
  return (
    <AppShell>
      <div className="min-h-0 flex-1 overflow-y-auto">
        <div className="mx-auto max-w-5xl px-5 py-6">
          <header className="pb-5">
            <p className="label-xs text-gold">{eyebrow}</p>
            <h1 className="mt-1 text-2xl font-medium text-gold">{title}</h1>
            {intro && <p className="mt-1.5 max-w-2xl text-sm text-muted-foreground">{intro}</p>}
          </header>
          {children}
        </div>
      </div>
    </AppShell>
  );
}

export function StatusPill({ status }: { status: string }) {
  const tone =
    status === "pending"
      ? "border-warning/40 bg-warning-surface text-warning"
      : status === "answered"
        ? "border-info/40 bg-info-surface text-info"
        : status === "open"
          ? "border-danger/40 bg-danger-surface text-danger-foreground"
          : "border-success/40 bg-success-surface text-success-foreground";
  return (
    <span
      className={`inline-flex shrink-0 items-center rounded-sm border px-1.5 py-px text-[10px] uppercase tracking-wide ${tone}`}
    >
      {status}
    </span>
  );
}
