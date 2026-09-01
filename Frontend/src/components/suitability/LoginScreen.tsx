import { Moon, ShieldCheck, Sun, UserCircle2 } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { DEMO_USERS, useAuth } from "@/lib/auth";
import { useTheme } from "@/lib/theme";

export function LoginScreen() {
  const { signIn } = useAuth();
  const { theme, toggle } = useTheme();
  const [name, setName] = useState("");
  const [role, setRole] = useState("");
  const [password, setPassword] = useState("");

  return (
    <div className="flex min-h-screen flex-col bg-background">
      <header className="flex items-center justify-end border-b border-border bg-surface px-3 py-2">
        <button
          type="button"
          onClick={toggle}
          aria-label="Toggle colour mode"
          className="rounded-sm border border-border p-1.5 text-gold transition-colors hover:border-gold"
        >
          {theme === "dark" ? <Sun className="size-3.5" /> : <Moon className="size-3.5" />}
        </button>
      </header>

      <main className="flex flex-1 items-center justify-center px-5 py-10">
        <div className="w-full max-w-md rounded-md border border-border bg-card p-6">
          <p className="label-xs text-gold">Julius Baer · Internal</p>
          <h1 className="mt-1 text-2xl font-medium text-gold">Suitability Copilot</h1>
          <p className="mt-2 text-sm text-muted-foreground">
            Demo sign-in. No credentials are verified — this environment holds no client data.
          </p>

          <div className="mt-6">
            <p className="label-xs mb-2 text-muted-foreground">Quick demo sign-in</p>
            <div className="space-y-1.5">
              {DEMO_USERS.map((u) => (
                <button
                  key={u.name}
                  type="button"
                  onClick={() => signIn(u)}
                  className="flex w-full items-center gap-2.5 rounded-sm border border-border bg-surface-2 px-3 py-2.5 text-left transition-colors hover:border-gold"
                >
                  <UserCircle2 className="size-4 shrink-0 text-gold" />
                  <span className="min-w-0">
                    <span className="block text-sm font-medium">{u.name}</span>
                    <span className="block text-xs text-muted-foreground">{u.role}</span>
                  </span>
                </button>
              ))}
            </div>
          </div>

          <form
            className="mt-6 space-y-2.5 border-t border-border pt-5"
            onSubmit={(e) => {
              e.preventDefault();
              if (!name.trim()) return;
              signIn({ name: name.trim(), role: role.trim() || "Relationship Manager" });
            }}
          >
            <p className="label-xs text-muted-foreground">Or sign in manually</p>
            <Input
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Full name"
              autoComplete="name"
            />
            <Input
              value={role}
              onChange={(e) => setRole(e.target.value)}
              placeholder="Role (e.g. RM, Zurich)"
            />
            <Input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Password (not checked in demo)"
              autoComplete="current-password"
            />
            <Button type="submit" className="w-full" disabled={!name.trim()}>
              Sign in
            </Button>
            <p className="flex items-start gap-1.5 pt-1 text-[11px] text-muted-foreground">
              <ShieldCheck className="mt-px size-3 shrink-0" />
              Demo only — any password is accepted.
            </p>
          </form>
        </div>
      </main>
    </div>
  );
}
