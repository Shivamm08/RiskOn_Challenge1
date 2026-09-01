import { useNavigate } from "@tanstack/react-router";
import { Bell, BookOpenCheck, MessageSquare } from "lucide-react";
import { useState } from "react";

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useAuth } from "@/lib/auth";
import { getExpert } from "@/lib/experts/roster";
import { useExperts, type Notification } from "@/lib/experts/store";
import { cn } from "@/lib/utils";

function when(iso: string) {
  return new Date(iso).toLocaleString(undefined, {
    day: "2-digit",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function NotificationBell() {
  const { user } = useAuth();
  const {
    notificationsFor,
    markNotificationsRead,
    markNotificationRead,
    triggerDemoKbNotification,
    kbEntries,
  } = useExperts();
  const navigate = useNavigate();
  const [kbOpen, setKbOpen] = useState<Notification | null>(null);
  if (!user) return null;

  const list = notificationsFor({
    kind: user.kind,
    ...(user.expertId ? { expertId: user.expertId } : {}),
  });
  const unread = list.filter((n) => !n.read).length;

  const kbEntry = kbOpen
    ? (kbOpen.kbEntryId ? kbEntries.find((e) => e.id === kbOpen.kbEntryId) : undefined) ??
      kbEntries[0]
    : undefined;
  const kbAuthor = getExpert(kbEntry?.expertId);

  const handleClick = (n: Notification) => {
    markNotificationRead(n.id);
    if (n.kind === "kb") {
      setKbOpen(n);
      return;
    }
    void navigate({
      to: "/messages",
      ...(n.messageId ? { search: { m: n.messageId } } : {}),
    });
  };

  return (
    <>
      <DropdownMenu onOpenChange={(open) => open && setTimeout(markNotificationsRead, 1200)}>
        <DropdownMenuTrigger
          aria-label={`Notifications (${unread} unread)`}
          className="relative rounded-sm border border-border p-1.5 text-gold transition-colors hover:border-gold"
        >
          <Bell className="size-3.5" />
          {unread > 0 && (
            <span className="absolute -right-1.5 -top-1.5 flex size-4 items-center justify-center rounded-full bg-danger font-mono text-[9px] font-medium text-primary-foreground">
              {unread}
            </span>
          )}
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end" className="w-80 p-0">
          <div className="flex items-center justify-between border-b border-border px-3 py-2">
            <span className="label-xs text-gold">Notifications</span>
            <button
              type="button"
              onClick={triggerDemoKbNotification}
              className="rounded-sm border border-border px-1.5 py-0.5 text-[10px] text-muted-foreground transition-colors hover:border-gold hover:text-gold"
            >
              Trigger KB update (demo)
            </button>
          </div>
          <ul className="max-h-80 overflow-y-auto">
            {list.length === 0 && (
              <li className="px-3 py-6 text-center text-xs text-muted-foreground">
                No notifications yet.
              </li>
            )}
            {list.map((n) => (
              <li key={n.id} className="border-b border-border last:border-0">
                <button
                  type="button"
                  onClick={() => handleClick(n)}
                  className="flex w-full gap-2.5 px-3 py-2.5 text-left transition-colors hover:bg-surface-2"
                >
                  <span className="mt-0.5 shrink-0 text-gold">
                    {n.kind === "kb" ? (
                      <BookOpenCheck className="size-3.5" />
                    ) : (
                      <MessageSquare className="size-3.5" />
                    )}
                  </span>
                  <span className="min-w-0 flex-1">
                    <span className="block text-xs font-medium leading-snug">{n.title}</span>
                    <span className="mt-0.5 line-clamp-2 block text-[11px] leading-snug text-muted-foreground">
                      {n.body}
                    </span>
                    <span className="mt-1 block font-mono text-[10px] text-muted-foreground">
                      {when(n.at)} · {n.kind === "kb" ? "View KB entry" : "Open message"}
                    </span>
                  </span>
                  <span
                    className={cn(
                      "mt-1 size-1.5 shrink-0 rounded-full",
                      n.read ? "bg-transparent" : "bg-danger",
                    )}
                  />
                </button>
              </li>
            ))}
          </ul>
        </DropdownMenuContent>
      </DropdownMenu>

      <Dialog open={!!kbOpen} onOpenChange={(open) => !open && setKbOpen(null)}>
        <DialogContent className="max-w-xl">
          <DialogHeader>
            <DialogTitle className="text-gold">Added to the knowledge base</DialogTitle>
            <DialogDescription>
              {kbEntry
                ? `Contributed by ${kbAuthor?.name ?? "an expert"}${
                    kbAuthor ? ` · ${kbAuthor.rank}, ${kbAuthor.office}` : ""
                  } · ${when(kbEntry.publishedAt)}`
                : "This contribution is no longer available."}
            </DialogDescription>
          </DialogHeader>
          {kbEntry && (
            <div className="space-y-3">
              <div className="rounded-sm border border-border bg-surface-2 px-3 py-2.5">
                <p className="label-xs text-muted-foreground">Question</p>
                <p className="mt-1 text-sm leading-relaxed">{kbEntry.question}</p>
              </div>
              <div className="rounded-sm border border-success/40 bg-success-surface px-3 py-2.5">
                <p className="label-xs text-success-foreground">Expert answer</p>
                <p className="mt-1 text-sm leading-relaxed">{kbEntry.answer}</p>
              </div>
              <p className="text-[11px] text-muted-foreground">
                Filed under {kbEntry.sourceTitle} · {kbEntry.endorsedBy.length} peer endorsement
                {kbEntry.endorsedBy.length === 1 ? "" : "s"}
              </p>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </>
  );
}
