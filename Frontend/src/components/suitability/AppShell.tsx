import { Menu, Moon, Sun } from "lucide-react";
import { useState, type ReactNode } from "react";

import { Sheet, SheetContent, SheetTitle, SheetTrigger } from "@/components/ui/sheet";
import { NotificationBell } from "@/components/experts/NotificationBell";
import { ExpertSidebar } from "@/components/experts/ExpertSidebar";
import { useAuth } from "@/lib/auth";
import { useTheme } from "@/lib/theme";
import { AppSidebar } from "./AppSidebar";
import { SourcePreviewDialog } from "./SourcePreviewDialog";

export function AppShell({ children }: { children: ReactNode }) {
  const [open, setOpen] = useState(false);
  const { theme, toggle } = useTheme();
  const { user } = useAuth();

  const Sidebar = user?.kind === "expert" ? ExpertSidebar : AppSidebar;

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      <div className="hidden lg:block">
        <Sidebar />
      </div>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex items-center gap-3 border-b border-border bg-surface px-3 py-2">
          <Sheet open={open} onOpenChange={setOpen}>
            <SheetTrigger
              aria-label="Open navigation"
              className="rounded-sm border border-border p-1.5 text-muted-foreground lg:hidden"
            >
              <Menu className="size-4" />
            </SheetTrigger>
            <SheetContent side="left" className="w-72 p-0">
              <SheetTitle className="sr-only">Navigation</SheetTitle>
              <Sidebar />
            </SheetContent>
          </Sheet>
          <span className="text-sm font-medium text-gold lg:hidden">Suitability Copilot</span>

          <div className="ml-auto flex items-center gap-2">
            <span className="hidden text-[11px] text-muted-foreground sm:inline">
              {theme === "dark" ? "Gold on charcoal" : "Crimson on cream"}
            </span>
            <NotificationBell />
            <button
              type="button"
              onClick={toggle}
              aria-label="Toggle colour mode"
              className="rounded-sm border border-border p-1.5 text-gold transition-colors hover:border-gold"
            >
              {theme === "dark" ? <Sun className="size-3.5" /> : <Moon className="size-3.5" />}
            </button>
          </div>
        </header>

        {children}
        <SourcePreviewDialog />
      </div>
    </div>
  );
}
