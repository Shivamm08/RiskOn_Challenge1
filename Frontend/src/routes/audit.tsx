import { createFileRoute } from "@tanstack/react-router";

import { AppShell } from "@/components/suitability/AppShell";
import { AuditTrailTable } from "@/components/suitability/AuditTrailTable";

const title = "Audit Trail — Suitability Copilot";
const description =
  "Compliance review log of every suitability question asked: sources cited, confidence scores, escalation reasoning and resolutions.";

export const Route = createFileRoute("/audit")({
  head: () => ({
    meta: [
      { title },
      { name: "description", content: description },
      { property: "og:title", content: title },
      { property: "og:description", content: description },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
      { name: "robots", content: "noindex" },
    ],
  }),
  component: AuditPage,
});

function AuditPage() {
  return (
    <AppShell>
      <div className="min-h-0 flex-1 overflow-y-auto">
        <div className="mx-auto max-w-6xl px-5 py-6">
          <header className="pb-5">
            <p className="label-xs text-gold">Compliance review</p>
            <h1 className="mt-1 text-2xl font-medium text-gold">Audit trail &amp; source log</h1>
            <p className="mt-1.5 max-w-2xl text-sm text-muted-foreground">
              Every question asked through the Copilot, with the exact excerpts relied upon, the
              confidence reported at the time, and the full escalation and resolution record.
            </p>
          </header>
          <AuditTrailTable />
        </div>
      </div>
    </AppShell>
  );
}
