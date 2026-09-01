import { X } from "lucide-react";

import { rmProfileFor, type DemoUser } from "@/lib/auth";

export function RmProfilePanel({ user, onClose }: { user: DemoUser; onClose: () => void }) {
  const profile = rmProfileFor(user.name);

  return (
    <aside className="fixed right-0 top-0 z-40 h-full w-72 overflow-y-auto border-l border-border bg-card p-4 shadow-lg">
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <p className="label-xs text-gold">Your profile</p>
          <p className="mt-1 text-sm font-medium">{user.name}</p>
          <p className="text-xs text-muted-foreground">{user.role}</p>
        </div>
        <button
          type="button"
          onClick={onClose}
          aria-label="Close profile"
          className="rounded-sm border border-border p-1 text-muted-foreground transition-colors hover:border-gold hover:text-gold"
        >
          <X className="size-3.5" />
        </button>
      </div>

      <dl className="mt-4 space-y-2.5 text-xs">
        <div>
          <dt className="label-xs text-muted-foreground">Office</dt>
          <dd className="mt-0.5">{profile.office}</dd>
        </div>
        <div>
          <dt className="label-xs text-muted-foreground">Years at Julius Baer</dt>
          <dd className="mt-0.5 font-mono">{profile.yearsAtJb}</dd>
        </div>
        <div>
          <dt className="label-xs text-muted-foreground">Typical client segment</dt>
          <dd className="mt-0.5">{profile.clientSegment}</dd>
        </div>
        <div>
          <dt className="label-xs text-muted-foreground">Languages</dt>
          <dd className="mt-0.5">{profile.languages.join(", ")}</dd>
        </div>
        <div>
          <dt className="label-xs text-muted-foreground">Specialization</dt>
          <dd className="mt-0.5">{profile.specialization}</dd>
        </div>
      </dl>

      <p className="mt-4 border-t border-border pt-3 text-[10px] text-muted-foreground">
        Demo profile data. Read-only.
      </p>
    </aside>
  );
}
