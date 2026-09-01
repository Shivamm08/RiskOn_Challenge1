import { Link, useRouterState } from "@tanstack/react-router";
import {
  CheckCircle2,
  ChevronDown,
  Circle,
  FlaskConical,
  LogOut,
  MessageSquare,
  MessagesSquare,
  Plus,
  ScrollText,
} from "lucide-react";
import { useState, type ReactNode } from "react";

import { AddSourceDialog } from "./AddSourceDialog";
import { useAuth } from "@/lib/auth";
import { useSuitability } from "@/lib/suitability/store";
import type { Exchange } from "@/lib/suitability/types";
import { cn } from "@/lib/utils";

const STATUS_DOT: Record<string, string> = {
  answered: "bg-success",
  escalated: "bg-danger",
  clarification_needed: "bg-info",
};

function Section({
  title,
  count,
  open,
  onToggle,
  action,
  children,
}: {
  title: string;
  count: number;
  open: boolean;
  onToggle: () => void;
  action?: ReactNode;
  children: ReactNode;
}) {
  return (
    <div className="border-b border-border py-2">
      <div className="flex items-center gap-1">
        <button
          type="button"
          onClick={onToggle}
          aria-expanded={open}
          className="flex min-w-0 flex-1 items-center justify-between rounded-sm px-2.5 py-1.5 text-left transition-colors hover:bg-surface-2"
        >
          <span className="label-xs text-gold">
            {title} <span className="text-muted-foreground">({count})</span>
          </span>
          <ChevronDown
            className={cn(
              "size-3.5 text-muted-foreground transition-transform",
              open && "rotate-180",
            )}
          />
        </button>
        {action}
      </div>
      {open && <div className="pt-1">{children}</div>}
    </div>
  );
}

function ExchangeLink({ exchange, onSelect }: { exchange: Exchange; onSelect: () => void }) {
  return (
    <li>
      <Link
        to="/"
        hash={exchange.id}
        onClick={onSelect}
        className="flex items-start gap-2 rounded-sm px-2.5 py-2 text-left text-xs leading-snug text-muted-foreground transition-colors hover:bg-surface-2 hover:text-foreground"
      >
        <span
          className={cn(
            "mt-1 size-1.5 shrink-0 rounded-full",
            STATUS_DOT[exchange.response.status],
          )}
        />
        <span className="min-w-0">
          <span className="line-clamp-2">{exchange.question}</span>
          <span className="mt-1 inline-flex items-center gap-1 rounded-sm border border-gold/50 px-1 py-px text-[10px] uppercase tracking-wide text-gold">
            <FlaskConical className="size-2.5" /> Demo
          </span>
        </span>
      </Link>
    </li>
  );
}

export function AppSidebar() {
  const {
    demoExchanges,
    chats,
    activeChatId,
    startNewChat,
    selectChat,
    showDemo,
    knowledgeSources,
  } = useSuitability();
  const { user, signOut } = useAuth();
  const pathname = useRouterState({ select: (s) => s.location.pathname });
  const [demoOpen, setDemoOpen] = useState(true);
  const [chatsOpen, setChatsOpen] = useState(true);

  const orderedChats = [...chats].reverse();

  return (
    <aside className="flex h-full w-72 shrink-0 flex-col border-r border-border bg-surface">
      <div className="border-b border-border px-4 py-4">
        <p className="label-xs text-gold">Julius Baer · Internal</p>
        <h1 className="mt-1 text-lg font-medium leading-tight text-gold">Suitability Copilot</h1>
      </div>

      <nav className="space-y-1 px-2 py-3">
        <Link
          to="/"
          className={cn(
            "flex items-center gap-2.5 rounded-sm px-2.5 py-2 text-sm font-medium text-gold transition-colors",
            pathname === "/" ? "bg-cream border border-gold/40" : "hover:bg-surface-2",
          )}
        >
          <MessagesSquare className="size-4" /> Copilot
        </Link>
        <Link
          to="/audit"
          className={cn(
            "flex items-center gap-2.5 rounded-sm px-2.5 py-2 text-sm font-medium text-gold transition-colors",
            pathname === "/audit" ? "bg-cream border border-gold/40" : "hover:bg-surface-2",
          )}
        >
          <ScrollText className="size-4" /> Audit trail
        </Link>
      </nav>

      <div className="min-h-0 flex-1 overflow-y-auto border-t border-border px-2">
        <Section
          title="Demo"
          count={demoExchanges.length}
          open={demoOpen}
          onToggle={() => setDemoOpen((v) => !v)}
        >
          <ul className="space-y-0.5">
            {demoExchanges.map((exchange) => (
              <ExchangeLink key={exchange.id} exchange={exchange} onSelect={showDemo} />
            ))}
          </ul>
        </Section>

        <Section
          title="Chats"
          count={chats.length}
          open={chatsOpen}
          onToggle={() => setChatsOpen((v) => !v)}
          action={
            <button
              type="button"
              onClick={() => {
                setChatsOpen(true);
                startNewChat();
              }}
              aria-label="New chat"
              title="New chat"
              className="mr-1 rounded-sm border border-border p-1 text-gold transition-colors hover:border-gold"
            >
              <Plus className="size-3.5" />
            </button>
          }
        >
          {orderedChats.length === 0 ? (
            <p className="px-2.5 py-2 text-xs text-muted-foreground">
              No chats yet. Press + to start one.
            </p>
          ) : (
            <ul className="space-y-0.5">
              {orderedChats.map((chat) => (
                <li key={chat.id}>
                  <Link
                    to="/"
                    onClick={() => selectChat(chat.id)}
                    className={cn(
                      "flex items-start gap-2 rounded-sm px-2.5 py-2 text-left text-xs leading-snug transition-colors hover:bg-surface-2 hover:text-foreground",
                      chat.id === activeChatId
                        ? "bg-surface-2 text-foreground"
                        : "text-muted-foreground",
                    )}
                  >
                    <MessageSquare className="mt-0.5 size-3.5 shrink-0" />
                    <span className="line-clamp-2 min-w-0">{chat.title}</span>
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </Section>
      </div>

      <div className="border-t border-border px-4 py-3">
        <p className="label-xs pb-2 text-muted-foreground">Knowledge sources connected</p>
        <ul className="space-y-1.5 text-xs">
          {knowledgeSources.map((source) => (
            <li
              key={source.ref + source.name}
              className={cn("flex items-center gap-2", !source.connected && "text-muted-foreground")}
            >
              {source.connected ? (
                <CheckCircle2 className="size-3.5 shrink-0 text-success" />
              ) : (
                <Circle className="size-3.5 shrink-0" />
              )}
              <span className="line-clamp-1">{source.name}</span>
            </li>
          ))}
        </ul>
        <AddSourceDialog />
      </div>

      <div className="flex items-center justify-between gap-2 border-t border-border px-4 py-3">
        <span className="min-w-0 text-xs text-muted-foreground">
          <span className="line-clamp-1">
            {user ? `${user.name}${user.role ? ` · ${user.role}` : ""}` : "Not signed in"}
          </span>
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
