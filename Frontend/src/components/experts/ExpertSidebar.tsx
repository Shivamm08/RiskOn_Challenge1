import { Link, useRouterState } from "@tanstack/react-router";
import { BookOpenCheck, Gauge, Inbox, LogOut, ScrollText, ShieldAlert } from "lucide-react";

import { useAuth } from "@/lib/auth";
import { getExpert, localTimeLabel, supervisorOf } from "@/lib/experts/roster";
import { useExperts } from "@/lib/experts/store";
import { cn } from "@/lib/utils";

const NAV = [
  { to: "/expert", label: "Inbox", icon: Inbox },
  { to: "/expert/favorability", label: "Favorability & ranking", icon: Gauge },
  { to: "/expert/kb", label: "Recently added to KB", icon: BookOpenCheck },
  { to: "/expert/reviews", label: "Supervisor reviews", icon: ShieldAlert },
  { to: "/expert/audit", label: "Audit trail", icon: ScrollText },
] as const;

export function ExpertSidebar() {
  const { user, signOut } = useAuth();
  const pathname = useRouterState({ select: (s) => s.location.pathname });
  const { messages, reviews, favorabilityOf } = useExperts();

  const expert = getExpert(user?.expertId);
  const supervisor = expert ? supervisorOf(expert) : undefined;
  const pending = messages.filter((m) => m.expertId === expert?.id && m.status === "pending").length;
  const openReviews = reviews.filter(
    (r) => r.supervisorId === expert?.id && r.status === "open",
  ).length;

  return (
    <aside className="flex h-full w-72 shrink-0 flex-col border-r border-border bg-surface">
      <div className="border-b border-border px-4 py-4">
        <p className="label-xs text-gold">Julius Baer · Expert Portal</p>
        <h1 className="mt-1 text-lg font-medium leading-tight text-gold">Suitability Copilot</h1>
      </div>

      {expert && (
        <div className="border-b border-border px-4 py-3">
          <div className="flex items-center gap-2.5">
            <span className="flex size-9 shrink-0 items-center justify-center rounded-full bg-cream text-xs font-medium text-cream-foreground">
              {expert.initials}
            </span>
            <div className="min-w-0">
              <p className="truncate text-sm font-medium">{expert.name}</p>
              <p className="truncate text-[11px] text-muted-foreground">{expert.title}</p>
            </div>
          </div>
          <p className="mt-2 font-mono text-[11px] text-muted-foreground">
            {localTimeLabel(expert)} · favorability {favorabilityOf(expert)}/100
          </p>
          {supervisor && (
            <p className="mt-1 text-[11px] text-muted-foreground">
              Supervisor: {supervisor.name} ({supervisor.rank})
            </p>
          )}
        </div>
      )}

      <nav className="min-h-0 flex-1 space-y-1 overflow-y-auto px-2 py-3">
        {NAV.map(({ to, label, icon: Icon }) => {
          const badge = to === "/expert" ? pending : to === "/expert/reviews" ? openReviews : 0;
          return (
            <Link
              key={to}
              to={to}
              className={cn(
                "flex items-center gap-2.5 rounded-sm px-2.5 py-2 text-sm font-medium text-gold transition-colors",
                pathname === to ? "bg-cream border border-gold/40" : "hover:bg-surface-2",
              )}
            >
              <Icon className="size-4" />
              <span className="min-w-0 flex-1 truncate">{label}</span>
              {badge > 0 && (
                <span className="rounded-full bg-danger px-1.5 font-mono text-[10px] text-primary-foreground">
                  {badge}
                </span>
              )}
            </Link>
          );
        })}
      </nav>

      <div className="flex items-center justify-between gap-2 border-t border-border px-4 py-3">
        <span className="min-w-0 text-xs text-muted-foreground">
          <span className="line-clamp-1">{user?.role ?? "Expert"}</span>
        </span>
        <button
          type="button"
          onClick={signOut}
          className="flex shrink-0 items-center gap-1 rounded-sm border border-border px-2 py-1 text-[11px] text-gold transition-colors hover:border-gold"
        >
          <LogOut className="size-3" /> Log out
        </button>
      </div>
    </aside>
  );
}
